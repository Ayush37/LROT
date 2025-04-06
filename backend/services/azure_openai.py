# backend/services/azure_openai.py
import json
import os
from openai import AzureOpenAI
import json
from azure.identity import CertificateCredential
import os

def get_access_token():
    dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    print(dir_path)
    cert_path = dir_path + "/cert/apim-exp.pem"
    print(cert_path)
    
    scope = "https://cognitiveservices.azure.com/.default"
    credential = CertificateCredential(
        client_id=os.environ["AZURE_SPN_CLIENT_ID"],
        certificate_path=cert_path,
        tenant_id=os.environ["AZURE_TENANT_ID"],
        scope=scope,
        logging_enable=False
    )
    
    access_token = credential.get_token(scope).token
    print(f"ACCESS_TOKEN===" + access_token + "\n")
    return access_token

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
    
    # Get access token
    token = get_access_token()
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    print(f"Azure OpenAI Endpoint: {azure_endpoint}")  # Debugging line
    
    # Initialize Azure OpenAI client
    client = AzureOpenAI(
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        api_version="2024-12-01-preview",
        default_headers={
            "Authorization": f"Bearer {token}",
            "user_sid": "1792420"
        }
    )
    
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
        model="gpt-4o-2024-08-06",  # Using the model from your screenshot
        messages=messages,
        functions=functions,
        function_call="auto"
    )
    
    return response.choices[0].message
