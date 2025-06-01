from typing import List, TypedDict, Optional
from pydantic import BaseModel, Field


class CodeSolution(BaseModel):
    """Schema for an optimized user prompt and the reasoning behind it."""
    optimized_prompt: str = Field(description="A detailed, optimized prompt for a code generation AI, incorporating all user requirements.")
    reasoning: str = Field(description="A clear justification for why the new prompt is better and how it will lead to a superior code solution.")


class PythonCode(BaseModel):
    """Schema for a complete Python code solution."""
    task_description: str = Field(description="A concise description of the coding task and the proposed approach.")
    imports: str = Field(description="All necessary import statements for the code, separated by newlines.")
    code: str = Field(description="The complete, executable Python code block, without any import statements.")


class GraphState(TypedDict):
    """Represents the state of our workflow graph."""
    initial_question: str
    optimized_prompt: str
    generation: Optional[PythonCode]
    execution_result: Optional[str]
    error_message: Optional[str]
    feedback_history: List[str]
    iteration: int
