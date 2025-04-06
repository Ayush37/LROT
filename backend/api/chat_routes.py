# backend/api/chat_routes.py
import logging
from flask import Blueprint, request, jsonify
from services.azure_openai import get_openai_response
from services.function_router import route_function_call

logger = logging.getLogger(__name__)
chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
def chat():
    logger.debug(f"Received chat request: {request.data}")
    
    try:
        data = request.json
        if not data or 'message' not in data:
            logger.warning("Invalid request. Message is required.")
            return jsonify({"error": "Invalid request. Message is required."}), 400
        
        user_message = data['message']
        chat_history = data.get('history', [])
        
        logger.info(f"Processing message: {user_message}")
        
        # Get response from OpenAI
        try:
            ai_response = get_openai_response(user_message, chat_history)
            # Convert OpenAI response to a serializable format
            serializable_response = {
                "content": ai_response.content if hasattr(ai_response, 'content') else None,
                "function_call": None
            }
            
            # If there's a function call, also convert it
            if hasattr(ai_response, 'function_call') and ai_response.function_call:
                serializable_response["function_call"] = {
                    "name": ai_response.function_call.name,
                    "arguments": ai_response.function_call.arguments
                }
                
            logger.debug(f"Serializable response: {serializable_response}")
            
        except Exception as e:
            logger.error(f"Error getting OpenAI response: {str(e)}")
            return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500
        
        # Check if we need to execute a function
        if hasattr(ai_response, 'function_call') and ai_response.function_call:
            function_name = ai_response.function_call.name
            function_args = ai_response.function_call.arguments
            
            logger.info(f"Function call detected: {function_name}")
            
            # Route to appropriate function
            try:
                function_result = route_function_call(function_name, function_args)
                logger.debug(f"Function result: {function_result}")
            except Exception as e:
                logger.error(f"Error executing function {function_name}: {str(e)}")
                return jsonify({"error": f"Function execution error: {str(e)}"}), 500
            
            # Get final response incorporating function result
            try:
                final_response = get_openai_response(user_message, chat_history, function_result)
                # Convert the final response to a serializable format
                serializable_final_response = {
                    "content": final_response.content if hasattr(final_response, 'content') else None,
                    "function_call": None
                }
                
                if hasattr(final_response, 'function_call') and final_response.function_call:
                    serializable_final_response["function_call"] = {
                        "name": final_response.function_call.name,
                        "arguments": final_response.function_call.arguments
                    }
                    
                logger.debug(f"Final serializable response: {serializable_final_response}")
                return jsonify({"response": serializable_final_response})
            except Exception as e:
                logger.error(f"Error getting final response: {str(e)}")
                return jsonify({"error": f"Error getting final response: {str(e)}"}), 500
        
        return jsonify({"response": serializable_response})
    
    except Exception as e:
        logger.error(f"Unhandled error in chat endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
