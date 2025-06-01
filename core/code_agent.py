from dataclasses import dataclass
import time
from typing import Dict, Any, Optional, List

from config import MAX_RETRY_ITERATIONS
from core.graph_flow import create_graph_flow


code_agent_app = create_graph_flow()


@dataclass
class ExecutionResult:
    """Result of code execution with metadata."""
    success: bool
    code: Optional[str] = None
    imports: Optional[str] = None
    output: Optional[str] = None
    error_message: Optional[str] = None
    iterations: int = 0
    execution_time: float = 0.0
    feedback_history: List[str] = None
    
    def __post_init__(self):
        if self.feedback_history is None:
            self.feedback_history = []


class CodeAgent:
    """
    A high-level wrapper for the AI code generation workflow.

    This class provides a clean interface for generating and executing Python code
    based on natural language descriptions, with automatic retry logic and
    comprehensive error handling.
    """

    def __init__(self, max_retries: Optional[int] = None, verbose: bool = True):
        """
        Initialize the CodeAgent.

        Args:
            max_retries: Maximum number of retry attempts (defaults to config value)
            verbose: Whether to print detailed execution logs
        """
        self.max_retries = max_retries or MAX_RETRY_ITERATIONS
        self.verbose = verbose
        self._app = code_agent_app

    def generate_and_execute(self, question: str) -> ExecutionResult:
        """
        Generate and execute Python code based on a natural language question.

        Args:
            question: Natural language description of the coding task

        Returns:
            ExecutionResult containing the outcome and metadata
        """
        start_time = time.time()

        if self.verbose:
            print(f"🤖 CodeAgent: Processing request: '{question}'")
            print("=" * 60)
        
        # Prepare initial state
        initial_state = {
            "initial_question": question,
            "iteration": 0,
            "feedback_history": [],
            "optimized_prompt": "",
            "generation": None,
            "execution_result": None,
            "error_message": None
        }
        
        try:
            # Execute the workflow
            final_state = self._run_workflow(initial_state)
            execution_time = time.time() - start_time
            
            # Process results
            result = self._process_final_state(final_state, execution_time)
            
            if self.verbose:
                self._print_summary(result)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Workflow execution failed: {str(e)}"
            
            if self.verbose:
                print(f"❌ Fatal Error: {error_msg}")
            
            return ExecutionResult(
                success=False,
                error_message=error_msg,
                execution_time=execution_time
            )
    
    def generate_code_only(self, question: str) -> ExecutionResult:
        """
        Generate Python code without executing it.
        
        Args:
            question: Natural language description of the coding task
            
        Returns:
            ExecutionResult with generated code (not executed)
        """
        start_time = time.time()
        
        if self.verbose:
            print(f"🤖 CodeAgent: Generating code for: '{question}'")
            print("=" * 60)
        
        # Prepare initial state for code generation only
        initial_state = {
            "initial_question": question,
            "iteration": 0,
            "feedback_history": [],
            "optimized_prompt": "",
            "generation": None,
            "execution_result": None,
            "error_message": None
        }
        
        try:
            # Run only the optimization and generation steps
            state = initial_state.copy()
            
            # Execute workflow until code generation
            for event in self._app.stream(state):
                for node_name, node_data in event.items():
                    state.update(node_data)
                    if self.verbose:
                        print(f"✓ Completed: {node_name}")
                    
                    # Stop after code generation
                    if node_name == "code_generate" and not state.get("error_message"):
                        break
            
            execution_time = time.time() - start_time
            result = self._process_generation_state(state, execution_time)
            
            if self.verbose:
                self._print_generation_summary(result)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Code generation failed: {str(e)}"
            
            if self.verbose:
                print(f"❌ Fatal Error: {error_msg}")
            
            return ExecutionResult(
                success=False,
                error_message=error_msg,
                execution_time=execution_time
            )
    
    def _run_workflow(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete workflow and return final state."""
        final_state = initial_state.copy()
        
        for event in self._app.stream(initial_state):
            for node_name, node_data in event.items():
                final_state.update(node_data)
                if self.verbose:
                    print(f"✓ Completed: {node_name}")
        
        return final_state
    
    def _process_final_state(self, state: Dict[str, Any], execution_time: float) -> ExecutionResult:
        """Process the final workflow state into an ExecutionResult."""
        generation = state.get("generation")
        success = state.get("error_message") is None and state.get("execution_result") is not None
        
        return ExecutionResult(
            success=success,
            code=generation.code if generation else None,
            imports=generation.imports if generation else None,
            output=state.get("execution_result"),
            error_message=state.get("error_message"),
            iterations=state.get("iteration", 0),
            execution_time=execution_time,
            feedback_history=state.get("feedback_history", [])
        )
    
    def _process_generation_state(self, state: Dict[str, Any], execution_time: float) -> ExecutionResult:
        """Process the state after code generation (without execution)."""
        generation = state.get("generation")
        success = state.get("error_message") is None and generation is not None
        
        return ExecutionResult(
            success=success,
            code=generation.code if generation else None,
            imports=generation.imports if generation else None,
            output=None,  # No execution performed
            error_message=state.get("error_message"),
            iterations=state.get("iteration", 0),
            execution_time=execution_time,
            feedback_history=state.get("feedback_history", [])
        )
    
    def _print_summary(self, result: ExecutionResult) -> None:
        """Print a summary of the execution results."""
        print("=" * 60)
        
        if result.success:
            print("🎉 SUCCESS: Code generated and executed successfully!")
            print(f"⏱️  Execution time: {result.execution_time:.2f} seconds")
            print(f"🔄 Iterations: {result.iterations}")
            
            if result.output:
                print("\n📋 Output:")
                print("-" * 40)
                print(result.output)
                print("-" * 40)
        else:
            print("❌ FAILED: Code generation or execution failed")
            print(f"⏱️  Execution time: {result.execution_time:.2f} seconds")
            print(f"🔄 Iterations: {result.iterations}")
            
            if result.error_message:
                print(f"\n🚨 Error: {result.error_message}")
            
            if result.feedback_history:
                print("\n📝 Feedback History:")
                for i, feedback in enumerate(result.feedback_history, 1):
                    print(f"  {i}. {feedback}")
    
    def _print_generation_summary(self, result: ExecutionResult) -> None:
        """Print a summary of the code generation results."""
        print("=" * 60)
        
        if result.success:
            print("🎉 SUCCESS: Code generated successfully!")
            print(f"⏱️  Generation time: {result.execution_time:.2f} seconds")
            print(f"🔄 Iterations: {result.iterations}")
            
            if result.code:
                print("\n💻 Generated Code:")
                print("-" * 40)
                if result.imports:
                    print(result.imports)
                    print()
                print(result.code)
                print("-" * 40)
        else:
            print("❌ FAILED: Code generation failed")
            print(f"⏱️  Generation time: {result.execution_time:.2f} seconds")
            
            if result.error_message:
                print(f"\n🚨 Error: {result.error_message}")
    
    def get_full_code(self, result: ExecutionResult) -> Optional[str]:
        """
        Get the complete code (imports + code) from an ExecutionResult.
        
        Args:
            result: ExecutionResult from generate_and_execute or generate_code_only
            
        Returns:
            Complete code string or None if no code was generated
        """
        if not result.success or not result.code:
            return None
        
        imports = result.imports or ""
        code = result.code or ""
        
        if imports.strip():
            return f"{imports.strip()}\n\n{code.strip()}"
        else:
            return code.strip()
    
    def save_code(self, result: ExecutionResult, filename: str) -> bool:
        """
        Save generated code to a file.
        
        Args:
            result: ExecutionResult containing the code
            filename: Path to save the code file
            
        Returns:
            True if saved successfully, False otherwise
        """
        full_code = self.get_full_code(result)
        if not full_code:
            if self.verbose:
                print("❌ No code to save")
            return False
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(full_code)
            
            if self.verbose:
                print(f"💾 Code saved to: {filename}")
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Failed to save code: {str(e)}")
            return False


# Convenience function for quick usage
def generate_code(question: str, execute: bool = True, verbose: bool = True) -> ExecutionResult:
    """
    Convenience function for quick code generation.
    
    Args:
        question: Natural language description of the coding task
        execute: Whether to execute the generated code
        verbose: Whether to print detailed logs
        
    Returns:
        ExecutionResult with the outcome
    """
    agent = CodeAgent(verbose=verbose)
    
    if execute:
        return agent.generate_and_execute(question)
    else:
        return agent.generate_code_only(question)
