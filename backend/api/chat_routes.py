# backend/api/chat_routes.py
import logging
import traceback
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
            logger.debug(f"OpenAI response: {ai_response}")
        except Exception as e:
            logger.error(f"Error getting OpenAI response: {str(e)}")
            logger.error(traceback.format_exc())
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
                logger.error(traceback.format_exc())
                return jsonify({"error": f"Function execution error: {str(e)}"}), 500
            
            # Get final response incorporating function result
            try:
                final_response = get_openai_response(user_message, chat_history, function_result)
                logger.debug(f"Final response with function result: {final_response}")
                return jsonify({"response": final_response})
            except Exception as e:
                logger.error(f"Error getting final response: {str(e)}")
                logger.error(traceback.format_exc())
                return jsonify({"error": f"Error getting final response: {str(e)}"}), 500
        
        return jsonify({"response": ai_response})
    
    except Exception as e:
        logger.error(f"Unhandled error in chat endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Server error: {str(e)}"}), 500
