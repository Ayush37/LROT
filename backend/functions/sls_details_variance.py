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
    Calculate variance for SLS details between two dates.
    
    Args:
        date1 (str): First date in format YYYY-MM-DD
        date2 (str): Second date in format YYYY-MM-DD
        
    Returns:
        dict: Variance information
    """
    try:
        # Construct query to get data for both dates
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
        conn_string = "DSN=IMPALA_LRI_DR"  # Using the DSN from the example
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
            
            # Process the data to calculate variances
            # First, verify we have data for both dates
            if date1 not in df['cob_date'].values or date2 not in df['cob_date'].values:
                return {
                    "error": "Missing data for one or both dates",
                    "details": f"Data for {date1} and/or {date2} not found in the results."
                }
            
            # Create separate dataframes for each date
            df1 = df[df['cob_date'] == date1]
            df2 = df[df['cob_date'] == date2]
            
            # Create a unique identifier for each sls_line_number + context_name combination
            df1['composite_key'] = df1['sls_line_number'] + '|' + df1['context_name']
            df2['composite_key'] = df2['sls_line_number'] + '|' + df2['context_name']
            
            # Set the composite_key as index for both dataframes
            df1.set_index('composite_key', inplace=True)
            df2.set_index('composite_key', inplace=True)
            
            # Get the list of composite keys that appear in both dates
            common_keys = list(set(df1.index) & set(df2.index))
            
            # Initialize results
            variance_data = []
            
            # Calculate variance for each sls_line_number + context_name combination
            for key in common_keys:
                row1 = df1.loc[key]
                row2 = df2.loc[key]
                
                # Split the composite key back to components
                sls_line_number, context_name = key.split('|')
                
                # Calculate variance for each metric
                variance_row = {
                    'sls_line_number': sls_line_number,
                    'context_name': context_name,
                    'amt_reporting_measure_date1': float(row1['amt_reporting_measure']),
                    'amt_reporting_measure_date2': float(row2['amt_reporting_measure']),
                    'amt_cof_flow_date1': float(row1['amt_cof_flow']),
                    'amt_cof_flow_date2': float(row2['amt_cof_flow']),
                    'amt_curr_mkt_value_date1': float(row1['amt_curr_mkt_value']),
                    'amt_curr_mkt_value_date2': float(row2['amt_curr_mkt_value']),
                }
                
                # Calculate absolute variance
                variance_row['amt_reporting_measure_variance'] = variance_row['amt_reporting_measure_date2'] - variance_row['amt_reporting_measure_date1']
                variance_row['amt_cof_flow_variance'] = variance_row['amt_cof_flow_date2'] - variance_row['amt_cof_flow_date1']
                variance_row['amt_curr_mkt_value_variance'] = variance_row['amt_curr_mkt_value_date2'] - variance_row['amt_curr_mkt_value_date1']
                
                # Calculate percentage variance (avoid division by zero)
                variance_row['amt_reporting_measure_pct'] = (
                    (variance_row['amt_reporting_measure_variance'] / variance_row['amt_reporting_measure_date1']) * 100 
                    if variance_row['amt_reporting_measure_date1'] != 0 else 0
                )
                
                variance_row['amt_cof_flow_pct'] = (
                    (variance_row['amt_cof_flow_variance'] / variance_row['amt_cof_flow_date1']) * 100 
                    if variance_row['amt_cof_flow_date1'] != 0 else 0
                )
                
                variance_row['amt_curr_mkt_value_pct'] = (
                    (variance_row['amt_curr_mkt_value_variance'] / variance_row['amt_curr_mkt_value_date1']) * 100 
                    if variance_row['amt_curr_mkt_value_date1'] != 0 else 0
                )
                
                # Check if any variance exceeds threshold (10%)
                threshold = 10.0
                variance_row['has_significant_variance'] = (
                    abs(variance_row['amt_reporting_measure_pct']) > threshold or
                    abs(variance_row['amt_cof_flow_pct']) > threshold or
                    abs(variance_row['amt_curr_mkt_value_pct']) > threshold
                )
                
                variance_data.append(variance_row)
            
            # Also identify unique entries that exist in only one date
            only_in_date1 = list(set(df1.index) - set(df2.index))
            only_in_date2 = list(set(df2.index) - set(df1.index))
            
            date1_only_data = []
            for key in only_in_date1:
                row = df1.loc[key]
                sls_line_number, context_name = key.split('|')
                date1_only_data.append({
                    'sls_line_number': sls_line_number,
                    'context_name': context_name,
                    'amt_reporting_measure': float(row['amt_reporting_measure']),
                    'amt_cof_flow': float(row['amt_cof_flow']),
                    'amt_curr_mkt_value': float(row['amt_curr_mkt_value'])
                })
            
            date2_only_data = []
            for key in only_in_date2:
                row = df2.loc[key]
                sls_line_number, context_name = key.split('|')
                date2_only_data.append({
                    'sls_line_number': sls_line_number,
                    'context_name': context_name,
                    'amt_reporting_measure': float(row['amt_reporting_measure']),
                    'amt_cof_flow': float(row['amt_cof_flow']),
                    'amt_curr_mkt_value': float(row['amt_curr_mkt_value'])
                })
            
            # Create summary statistics
            significant_variances = [row for row in variance_data if row['has_significant_variance']]
            
            summary = {
                "date1": date1,
                "date2": date2,
                "total_combinations": len(common_keys),
                "combinations_with_variance": len(significant_variances),
                "threshold_percentage": threshold,
                "only_in_date1_count": len(only_in_date1),
                "only_in_date2_count": len(only_in_date2),
                "largest_amt_reporting_measure_variance": max(variance_data, key=lambda x: abs(x['amt_reporting_measure_variance'])) if variance_data else None,
                "largest_amt_cof_flow_variance": max(variance_data, key=lambda x: abs(x['amt_cof_flow_variance'])) if variance_data else None,
                "largest_amt_curr_mkt_value_variance": max(variance_data, key=lambda x: abs(x['amt_curr_mkt_value_variance'])) if variance_data else None,
            }
            
            # Sort the variance data by significance and limit to most significant ones
            variance_data.sort(key=lambda x: max(
                abs(x['amt_reporting_measure_pct']), 
                abs(x['amt_cof_flow_pct']), 
                abs(x['amt_curr_mkt_value_pct'])
            ), reverse=True)
            
            return {
                "summary": summary,
                "variance_data": variance_data[:20],  # Return only top 20 most significant variances
                "unique_to_date1": date1_only_data[:5],  # First 5 entries unique to date1
                "unique_to_date2": date2_only_data[:5],  # First 5 entries unique to date2
                "all_variance_count": len(variance_data)
            }
            
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "error": f"Database connection error: {str(e)}",
                "details": "Error connecting to Impala database or processing results."
            }
        
    except Exception as e:
        logger.error(f"Error in sls_details_variance: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}

# Register the function
register_function("sls_details_variance", sls_details_variance)
