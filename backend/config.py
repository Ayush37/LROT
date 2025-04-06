# backend/config.py
import os

class Config:
    # Azure OpenAI Configuration
    AZURE_TENANT_ID = os.environ.get('AZURE_TENANT_ID', '')
    AZURE_SPN_CLIENT_ID = os.environ.get('AZURE_SPN_CLIENT_ID', '')
    AZURE_OPENAI_API_KEY = os.environ.get('AZURE_OPENAI_API_KEY', '')
    AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT', '')
    
    # Other configuration
    IMPALA_COMMAND = "impala.sh"
    EOD_HOUR = 17  # 5 PM EST
    EOD_TIMEZONE = "America/New_York"
