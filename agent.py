import os
import subprocess
import time
import shutil
import piexif
from PIL import Image
from watchdog.observers import Observer # shows updates to the input
from watchdog.events import FileSystemEventHandler # manages events when new input
# Automatic triggering when the new files appear
'''import logging
logging.basicConfig(filename="agent.log", level=logging.INFO)
logging.info(f"Processed {file_name} -> {new_path}")'''

"""
Pipeline:
1. Monitor the INPUT_DIR for new media files
2. when new file detected, Move to PROCESSING_DIR
3. Image Processing
4. Add metadata from AGENT to the processed file
5. Move the Processed file to OUTPUT_DIR #Image sorting comes later on Based on metadata
"""


# ====== Basic File Monitoring  ======

INPUT_DIR = "input" # all input images/videos go here
PROCESSED_DIR = "processed" # files go here for processing
OUTPUT_DIR = "output" # processed files go here

VALID_CATEGORIES = {"Religious", "Holiday", "Home-Decor", "Clothing", "Kitchenware", "Drinkware"}

class MediaHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        # Indicator for new file in the /input directory
        print(f"New file detected: {event.src_path}")
        # Move to Processing dir
        time.sleep(1) # Wait for file to be fully written
        process_file(event.src_path)

# ======== File Processing ==========
def process_file(filepath):
    file_name = os.path.basename(filepath)

    print(f"Analizing {filepath}...")

    data = analyze_image(filepath) 
    ext = os.path.splitext(file_name)[1] # Get the file extension
    new_name = f"{data['name']}{ext}"
    category_folder = os.path.join(PROCESSED_DIR, data['category'])

    os.makedirs(category_folder, exist_ok=True) # Create a category folder if the category doesn't exist yet
    
    new_path = os.path.join(category_folder, new_name)
    
    shutil.move(filepath, new_path)
    
    print(f"Moved {file_name} to {new_path} for processing.")

    # Sumulate note creation
    create_simulated_note(data, new_path)
    if filepath.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        embed_image_metadata(new_path, data)
        print(f"Metadata embedded into {new_name, data}.")
    elif filepath.lower().endswith(('.mp4', '.avi', '.mov')):
        try:
            embed_video_metadata(new_path, data)
        except subprocess.CalledProcessError as e:
            print(f"Warning: ffmpeg failed for {new_path}: {e}")


# AI Implementation for Anlizing the image and generating Metadata
'''def analyze_image(filepath):
    return {
        "name": "modern-wooden-lamp",
        "alt_text": "A modern wooden lamp with warm lighting", 
        "category": "Lighting",
        "tags": ["modern", "wooden", "lamp", "lighting", "home"]
    }'''

# ========== AI Analizer ============
import requests
import base64
import json
import re

def fallback_data():
    return {
        "name": "unknown-product",
        "alt_text": "unidentified product image",
        "category": "Misc",
        "tags": ["unknown"]
    }

def parse_ai_response(text):
    print("Raw AI output:\n", text)

    # Remove markdown wrappers
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    # Extract JSON block
    match = re.search(r'\{.*\}', text, re.DOTALL)

    if match:
        json_text = match.group(0)
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            print("⚠️ JSON decode error:", e)
    else:
        print("⚠️ No JSON found in response")

    return fallback_data()

def load_rules(path="rules.md"):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def analyze_image(filepath):
    with open(filepath, "rb") as f:
        image_bytes = f.read()
    
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt = load_rules("rules.md")

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "llava",
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "format": "json" 
        }
    )

    result = response.json()
    text = result.get("response", "").strip()

    data = parse_ai_response(text)

    if data.get("category") not in VALID_CATEGORIES:
        print(f"⚠️ Invalid category '{data.get('category')}' — defaulting to MISC")
        data["category"] = "MISC"

    data["name"] = data["name"].lower().replace(" ", "-").replace(",", "")
    return data

    # Cleanup for metadata atachment 
    data["name"]= data ["name"].lower().replace(" ", "-").replace(",", "")
    return data


def embed_video_metadata(filepath, data):  # Subprocess is being called here
    tmp_output = filepath.replace(".", "_tmp.")
    cmd = [
        "ffmpeg", "-i", filepath,
        "-metadata", f"title={data['name']}",
        "-metadata", f"comment={data['alt_text']}",
        "-c", "copy", tmp_output
    ]
    subprocess.run(cmd, check=True)
    # Replace original
    os.replace(tmp_output, filepath)

def embed_image_metadata(filepath, data):
    img = Image.open(filepath)
    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    # Title / Name
    exif_dict["0th"][piexif.ImageIFD.ImageDescription] = data['alt_text']
    exif_dict["0th"][piexif.ImageIFD.XPTitle] = data['name'].encode("utf-16le")
    exif_dict["0th"][piexif.ImageIFD.XPKeywords] = ";".join(data['tags']).encode("utf-16le")

    exif_bytes = piexif.dump(exif_dict)
    img.save(filepath, exif=exif_bytes)

# ======== Notes (RECORDING) ==========
NOTES_DIR = 'notes'
os.makedirs(NOTES_DIR, exist_ok=True)

def create_simulated_note(data, file_path):
    note_name = f"{data['name']}.md"
    note_path = os.path.join(NOTES_DIR, note_name)
    note_content= f"""# {data['name']}
**Alt Text:** {data['alt_text']}
**Category:** {data['category']}
**Tags:** {', '.join(data['tags'])}
**File Path:** {file_path}
"""
    with open(note_path, "w") as f:
        f.write(note_content)
    print(f"Note created: {note_path}")



if __name__ == "__main__":

    # Observer monitoring the INPUT_DIR
    observer = Observer()
    observer.schedule(MediaHandler(), INPUT_DIR, recursive=False)
    observer.start()
    print(f"Monitoring {INPUT_DIR} for new media files...")
    # Observer loop
    try:
        while True:
            time.sleep(1) # Keep script running and scanning 
    except KeyboardInterrupt: # CMD + C to stop script. 
        """TODO: Modify this to include other commands when User wants to stop the script.
        SSH termnal should be able to close without killing the script."""
        observer.stop()
    observer.join()

    # File Processing 

