# backend/functions/sls_details_variance.py
import pandas as pd
import pyodbc
import os
import traceback
import logging
from functions.function_registry import register_function
from config import Config

logger = logging.getLogger(__name__)

def sls_details_variance(date1, date2):
    """
    Get SLS details for two dates using pyodbc connection and let OpenAI calculate the variance.
    
    Args:
        date1 (str): First date in format YYYY-MM-DD
        date2 (str): Second date in format YYYY-MM-DD
        
    Returns:
        dict: Query results for both dates
    """
    try:
        # Construct query to compare data between the two dates
        # Includes SLS_LINE_NUMBER and context_name for grouping
        query = f"""
        SELECT 
            sls.lri_position_str_cob_date as cob_date,
            sls.lri_position_str_sls_line_no as sls_line_number,
            rcl.context_name,
            COUNT(*) AS no_of_rows,
            ROUND(SUM(sls.std_rptg_meas_amt_base)) AS amt_reporting_measure,
            ROUND(SUM(sls.ccf_flow_amt_base)) AS amt_cof_flow,
            ROUND(SUM(sls.curr_mkt_value_clean_base)) AS amt_curr_mkt_value
        FROM lri_base.sls_details_prdl sls
        LEFT JOIN lri_base.result_context_list rcl ON sls.context_key = rcl.context_key
        WHERE sls.context_key IN (
            SELECT context_key
            FROM lri_base.result_context_list rcl
            WHERE rcl.cob_date IN ('{date1}', '{date2}')
            AND rcl.run_type = 'EOD'
            AND rcl.snapshot_label = 'FINAL'
            AND rcl.ctx_status = 'COMPLETED'
            AND rcl.service_name = 'SLS_REP_IMPALA'
            AND context_name NOT IN ('AWS_FNO_COLLATERAL_SLS_IC', 'AWS_DIVIDENDS_SLS_AND_IC')
        )
        AND sls.snapshot_label = 'FINAL'
        GROUP BY 1, 2, 3
        """
        
        logger.debug(f"Executing query: {query}")
        
        # Connect to Impala using pyodbc
        conn_string = "DSN=IMPALA_LRI_DR"  # Using the DSN from your example
        cert = '/etc/security/certs/JPMCROOTCA.pem'
        
        try:
            conn = pyodbc.connect(
                conn_string, 
                ssl=1, 
                AllowSelfSignedServerCert=1, 
                TrustedCerts=cert, 
                autocommit=True
            )
            
            # Execute query and get results as DataFrame
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            logger.debug(f"Query returned {len(df)} rows")
            
            # Return the data for OpenAI to calculate variance
            return {
                "date1": date1,
                "date2": date2,
                "columns_for_variance": ["amt_reporting_measure", "amt_cof_flow", "amt_curr_mkt_value"],
                "group_by_columns": ["sls_line_number", "context_name"],
                "threshold_percentage": 10,  # Define threshold for significant variance (10%)
                "query_results": df.to_dict(orient='records'),
                "instructions": """
                Please calculate the variance for each combination of sls_line_number and context_name between the two dates 
                for the columns: amt_reporting_measure, amt_cof_flow, and amt_curr_mkt_value.
                For each pair (sls_line_number + context_name), calculate:
                1. The absolute difference between values on the two dates
                2. The percentage change
                3. Flag any variance that exceeds the threshold percentage (10%)
                4. Summarize the findings, highlighting significant variances
                """
            }
            
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "error": f"Database connection error: {str(e)}",
                "details": "Error connecting to Impala database. Please check the connection settings."
            }
        
    except Exception as e:
        logger.error(f"Error in sls_details_variance: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}

# Register the function
register_function("sls_details_variance", sls_details_variance)
