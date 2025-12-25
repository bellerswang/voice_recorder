import os
import glob
from datetime import datetime
from faster_whisper import WhisperModel

# Configuration
# Use a smaller model for CI to save time/resources, or 'large-v3-turbo' if speed is acceptable (~2-3x slower on CPU)
MODEL_SIZE = "medium" 
RECORDINGS_DIR = "recordings"

def transcribe_file(model, file_path):
    print(f"Transcribing {file_path} with model {MODEL_SIZE}...")
    try:
        segments, info = model.transcribe(file_path, beam_size=5)
        text = "".join([segment.text for segment in segments])
        return text.strip()
    except Exception as e:
        print(f"Error transcribing {file_path}: {e}")
        return None

def main():
    # 1. Find Files
    extensions = ['*.webm', '*.m4a', '*.wav', '*.mp3']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(RECORDINGS_DIR, ext)))
    
    files_to_process = []
    for audio_file in files:
        base_name = os.path.splitext(os.path.basename(audio_file))[0]
        md_file = os.path.join(RECORDINGS_DIR, f"{base_name}.md")
        
        if not os.path.exists(md_file):
            files_to_process.append(audio_file)
    
    if not files_to_process:
        print("No new files to transcribe.")
        return

    # 2. Load Model (only if needed)
    print(f"Loading '{MODEL_SIZE}' model... (this may take a moment)")
    # compute_type="int8" is good for CPU
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

    # 3. Process
    for audio_file in files_to_process:
        transcription = transcribe_file(model, audio_file)
        
        if transcription:
            base_name = os.path.splitext(os.path.basename(audio_file))[0]
            md_file = os.path.join(RECORDINGS_DIR, f"{base_name}.md")
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            content = f"**Timestamp:** {timestamp}\n\n**Transcription (GitHub Actions):**\n\n{transcription}"
            
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Generated {md_file}")

if __name__ == "__main__":
    main()
