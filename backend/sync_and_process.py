"""
Voice Recorder Sync & Process
- Pulls new recordings from GitHub
- Transcribes using local Whisper
- Uploads transcriptions to Google Drive
- Cleans up processed audio files
"""
import os
import sys
import glob
import json
import time
import random
import subprocess
import logging
from datetime import datetime

# Setup path for Util imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
python_scripts_root = os.path.dirname(project_root)
util_path = os.path.join(python_scripts_root, 'Util')
if util_path not in sys.path:
    sys.path.append(util_path)

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Import transcriber
try:
    from multimedia_to_text import WhisperTranscriber
    transcriber_instance = WhisperTranscriber()
except ImportError as e:
    print(f"Error importing WhisperTranscriber: {e}")
    transcriber_instance = None

# ======== Configuration ========
GDRIVE_FOLDER_ID = '1c6IZkrEqOQnzF3hyByxQGYgyVyeUfxsu'
CREDENTIALS_PATH = os.path.join(current_dir, 'credential', 'key.json')
RECORDINGS_DIR = os.path.join(project_root, 'recordings')
LOG_DIR = os.path.join(project_root, 'logs')
STATE_FILE = os.path.join(LOG_DIR, 'processed_state.json')

# API Settings
BASE_INTERVAL = 2.0
MAX_RETRIES = 3
JITTER_RANGE = (0.8, 1.2)

# Logging
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'sync_process.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class GoogleDocManager:
    def __init__(self):
        if not os.path.exists(CREDENTIALS_PATH):
            raise FileNotFoundError(f"Credentials not found at {CREDENTIALS_PATH}")
        
        self.creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_PATH,
            scopes=[
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/documents'
            ]
        )
        self.drive_service = build('drive', 'v3', credentials=self.creds)
        self.docs_service = build('docs', 'v1', credentials=self.creds)

    def _rate_limited_call(self, api_call, **kwargs):
        for attempt in range(MAX_RETRIES + 1):
            try:
                delay = BASE_INTERVAL * random.uniform(*JITTER_RANGE)
                time.sleep(delay)
                return api_call(**kwargs).execute()
            except HttpError as e:
                if e.resp.status in [429, 500, 503]:
                    backoff = delay * (2 ** attempt)
                    logging.warning(f"API error {e.resp.status}, retrying in {backoff:.1f}s...")
                    time.sleep(backoff)
                else:
                    raise
        raise Exception("API call exceeded max retries")

    def create_document(self, doc_name, content):
        """Create a new Google Doc with content"""
        try:
            # Create empty doc
            file_metadata = {
                'name': doc_name,
                'parents': [GDRIVE_FOLDER_ID],
                'mimeType': 'application/vnd.google-apps.document'
            }
            doc = self._rate_limited_call(
                self.drive_service.files().create,
                body=file_metadata,
                fields='id'
            )
            doc_id = doc['id']
            
            # Add content
            if content.strip():
                requests_body = {
                    'requests': [{
                        'insertText': {
                            'text': content,
                            'location': {'index': 1}
                        }
                    }]
                }
                self._rate_limited_call(
                    self.docs_service.documents().batchUpdate,
                    documentId=doc_id,
                    body=requests_body
                )
            
            logging.info(f"Created Google Doc: {doc_name}")
            return doc_id
        except Exception as e:
            logging.error(f"Failed to create document: {e}")
            return None


def run_git_command(args, cwd=project_root):
    try:
        result = subprocess.run(
            ['git'] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Git command failed: git {' '.join(args)}\n{e.stderr}")
        return None


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {'processed_files': []}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def transcribe_audio(file_path):
    if not transcriber_instance:
        return None
    
    try:
        if hasattr(transcriber_instance, 'transcribe_to_text'):
            return transcriber_instance.transcribe_to_text(file_path)
        elif hasattr(transcriber_instance, 'transcribe'):
            return transcriber_instance.transcribe(file_path)
    except Exception as e:
        logging.error(f"Transcription error: {e}")
    return None


def main():
    logging.info("=" * 50)
    logging.info("Starting Voice Recorder Sync & Process")
    
    # 1. Git Pull
    logging.info("Pulling latest from GitHub...")
    run_git_command(['pull'])
    
    # 2. Find new audio files
    extensions = ['*.webm', '*.m4a', '*.wav', '*.mp3']
    all_files = []
    for ext in extensions:
        all_files.extend(glob.glob(os.path.join(RECORDINGS_DIR, ext)))
    
    state = load_state()
    processed_set = set(state.get('processed_files', []))
    new_files = [f for f in all_files if os.path.basename(f) not in processed_set]
    
    if not new_files:
        logging.info("No new files to process.")
        return
    
    logging.info(f"Found {len(new_files)} new file(s) to process")
    
    # 3. Initialize Google Docs Manager
    try:
        gdocs = GoogleDocManager()
    except FileNotFoundError as e:
        logging.error(str(e))
        logging.error("Please place your Google API key.json in backend/credential/")
        return
    
    files_to_delete = []
    
    for audio_file in new_files:
        filename = os.path.basename(audio_file)
        logging.info(f"Processing: {filename}")
        
        # Transcribe
        text = transcribe_audio(audio_file)
        if not text:
            logging.warning(f"Empty or failed transcription for {filename}")
            text = "[No speech detected or transcription failed]"
        
        # Create Google Doc
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        doc_name = filename.replace('.webm', '').replace('.m4a', '').replace('.wav', '').replace('.mp3', '')
        doc_content = f"Recording: {filename}\nProcessed: {timestamp}\n\n{'='*40}\n\n{text}"
        
        doc_id = gdocs.create_document(doc_name, doc_content)
        
        if doc_id:
            # Mark as processed
            state['processed_files'].append(filename)
            save_state(state)
            files_to_delete.append(audio_file)
            logging.info(f"✅ Uploaded to Google Drive: {doc_name}")
        else:
            logging.error(f"❌ Failed to upload: {filename}")
    
    # 4. Clean up - delete processed audio files from GitHub
    if files_to_delete:
        logging.info("Cleaning up processed audio files from GitHub...")
        for f in files_to_delete:
            rel_path = os.path.relpath(f, project_root)
            run_git_command(['rm', rel_path])
        
        run_git_command(['commit', '-m', f'Processed {len(files_to_delete)} audio file(s)'])
        push_result = run_git_command(['push'])
        
        if push_result is not None:
            logging.info(f"✅ Deleted {len(files_to_delete)} audio file(s) from GitHub")
        else:
            logging.warning("Failed to push deletions to GitHub")
    
    logging.info("Done!")
    logging.info(f"View transcriptions: https://drive.google.com/drive/folders/{GDRIVE_FOLDER_ID}")


if __name__ == "__main__":
    main()
