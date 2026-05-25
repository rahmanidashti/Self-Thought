import re
import io
import sys
import os
import signal
import time
from contextlib import contextmanager
from urllib.parse import urlparse

class TimeoutException(Exception):
    pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Code execution timed out")
    
    # Set the timeout handler
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Disable the alarm
        signal.alarm(0)

class Utils:

    def __init__(self, timeout_seconds=5):
        self.timeout_seconds = timeout_seconds

    def extract_and_execute_code(self, text):
        # Possible start and end markers
        code_start_markers = ["```python", "```Python", "```"]
        code_end_marker = "```"

        # Find python part
        code_start_index = -1
        code_start_marker_used = None
        for marker in code_start_markers:
            try:
                code_start_index = text.lower().find(marker.lower())
            except:
                continue
            if code_start_index != -1:
                code_start_marker_used = marker
                break

        # If find code
        if code_start_index != -1:
            # Try to find the end point
            code_end_index = text.find(code_end_marker, code_start_index + len(code_start_marker_used))
            
            # If not, we assume the code is appended to the end of the text
            if code_end_index == -1:
                code_end_index = len(text)
            
            # Extract the code
            code_str = text[code_start_index + len(code_start_marker_used):code_end_index].strip()
            
            # Clean up the code string
            for marker in code_start_markers:
                code_str = code_str.replace(marker, "")
            code_str = code_str.replace(code_end_marker, "").strip()

            # # Dictionary for executing code safely
            exec_globals = {}
            
            try:
                # Execute with timeout protection
                with time_limit(self.timeout_seconds):
                    exec(code_str, exec_globals)  # Execute the string
                result = exec_globals.get("result", None)  # Retrieve the result variable
                if result == None:
                    # Create a stream
                    old_stdout = sys.stdout
                    new_stdout = io.StringIO()
                    sys.stdout = new_stdout
                    
                    # Execute the code
                    try:
                        # Execute with timeout protection
                        with time_limit(self.timeout_seconds):
                            exec(code_str, globals())
                    except Exception as e:
                        # Primary output
                        sys.stdout = old_stdout
                        return f"An error occurred: {e}", code_str
                    
                    # Extract the output
                    sys.stdout = old_stdout
                    return new_stdout.getvalue(), code_str
                else:    
                    return result, code_str  # Return both result and the original code
            except Exception as e:
                return f"An error occurred: {e}", code_str
        else:
            return "No Python code found in the provided string.", None
        

def update_api_key(model):

    if model['is_azure'] is None:
        print("INFO:: Model is not an Azure model, skipping API key update.")
        return
    elif ("trapi.research.microsoft.com" in model['endpoint']):
        print("INFO:: Model is a TRAPI model, setting dummy API key.")
        model['api_key'] = ""
        return

    # Derive API key env var name from endpoint
    endpoint = model.get('endpoint')
    if not endpoint:
        raise ValueError(f"Endpoint not defined for model '{model['model_id']}'.")
    
    hostname = urlparse(endpoint).hostname
    if not hostname:
        raise ValueError(f"Could not parse hostname from endpoint '{endpoint}'.")
        
    endpoint_key_part = hostname.split('.')[0]
    env_var_name = f"{endpoint_key_part.upper().replace('-', '_')}_API_KEY"
    api_key = os.getenv(env_var_name)

    if not api_key:
        raise ValueError(f"API key environment variable '{env_var_name}' not set for endpoint '{endpoint}'.")
    
    model['api_key'] = api_key