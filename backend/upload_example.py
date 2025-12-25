"""
Incremental NotebookLM Uploader
- Only uploads NEW files that haven't been uploaded before
- Appends to existing documents when possible
- Creates new volumes only when size limit is reached
"""
import os
import time
import random
import json
from tqdm import tqdm
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ======== Configuration ========
CREDENTIALS_PATH = 'credential/key.json'
FOLDER_ID = '10s3hHDtRhrxvtdApd-pbHYl1aRyMXf64'
TRANSCRIPTS_DIR = 'transcripts'
UPLOAD_STATE_FILE = 'logs/notebooklm_upload_state.json'

# Size limits
MAX_DOC_SIZE = 800000  # 800K characters per document
MAX_CHUNK_SIZE = 40000  # Upload in 40K chunks

# API Control
BASE_INTERVAL = 3.0
MAX_RETRIES = 5
JITTER_RANGE = (0.8, 1.2)


class GoogleDocManager:
    def __init__(self):
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
        """Rate-limited API call with retry logic"""
        for attempt in range(MAX_RETRIES + 1):
            try:
                delay = BASE_INTERVAL * random.uniform(*JITTER_RANGE)
                time.sleep(delay)
                return api_call(**kwargs).execute()
            except HttpError as e:
                if e.resp.status in [429, 500, 503]:
                    backoff = delay * (2 ** attempt)
                    print(f"  [RETRY] API error {e.resp.status}, waiting {backoff:.1f}s...")
                    time.sleep(backoff)
                else:
                    raise
        raise Exception("API call exceeded max retries")

    def find_doc_by_name(self, doc_name):
        """Find existing document by name"""
        try:
            result = self._rate_limited_call(
                self.drive_service.files().list,
                q=f"name='{doc_name}' and '{FOLDER_ID}' in parents and trashed=false",
                fields='files(id, name)'
            )
            files = result.get('files', [])
            return files[0]['id'] if files else None
        except:
            return None

    def get_doc_size(self, doc_id):
        """Get current document size (end index)"""
        try:
            doc = self._rate_limited_call(
                self.docs_service.documents().get,
                documentId=doc_id,
                fields='body(content(endIndex))'
            )
            content = doc.get('body', {}).get('content', [])
            if content:
                return content[-1].get('endIndex', 1)
            return 1
        except:
            return 1

    def create_document(self, doc_name):
        """Create a new empty Google Doc"""
        try:
            file_metadata = {
                'name': doc_name,
                'parents': [FOLDER_ID],
                'mimeType': 'application/vnd.google-apps.document'
            }
            doc = self._rate_limited_call(
                self.drive_service.files().create,
                body=file_metadata,
                fields='id'
            )
            return doc['id']
        except Exception as e:
            print(f"  [FAIL] Failed to create document {doc_name}: {e}")
            return None

    def append_content(self, doc_id, content):
        """Append content to the end of a document"""
        if not content.strip():
            return True
            
        try:
            # Get current end index
            doc = self._rate_limited_call(
                self.docs_service.documents().get,
                documentId=doc_id,
                fields='revisionId,body(content(endIndex))'
            )
            
            revision_id = doc.get('revisionId')
            doc_content = doc.get('body', {}).get('content', [])
            end_index = 1
            if doc_content:
                end_index = doc_content[-1].get('endIndex', 1) - 1
            
            # Insert content at end
            requests_body = {
                'requests': [{
                    'insertText': {
                        'text': content,
                        'location': {'index': end_index}
                    }
                }]
            }
            
            if revision_id:
                requests_body['writeControl'] = {'targetRevisionId': revision_id}
            
            self._rate_limited_call(
                self.docs_service.documents().batchUpdate,
                documentId=doc_id,
                body=requests_body
            )
            return True
            
        except Exception as e:
            print(f"  [WARN] Append failed: {str(e)[:100]}")
            return False


def load_state():
    """Load upload state"""
    if os.path.exists(UPLOAD_STATE_FILE):
        try:
            with open(UPLOAD_STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {'uploaded_files': {}, 'documents': {}}


def save_state(state):
    """Save upload state"""
    os.makedirs(os.path.dirname(UPLOAD_STATE_FILE), exist_ok=True)
    with open(UPLOAD_STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def get_new_files(category_path, category_name, state):
    """Get list of files that haven't been uploaded yet"""
    all_files = sorted([f for f in os.listdir(category_path) if f.endswith('.txt')])
    uploaded = set(state.get('uploaded_files', {}).get(category_name, []))
    new_files = [f for f in all_files if f not in uploaded]
    return new_files


def read_file_content(file_path, filename):
    """Read a single file and format it for the document"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read().strip()
            if text:
                return f"\n{'='*60}\n{filename}\n{'='*60}\n{text}\n"
    except Exception as e:
        print(f"  [WARN] Could not read {filename}: {e}")
    return None


def get_latest_volume(category_name, state, manager):
    """Get the latest volume document for a category, or None if none exists"""
    docs = state.get('documents', {})
    
    # Check for volumes: category-v1, category-v2, etc. or just category
    volume_names = []
    for name in docs.keys():
        if name == category_name or name.startswith(f"{category_name}-v"):
            volume_names.append(name)
    
    if not volume_names:
        return None, None, 0
    
    # Sort to get latest volume
    volume_names.sort()
    latest_name = volume_names[-1]
    doc_info = docs[latest_name]
    
    # Verify doc still exists and get current size
    doc_id = doc_info.get('id')
    if doc_id:
        current_size = manager.get_doc_size(doc_id)
        return latest_name, doc_id, current_size
    
    return None, None, 0


def get_next_volume_name(category_name, state):
    """Generate the next volume name for a category"""
    docs = state.get('documents', {})
    
    existing_volumes = [name for name in docs.keys() 
                       if name == category_name or name.startswith(f"{category_name}-v")]
    
    if not existing_volumes:
        return category_name  # First volume is just the category name
    
    # Find highest volume number
    max_vol = 0
    for name in existing_volumes:
        if name == category_name:
            max_vol = max(max_vol, 1)
        elif '-v' in name:
            try:
                vol_num = int(name.split('-v')[-1])
                max_vol = max(max_vol, vol_num)
            except:
                pass
    
    return f"{category_name}-v{max_vol + 1}"


def main():
    print("[START] Incremental NotebookLM Uploader")
    
    manager = GoogleDocManager()
    state = load_state()
    
    # Get all categories
    categories = sorted([d for d in os.listdir(TRANSCRIPTS_DIR)
                        if os.path.isdir(os.path.join(TRANSCRIPTS_DIR, d))])
    
    print(f"[INFO] Found {len(categories)} categories")
    
    total_new_files = 0
    categories_with_new = 0
    
    for category in tqdm(categories, desc="Checking"):
        category_path = os.path.join(TRANSCRIPTS_DIR, category)
        
        # Check for new files
        new_files = get_new_files(category_path, category, state)
        
        if not new_files:
            continue  # No new files, skip this category
        
        categories_with_new += 1
        tqdm.write(f"\n[NEW] {category}: {len(new_files)} new file(s)")
        
        # Get current latest volume
        current_vol_name, current_doc_id, current_size = get_latest_volume(category, state, manager)
        
        # Initialize tracking
        if category not in state['uploaded_files']:
            state['uploaded_files'][category] = []
        
        for filename in new_files:
            file_path = os.path.join(category_path, filename)
            content = read_file_content(file_path, filename)
            
            if not content:
                continue
            
            content_size = len(content)
            
            # Check if we need a new volume
            if current_doc_id is None or (current_size + content_size > MAX_DOC_SIZE):
                # Create new volume
                new_vol_name = get_next_volume_name(category, state)
                tqdm.write(f"  [CREATE] New volume: {new_vol_name}")
                new_doc_id = manager.create_document(new_vol_name)
                
                if new_doc_id:
                    current_vol_name = new_vol_name
                    current_doc_id = new_doc_id
                    current_size = 1
                    state['documents'][new_vol_name] = {
                        'id': new_doc_id,
                        'files': [],
                        'size': 0
                    }
                    save_state(state)
                else:
                    tqdm.write(f"  [FAIL] Could not create volume, skipping")
                    continue
            
            # Append to current volume
            if manager.append_content(current_doc_id, content):
                current_size += content_size
                total_new_files += 1
                
                # Update state
                state['uploaded_files'][category].append(filename)
                if current_vol_name in state['documents']:
                    state['documents'][current_vol_name]['files'].append(filename)
                    state['documents'][current_vol_name]['size'] = current_size
                
                save_state(state)
                tqdm.write(f"  [OK] {filename}")
            else:
                tqdm.write(f"  [FAIL] {filename}")
    
    if total_new_files == 0:
        print("\n[DONE] No new files to upload. Everything is up to date!")
    else:
        print(f"\n[DONE] Uploaded {total_new_files} new files across {categories_with_new} categories")
    
    print(f"[LINK] https://drive.google.com/drive/folders/{FOLDER_ID}")


if __name__ == '__main__':
    main()
