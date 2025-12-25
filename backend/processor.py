import sys
import os
import logging

# Setup Path to include 'Util' directory
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

transcriber_instance = None

try:
    from multimedia_to_text import WhisperTranscriber
    # Initialize once if possible, or lazy init
    # We will lazy init in the function or global scope if arguments aren't needed
    # Assuming default init is fine. If it requires model_path, we might need to adjust.
    try:
        transcriber_instance = WhisperTranscriber()
    except Exception as e:
        print(f"Error initializing WhisperTranscriber: {e}")
        
except ImportError as e:
    print(f"ImportError: {e}")

def process_audio(file_path):
    """
    Process the audio file using the imported transcriber.
    Returns the transcription text.
    """
    global transcriber_instance
    if not transcriber_instance:
        return "Error: Transcriber module not loaded or initialized."

    print(f"Transcribing {file_path}...")
    
    try:
        # Check methods
        if hasattr(transcriber_instance, 'transcribe_to_text'):
            return transcriber_instance.transcribe_to_text(file_path)
        elif hasattr(transcriber_instance, 'transcribe'):
             return transcriber_instance.transcribe(file_path)
        else:
            return "Error: No suitable transcribe method found on WhisperTranscriber."

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
