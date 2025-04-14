# backend/functions/get_6g_status.py
import json
import os
import logging
import cx_Oracle
import traceback
from datetime import datetime
from dateutil import parser
from functions.function_registry import register_function

logger = logging.getLogger(__name__)

# Load FR2052a configuration
def load_config():
    """Load FR2052a configuration from JSON file."""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  'config', 'fr2052a_config.json')
        with open(config_path, 'r') as config_file:
            return json.load(config_file)
    except Exception as e:
        logger.error(f"Error loading FR2052a configuration: {str(e)}")
        raise

def get_table_by_name_or_bpf(config, table_identifier):
    """Get table details by name or BPF ID."""
    if not table_identifier:
        return None
        
    # Try to find by name (case-insensitive partial match)
    for table in config['tables']:
        if table_identifier.lower() in table['name'].lower():
            return table
            
    # Try to find by BPF ID
    for table in config['tables']:
        if table_identifier == table['bpf_id']:
            return table
            
    return None

def format_date(date_str):
    """Format date string to DD-Mon-YYYY format for Oracle."""
    try:
        # Parse the input date string
        date_obj = parser.parse(date_str)
        # Format to Oracle's preferred format
        return date_obj.strftime('%d-%b-%Y')
    except Exception as e:
        logger.error(f"Error formatting date: {str(e)}")
        raise ValueError(f"Invalid date format: {date_str}. Please use MM-DD-YYYY format.")

def generate_sql_query(config, cob_date, table_identifier=None):
    """Generate SQL query based on configuration and parameters."""
    try:
        formatted_cob_date = format_date(cob_date)
        
        # Get process markers
        prelim_marker = config['process_markers']['prelim_end']
        sls_lock_marker = config['process_markers']['sls_lock_start']
        
        # Format SLS lock run types
        sls_lock_run_types = ", ".join([f"'{run_type}'" for run_type in sls_lock_marker['run_type']])
        
        # Create time window part of the query
        time_window_query = config['query_templates']['time_window'].format(
            prelim_bpf_id=prelim_marker['bpf_id'],
            prelim_process_id=prelim_marker['process_id'],
            prelim_run_type=prelim_marker['run_type'],
            sls_lock_bpf_id=sls_lock_marker['bpf_id'],
            sls_lock_process_id=sls_lock_marker['process_id'],
            sls_lock_run_types=sls_lock_run_types,
            cob_date=formatted_cob_date
        )
        
        # If a specific table is requested
        if table_identifier:
            table = get_table_by_name_or_bpf(config, table_identifier)
            if not table:
                raise ValueError(f"Table not found: {table_identifier}")
                
            return config['query_templates']['single_table'].format(
                time_window=time_window_query,
                bpf_id=table['bpf_id'],
                cob_date=formatted_cob_date
            )
        else:
            # All tables query
            all_bpf_ids = ", ".join([f"'{table['bpf_id']}'" for table in config['tables']])
            
            return config['query_templates']['all_tables'].format(
                time_window=time_window_query,
                bpf_ids=all_bpf_ids,
                cob_date=formatted_cob_date
            )
    except Exception as e:
        logger.error(f"Error generating SQL query: {str(e)}")
        raise

def execute_oracle_query(query):
    """Execute the Oracle query and return results."""
    try:
        # Get database connection parameters from environment
        oracle_user = os.environ.get('ORACLE_USER')
        oracle_password = os.environ.get('ORACLE_PASSWORD')
        oracle_host = os.environ.get('ORACLE_HOST')
        oracle_port = os.environ.get('ORACLE_PORT')
        oracle_service_name = os.environ.get('ORACLE_SERVICE_NAME')
        
        # Validate connection parameters
        if not all([oracle_user, oracle_password, oracle_host, oracle_port, oracle_service_name]):
            raise ValueError("Missing Oracle database connection parameters")
            
        # Create connection string
        dsn = cx_Oracle.makedsn(oracle_host, oracle_port, service_name=oracle_service_name)
        
        # Connect to Oracle
        connection = cx_Oracle.connect(
            user=oracle_user,
            password=oracle_password,
            dsn=dsn
        )
        
        logger.debug(f"Executing Oracle query: {query}")
        
        # Execute query
        cursor = connection.cursor()
        cursor.execute(query)
        
        # Fetch all data and column names
        data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        # Close cursor and connection
        cursor.close()
        connection.close()
        
        # Convert to list of dictionaries
        results = []
        for row in data:
            result_row = {}
            for i, column in enumerate(columns):
                result_row[column] = row[i]
            results.append(result_row)
            
        return results
    except cx_Oracle.Error as e:
        logger.error(f"Oracle error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def get_6g_status(cob_date, table_name=None):
    """
    Get the status of the FR2052a (6G) batch process for a specific date.
    
    Args:
        cob_date (str): The COB date in MM-DD-YYYY format
        table_name (str, optional): Specific table name or BPF ID to check
        
    Returns:
        dict: Status information for the 6G batch process
    """
    try:
        logger.info(f"Getting 6G status for COB date: {cob_date}, table: {table_name}")
        
        # Load configuration
        config = load_config()
        
        # Generate SQL query
        query = generate_sql_query(config, cob_date, table_name)
        
        # Execute query
        results = execute_oracle_query(query)
        
        # Process results
        if not results:
            return {
                "success": True,
                "cob_date": cob_date,
                "message": "No results found for the specified parameters",
                "tables_completed": 0,
                "total_tables": len(config['tables']),
                "tables": []
            }
            
        # Organize results by table
        tables_data = {}
        for row in results:
            bpf_id = row['BPF_ID']
            
            # Find table name from BPF ID
            table_info = next((t for t in config['tables'] if t['bpf_id'] == str(bpf_id)), None)
            if not table_info:
                continue
                
            # Format dates for output
            start_time = row['START_TIME'].strftime('%Y-%m-%d %H:%M:%S') if row['START_TIME'] else None
            end_time = row['END_TIME'].strftime('%Y-%m-%d %H:%M:%S') if row['END_TIME'] else None
            
            # Store table data
            tables_data[bpf_id] = {
                "bpf_id": str(bpf_id),
                "name": table_info['name'],
                "status": row['STATUS'],
                "process_name": row['PROCESS_NAME'],
                "start_time": start_time,
                "end_time": end_time,
                "duration_minutes": round((row['END_TIME'] - row['START_TIME']).total_seconds() / 60) if row['END_TIME'] and row['START_TIME'] else None
            }
            
        # Convert to list and sort by table ID
        tables_list = list(tables_data.values())
        tables_list.sort(key=lambda x: next((t['id'] for t in config['tables'] if t['bpf_id'] == x['bpf_id']), 999))
        
        # Create summary
        response = {
            "success": True,
            "cob_date": cob_date,
            "process_name": config['process_name'],
            "process_alias": config['process_alias'],
            "tables_completed": len(tables_list),
            "total_tables": len(config['tables']),
            "completion_percentage": round((len(tables_list) / len(config['tables'])) * 100),
            "tables": tables_list
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in get_6g_status: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "cob_date": cob_date,
            "table_name": table_name
        }

# Register the function
register_function("get_6g_status", get_6g_status)
