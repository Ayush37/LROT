# backend/functions/sls_details_variance.py
import pandas as pd
import pyodbc
import os
import traceback
import logging
from datetime import datetime
from functions.function_registry import register_function
from config import Config

logger = logging.getLogger(__name__)

def sls_details_variance(date1, date2, product_identifiers=None):
    """
    Perform comprehensive variance analysis for SLS details between two dates.
    
    Args:
        date1 (str): First date in format YYYY-MM-DD
        date2 (str): Second date in format YYYY-MM-DD
        product_identifiers (str, optional): Comma-separated list of product identifiers (e.g., 'OS-09,OS-10')
        
    Returns:
        dict: Comprehensive variance information including analysis from multiple tables
    """
    try:
        # Parse and format dates
        date1_obj = datetime.strptime(date1, '%Y-%m-%d')
        date2_obj = datetime.strptime(date2, '%Y-%m-%d')
        date1_formatted = date1_obj.strftime('%Y-%m-%d')
        date2_formatted = date2_obj.strftime('%Y-%m-%d')
        
        # Parse product identifiers if provided
        product_ids = []
        if product_identifiers:
            product_ids = [pid.strip() for pid in product_identifiers.split(',')]
        
        # Step 1: Check variance in reporting table
        reporting_variance = analyze_reporting_table(date1_formatted, date2_formatted, product_ids)
        
        # If no significant variance found in reporting, return early
        if not reporting_variance['sls_lines_with_variance']:
            return {
                "success": True,
                "date1": date1,
                "date2": date2,
                "message": "No significant variance found in the reporting table.",
                "product_identifiers": product_ids,
                "reporting_table_analysis": reporting_variance,
                "base_data_analysis": None,
                "sls_details_analysis": None
            }
        
        # Step 2: Check variance in base data for SLS lines with significant variance
        sls_lines_with_variance = reporting_variance['sls_lines_with_variance']
        base_data_variance = analyze_base_data_table(date1_formatted, date2_formatted, sls_lines_with_variance)
        
        # Step 3: Check variance in SLS details table for the same SLS lines
        sls_details_variance = analyze_sls_details_table(date1_formatted, date2_formatted, sls_lines_with_variance)
        
        # Compile all results
        return {
            "success": True,
            "date1": date1,
            "date2": date2,
            "product_identifiers": product_ids,
            "reporting_table_analysis": reporting_variance,
            "base_data_analysis": base_data_variance,
            "sls_details_analysis": sls_details_variance
        }
        
    except Exception as e:
        logger.error(f"Error in sls_details_variance: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "date1": date1,
            "date2": date2,
            "product_identifiers": product_identifiers
        }

def analyze_reporting_table(date1, date2, product_ids):
    """
    Analyze the reporting table to find SLS lines with significant variance.
    
    Args:
        date1 (str): First date in format YYYY-MM-DD
        date2 (str): Second date in format YYYY-MM-DD
        product_ids (list): List of product identifiers to check
        
    Returns:
        dict: Analysis results from the reporting table
    """
    try:
        # Build the product_identifier filter if product_ids are provided
        product_filter = ""
        if product_ids:
            product_filter = f"AND product_identifier IN ({', '.join([f\"'{pid}'\" for pid in product_ids])})"
        
        # Construct query for reporting table
        query = f"""
        SELECT sls.context_key, sls.cob_date, sls_line_number, basedata_context_key, sls.snapshot_label, 
               rcl.context_name, COUNT(*) AS count,
               SUM(ccf_flow_amt) AS ccf_flow_amt,
               SUM(xml_collateral_value_usd) AS xml_collateral_value_usd,
               SUM(xml_market_value_usd) AS xml_market_value_usd,
               SUM(xml_maturity_value_usd) AS xml_maturity_value_usd
        FROM lri_base.us_reg_2052a_reporting sls
        LEFT JOIN lri_base.result_context_list rcl ON sls.context_key = rcl.context_key
        WHERE sls.context_key IN (
            SELECT rcl.context_key FROM lri_base.result_context_list rcl
            WHERE rcl.cob_date IN ('{date1}', '{date2}')
            AND rcl.run_type = 'EOD'
            AND rcl.snapshot_label = 'FINAL'
            AND rcl.service_name IN ('FR2052A_REPORT')
        )
        {product_filter}
        GROUP BY 1, 2, 3, 4, 5, 6
        ORDER BY 3, 2, 1
        """
        
        logger.debug(f"Executing reporting table query: {query}")
        
        # Connect to Impala using pyodbc
        conn_string = "DSN=IMPALA_LRI_DR"
        cert = '/etc/security/certs/JPMCROOTCA.pem'
        
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
        
        # Perform variance analysis
        analysis_results = analyze_variance_in_dataframe(
            df, 
            'sls_line_number', 
            'ccf_flow_amt', 
            date1, 
            date2, 
            context_key_column='context_key',
            context_name_column='context_name'
        )
        
        return analysis_results
        
    except Exception as e:
        logger.error(f"Error analyzing reporting table: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def analyze_base_data_table(date1, date2, sls_lines):
    """
    Analyze the base data table for SLS lines with significant variance.
    
    Args:
        date1 (str): First date in format YYYY-MM-DD
        date2 (str): Second date in format YYYY-MM-DD
        sls_lines (list): List of SLS line numbers to check
        
    Returns:
        dict: Analysis results from the base data table
    """
    try:
        if not sls_lines:
            return {
                "message": "No SLS lines to analyze in base data table",
                "sls_lines_analyzed": [],
                "variance_data": [],
                "missing_pairs": []
            }
        
        # Build the SLS line filter
        sls_line_filter = f"AND sls.lri_position_str_sls_line_no IN ({', '.join([f\"'{line}'\" for line in sls_lines])})"
        
        # Construct query for base data table
        query = f"""
        SELECT sls.context_key, sls.cob_date, sls.lri_position_str_sls_line_no, 
               sls.sls_context_key, sls.snapshot_label, rcl.context_name, 
               COUNT(*) AS count, SUM(ccf_flow_amt) AS ccf_flow_amt
        FROM lri_base.us_reg_base_data sls
        LEFT JOIN lri_base.result_context_list rcl ON sls.context_key = rcl.context_key
        WHERE sls.context_key IN (
            SELECT rcl.context_key FROM lri_base.result_context_list rcl
            WHERE rcl.cob_date IN ('{date1}', '{date2}')
            AND rcl.run_type = 'EOD'
            AND rcl.snapshot_label = 'FINAL'
            AND rcl.service_name IN ('FR2052A_REPORT', 'SLS_REP.FR2052A_BASE_SUPPLY')
        )
        {sls_line_filter}
        AND sls.snapshot_label IN ('FINAL')
        GROUP BY 1, 2, 3, 4, 5, 6
        ORDER BY 3, 2, 1
        """
        
        logger.debug(f"Executing base data table query: {query}")
        
        # Connect to Impala using pyodbc
        conn_string = "DSN=IMPALA_LRI_DR"
        cert = '/etc/security/certs/JPMCROOTCA.pem'
        
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
        
        logger.debug(f"Base data query returned {len(df)} rows")
        
        # Perform variance analysis
        analysis_results = analyze_variance_in_dataframe(
            df, 
            'lri_position_str_sls_line_no', 
            'ccf_flow_amt', 
            date1, 
            date2, 
            context_key_column='context_key',
            context_name_column='context_name'
        )
        
        return analysis_results
        
    except Exception as e:
        logger.error(f"Error analyzing base data table: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def analyze_sls_details_table(date1, date2, sls_lines):
    """
    Analyze the SLS details table for SLS lines with significant variance.
    
    Args:
        date1 (str): First date in format YYYY-MM-DD
        date2 (str): Second date in format YYYY-MM-DD
        sls_lines (list): List of SLS line numbers to check
        
    Returns:
        dict: Analysis results from the SLS details table
    """
    try:
        if not sls_lines:
            return {
                "message": "No SLS lines to analyze in SLS details table",
                "sls_lines_analyzed": [],
                "variance_data": [],
                "missing_pairs": []
            }
        
        # Build the SLS line filter
        sls_line_filter = f"AND sls.lri_position_str_sls_line_no IN ({', '.join([f\"'{line}'\" for line in sls_lines])})"
        
        # Construct query for SLS details table
        query = f"""
        SELECT sls.context_key, sls.lri_position_str_cob_date, sls.lri_position_str_sls_line_no, 
               sls.snapshot_label, rcl.context_name, COUNT(*) AS count,
               SUM(ccf_flow_amt_base) AS ccf_flow_amt
        FROM lri_base.sls_details_prdl sls
        LEFT JOIN lri_base.result_context_list rcl ON sls.context_key = rcl.context_key
        WHERE sls.context_key IN (
            SELECT rcl.context_key FROM lri_base.result_context_list rcl
            WHERE rcl.cob_date IN ('{date1}', '{date2}')
            AND rcl.run_type = 'EOD'
            AND rcl.snapshot_label = 'FINAL'
            AND rcl.service_name IN ('SLS_REP_IMPALA')
        )
        {sls_line_filter}
        AND sls.snapshot_label IN ('FINAL')
        GROUP BY 1, 2, 3, 4, 5
        ORDER BY 3, 2, 1
        """
        
        logger.debug(f"Executing SLS details table query: {query}")
        
        # Connect to Impala using pyodbc
        conn_string = "DSN=IMPALA_LRI_DR"
        cert = '/etc/security/certs/JPMCROOTCA.pem'
        
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
        
        logger.debug(f"SLS details query returned {len(df)} rows")
        
        # Convert date column to match expected format
        if 'lri_position_str_cob_date' in df.columns:
            df['cob_date'] = df['lri_position_str_cob_date']
        
        # Perform variance analysis
        analysis_results = analyze_variance_in_dataframe(
            df, 
            'lri_position_str_sls_line_no', 
            'ccf_flow_amt', 
            date1, 
            date2, 
            context_key_column='context_key',
            context_name_column='context_name'
        )
        
        return analysis_results
        
    except Exception as e:
        logger.error(f"Error analyzing SLS details table: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def analyze_variance_in_dataframe(df, sls_line_column, amount_column, date1, date2, context_key_column='context_key', context_name_column='context_name'):
    """
    Generic function to analyze variance in a DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with the query results
        sls_line_column (str): Column name for SLS line number
        amount_column (str): Column name for the amount to analyze
        date1 (str): First date
        date2 (str): Second date
        context_key_column (str): Column name for context key
        context_name_column (str): Column name for context name
        
    Returns:
        dict: Analysis results
    """
    try:
        if df.empty:
            return {
                "message": "No data found for analysis",
                "sls_lines_analyzed": [],
                "variance_data": [],
                "missing_pairs": []
            }
        
        # Create a unique pair identifier for SLS line and context name
        df['pair_id'] = df[sls_line_column] + '|' + df[context_name_column]
        
        # Split data by date
        df1 = df[df['cob_date'] == date1].copy()
        df2 = df[df['cob_date'] == date2].copy()
        
        # Check if we have data for both dates
        if df1.empty or df2.empty:
            missing_dates = []
            if df1.empty:
                missing_dates.append(date1)
            if df2.empty:
                missing_dates.append(date2)
                
            return {
                "message": f"Missing data for dates: {', '.join(missing_dates)}",
                "sls_lines_analyzed": [],
                "variance_data": [],
                "missing_pairs": []
            }
        
        # Find unique SLS lines
        all_sls_lines = set(df[sls_line_column].dropna().unique())
        
        # Find all unique pairs
        all_pairs = set(df['pair_id'].dropna().unique())
        pairs_in_df1 = set(df1['pair_id'].dropna().unique())
        pairs_in_df2 = set(df2['pair_id'].dropna().unique())
        
        # Identify missing pairs
        missing_from_df1 = pairs_in_df2 - pairs_in_df1
        missing_from_df2 = pairs_in_df1 - pairs_in_df2
        
        # Prepare missing pairs data
        missing_pairs = []
        
        for pair in missing_from_df1:
            pair_data = df2[df2['pair_id'] == pair].iloc[0]
            missing_pairs.append({
                "sls_line": pair_data[sls_line_column],
                "context_name": pair_data[context_name_column],
                "context_key": pair_data[context_key_column],
                "missing_from": date1,
                "present_in": date2,
                "amount": float(pair_data[amount_column]) if pd.notna(pair_data[amount_column]) else None
            })
            
        for pair in missing_from_df2:
            pair_data = df1[df1['pair_id'] == pair].iloc[0]
            missing_pairs.append({
                "sls_line": pair_data[sls_line_column],
                "context_name": pair_data[context_name_column],
                "context_key": pair_data[context_key_column],
                "missing_from": date2,
                "present_in": date1,
                "amount": float(pair_data[amount_column]) if pd.notna(pair_data[amount_column]) else None
            })
        
        # Analyze variance for pairs present in both dates
        common_pairs = pairs_in_df1.intersection(pairs_in_df2)
        variance_data = []
        sls_lines_with_variance = set()
        
        for pair in common_pairs:
            row1 = df1[df1['pair_id'] == pair].iloc[0]
            row2 = df2[df2['pair_id'] == pair].iloc[0]
            
            # Skip pairs with null amounts
            if pd.isna(row1[amount_column]) or pd.isna(row2[amount_column]):
                continue
                
            amount1 = float(row1[amount_column])
            amount2 = float(row2[amount_column])
            
            # Calculate absolute and percentage variance
            absolute_variance = amount2 - amount1
            
            # Avoid division by zero
            if amount1 == 0:
                if amount2 == 0:
                    pct_variance = 0
                else:
                    pct_variance = float('inf')
            else:
                pct_variance = (absolute_variance / abs(amount1)) * 100
            
            # Check if variance exceeds threshold (10%)
            if abs(pct_variance) >= 10:
                sls_line = row1[sls_line_column]
                sls_lines_with_variance.add(sls_line)
                
                variance_data.append({
                    "sls_line": sls_line,
                    "context_name": row1[context_name_column],
                    "context_key_date1": row1[context_key_column],
                    "context_key_date2": row2[context_key_column],
                    "amount_date1": amount1,
                    "amount_date2": amount2,
                    "absolute_variance": absolute_variance,
                    "percentage_variance": pct_variance,
                    "pair_id": pair
                })
        
        # Sort variance data by absolute variance
        variance_data.sort(key=lambda x: abs(x['percentage_variance']), reverse=True)
        
        return {
            "message": f"Analysis completed. Found {len(variance_data)} pairs with significant variance (>=10%).",
            "sls_lines_analyzed": list(all_sls_lines),
            "sls_lines_with_variance": list(sls_lines_with_variance),
            "variance_data": variance_data,
            "missing_pairs": missing_pairs
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_variance_in_dataframe: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# Register the function
register_function("sls_details_variance", sls_details_variance)
