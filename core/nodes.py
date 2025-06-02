import os
import re
import subprocess
import sys
import tempfile
import time
import logging

from e2b_code_interpreter import Sandbox

from config import (MAX_CODE_TIMEOUT,
                    MAX_RETRY_ITERATIONS,
                    E2B_API_KEY,
                    ALLOW_LOCAL_EXECUTION)
from core.interaction import call_llm_with_tool
from core.state_models import GraphState, CodeSolution, PythonCode
from core.prompts import (PROMPT_OPTIMIZATION_SYSTEM_PROMPT,
                          CODE_GENERATION_PROMPT,
                          get_code_optimization_user_prompt)


logger = logging.getLogger(__name__)


def optimize_prompt(state: GraphState) -> GraphState:
    """
    Takes the initial user question and refines it into a detailed prompt 
    for the code generator. Should be used as the first node in the graph.
    """
    logger.info("NODE: optimize_prompt")
    question = state["initial_question"]

    user_prompt = get_code_optimization_user_prompt(question)

    messages = [
        {"role": "system", "content": PROMPT_OPTIMIZATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    instance, error = call_llm_with_tool(messages, CodeSolution)

    if error:
        logger.error(f"LLM call for prompt optimization failed: {error}")
        return {**state, "error_message": error}

    logger.info("Prompt optimized successfully.")
    return {
        **state,
        "optimized_prompt": instance.optimized_prompt,
        "feedback_history": [f"Reasoning for prompt optimization: {instance.reasoning}"]
    }


def generate_code(state: GraphState) -> GraphState:
    """
    Generates Python code based on the optimized prompt. 
    Incorporates feedback from previous failed runs.
    """
    logger.info(f"NODE: code_generate (Iteration {state['iteration'] + 1})")

    system_prompt = CODE_GENERATION_PROMPT

    feedback_message = "\n".join(state['feedback_history'])
    user_prompt = f"USER PROMPT:\n{state['optimized_prompt']}\n\nPREVIOUS ATTEMPTS FEEDBACK:\n{feedback_message}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    instance, error = call_llm_with_tool(messages, PythonCode)

    if error:
        logger.error(f"Code generation by LLM failed: {error}")
        return {**state, "error_message": error}

    logger.info("Code generated successfully.")
    return {**state,
            "generation": instance,
            "iteration": state["iteration"] + 1}


def execute_code(state: GraphState) -> GraphState:
    """
    Executes the generated code in a secure E2B sandbox environment or falls back to local execution.
    """
    logger.info("NODE: code_execute")

    code_gen = state.get("generation")
    if not code_gen:
        logger.error("Code generation was skipped or failed prior to execution.")
        return {**state,
                "error_message": "Code generation was skipped or failed."}

    imports = re.sub(r"```python\n|```", "", code_gen.imports).strip()
    code = re.sub(r"```python\n|```", "", code_gen.code).strip()
    full_code = f"{imports}\n\n{code}"
    logger.debug(f"Prepared Code for execution:\n---\n{full_code}\n---")

    return _execute_with_e2b(state, full_code, imports)


def _execute_with_e2b(state: GraphState, full_code: str, imports: str) -> GraphState:
    """Execute code using E2B Sandbox"""
    logger.info("Attempting E2B Sandbox for code execution...")

    libs = set(re.findall(r'^\s*(?:import|from)\s+([\w\d_]+)', imports, re.MULTILINE))

    max_sandbox_retries = 3
    for attempt in range(max_sandbox_retries):
        try:
            sandbox_lifecycle_timeout = MAX_CODE_TIMEOUT
            logger.info("Initializing E2B sandbox with template, " +
                        f"lifecycle timeout {sandbox_lifecycle_timeout}" +
                        f"s (attempt {attempt + 1}/{max_sandbox_retries})...")

            with Sandbox(
                api_key=E2B_API_KEY,
                timeout=sandbox_lifecycle_timeout
            ) as sandbox:
                logger.info("Sandbox initialized successfully.")

                if libs:
                    logger.info(f"Installing required libraries in sandbox: {libs}")
                    for lib in libs:
                        pip_install_op_timeout = 120 
                        try:
                            logger.info(f"Installing {lib} in sandbox...")
                            install_cmd = (
                                f"import subprocess, sys; "
                                f"proc = subprocess.run([sys.executable, '-m', 'pip', 'install', '{lib}'], capture_output=True, text=True, check=False); "
                                f"sys.stdout.write(proc.stdout); sys.stdout.flush(); "
                                f"sys.stderr.write(proc.stderr); sys.stderr.flush(); "
                                f"exit(proc.returncode)"
                            )
                            install_result = sandbox.run_code(
                                install_cmd,
                                timeout=pip_install_op_timeout
                            )

                            if install_result.error:
                                error_message = str(install_result.error)
                                pip_stdout_list = install_result.logs.stdout if install_result.logs.stdout else ""
                                pip_stderr_list = install_result.logs.stderr if install_result.logs.stderr else ""
                                logger.warning(f"Failed to install {lib}" + 
                                               "in sandbox. Sandbox Error: " +
                                               f"{error_message}")
                                if pip_stdout_list:
                                    for pip_stdout in pip_stdout_list:
                                        print(f"    Pip stdout: {pip_stdout}")
                                if pip_stderr_list:
                                    for pip_stderr in pip_stderr_list:
                                        print(f"    Pip stderr: {pip_stderr}")
                            else:
                                logger.info("Successfully installed " + 
                                            f"{lib} in sandbox.")
                                if install_result.logs.stdout:
                                    logger.info(f"Pip stdout: {install_result.logs.stdout}")
                                if install_result.logs.stderr:
                                    logger.warning(f"Pip stderr (warnings/info): {install_result.logs.stderr}")

                        except Exception as e:
                            logger.warning(f"Exception while trying to install {lib}: {e}")

                logger.info("Executing main code in E2B sandbox...")
                execution = sandbox.run_code(
                    full_code,
                    timeout=MAX_CODE_TIMEOUT
                )

                if execution.error:
                    error_output = str(execution.error)
                    if hasattr(execution.error, 'traceback') and isinstance(execution.error.traceback, list):
                        error_output += "\nTraceback:\n" + "\n".join(execution.error.traceback)
                    if hasattr(execution.logs, 'stderr') and execution.logs.stderr:
                        error_output += "\nStderr from execution:\n" + str(execution.logs.stderr)
                    logger.error(f"Code execution in sandbox resulted in an error:\n---\n{error_output}\n---")
                    feedback = f"Your code failed to execute. Error:\n{error_output}"
                    return {**state,
                            "error_message": "Execution failed with sandbox error.",
                            "feedback_history": state["feedback_history"] + [feedback]}
                else:
                    logger.info("Code executed successfully in sandbox " +
                                "(from sandbox perspective).")
                    output_parts = []
                    if execution.logs.stdout:
                        output_parts.extend(execution.logs.stdout)

                    final_output = "\n".join(output_parts).strip() if output_parts else "Code executed successfully (no direct stdout)"

                    if execution.logs.stderr:
                        logger.info(f"Execution Stderr from sandbox (may contain warnings or script errors):\n---\n{execution.logs.stderr}\n---")

                    logger.info(f"Execution Output from sandbox (stdout):\n---\n{final_output}\n---")
                    return {**state,
                            "execution_result": final_output,
                            "error_message": None}

        except Exception as e:
            error_msg = str(e)
            logger.error(f"E2B operation failed (attempt {attempt + 1}/{max_sandbox_retries}): {error_msg}", exc_info=True)

            if "port is not open" in error_msg.lower() or "sandbox" in error_msg.lower() or "502" in error_msg:
                if attempt < max_sandbox_retries - 1:
                    logger.warning("Sandbox connection/initialization " +
                                   "failed. Retrying in 5 seconds...")
                    time.sleep(5)
                    continue
                elif ALLOW_LOCAL_EXECUTION:
                    logger.error("Failed to connect to/initialize " +
                                 "sandbox after multiple attempts. " +
                                 "Falling back to local execution if possible.")
                    return _execute_locally(state, full_code)
            elif "timeout" in error_msg.lower() and "sandbox.run_code" not in error_msg.lower():
                logger.error("Sandbox lifecycle timeout.")
                feedback = "The code execution environment took too " +\
                    "long to initialize or operate (overall timeout " +\
                    f"{sandbox_lifecycle_timeout}s)."
                return {**state,
                        "error_message": "Sandbox lifecycle timeout.",
                        "feedback_history": state["feedback_history"] + [feedback]}
            else:
                if attempt < max_sandbox_retries - 1:
                    logger.warning("Unexpected E2B error. " +
                                   "Retrying in 5 seconds...")
                    time.sleep(5)
                    continue
                else:
                    logger.error("An unexpected error occurred with " +
                                 "E2B after retries. Falling back " +
                                 "to local execution.")
                    return _execute_locally(state, full_code)

    logger.critical("All E2B attempts failed. Falling back to local execution.")
    return _execute_locally(state, full_code)


def _execute_locally(state: GraphState, full_code: str) -> GraphState:
    """Fallback local execution method"""
    logger.warning("Using local execution (WARNING: Less secure than sandbox).")

    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(full_code)
            temp_file_path = f.name

        logger.info("Executing code locally from " +
                    f"temporary file: {temp_file_path}...")
        result = subprocess.run(
            [sys.executable, temp_file_path],
            capture_output=True,
            text=True,
            timeout=MAX_CODE_TIMEOUT,
            check=False
        )

        if result.returncode != 0:
            error_output = result.stderr.strip() or "Unknown error occurred during local execution"
            logger.error(f"Local code execution failed with return code {result.returncode}.\nError:\n---\n{error_output}\n---")
            feedback = f"Your code failed to execute locally. Error:\n{error_output}"
            return {**state,
                    "error_message": "Local execution failed.",
                    "feedback_history": state["feedback_history"] + [feedback]}
        else:
            output = result.stdout.strip() or "Code executed successfully locally (no output)"
            logger.info("Local code executed successfully.\n" +
                        f"Output:\n---\n{output}\n---")
            if result.stderr.strip():
                logger.info("Local Execution Stderr (warnings/info):\n" +
                            f"---\n{result.stderr.strip()}\n---")
            return {**state,
                    "execution_result": output,
                    "error_message": None}

    except subprocess.TimeoutExpired:
        logger.error("Local code execution timed out " +
                     "after {MAX_CODE_TIMEOUT} seconds.")
        feedback = f"Your code took longer than {MAX_CODE_TIMEOUT} " +\
            "seconds to run and was terminated. " + \
            "Please optimize for performance."
        return {**state,
                "error_message": "Local execution timed out.",
                "feedback_history": state["feedback_history"] + [feedback]}
    except Exception as e:
        logger.error(f"Local execution failed with an unexpected error: {e}",
                     exc_info=True)
        feedback = f"The code could not be executed locally due to an error: {e}"
        return {**state,
                "error_message": str(e),
                "feedback_history": state["feedback_history"] + [feedback]}
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.debug(f"Cleaned up temporary file: {temp_file_path}")
            except OSError as e:
                logger.warning("Error deleting temporary" +
                               f"file {temp_file_path}: {e}")


def should_continue(state: GraphState) -> str:
    """
    Decides the next step based on the current state. Router node.
    """
    logger.info("ROUTER: should_continue")
    if state.get("error_message") is None:
        logger.info("Conclusion: Success. Ending workflow.")
        return "end"
    if state["iteration"] >= MAX_RETRY_ITERATIONS:
        logger.info(f"Conclusion: Max retries ({MAX_RETRY_ITERATIONS})" +
                    "reached. Ending workflow.")
        return "end"
    else:
        logger.info(f"Conclusion: Error detected. " +
                    "Retrying (Attempt " +
                    f"{state['iteration'] + 1}/{MAX_RETRY_ITERATIONS}).")
        return "retry"
