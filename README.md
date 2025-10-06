# Manim Video Generator - Quick Start

## What This App Does

This application generates mathematical animation videos using:
1. **Data Source**: 2,407 Manim code examples from 3Blue1Brown dataset (CSV file) - Uses the https://huggingface.co/datasets/dalle2/3blue1brown-manim/
2. **Code Execution**: E2B sandboxed Python interpreter runs the Manim code
3. **Video Output**: Returns MP4 videos to users via web interface

## Architecture

```
User → Web UI → Flask API → CSV Data → E2B Sandbox → Manim → MP4 Video
                                ↓
                         ClickHouse Cloud
                      (original data source)
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   Create `.env` file with your E2B API key:
   ```
   E2B_API_KEY=your_key_here
   ```

3. **Run the app:**
   ```bash
   python app.py
   ```

4. **Open browser:**
   Navigate to http://127.0.0.1:5001

## Features

### Web UI (http://127.0.0.1:5001)
- 🎯 **Generate from Prompt**: Enter keywords like "circle", "rotate", "animate"
- 🎲 **Random Generation**: Get a random animation from 2,407 examples
- 📋 **Browse Prompts**: Dropdown with ALL 2,407 available prompts
- 🎬 **Video Player**: Watch generated videos inline
- 💾 **Download**: Save MP4 files locally

### API Endpoints

#### `GET /prompts`
List all available prompts
```bash
curl http://127.0.0.1:5001/prompts
# Returns: {"count": 2407, "prompts": [...]}
```

#### `POST /generate`
Generate video from prompt
```bash
curl -X POST http://127.0.0.1:5001/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"circle"}' \
  --output animation.mp4
```

#### `GET /generate/random`
Generate random video
```bash
curl http://127.0.0.1:5001/generate/random --output random.mp4
```

#### `POST /code`
Get code without generating video
```bash
curl -X POST http://127.0.0.1:5001/code \
  -H "Content-Type: application/json" \
  -d '{"prompt":"text"}'
```

## How Video Generation Works

1. **User Request**: User enters prompt or clicks random
2. **Data Fetch**: Flask searches CSV for matching Manim code
3. **E2B Sandbox**: Creates isolated Python environment
4. **Install Manim**: `pip install manim` in sandbox
5. **Execute Code**: Runs Manim code to generate video
6. **Return MP4**: Streams video file back to user

## Example Prompts

- "Create a circle"
- "Animate text"
- "Rotate square"
- "Draw graph"
- "Transform shape"
- "Write equation"

## Data Source

The app uses `3blue1brown-manim-prompts.csv` containing:
- **Column 1**: Prompt description (what the animation does)
- **Column 2**: Manim Python code
- **Total Records**: 2,407 examples

This data was originally loaded into ClickHouse Cloud database for demonstration purposes.

## Tech Stack

- **Backend**: Flask (Python)
- **Data**: CSV/Pandas (can be connected to ClickHouse)
- **Execution**: E2B Code Interpreter (sandboxed Python)
- **Animation**: Manim Community Edition
- **Frontend**: Vanilla HTML/CSS/JavaScript

## Current Status

✅ All 2,407 prompts loaded and searchable
✅ Web UI with dropdown browser
✅ Code retrieval working
✅ E2B sandbox configured
✅ API endpoints functional

The app is ready to generate Manim videos!

## Troubleshooting

**Port 5000 in use?**
The app runs on port 5001 by default (port 5000 is often used by macOS AirPlay).

**E2B API Key missing?**
Set `E2B_API_KEY` in `.env` file. Get key from https://e2b.dev

**Video generation slow?**
First generation takes 30-60 seconds as E2B installs Manim. Subsequent requests may be faster.

**No prompts loading?**
Ensure `3blue1brown-manim-prompts.csv` exists in the root directory.
