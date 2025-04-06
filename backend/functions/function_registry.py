# backend/functions/function_registry.py
# Dictionary to store available functions
_FUNCTION_REGISTRY = {}

def register_function(name, func):
    """
    Register a function in the registry.
    
    Args:
        name (str): Function name
        func (callable): Function implementation
    """
    _FUNCTION_REGISTRY[name] = func

def get_function(name):
    """
    Get a function from the registry.
    
    Args:
        name (str): Function name
        
    Returns:
        callable: Function implementation or None if not found
    """
    return _FUNCTION_REGISTRY.get(name)
