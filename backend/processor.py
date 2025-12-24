import sys
import os
import logging

# Setup Path to include 'Util' directory
# Assuming structure:
# .../PythonScripts/
#       |-- voice_recorder/backend/processor.py
#       |-- Util/multimedia_to_text/
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # voice_recorder
python_scripts_root = os.path.dirname(project_root) # PythonScripts
util_path = os.path.join(python_scripts_root, 'Util')

if os.path.exists(util_path):
    if util_path not in sys.path:
        sys.path.append(util_path)
    print(f"Added {util_path} to sys.path")
else:
    print(f"Warning: Util directory not found at {util_path}")

# Attempt to import the transcriber
# User instructions: "calls the transcription functions from your Util folder"
try:
    # Try generic import first. Adjust this based on actual Util structure.
    # If the folder is 'multimedia_to_text' inside 'Util':
    from multimedia_to_text import main as transcriber_module
    # OR if it's directly in Util:
    # import multimedia_to_text as transcriber_module
except ImportError as e:
    print(f"ImportError: {e}")
    transcriber_module = None

def process_audio(file_path):
    """
    Process the audio file using the imported transcriber.
    Returns the transcription text.
    """
    if not transcriber_module:
        return "Error: Transcriber module not loaded. Check processor.py imports."

    print(f"Transcribing {file_path}...")
    
    try:
        # Assuming a 'transcribe' or 'process' function exists. 
        # You may need to adjust this function name matches your Util code.
        if hasattr(transcriber_module, 'transcribe_file'):
            return transcriber_module.transcribe_file(file_path)
        elif hasattr(transcriber_module, 'transcribe'):
            return transcriber_module.transcribe(file_path)
        elif hasattr(transcriber_module, 'main'):
             # Some scripts use main(args)
             return transcriber_module.main(file_path)
        else:
            # Fallback: try to find a callable
            for attr_name in dir(transcriber_module):
                attr = getattr(transcriber_module, attr_name)
                if callable(attr) and 'transcribe' in attr_name.lower():
                    return attr(file_path)
            
            return "Error: Could not find a suitable transcribe function in module."

    except Exception as e:
        print(f"Error during transcription: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python processor.py <audio_file_path>")
        sys.exit(1)
    
    path = sys.argv[1]
    result = process_audio(path)
    print("Transcription Result:")
    print(result)
