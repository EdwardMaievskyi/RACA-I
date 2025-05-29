import logging
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel, ValidationError
from openai import OpenAI, APIError
from config import PRIMARY_MODEL_NAME, OPENAI_API_KEY


logger = logging.getLogger(__name__)
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def call_llm_with_tool(
    messages: List[Dict[str, Any]],
    pydantic_model: Type[BaseModel]) -> tuple[Optional[BaseModel],
                                              Optional[str]]:
    """
    Calls the OpenAI API and parses the response into a Pydantic model.

    Analogy: This function is like a universal adapter. You give it a plug type
    (Pydantic model) and an outlet (the LLM), and it handles making the
    connection and ensuring the power (data) flows correctly and safely.
    """
    try:
        tool_definition = {
            "type": "function",
            "function": {
                "name": pydantic_model.__name__,
                "description": pydantic_model.__doc__ or f"Extracts data using the {pydantic_model.__name__} schema.",
                "parameters": pydantic_model.model_json_schema()
            }
        }

        response = openai_client.chat.completions.create(
            model=PRIMARY_MODEL_NAME,
            messages=messages,
            tools=[tool_definition],
            tool_choice={"type": "function",
                         "function": {"name": pydantic_model.__name__}},
        )

        message = response.choices[0].message
        if not message.tool_calls:
            return None, "The model failed to use the required tool. It might have refused or misunderstood."

        tool_args = message.tool_calls[0].function.arguments
        instance = pydantic_model.model_validate_json(tool_args)
        return instance, None

    except APIError as e:
        return None, f"OpenAI API Error: {e}"
    except ValidationError as e:
        return None, f"Pydantic Validation Error: The model's output did not match the required schema. Details: {e}"
    except Exception as e:
        return None, f"An unexpected error occurred during the LLM call: {e}"
