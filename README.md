# SeoImage-AI

# AI Media Processing Agent

## Overview

This project is an automated media processing pipeline that monitors a directory for new files, analyzes them using an AI model, enriches them with metadata, and organizes them into structured folders.

## How It Works

1. Watches the `input/` directory for new files
2. Moves detected files into a processing directory
3. Sends images to a local AI model for analysis
4. Generates metadata including:

   * Name
   * Alt text
   * Category
   * Tags
5. Renames and organizes files based on metadata
6. Embeds metadata into the file (image or video)
7. Creates a corresponding markdown note for each file

## Directory Structure

input/        Incoming media files
processed/    Files organized by category during processing
output/       Reserved for future use
notes/        Generated markdown notes
rules.md      Prompt rules for AI analysis

## Requirements

* Python 3.8+
* ffmpeg (for video metadata handling)
* A local AI inference server (Ollama or similar) running LLaVA

### Python Dependencies

pip install pillow piexif watchdog requests

## Configuration

INPUT_DIR = "input"
PROCESSED_DIR = "processed"
OUTPUT_DIR = "output"

## Valid Categories

VALID_CATEGORIES = {
"Religious",
"Holiday",
"Home-Decor",
"Clothing",
"Kitchenware",
"Drinkware"
}

If the AI returns a category not in this list, it defaults to:

MISC

## Pipeline Workflow

### File Detection

The system uses watchdog to monitor the input directory and triggers processing when a new file is created.

### Processing Steps

Each file goes through:

* Detection
* Temporary holding
* AI analysis
* Renaming based on metadata
* Categorization
* Metadata embedding
* Note creation

## AI Analysis

Images are sent to a local endpoint:

[http://localhost:11434/api/generate](http://localhost:11434/api/generate)

Model used:

llava

The request includes:

* Base64 image data
* Prompt from rules.md
* JSON output requirement

## Expected AI Output

The AI must return valid JSON:

{
"name": "string",
"alt_text": "string",
"category": "string",
"tags": ["tag1", "tag2"]
}

If parsing fails, fallback metadata is used.

## Metadata Embedding

### Images

Uses EXIF via piexif:

* ImageDescription → alt text
* XPTitle → name
* XPKeywords → tags

### Videos

Uses ffmpeg:

ffmpeg -i input.mp4 -metadata title=name -metadata comment=alt_text -c copy output.mp4

## Notes System

Each processed file generates a markdown note:

notes/<file-name>.md

Example:

# modern-wooden-lamp

Alt Text: A modern wooden lamp with warm lighting
Category: Home-Decor
Tags: modern, wooden, lamp
File Path: processed/Home-Decor/modern-wooden-lamp.jpg

## Running the Agent

python main.py

The script will continuously monitor the input directory.

## Stopping the Agent

CTRL + C

## Logging (Optional)

Logging can be enabled:

import logging

logging.basicConfig(filename="agent.log", level=logging.INFO)
logging.info(f"Processed file -> path")

## Known Issues

* File write timing may require small delays
* AI output must be valid JSON
* Strict category enforcement may default to MISC

## Future Improvements

* Add structured logging system
* Improve AI retry handling
* Add batch processing mode
* Build dashboard UI
* Expand category system dynamically
* Add cloud storage support
