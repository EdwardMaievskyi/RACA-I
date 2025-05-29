PROMPT_OPTIMIZATION_SYSTEM_PROMPT = """You are an expert prompt engineer. 
Your task is to refine a user's request into a detailed, clear, and 
effective prompt for a Python code generation AI.
The refined prompt must guide the AI to generate a complete, standalone, 
and executable Python script.
Crucially, ensure the generated code:
1. Includes all necessary imports.
2. Contains a `if __name__ == '__main__':` block for execution.
3. Hardcodes any necessary inputs or uses placeholder variables; it must not ask for interactive user input.
"""

CODE_GENERATION_PROMPT = """You are an expert Python developer. 
Your task is to write a complete, executable Python script to solve the user's 
request.
Adhere strictly to the provided Pydantic schema for your response.
The script must be self-contained, runnable, and include all necessary imports 
and logic in the correct fields.
Pay close attention to any feedback from previous attempts to correct 
your mistakes."""


def get_code_optimization_user_prompt(question: str) -> str:
    output = "Please refine the following user request into an " +\
        "optimized prompt for a code generation AI:\n\n---\n" +\
        f"USER REQUEST: \"{question}\"\n---"
    return output


def get_code_generation_user_prompt(question: str) -> str:
    output = "Please generate a complete, standalone, and executable Python script to solve the following user request:\n\n---\n" +\
        f"USER REQUEST: \"{question}\"\n---"
    return output
