# backend/functions/sls_details_variance.py
import subprocess
import json
import pandas as pd
from functions.function_registry import register_function
from config import Config

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
        # Construct query
        query = f"""
        SELECT sls.lri_position_str_cob_date as cob_date,
        sls.snapshot_label, sls.context_key, rcl.context_name,
        sls.lri_position_str_sls_line_no as sls_line_number,
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
            AND rcl.snapshot_label = 'SLS_LOCK'
            AND rcl.ctx_status = 'COMPLETED'
            AND rcl.service_name = 'SLS_REP_IMPALA'
            AND context_name NOT IN ('AWS_FNO_COLLATERAL_SLS_IC', 'AWS_DIVIDENDS_SLS_AND_IC')
        )
        AND sls.snapshot_label = 'SLS_LOCK'
        GROUP BY 1, 2, 3, 4, 5
        """
        
        # Execute query using impala.sh
        cmd = f"{Config.IMPALA_COMMAND} -q \"{query}\" --output_delimiter=, -B"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            return {"error": f"Impala query failed: {stderr.decode('utf-8')}"}
        
        # Convert result to DataFrame
        result_data = stdout.decode('utf-8')
        
        # Create DataFrame from CSV data
        df = pd.read_csv(pd.io.common.StringIO(result_data))
        
        # Pivot the data to separate by date
        date1_data = df[df['cob_date'] == date1]
        date2_data = df[df['cob_date'] == date2]
        
        # Merge the data on sls_line_number
        merged_df = pd.merge(
            date1_data, 
            date2_data, 
            on='sls_line_number', 
            suffixes=('_date1', '_date2'),
            how='outer'
        )
        
        # Calculate variance
        merged_df['amt_reporting_measure_variance'] = merged_df['amt_reporting_measure_date2'] - merged_df['amt_reporting_measure_date1']
        merged_df['amt_cof_flow_variance'] = merged_df['amt_cof_flow_date2'] - merged_df['amt_cof_flow_date1']
        merged_df['amt_curr_mkt_value_variance'] = merged_df['amt_curr_mkt_value_date2'] - merged_df['amt_curr_mkt_value_date1']
        
        # Calculate percent variance
        merged_df['amt_reporting_measure_pct'] = (merged_df['amt_reporting_measure_variance'] / merged_df['amt_reporting_measure_date1']) * 100
        merged_df['amt_cof_flow_pct'] = (merged_df['amt_cof_flow_variance'] / merged_df['amt_cof_flow_date1']) * 100
        merged_df['amt_curr_mkt_value_pct'] = (merged_df['amt_curr_mkt_value_variance'] / merged_df['amt_curr_mkt_value_date1']) * 100
        
        # Fill NaN with 0
        merged_df = merged_df.fillna(0)
        
        # Convert to dict
        variance_data = merged_df[[
            'sls_line_number', 
            'amt_reporting_measure_date1', 'amt_reporting_measure_date2', 'amt_reporting_measure_variance', 'amt_reporting_measure_pct',
            'amt_cof_flow_date1', 'amt_cof_flow_date2', 'amt_cof_flow_variance', 'amt_cof_flow_pct',
            'amt_curr_mkt_value_date1', 'amt_curr_mkt_value_date2', 'amt_curr_mkt_value_variance', 'amt_curr_mkt_value_pct'
        ]].to_dict(orient='records')
        
        # Create summary data
        summary = {
            "date1": date1,
            "date2": date2,
            "total_lines": len(variance_data),
            "lines_with_variance": len([x for x in variance_data if 
                                       x['amt_reporting_measure_variance'] != 0 or 
                                       x['amt_cof_flow_variance'] != 0 or 
                                       x['amt_curr_mkt_value_variance'] != 0]),
            "threshold_crossed": any([
                abs(x['amt_reporting_measure_pct']) > 10 or 
                abs(x['amt_cof_flow_pct']) > 10 or 
                abs(x['amt_curr_mkt_value_pct']) > 10 
                for x in variance_data if x['amt_reporting_measure_date1'] != 0 and 
                                          x['amt_cof_flow_date1'] != 0 and 
                                          x['amt_curr_mkt_value_date1'] != 0
            ])
        }
        
        return {
            "summary": summary,
            "variance_data": variance_data
        }
        
    except Exception as e:
        return {"error": str(e)}

# Register the function
register_function("sls_details_variance", sls_details_variance)
