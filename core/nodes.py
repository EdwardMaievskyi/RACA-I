import os
import re
import subprocess
import sys
import tempfile

from config import MAX_CODE_TIMEOUT, MAX_RETRY_ITERATIONS
from core.interaction import call_llm_with_tool
from core.state_models import GraphState, CodeSolution, PythonCode
from core.prompts import (PROMPT_OPTIMIZATION_SYSTEM_PROMPT,
                          CODE_GENERATION_PROMPT,
                          get_code_optimization_user_prompt)


def optimize_prompt(state: GraphState) -> GraphState:
    """
    Takes the initial user question and refines it into a detailed prompt 
    for the code generator. Should be used as the first node in the graph.
    """
    print("## NODE: optimize_prompt")
    question = state["initial_question"]

    user_prompt = get_code_optimization_user_prompt(question)

    messages = [
        {"role": "system", "content": PROMPT_OPTIMIZATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    instance, error = call_llm_with_tool(messages, CodeSolution)

    if error:
        print(f"  ERROR: {error}")
        return {**state, "error_message": error}

    print("  SUCCESS: Prompt optimized.")
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
    print(f"## NODE: code_generate (Iteration {state['iteration'] + 1})")

    system_prompt = CODE_GENERATION_PROMPT

    feedback_message = "\n".join(state['feedback_history'])
    user_prompt = f"USER PROMPT:\n{state['optimized_prompt']}\n\nPREVIOUS ATTEMPTS FEEDBACK:\n{feedback_message}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    instance, error = call_llm_with_tool(messages, PythonCode)

    if error:
        print(f"  ERROR: {error}")
        return {**state, "error_message": error}

    print("  SUCCESS: Code generated.")
    return {**state,
            "generation": instance,
            "iteration": state["iteration"] + 1}


def execute_code(state: GraphState) -> GraphState:
    """
    Cleans, prepares, and executes the generated code in a secure environment.
    """
    print("## NODE: code_execute")
    code_gen = state.get("generation")
    if not code_gen:
        return {**state,
                "error_message": "Code generation was skipped or failed."}

    imports = re.sub(r"```python\n|```", "", code_gen.imports).strip()
    code = re.sub(r"```python\n|```", "", code_gen.code).strip()
    full_code = f"{imports}\n\n{code}"
    print("  ---\n  Prepared Code:\n  ---\n" + full_code + "\n  ---")

    libs = re.findall(r'^\s*(?:import|from)\s+([\w\d_]+)', imports, re.MULTILINE)
    if libs:
        print(f"  INFO: Attempting to install required libraries: {libs}")
        for lib in set(libs):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                error_msg = f"Failed to install required library: {lib}. The code may fail."
                print(f"  WARNING: {error_msg}")

    try:
        with tempfile.NamedTemporaryFile(mode='w',
                                         suffix='.py',
                                         delete=False) as temp_file:
            temp_file.write(full_code)
            temp_file_path = temp_file.name

        result = subprocess.run(
            [sys.executable, temp_file_path],
            capture_output=True,
            text=True,
            timeout=MAX_CODE_TIMEOUT
        )

        os.remove(temp_file_path)

        if result.returncode == 0:
            print("  SUCCESS: Code executed without errors.")
            print("  ---\n  Execution Output:\n  ---\n" + result.stdout + "\n  ---")
            return {**state,
                    "execution_result": result.stdout,
                    "error_message": None}
        else:
            print("  ERROR: Code execution failed.")
            error_output = result.stderr or result.stdout
            print("  ---\n  Execution Error:\n  ---\n" + error_output + "\n  ---")
            feedback = f"Your code failed to execute. Error:\n{error_output}"
            return {**state,
                    "error_message": "Execution failed.",
                    "feedback_history": state["feedback_history"] + [feedback]}

    except subprocess.TimeoutExpired:
        print("  ERROR: Code execution timed out.")
        feedback = f"Your code took longer than {MAX_CODE_TIMEOUT} seconds to run and was terminated. Please optimize for performance."
        return {**state,
                "error_message": "Execution timed out.",
                "feedback_history": state["feedback_history"] + [feedback]}
    except Exception as e:
        print(f"  ERROR: An unexpected error occurred during execution: {e}")
        feedback = f"The code could not be run due to a setup error: {e}"
        return {**state,
                "error_message": str(e),
                "feedback_history": state["feedback_history"] + [feedback]}


def should_continue(state: GraphState) -> str:
    """
    Decides the next step based on the current state. Router node.
    """
    print("## ROUTER: should_continue")
    if state.get("error_message") is None:
        print("  --> Conclusion: Success. Ending workflow.")
        return "end"
    if state["iteration"] >= MAX_RETRY_ITERATIONS:
        print("  --> Conclusion: Max retries reached. Ending workflow.")
        return "end"
    else:
        print(f"  --> Conclusion: Error detected. Retrying (Attempt {state['iteration'] + 1}/{MAX_RETRY_ITERATIONS}).")
        return "retry"
