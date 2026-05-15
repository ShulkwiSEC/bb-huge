import sys
import requests
import os

# Match your MCP config
BASE_URL = os.environ.get("BB_HUGE_URL", "http://127.0.0.1:5000")
DEV_KEY  = os.environ.get("DEV_KEY", "shulkwisec_123")
HEADERS  = {"X-Dev-Key": DEV_KEY}

def dump_attachments(finding_id):
    # Match the API versioning from your MCP
    api_url = f"{BASE_URL}/api/v1/findings/{finding_id}"
    
    output_dir = f"./finding_{finding_id}_assets"
    os.makedirs(output_dir, exist_ok=True)
    
    # Get finding details (sending the X-Dev-Key)
    r = requests.get(api_url, headers=HEADERS)
    
    if r.status_code != 200:
        print(f"Error: Finding {finding_id} not found or Auth failed. (Status: {r.status_code})")
        return

    finding_data = r.json()
    # Ensure we look for 'attachments' in the JSON response
    attachments = finding_data.get('attachments', [])
    
    if not attachments:
        print(f"No attachments found for finding {finding_id}.")
        return

    for att in attachments:
        # Flask Blueprint serves files at /uploads/<filename>
        # Your MCP uses /api/v1, but the file server is usually at the base
        file_url = f"{BASE_URL}/uploads/{att['filename']}"
        
        print(f"[*] Downloading {att.get('original_name', att['filename'])}...")
        
        try:
            file_res = requests.get(file_url, headers=HEADERS, stream=True)
            if file_res.status_code == 200:
                # Use original_name if available, fallback to the UUID filename
                local_filename = att.get('original_name', att['filename'])
                with open(os.path.join(output_dir, local_filename), 'wb') as f:
                    for chunk in file_res.iter_content(chunk_size=8192):
                        f.write(chunk)
            else:
                print(f"[!] Failed to download {att['filename']} (Status: {file_res.status_code})")
        except Exception as e:
            print(f"[!] Error downloading {att['filename']}: {e}")

    print(f"\nSuccess: Processed {len(attachments)} files. Saved to: {output_dir}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        dump_attachments(sys.argv[1])
    else:
        print("Usage: python bb-dump-attachments.py <finding_id>")