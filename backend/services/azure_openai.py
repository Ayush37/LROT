# backend/services/azure_openai.py
import json
import os
from openai import AzureOpenAI
from config import Config

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
    api_key=Config.AZURE_OPENAI_API_KEY,
    api_version="2023-05-15"
)

def get_openai_response(message, history=None, function_result=None):
    """
    Get a response from Azure OpenAI API.
    
    Args:
        message (str): User message
        history (list): Chat history
        function_result (dict, optional): Result from a function call
        
    Returns:
        dict: OpenAI response
    """
    if history is None:
        history = []
    
    # Construct messages for API
    messages = [{"role": "system", "content": "You are LROT, an AI assistant that can help with various tasks."}]
    
    # Add chat history
    for entry in history:
        messages.append({"role": "user", "content": entry.get("user", "")})
        if "assistant" in entry:
            messages.append({"role": "assistant", "content": entry.get("assistant", "")})
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    # If we have a function result, add it
    if function_result:
        messages.append({
            "role": "function", 
            "name": function_result.get("name", ""),
            "content": json.dumps(function_result.get("result", {}))
        })
    
    # Define available functions
    functions = [
        {
            "name": "sls_details_variance",
            "description": "Calculate variance for SLS details between two dates",
            "parameters": {
                "type": "object",
                "properties": {
                    "date1": {"type": "string", "description": "First date in format YYYY-MM-DD"},
                    "date2": {"type": "string", "description": "Second date in format YYYY-MM-DD"}
                },
                "required": ["date1", "date2"]
            }
        },
        {
            "name": "time_remaining",
            "description": "Get current time and time remaining until EOD (5PM EST)",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    ]
    
    # Call Azure OpenAI API
    response = client.chat.completions.create(
        model="gpt-4",  # Replace with your deployed model name
        messages=messages,
        functions=functions,
        function_call="auto"
    )
    
    return response.choices[0].message
