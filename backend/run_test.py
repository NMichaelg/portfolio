import subprocess
import sys

# Define the exact testing command as a list
test_list_k = "auth or byok or password or chat_endpoint or stream_chat_response"

command = [
    "uv", "run", "pytest", "test.py",
    "-k", "tool",
    "-v"
]

try:
    # Run the command and stream output directly to the terminal
    subprocess.run(command, check=True)
except subprocess.CalledProcessError:
    sys.exit(1) # Exit with failure code if tests fail
