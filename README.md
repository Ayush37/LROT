# LROT Assistant

LROT Assistant is an interactive AI chatbot for financial analysis that integrates with Azure OpenAI. The application consists of a React frontend with Tailwind CSS and a Flask backend. The chatbot performs specific financial analysis functions based on user prompts.

## Features

- **Interactive Chat Interface**: Modern UI with real-time message display
- **Financial Analysis Functions**:
  - `SLS_DETAILS_VARIANCE`: Calculates variance in financial data between two dates
  - `TIME_REMAINING`: Provides current time and time remaining until EOD (5PM EST)
  - `GET_6G_STATUS`: Tracks the status of FR2052a (6G) batch process tables
- **Azure OpenAI Integration**: Leverages OpenAI's capabilities for natural language understanding
- **Database Connections**: Connects to Impala and Oracle databases for data retrieval and analysis

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- npm 6 or higher
- Access to Impala database
- Access to Oracle database
- Azure OpenAI API access
- Oracle JDBC driver (ojdbc8.jar)

## Installation

### Clone the Repository

```bash
git clone https://github.com/Ayush37/LROT.git
cd LROT
```

### Set Up Backend

1. Create and activate a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

2. Install required Python packages:

```bash
cd backend
pip install -r requirements.txt

# Additional packages for Oracle connectivity
pip install jaydebeapi JPype1 python-dateutil
```

3. Create a directory for the Oracle JDBC driver:

```bash
mkdir -p lib
```

4. Download the Oracle JDBC driver (ojdbc8.jar) and place it in the `lib` directory.

5. Create a configuration directory:

```bash
mkdir -p config
```

6. Create required certificate directories:

```bash
mkdir -p cert
```

### Set Up Frontend

1. Install frontend dependencies:

```bash
cd ../frontend
npm install
```

## Configuration

### Environment Variables

Create a `.env` file in the `backend` directory with the following variables:

```
# Azure OpenAI Configuration
AZURE_TENANT_ID=your_tenant_id
AZURE_SPN_CLIENT_ID=your_client_id
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=your_endpoint

# Impala Configuration
IMPALA_HOST=your_impala_host
IMPALA_PORT=your_impala_port

# Oracle Configuration
ORACLE_USER=your_oracle_username
ORACLE_PASSWORD=your_oracle_password
ORACLE_HOST=your_oracle_host
ORACLE_PORT=your_oracle_port
ORACLE_SERVICE_NAME=your_oracle_service_name
JDBC_DRIVER_PATH=lib/ojdbc8.jar

# Other Configuration
PORT=5000
FLASK_ENV=development
```

### FR2052a Configuration

Create a `fr2052a_config.json` file in the `backend/config` directory using the provided template:

```json
{
  "process_name": "FR2052a REPORT",
  "process_alias": "6G",
  "tables": [
    {
      "id": 1,
      "name": "Inflow Asset",
      "bpf_id": "6101"
    },
    ...
  ],
  "process_markers": {
    "prelim_end": {
      "bpf_id": "16011",
      "process_id": "1",
      "run_type": "EOD"
    },
    "sls_lock_start": {
      "bpf_id": "200163",
      "process_id": "1",
      "run_type": ["SOD", "EOD"]
    }
  },
  "query_templates": {
    ...
  }
}
```

### Azure OpenAI Certificate

Place your Azure OpenAI certificate file (`apim-exp.pem`) in the `backend/cert` directory.

## Running the Application

### Start the Backend Server

```bash
cd backend
python app.py
```

The Flask server should start on the default port 5000 (or the port specified in your configuration).

### Start the Frontend Server

In a new terminal window:

```bash
cd frontend
npm start
```

This will start the React development server, typically on port 3000. Your browser should automatically open to http://localhost:3000, showing the LROT Assistant interface.

## Using the Application

### Available Functions

1. **SLS_DETAILS_VARIANCE**: 
   - Query: "Calculate the variance for SLS details between [date1] and [date2]"
   - This will open a date selector for you to choose two dates for comparison

2. **TIME_REMAINING**:
   - Query: "How many hours of work left for today?"
   - Shows current time and time remaining until EOD (5PM EST)

3. **GET_6G_STATUS**:
   - Query: "What is the status of 6G batch process for [date]?"
   - Shows the completion status of FR2052a (6G) batch process tables

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   - Verify that your database credentials in the `.env` file are correct
   - Check network connectivity to the database servers
   - Ensure that the required certificates are in place

2. **Azure OpenAI Connection Issues**:
   - Check that the certificate is valid and properly located
   - Verify that your Azure OpenAI credentials are correct
   - Ensure the API endpoint is accessible from your network

3. **JDBC Driver Issues**:
   - Make sure ojdbc8.jar is properly placed in the specified directory
   - Verify that Java is installed and properly configured on your system
   - Try using the full path to the JDBC driver in your `.env` file

4. **Frontend API Connection**:
   - Check that the backend server is running
   - Verify the API URL in the frontend configuration
   - Check for CORS issues in the browser console

### Oracle JDBC Connection

If you're having issues with the Oracle connection:

1. Test the connection with a simple script:

```python
import jaydebeapi
import os
from dotenv import load_dotenv

load_dotenv()

oracle_user = os.environ.get('ORACLE_USER')
oracle_password = os.environ.get('ORACLE_PASSWORD')
oracle_host = os.environ.get('ORACLE_HOST')
oracle_port = os.environ.get('ORACLE_PORT')
oracle_service_name = os.environ.get('ORACLE_SERVICE_NAME')
jdbc_driver_path = os.environ.get('JDBC_DRIVER_PATH')

jdbc_url = f"jdbc:oracle:thin:@{oracle_host}:{oracle_port}/{oracle_service_name}"
jdbc_driver_class = "oracle.jdbc.OracleDriver"

try:
    connection = jaydebeapi.connect(
        jdbc_driver_class,
        jdbc_url,
        [oracle_user, oracle_password],
        jdbc_driver_path
    )
    print("Connection successful!")
    connection.close()
except Exception as e:
    print(f"Connection failed: {str(e)}")
```

2. Verify that your Java environment is properly set up:

```bash
java -version
```

## Production Deployment

For production deployment:

1. For the frontend:
   ```bash
   cd frontend
   npm run build
   ```
   This creates optimized files in the `build` folder that you can serve with any static file server.

2. For the backend, use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   cd backend
   gunicorn -w 4 app:app
   ```

## Directory Structure

```
lrot-chatbot/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.jsx
│   │   │   ├── ChatMessage.jsx
│   │   │   ├── DateSelector.jsx
│   │   │   └── Header.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── styles/
│   │   ├── App.js
│   │   └── index.js
│   ├── tailwind.config.js
│   └── package.json
└── backend/
    ├── api/
    │   ├── __init__.py
    │   └── chat_routes.py
    ├── services/
    │   ├── __init__.py
    │   ├── azure_openai.py
    │   └── function_router.py
    ├── functions/
    │   ├── __init__.py
    │   ├── sls_details_variance.py
    │   ├── time_remaining.py
    │   ├── get_6g_status.py
    │   └── function_registry.py
    ├── utils/
    │   ├── __init__.py
    │   ├── impala_connector.py
    │   └── date_utils.py
    ├── config/
    │   └── fr2052a_config.json
    ├── lib/
    │   └── ojdbc8.jar
    ├── cert/
    │   └── apim-exp.pem
    ├── app.py
    ├── config.py
    └── requirements.txt
```

## Contributing

When adding new functions to the LROT Assistant:

1. Create a new Python file in the `backend/functions/` directory
2. Implement your function with proper error handling
3. Register the function with the function registry
4. Update the `backend/functions/__init__.py` file to include your function
5. Add your function definition to the OpenAI function list in `azure_openai.py`
6. Update the frontend to handle and display your function results

## License

This project is proprietary and confidential.
