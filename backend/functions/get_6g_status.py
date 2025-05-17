# backend/functions/get_6g_status.py
import json
import os
import logging
import jaydebeapi
import traceback
import pandas as pd
import numpy as np
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
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

def get_yarn_cluster_metrics():
    """Fetch current YARN cluster health metrics."""
    try:
        # Call YARN API
        url = "https://bdtashr36n15.svr.us.jpmchase.net:8090/ws/v1/cluster/metrics"
        
        # Disable SSL verification if needed (for internal certificates)
        response = requests.get(url, verify=False, timeout=10)
        response.raise_for_status()
        
        # Parse XML response
        root = ET.fromstring(response.text)
        
        # Extract metrics
        total_memory = int(root.find('totalMB').text)
        allocated_memory = int(root.find('allocatedMB').text)
        total_vcores = int(root.find('totalVirtualCores').text)
        allocated_vcores = int(root.find('allocatedVirtualCores').text)
        
        # Calculate utilization
        memory_utilization = (allocated_memory / total_memory) * 100 if total_memory > 0 else 0
        cpu_utilization = (allocated_vcores / total_vcores) * 100 if total_vcores > 0 else 0
        
        # Check if cluster is overloaded
        is_overloaded = memory_utilization > 90 or cpu_utilization > 90
        
        return {
            'memory_utilization': round(memory_utilization, 2),
            'cpu_utilization': round(cpu_utilization, 2),
            'is_overloaded': is_overloaded,
            'total_memory_mb': total_memory,
            'allocated_memory_mb': allocated_memory,
            'total_vcores': total_vcores,
            'allocated_vcores': allocated_vcores
        }
    except Exception as e:
        logger.error(f"Error fetching YARN metrics: {str(e)}")
        # Return default values if API call fails
        return {
            'memory_utilization': 0,
            'cpu_utilization': 0,
            'is_overloaded': False,
            'error': str(e)
        }
def get_yarn_cluster_metrics():
    """Fetch current YARN cluster health metrics."""
    try:
        import subprocess
        import json
        
        # Use curl to fetch the metrics
        url = "https://bdtashr36n15.svr.us.jpmchase.net:8090/ws/v1/cluster/metrics"
        
        # Run curl command
        result = subprocess.run(
            ['curl', '-k', url],  # -k flag ignores SSL certificate verification
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            raise Exception(f"Curl failed with return code {result.returncode}")
        
        # Parse JSON response
        data = json.loads(result.stdout)
        
        # Extract metrics from clusterMetrics
        cluster_metrics = data.get('clusterMetrics', {})
        
        total_memory = cluster_metrics.get('totalMB', 0)
        allocated_memory = cluster_metrics.get('allocatedMB', 0)
        total_vcores = cluster_metrics.get('totalVirtualCores', 0)
        allocated_vcores = cluster_metrics.get('allocatedVirtualCores', 0)
        
        # Calculate utilization
        memory_utilization = (allocated_memory / total_memory) * 100 if total_memory > 0 else 0
        cpu_utilization = (allocated_vcores / total_vcores) * 100 if total_vcores > 0 else 0
        
        # Check if cluster is overloaded
        is_overloaded = memory_utilization > 90 or cpu_utilization > 90
        
        return {
            'memory_utilization': round(memory_utilization, 2),
            'cpu_utilization': round(cpu_utilization, 2),
            'is_overloaded': is_overloaded,
            'total_memory_mb': total_memory,
            'allocated_memory_mb': allocated_memory,
            'total_vcores': total_vcores,
            'allocated_vcores': allocated_vcores,
            'apps_running': cluster_metrics.get('appsRunning', 0),
            'apps_pending': cluster_metrics.get('appsPending', 0),
            'active_nodes': cluster_metrics.get('activeNodes', 0),
            'total_nodes': cluster_metrics.get('totalNodes', 0)
        }
    except subprocess.TimeoutExpired:
        logger.error("Timeout while fetching YARN metrics")
        return {
            'memory_utilization': 0,
            'cpu_utilization': 0,
            'is_overloaded': False,
            'error': 'Timeout while fetching YARN metrics'
        }
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {str(e)}")
        return {
            'memory_utilization': 0,
            'cpu_utilization': 0,
            'is_overloaded': False,
            'error': f'Failed to parse JSON response: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Error fetching YARN metrics: {str(e)}")
        return {
            'memory_utilization': 0,
            'cpu_utilization': 0,
            'is_overloaded': False,
            'error': str(e)
        }
def get_historical_runtime_data(bpf_ids, days=30):
    """Get historical runtime data for the last N days."""
    try:
        # Get database connection parameters
        oracle_user = os.environ.get('ORACLE_USER')
        oracle_password = os.environ.get('ORACLE_PASSWORD')
        oracle_host = os.environ.get('ORACLE_HOST')
        oracle_port = os.environ.get('ORACLE_PORT')
        oracle_service_name = os.environ.get('ORACLE_SERVICE_NAME')
        jdbc_driver_path = os.environ.get('JDBC_DRIVER_PATH', 'ojdbc8.jar')
        jdbc_driver_class = "oracle.jdbc.driver.OracleDriver"
        
        # Create JDBC URL
        jdbc_url = f"jdbc:oracle:thin:@{oracle_host}:{oracle_port}/{oracle_service_name}"
        
        # Create BPF IDs string for SQL query
        bpf_ids_str = ", ".join([f"'{bpf_id}'" for bpf_id in bpf_ids])
        
        # SQL query for historical data
        query = f"""
        SELECT
            bpf_id,
            bpf_name,
            cob_date,
            start_time,
            end_time,
            status,
            TO_CHAR(start_time, 'HH24') as start_hour,
            TO_CHAR(start_time, 'D') as day_of_week,
            EXTRACT(DAY FROM cob_date) as day_of_month,
            (end_time - start_time) * 24 * 60 as duration_minutes
        FROM (
            SELECT
                bpf_id,
                bpf_name,
                cob_date,
                start_time,
                end_time,
                status
            FROM bpmdbo.v_bpf_run_instance_hist
            WHERE bpf_id IN ({bpf_ids_str})
                AND process_id = '10'
                AND status = 'COMPLETED'
                AND cob_date >= TRUNC(SYSDATE) - {days}
            UNION ALL
            SELECT
                bpf_id,
                bpf_name,
                cob_date,
                start_time,
                end_time,
                status
            FROM bpmdbo.v_bpf_run_instance
            WHERE bpf_id IN ({bpf_ids_str})
                AND process_id = '10'
                AND status = 'COMPLETED'
                AND cob_date >= TRUNC(SYSDATE) - {days}
        )
        ORDER BY bpf_id, cob_date DESC
        """
        
        # Connect to Oracle using jaydebeapi
        connection = jaydebeapi.connect(
            jdbc_driver_class,
            jdbc_url,
            [oracle_user, oracle_password],
            jdbc_driver_path
        )
        
        # Execute query
        cursor = connection.cursor()
        cursor.execute(query)
        
        # Fetch all data
        data = cursor.fetchall()
        
        # Get column names from cursor description
        column_names = [desc[0] for desc in cursor.description]
        
        # Close cursor and connection
        cursor.close()
        connection.close()
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(data, columns=column_names)
        
        # Convert data types
        df['BPF_ID'] = df['BPF_ID'].astype(str)
        df['START_HOUR'] = df['START_HOUR'].astype(int)
        df['DAY_OF_WEEK'] = df['DAY_OF_WEEK'].astype(int)
        df['DAY_OF_MONTH'] = df['DAY_OF_MONTH'].astype(int)
        df['DURATION_MINUTES'] = df['DURATION_MINUTES'].astype(float)
        
        return df
    except Exception as e:
        logger.error(f"Error getting historical runtime data: {str(e)}")
        logger.error(traceback.format_exc())
        return pd.DataFrame()  # Return empty DataFrame on error

def get_similar_days(day_of_week):
    """Get similar days for prediction (weekdays vs weekends)."""
    # 1 = Sunday, 2 = Monday, ..., 7 = Saturday (Oracle's day numbering)
    if day_of_week in [1, 7]:  # Weekend
        return [1, 7]
    else:  # Weekday
        return [2, 3, 4, 5, 6]

def predict_runtime_for_table(table_bpf_id, start_time, historical_data, cluster_metrics):
    """Predict runtime for a specific table using statistical approach."""
    try:
        # Filter historical data for this table
        table_history = historical_data[historical_data['BPF_ID'] == table_bpf_id]
        
        if table_history.empty:
            return {
                'predicted_duration': 30,  # Default 30 minutes if no history
                'lower_bound': 20,
                'upper_bound': 40,
                'confidence': 0,
                'adjustment_applied': 0
            }
        
        # Extract features from current run
        current_start_hour = start_time.hour
        # Oracle day of week: 1 = Sunday, 2 = Monday, ..., 7 = Saturday
        current_day_of_week = int(start_time.strftime('%w')) + 1
        
        # Get relevant historical runs (same hour ± 1, similar day type)
        similar_runs = table_history[
            (table_history['START_HOUR'].between(current_start_hour - 1, current_start_hour + 1)) &
            (table_history['DAY_OF_WEEK'].isin(get_similar_days(current_day_of_week)))
        ]
        
        # If not enough similar runs, use all data
        if len(similar_runs) < 5:
            similar_runs = table_history
        
        # Calculate base prediction (median of similar runs)
        base_prediction = similar_runs['DURATION_MINUTES'].median()
        
        # Adjust for cluster load
        adjustment = 0
        if cluster_metrics.get('is_overloaded', False):
            # Tables that typically run longer get more penalty
            long_running_tables = ['6101', '6103', '6112', '6108']  # Inflow Asset, Inflow Secured, etc.
            if table_bpf_id in long_running_tables:
                adjustment = 20  # 20 minutes
            else:
                adjustment = 10  # 10 minutes
        
        predicted_duration = base_prediction + adjustment
        
        # Calculate confidence interval (using IQR)
        q1 = similar_runs['DURATION_MINUTES'].quantile(0.25)
        q3 = similar_runs['DURATION_MINUTES'].quantile(0.75)
        
        return {
            'predicted_duration': predicted_duration,
            'lower_bound': max(q1, predicted_duration * 0.8),  # 80% of prediction as lower bound
            'upper_bound': min(q3, predicted_duration * 1.2),  # 120% of prediction as upper bound
            'confidence': len(similar_runs),
            'adjustment_applied': adjustment
        }
    except Exception as e:
        logger.error(f"Error predicting runtime: {str(e)}")
        # Return default values on error
        return {
            'predicted_duration': 30,
            'lower_bound': 20,
            'upper_bound': 40,
            'confidence': 0,
            'adjustment_applied': 0
        }

####def generate_sql_query(config, cob_date, table_identifier=None, include_running=False):
####    """Generate SQL query based on configuration and parameters."""
####    try:
####        formatted_cob_date = format_date(cob_date)
####        
####        # Get process markers
####        prelim_marker = config['process_markers']['prelim_end']
####        sls_lock_marker = config['process_markers']['sls_lock_start']
####        
####        # Format SLS lock run types
####        sls_lock_run_types = ", ".join([f"'{run_type}'" for run_type in sls_lock_marker['run_type']])
####        
####        # Create time window part of the query
####        time_window_query = config['query_templates']['time_window'].format(
####            prelim_bpf_id=prelim_marker['bpf_id'],
####            prelim_process_id=prelim_marker['process_id'],
####            prelim_run_type=prelim_marker['run_type'],
####            sls_lock_bpf_id=sls_lock_marker['bpf_id'],
####            sls_lock_process_id=sls_lock_marker['process_id'],
####            sls_lock_run_types=sls_lock_run_types,
####            cob_date=formatted_cob_date
####        )
####        
####        # Modify the status filter based on include_running parameter
####        status_filter = "status IN ('COMPLETED', 'RUNNING')" if include_running else "status = 'COMPLETED'"
####        
####        # Modify the query templates to include the new status filter
####        if table_identifier:
####            table = get_table_by_name_or_bpf(config, table_identifier)
####            if not table:
####                raise ValueError(f"Table not found: {table_identifier}")
####                
####            query = f"""{time_window_query}
####SELECT bpf_id, process_id, bpf_name, process_name, cob_date, status, start_time, end_time
####FROM (
####  SELECT bpf_id, process_id, bpf_name, process_name, cob_date, status, start_time, end_time
####  FROM bpmdbo.v_bpf_run_instance_hist
####  WHERE bpf_id = '{table['bpf_id']}'
####    AND process_id = '10'
####    AND cob_date = TO_DATE('{formatted_cob_date}', 'DD-Mon-YYYY')
####    AND {status_filter}
####    AND START_TIME >= (SELECT max_end_time_prelim FROM MaxTimes)
####    AND (status = 'RUNNING' OR 
####         (END_TIME <= (SELECT max_start_time_sls_lock FROM MaxTimes)
####          OR (SELECT max_start_time_sls_lock FROM MaxTimes) IS NULL))
####
####  UNION ALL
####
####  SELECT bpf_id, process_id, bpf_name, process_name, cob_date, status, start_time, end_time
####  FROM bpmdbo.v_bpf_run_instance
####  WHERE bpf_id = '{table['bpf_id']}'
####    AND process_id = '10'
####    AND cob_date = TO_DATE('{formatted_cob_date}', 'DD-Mon-YYYY')
####    AND {status_filter}
####    AND START_TIME >= (SELECT max_end_time_prelim FROM MaxTimes)
####    AND (status = 'RUNNING' OR 
####         (END_TIME <= (SELECT max_start_time_sls_lock FROM MaxTimes)
####          OR (SELECT max_start_time_sls_lock FROM MaxTimes) IS NULL))
####)
####ORDER BY END_TIME DESC"""
####        else:
####            # All tables query
####            all_bpf_ids = ", ".join([f"'{table['bpf_id']}'" for table in config['tables']])
####            
####            query = f"""{time_window_query}
####SELECT bpf_id, process_id, bpf_name, process_name, cob_date, status, start_time, end_time
####FROM (
####  SELECT bpf_id, process_id, bpf_name, process_name, cob_date, status, start_time, end_time
####  FROM bpmdbo.v_bpf_run_instance_hist
####  WHERE bpf_id IN ({all_bpf_ids})
####    AND process_id = '10'
####    AND cob_date = TO_DATE('{formatted_cob_date}', 'DD-Mon-YYYY')
####    AND {status_filter}
####    AND START_TIME >= (SELECT max_end_time_prelim FROM MaxTimes)
####    AND (status = 'RUNNING' OR 
####         (END_TIME <= (SELECT max_start_time_sls_lock FROM MaxTimes)
####          OR (SELECT max_start_time_sls_lock FROM MaxTimes) IS NULL))
####
####  UNION ALL
####
####  SELECT bpf_id, process_id, bpf_name, process_name, cob_date, status, start_time, end_time
####  FROM bpmdbo.v_bpf_run_instance
####  WHERE bpf_id IN ({all_bpf_ids})
####    AND process_id = '10'
####    AND cob_date = TO_DATE('{formatted_cob_date}', 'DD-Mon-YYYY')
####    AND {status_filter}
####    AND START_TIME >= (SELECT max_end_time_prelim FROM MaxTimes)
####    AND (status = 'RUNNING' OR 
####         (END_TIME <= (SELECT max_start_time_sls_lock FROM MaxTimes)
####          OR (SELECT max_start_time_sls_lock FROM MaxTimes) IS NULL))
####)
####ORDER BY bpf_id, END_TIME DESC"""
####        
####        return query
####    except Exception as e:
####        logger.error(f"Error generating SQL query: {str(e)}")
####        raise
def generate_sql_query(config, cob_date, table_identifier=None, include_running=False):
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
        
        # Modify the status filter based on include_running parameter
        if include_running:
            status_condition = """(
                status = 'RUNNING' 
                OR 
                (status = 'COMPLETED' AND 
                    (END_TIME <= (SELECT max_start_time_sls_lock FROM MaxTimes)
                     OR (SELECT max_start_time_sls_lock FROM MaxTimes) IS NULL)
                )
            )"""
        else:
            status_condition = """status = 'COMPLETED' 
                AND (END_TIME <= (SELECT max_start_time_sls_lock FROM MaxTimes)
                     OR (SELECT max_start_time_sls_lock FROM MaxTimes) IS NULL)"""
        
        # Build query for single table or all tables
        if table_identifier:
            table = get_table_by_name_or_bpf(config, table_identifier)
            if not table:
                raise ValueError(f"Table not found: {table_identifier}")
                
            query = f"""{time_window_query}
SELECT bpf_id, process_id, bpf_name, process_name, cob_date, status, start_time, end_time
FROM (
  SELECT bpf_id, process_id, bpf_name, process_name, cob_date, status, start_time, end_time
  FROM bpmdbo.v_bpf_run_instance_hist
  WHERE bpf_id = '{table['bpf_id']}'
    AND process_id = '10'
    AND cob_date = TO_DATE('{formatted_cob_date}', 'DD-Mon-YYYY')
    AND START_TIME >= (SELECT max_end_time_prelim FROM MaxTimes)
    AND {status_condition}

  UNION ALL

  SELECT bpf_id, process_id, bpf_name, process_name, cob_date, status, start_time, end_time
  FROM bpmdbo.v_bpf_run_instance
  WHERE bpf_id = '{table['bpf_id']}'
    AND process_id = '10'
    AND cob_date = TO_DATE('{formatted_cob_date}', 'DD-Mon-YYYY')
    AND START_TIME >= (SELECT max_end_time_prelim FROM MaxTimes)
    AND {status_condition}
)
ORDER BY END_TIME DESC"""
        else:
            # All tables query
            all_bpf_ids = ", ".join([f"'{table['bpf_id']}'" for table in config['tables']])
            
            query = f"""{time_window_query}
SELECT bpf_id, process_id, bpf_name, process_name, cob_date, status, start_time, end_time
FROM (
  SELECT bpf_id, process_id, bpf_name, process_name, cob_date, status, start_time, end_time
  FROM bpmdbo.v_bpf_run_instance_hist
  WHERE bpf_id IN ({all_bpf_ids})
    AND process_id = '10'
    AND cob_date = TO_DATE('{formatted_cob_date}', 'DD-Mon-YYYY')
    AND START_TIME >= (SELECT max_end_time_prelim FROM MaxTimes)
    AND {status_condition}

  UNION ALL

  SELECT bpf_id, process_id, bpf_name, process_name, cob_date, status, start_time, end_time
  FROM bpmdbo.v_bpf_run_instance
  WHERE bpf_id IN ({all_bpf_ids})
    AND process_id = '10'
    AND cob_date = TO_DATE('{formatted_cob_date}', 'DD-Mon-YYYY')
    AND START_TIME >= (SELECT max_end_time_prelim FROM MaxTimes)
    AND {status_condition}
)
ORDER BY bpf_id, END_TIME DESC"""
        
        return query
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
        
        # JDBC driver path and class
        jdbc_driver_path = os.environ.get('JDBC_DRIVER_PATH', 'ojdbc8.jar')
        jdbc_driver_class = "oracle.jdbc.driver.OracleDriver"
        
        # Create JDBC URL
        jdbc_url = f"jdbc:oracle:thin:@{oracle_host}:{oracle_port}/{oracle_service_name}"
        
        logger.debug(f"JDBC URL: {jdbc_url}")
        logger.debug(f"Executing Oracle query: {query}")
        
        # Connect to Oracle using jaydebeapi
        connection = jaydebeapi.connect(
            jdbc_driver_class,
            jdbc_url,
            [oracle_user, oracle_password],
            jdbc_driver_path
        )
        
        # Execute query
        cursor = connection.cursor()
        cursor.execute(query)
        
        # Fetch all data
        data = cursor.fetchall()
        
        # Get column names from cursor description
        column_names = [desc[0] for desc in cursor.description]
        
        # Close cursor and connection
        cursor.close()
        connection.close()
        
        # Convert to list of dictionaries
        results = []
        for row in data:
            result_row = {}
            for i, column in enumerate(column_names):
                # Handle special data types (dates, etc.)
                value = row[i]
                if isinstance(value, (datetime,)):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                result_row[column] = value
            results.append(result_row)
            
        return results
    except Exception as e:
        logger.error(f"Oracle error: {str(e)}")
        logger.error(traceback.format_exc())
        raise




###def get_6g_status(cob_date, table_name=None):
###   """
###   Get the status of the FR2052a (6G) batch process for a specific date.
###   
###   Args:
###       cob_date (str): The COB date in MM-DD-YYYY format
###       table_name (str, optional): Specific table name or BPF ID to check
###       
###   Returns:
###       dict: Status information for the 6G batch process
###   """
###   try:
###       logger.info(f"Getting 6G status for COB date: {cob_date}, table: {table_name}")
###       
###       # Load configuration
###       config = load_config()
###       
###       # Get all BPF IDs for historical data
###       all_bpf_ids = [table['bpf_id'] for table in config['tables']]
###       
###       # Get historical runtime data
###       historical_data = get_historical_runtime_data(all_bpf_ids, days=30)
###       
###       # Get current YARN cluster metrics
###       try:
###           cluster_metrics = get_yarn_cluster_metrics()
###       except Exception as e:
###           logger.warning(f"Failed to get YARN metrics: {str(e)}")
###           cluster_metrics = {'is_overloaded': False, 'memory_utilization': 0, 'cpu_utilization': 0}
###       
###       # Generate SQL query (include RUNNING tables)
###       query = generate_sql_query(config, cob_date, table_name, include_running=True)
###       
###       # Execute query
###       results = execute_oracle_query(query)
###       
###       # Process results
###       if not results:
###           return {
###               "success": True,
###               "cob_date": cob_date,
###               "message": "No results found for the specified parameters",
###               "tables_completed": 0,
###               "tables_running": 0,
###               "tables_pending": len(config['tables']),
###               "total_tables": len(config['tables']),
###               "tables": []
###           }
###           
###       # Organize results by table
###       tables_data = {}
###       tables_completed = 0
###       tables_running = 0
###       current_time = datetime.now()
###       
###       for row in results:
###           bpf_id = str(row['BPF_ID'])  # Ensure bpf_id is a string
###           status = row['STATUS']
###           
###           # Find table name from BPF ID
###           table_info = next((t for t in config['tables'] if t['bpf_id'] == bpf_id), None)
###           if not table_info:
###               continue
###               
###           # Get start and end times
###           start_time = row['START_TIME']
###           end_time = row['END_TIME']
###           
###           # Parse start_time for predictions
###           if isinstance(start_time, str):
###               start_time_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
###           else:
###               start_time_dt = start_time
###           
###           # Basic table data
###           table_data = {
###               "bpf_id": bpf_id,
###               "name": table_info['name'],
###               "status": status,
###               "process_name": row.get('PROCESS_NAME', ''),
###               "start_time": start_time,
###               "end_time": end_time
###           }
###           
###           if status == 'COMPLETED':
###               tables_completed += 1
###               # Calculate duration in minutes if both times are available
###               if isinstance(start_time, str) and isinstance(end_time, str):
###                   try:
###                       start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
###                       end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
###                       duration_minutes = round((end_dt - start_dt).total_seconds() / 60)
###                       table_data['duration_minutes'] = duration_minutes
###                   except Exception as e:
###                       logger.warning(f"Could not calculate duration: {str(e)}")
###           
###           elif status == 'RUNNING':
###               tables_running += 1
###               # Calculate elapsed time
###               elapsed_minutes = round((current_time - start_time_dt).total_seconds() / 60)
###               table_data['elapsed_minutes'] = elapsed_minutes
###               
###               # Predict remaining time
###               if not historical_data.empty:
###                   prediction = predict_runtime_for_table(
###                       bpf_id, start_time_dt, historical_data, cluster_metrics
###                   )
###                   
###                   remaining_minutes = max(0, prediction['predicted_duration'] - elapsed_minutes)
###                   estimated_completion = current_time + timedelta(minutes=remaining_minutes)
###                   
###                   table_data.update({
###                       'predicted_duration': round(prediction['predicted_duration'], 1),
###                       'estimated_remaining_minutes': round(remaining_minutes, 1),
###                       'estimated_completion_time': estimated_completion.strftime('%Y-%m-%d %H:%M:%S'),
###                       'prediction_confidence': prediction['confidence'],
###                       'prediction_range': f"{round(prediction['lower_bound'], 1)}-{round(prediction['upper_bound'], 1)} mins",
###                       'cluster_adjustment': prediction['adjustment_applied']
###                   })
###               else:
###                   # Fallback if no historical data
###                   table_data.update({
###                       'predicted_duration': 30,
###                       'estimated_remaining_minutes': 30,
###                       'estimated_completion_time': (current_time + timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S'),
###                       'prediction_confidence': 0,
###                       'prediction_range': "20-40 mins",
###                       'cluster_adjustment': 0
###                   })
###           
###           # Store table data
###           tables_data[bpf_id] = table_data
###       
###       # Convert to list and sort by table ID
###       tables_list = list(tables_data.values())
###       tables_list.sort(key=lambda x: next((t['id'] for t in config['tables'] if t['bpf_id'] == x['bpf_id']), 999))
###       
###       # Calculate pending tables
###       tables_pending = len(config['tables']) - tables_completed - tables_running
###       
###       # Create summary
###       response = {
###           "success": True,
###           "cob_date": cob_date,
###           "process_name": config['process_name'],
###           "process_alias": config['process_alias'],
###           "tables_completed": tables_completed,
###           "tables_running": tables_running,
###           "tables_pending": tables_pending,
###           "total_tables": len(config['tables']),
###           "completion_percentage": round((tables_completed / len(config['tables'])) * 100),
###           "cluster_health": {
###               "memory_utilization": cluster_metrics.get('memory_utilization', 0),
###               "cpu_utilization": cluster_metrics.get('cpu_utilization', 0),
###               "is_overloaded": cluster_metrics.get('is_overloaded', False)
###           },
###           "tables": tables_list
###       }
###       
###       return response
###       
###   except Exception as e:
###       logger.error(f"Error in get_6g_status: {str(e)}")
###       logger.error(traceback.format_exc())
###       return {
###           "success": False,
###           "error": str(e),
###           "cob_date": cob_date,
###           "table_name": table_name
###       }
        
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
        
        # Get all BPF IDs for historical data
        all_bpf_ids = [table['bpf_id'] for table in config['tables']]
        
        # Get historical runtime data
        historical_data = get_historical_runtime_data(all_bpf_ids, days=30)
        
        # Get current YARN cluster metrics
        try:
            cluster_metrics = get_yarn_cluster_metrics()
        except Exception as e:
            logger.warning(f"Failed to get YARN metrics: {str(e)}")
            cluster_metrics = {'is_overloaded': False, 'memory_utilization': 0, 'cpu_utilization': 0}
        
        # Generate SQL query (include RUNNING tables)
        query = generate_sql_query(config, cob_date, table_name, include_running=True)
        
        # Execute query
        results = execute_oracle_query(query)
        
        # Process results
        tables_data = {}
        tables_completed = 0
        tables_running = 0
        current_time = datetime.now()
        
        # First, process actual results from the database
        for row in results:
            bpf_id = str(row['BPF_ID'])
            status = row['STATUS']
            
            # Find table name from BPF ID
            table_info = next((t for t in config['tables'] if t['bpf_id'] == bpf_id), None)
            if not table_info:
                continue
                
            # Get start and end times
            start_time = row['START_TIME']
            end_time = row['END_TIME']
            
            # Parse start_time for predictions
            if isinstance(start_time, str):
                start_time_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            else:
                start_time_dt = start_time
            
            # Basic table data
            table_data = {
                "bpf_id": bpf_id,
                "name": table_info['name'],
                "status": status,
                "process_name": row.get('PROCESS_NAME', ''),
                "start_time": start_time,
                "end_time": end_time
            }
            
            if status == 'COMPLETED':
                tables_completed += 1
                # Calculate duration
                if isinstance(start_time, str) and isinstance(end_time, str):
                    try:
                        start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                        end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                        duration_minutes = round((end_dt - start_dt).total_seconds() / 60)
                        table_data['duration_minutes'] = duration_minutes
                    except Exception as e:
                        logger.warning(f"Could not calculate duration: {str(e)}")
            
            elif status == 'RUNNING':
                tables_running += 1
                # Calculate elapsed time
                elapsed_minutes = round((current_time - start_time_dt).total_seconds() / 60)
                table_data['elapsed_minutes'] = elapsed_minutes
                
                # Predict remaining time
                if not historical_data.empty:
                    prediction = predict_runtime_for_table(
                        bpf_id, start_time_dt, historical_data, cluster_metrics
                    )
                    
                    remaining_minutes = max(0, prediction['predicted_duration'] - elapsed_minutes)
                    estimated_completion = current_time + timedelta(minutes=remaining_minutes)
                    
                    table_data.update({
                        'predicted_duration': round(prediction['predicted_duration'], 1),
                        'estimated_remaining_minutes': round(remaining_minutes, 1),
                        'estimated_completion_time': estimated_completion.strftime('%Y-%m-%d %H:%M:%S'),
                        'prediction_confidence': prediction['confidence'],
                        'prediction_range': f"{round(prediction['lower_bound'], 1)}-{round(prediction['upper_bound'], 1)} mins",
                        'cluster_adjustment': prediction['adjustment_applied']
                    })
            
            # Store table data
            tables_data[bpf_id] = table_data
        
        # Now, add information for tables that haven't started yet
        for table_config in config['tables']:
            bpf_id = table_config['bpf_id']
            if bpf_id not in tables_data:
                # This table hasn't started yet (PENDING)
                table_data = {
                    "bpf_id": bpf_id,
                    "name": table_config['name'],
                    "status": "PENDING",
                    "process_name": "",
                    "start_time": None,
                    "end_time": None
                }
                
                # Add historical statistics for pending tables
                if not historical_data.empty:
                    table_history = historical_data[historical_data['BPF_ID'] == bpf_id]
                    if not table_history.empty:
                        avg_duration = table_history['DURATION_MINUTES'].mean()
                        median_duration = table_history['DURATION_MINUTES'].median()
                        min_duration = table_history['DURATION_MINUTES'].min()
                        max_duration = table_history['DURATION_MINUTES'].max()
                        
                        table_data.update({
                            'historical_avg_duration': round(avg_duration, 1),
                            'historical_median_duration': round(median_duration, 1),
                            'historical_range': f"{round(min_duration, 1)}-{round(max_duration, 1)} mins",
                            'historical_runs': len(table_history)
                        })
                
                tables_data[bpf_id] = table_data
        
        # Calculate pending tables
        tables_pending = len(config['tables']) - tables_completed - tables_running
        
        # Convert to list and sort by table ID
        tables_list = list(tables_data.values())
        tables_list.sort(key=lambda x: next((t['id'] for t in config['tables'] if t['bpf_id'] == x['bpf_id']), 999))
        
        # Add overall statistics
        overall_stats = {}
        if not historical_data.empty:
            # Calculate average total runtime for all tables
            daily_totals = historical_data.groupby('COB_DATE')['DURATION_MINUTES'].sum()
            overall_stats = {
                'avg_total_runtime': round(daily_totals.mean(), 1),
                'median_total_runtime': round(daily_totals.median(), 1),
                'min_total_runtime': round(daily_totals.min(), 1),
                'max_total_runtime': round(daily_totals.max(), 1),
                'historical_days': len(daily_totals)
            }
        
        # Create summary
        response = {
            "success": True,
            "cob_date": cob_date,
            "process_name": config['process_name'],
            "process_alias": config['process_alias'],
            "tables_completed": tables_completed,
            "tables_running": tables_running,
            "tables_pending": tables_pending,
            "total_tables": len(config['tables']),
            "completion_percentage": round((tables_completed / len(config['tables'])) * 100),
            "cluster_health": {
                "memory_utilization": cluster_metrics.get('memory_utilization', 0),
                "cpu_utilization": cluster_metrics.get('cpu_utilization', 0),
                "is_overloaded": cluster_metrics.get('is_overloaded', False)
            },
            "overall_statistics": overall_stats,
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