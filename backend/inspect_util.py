import sys
import os

# Setup Path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # voice_recorder
python_scripts_root = os.path.dirname(project_root) # PythonScripts
util_path = os.path.join(python_scripts_root, 'Util')
sys.path.append(util_path)

try:
    import multimedia_to_text
    from multimedia_to_text import transcriber
    print("Transcriber submodule contents:", dir(transcriber))
    
    # Check WhisperTranscriber class methods
    if hasattr(multimedia_to_text, 'WhisperTranscriber'):
        print("WhisperTranscriber methods:", dir(multimedia_to_text.WhisperTranscriber))
        
except Exception as e:
    print(f"Error: {e}")
