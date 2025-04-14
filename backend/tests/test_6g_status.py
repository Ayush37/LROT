# backend/tests/test_6g_status.py
import os
import sys
import json
from dotenv import load_dotenv

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Import the function
from functions.get_6g_status import get_6g_status

def test_get_6g_status():
    """Test the get_6g_status function with different parameters."""
    # Test with a specific date (adjust as needed)
    cob_date = "04-03-2025"  # MM-DD-YYYY format
    
    print(f"Testing 6G status for COB date: {cob_date}")
    print("-" * 80)
    
    # Test getting status for all tables
    print("Getting status for all tables...")
    result = get_6g_status(cob_date)
    print(json.dumps(result, indent=2))
    print("-" * 80)
    
    # Test getting status for a specific table by name
    print("Getting status for Inflow Asset table...")
    result = get_6g_status(cob_date, "Inflow Asset")
    print(json.dumps(result, indent=2))
    print("-" * 80)
    
    # Test getting status for a specific table by BPF ID
    print("Getting status for table with BPF ID 6101...")
    result = get_6g_status(cob_date, "6101")
    print(json.dumps(result, indent=2))
    
    return True

if __name__ == "__main__":
    test_get_6g_status()
