# backend/functions/sync_adjustments.py
import logging
import requests
import json
import traceback
from functions.function_registry import register_function

logger = logging.getLogger(__name__)

def sync_adjustments(adjustment_type, dmat_ids):
    """
    Clear or sync stuck adjustments for specified DMAT IDs.
    
    Args:
        adjustment_type (str): Type of adjustment - either "MDU" or "MSDU"
        dmat_ids (str): Comma-separated list of DMAT IDs to sync
        
    Returns:
        dict: Status of the sync operation
    """
    try:
        logger.info(f"Starting sync adjustments for type: {adjustment_type}, DMAT IDs: {dmat_ids}")
        
        # Validate adjustment type
        if adjustment_type not in ["MDU", "MSDU"]:
            return {
                "success": False,
                "error": "Invalid adjustment type. Must be either 'MDU' or 'MSDU'."
            }
        
        # Parse and validate DMAT IDs
        dmat_id_list = []
        if dmat_ids:
            # Split by comma and strip whitespace
            dmat_id_list = [dmat_id.strip() for dmat_id in dmat_ids.split(',')]
            
            # Validate that all DMAT IDs are numeric
            for dmat_id in dmat_id_list:
                if not dmat_id.isdigit():
                    return {
                        "success": False,
                        "error": f"Invalid DMAT ID: {dmat_id}. All DMAT IDs must be numeric."
                    }
        
        if not dmat_id_list:
            return {
                "success": False,
                "error": "No valid DMAT IDs provided."
            }
        
        # Step 1: Get access token
        try:
            token_url = "https://lri-limits-indicators-api.apps.prod.na-5y.gap.jpmchase.net/ida/getTokens"
            token_params = {
                "userSid": "I792420",  # You might want to make this configurable
                "appId": "adj"
            }
            
            logger.debug(f"Fetching access token from: {token_url}")
            token_response = requests.get(token_url, params=token_params)
            token_response.raise_for_status()
            
            token_data = token_response.json()
            access_token = token_data.get('access_token')
            
            if not access_token:
                raise ValueError("No access_token found in response")
                
            logger.debug("Access token retrieved successfully")
            
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to retrieve access token: {str(e)}"
            }
        
        # Step 2: Trigger adjustment sync
        try:
            callback_url = "https://lri-adjustments-api.gaiacloud.jpmchase.net/api/v2/adjustments/dmatcallback"
            
            headers = {
                "Cache-Control": "no-cache",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Cookie": access_token
            }
            
            payload = {
                "dmatIdList": dmat_id_list,
                "lriIdList": [],
                "cobDateList": [],
                "reportType": adjustment_type,
                "actionType": "UPDATE"
            }
            
            logger.debug(f"Triggering adjustment sync at: {callback_url}")
            logger.debug(f"Payload: {json.dumps(payload)}")
            
            sync_response = requests.post(callback_url, json=payload, headers=headers)
            sync_response.raise_for_status()
            
            logger.info("Adjustment sync triggered successfully")
            
            return {
                "success": True,
                "message": f"Sync successfully performed for {adjustment_type} adjustments on DMAT IDs: {', '.join(dmat_id_list)}",
                "dmat_ids": dmat_id_list,
                "adjustment_type": adjustment_type
            }
            
        except Exception as e:
            logger.error(f"Error triggering adjustment sync: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": f"Failed to trigger adjustment sync: {str(e)}"
            }
        
    except Exception as e:
        logger.error(f"Error in sync_adjustments: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": f"An unexpected error occurred: {str(e)}"
        }

# Register the function
register_function("sync_adjustments", sync_adjustments)
