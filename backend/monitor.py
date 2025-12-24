import time
import os
import subprocess
import glob
import logging
from datetime import datetime
try:
    from processor import process_audio
except ImportError:
    # If running from backend folder
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from processor import process_audio

# Configuration
REPO_DIR = os.path.dirname(os.path.abspath(__file__)) # Assuming monitor.py is in backend/, repo root is up one level? 
# Use absolute path to the project root
PROJECT_ROOT = os.path.dirname(REPO_DIR) # voice_recorder
RECORDINGS_DIR = os.path.join(PROJECT_ROOT, 'recordings')
POLL_INTERVAL = 300 # 5 minutes

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(REPO_DIR, 'monitor.log')),
        logging.StreamHandler()
    ]
)

def run_git_command(args, cwd=PROJECT_ROOT):
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
        logging.error(f"Git command failed: git {' '.join(args)}\nError: {e.stderr}")
        return None

def setup_git_auth():
    """
    Helper to ensure remote includes PAT if provided in env vars.
    NOTE: Storing PAT in remote URL is one way, but using Credential Manager is safer.
    If the user wants strictly PAT based:
    """
    pat = os.environ.get('GITHUB_PAT')
    username = os.environ.get('GITHUB_USER')
    repo = os.environ.get('GITHUB_REPO')
    
    if pat and username and repo:
        remote_url = f"https://{username}:{pat}@github.com/{username}/{repo}.git"
        logging.info("Configuring git remote with PAT...")
        run_git_command(['remote', 'set-url', 'origin', remote_url])
    elif not pat:
        logging.warning("GITHUB_PAT environment variable not set. Relying on existing git credentials.")

def process_new_files():
    # 1. Pull latest changes
    logging.info("Pulling changes from GitHub...")
    pull_res = run_git_command(['pull'])
    if pull_res is None:
        logging.warning("Git pull failed. Skipping this cycle.")
        # Continue anyway to process local files if any
    
    # 2. Scan for recordings
    if not os.path.exists(RECORDINGS_DIR):
        logging.info(f"Recordings directory {RECORDINGS_DIR} does not exist (yet).")
        return

    extensions = ['*.webm', '*.m4a', '*.wav', '*.mp3']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(RECORDINGS_DIR, ext)))
    
    changes_made = False

    for audio_file in files:
        base_name = os.path.splitext(os.path.basename(audio_file))[0]
        md_file = os.path.join(RECORDINGS_DIR, f"{base_name}.md")
        
        # Check if already processed
        if os.path.exists(md_file):
            continue
            
        logging.info(f"Processing new file: {audio_file}")
        
        # Process
        transcription = process_audio(audio_file)
        
        if transcription:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            content = f"**Timestamp:** {timestamp}\n\n**Transcription:**\n\n{transcription}"
            
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logging.info(f"Generated {md_file}")
            
            # Git Add
            run_git_command(['add', md_file])
            changes_made = True
        else:
            logging.error(f"Failed to transcribe {audio_file}")

    # 3. Push changes if any
    if changes_made:
        logging.info("Committing and pushing changes...")
        run_git_command(['commit', '-m', 'Add new transcriptions'])
        push_res = run_git_command(['push'])
        if push_res is not None:
             logging.info("Pushed successfully.")

def main_loop():
    logging.info("Starting Audio Monitor...")
    setup_git_auth()
    
    try:
        while True:
            process_new_files()
            logging.info(f"Sleeping for {POLL_INTERVAL} seconds...")
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        logging.info("Stopping Monitor.")

if __name__ == "__main__":
    main_loop()
