# backend/api/chat_routes.py
from flask import Blueprint, request, jsonify
from services.azure_openai import get_openai_response
from services.function_router import route_function_call

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
def chat():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"error": "Invalid request. Message is required."}), 400
    
    user_message = data['message']
    chat_history = data.get('history', [])
    
    # Get response from OpenAI
    ai_response = get_openai_response(user_message, chat_history)
    
    # Check if we need to execute a function
    if 'function_call' in ai_response:
        function_name = ai_response['function_call']['name']
        function_args = ai_response['function_call']['arguments']
        
        # Route to appropriate function
        function_result = route_function_call(function_name, function_args)
        
        # Get final response incorporating function result
        final_response = get_openai_response(user_message, chat_history, function_result)
        return jsonify({"response": final_response})
    
    return jsonify({"response": ai_response})
