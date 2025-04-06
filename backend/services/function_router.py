# backend/services/function_router.py
import json
from functions.function_registry import get_function

def route_function_call(function_name, function_args):
    """
    Routes a function call to the appropriate function implementation.
    
    Args:
        function_name (str): Name of the function to call
        function_args (str): JSON string of arguments
        
    Returns:
        dict: Result of the function call
    """
    try:
        # Parse arguments
        args = json.loads(function_args) if isinstance(function_args, str) else function_args
        
        # Get the function from registry
        func = get_function(function_name)
        if not func:
            return {
                "name": function_name,
                "result": {"error": f"Function {function_name} not found"}
            }
        
        # Execute the function
        result = func(**args)
        
        return {
            "name": function_name,
            "result": result
        }
        
    except Exception as e:
        return {
            "name": function_name,
            "result": {"error": str(e)}
        }
