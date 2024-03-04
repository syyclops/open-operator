from typing import TypedDict, Dict

class ToolParametersSchema(TypedDict):
  type: str
  properties: Dict[str, Dict[str, str]]
  required: list[str]

class Tool:
  def __init__(self, name: str, description: str, function, parameters_schema: ToolParametersSchema):
    """
    Initialize a new tool with a name, description, function to execute, and parameters schema.

    :param name: The name of the tool.
    :param description: A brief description of what the tool does.
    :param function: The function to execute when the tool is used.
    :param parameters_schema: A JSON schema dict describing the parameters for the function.
    """
    self.name = name
    self.description = description
    self.function = function
    self.parameters_schema = parameters_schema

  def get_json_schema(self) -> dict:
    """
    Returns the JSON schema for the tool's parameters.

    :return: A dict representing the JSON schema of the tool's parameters.
    """
    return {
        "type": "function",
        "function": {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters_schema
        }
    }

  def execute(self, **kwargs):
    """
    Executes the tool's function with the provided keyword arguments.

    :param kwargs: Keyword arguments that match the tool's parameters schema.
    :return: The result of the tool's function execution.
    """
    # Validate kwargs against self.parameters_schema if necessary
    return self.function(**kwargs)