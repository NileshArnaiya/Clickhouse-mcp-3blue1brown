from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import requests
import os
import tempfile
import shutil
from e2b import Sandbox
import time
from datetime import datetime
from dotenv import load_dotenv
import json
import pandas as pd

load_dotenv()

app = Flask(__name__)
CORS(app)

# ClickHouse Cloud configuration
SERVICE_ID = "your_service_id" # get clickhouse service id from clickhouse dashboard

# Load data from CSV as fallback
csv_file = '3blue1brown-manim-prompts.csv' #download the dataset from huggingface. 
df = None
if os.path.exists(csv_file):
    df = pd.read_csv(csv_file)
    # Filter out header row if it exists
    df = df[df.iloc[:, 0] != 'prompt']

def get_manim_code_from_clickhouse(prompt_text=None):
    """Fetch Manim code from CSV file"""
    global df

    if df is None or len(df) == 0:
        return None, None

    try:
        if prompt_text:
            # Search for matching prompt (case-insensitive)
            mask = df.iloc[:, 0].str.contains(prompt_text, case=False, na=False)
            matching = df[mask]
            if len(matching) > 0:
                row = matching.iloc[0]
                return row.iloc[0], row.iloc[1]
        else:
            # Get random row
            row = df.sample(n=1).iloc[0]
            return row.iloc[0], row.iloc[1]
    except Exception as e:
        print(f"Error fetching code: {e}")

    return None, None

def list_available_prompts(limit=None):
    """List available prompts from the CSV"""
    global df

    if df is None or len(df) == 0:
        return []

    try:
        if limit:
            prompts = df.iloc[:limit, 0].tolist()
        else:
            prompts = df.iloc[:, 0].tolist()
        return prompts
    except Exception as e:
        print(f"Error listing prompts: {e}")

    return []

def execute_manim_code(code):
    """Execute Manim code using E2B Sandbox and return video file"""
    sandbox = None

    try:
        # Create sandbox with E2B API key from environment
        print("🚀 Creating E2B sandbox...")
        sandbox = Sandbox.create()
        print(f"✅ Sandbox created: {sandbox.sandbox_id}")

        print("📦 Installing system dependencies and Manim...")
        # Try to install dependencies using sudo (E2B sandboxes have sudo access)
        setup_cmd = """
        sudo apt-get update &&
        sudo apt-get install -y libcairo2-dev libpango1.0-dev ffmpeg pkg-config &&
        pip install manim
        """
        try:
            install_result = sandbox.commands.run(setup_cmd)
            print(f"Setup completed with exit code: {install_result.exit_code}")
            if install_result.exit_code != 0:
                print(f"Setup stderr: {install_result.stderr[:500]}")
        except Exception as e:
            print(f"Setup error: {e}")
            # Try without texlive (faster)
            simple_setup = "pip install manim"
            install_result = sandbox.commands.run(simple_setup)
            print(f"Simple install exit code: {install_result.exit_code}")

        print("📝 Writing code to file...")
        # Write the code to a file
        sandbox.files.write("scene.py", code)

        print("🎬 Executing Manim...")
        # Execute manim to generate video
        manim_result = sandbox.commands.run("manim -ql scene.py --media_dir media")
        print(f"Manim completed with exit code: {manim_result.exit_code}")
        print(f"Manim stdout: {manim_result.stdout[:500]}")
        print(f"Manim stderr: {manim_result.stderr[:500]}")

        print("🔍 Finding video files...")
        # Find the generated video file
        find_result = sandbox.commands.run("find media -name '*.mp4'")
        print(f"Find output: {find_result.stdout}")

        if find_result.stdout.strip():
            video_path = find_result.stdout.strip().split('\n')[0]
            print(f"Video path: {video_path}")

            # Read the video file content
            print(f"📥 Reading video from {video_path}...")
            video_content = sandbox.files.read(video_path)
            print(f"✅ Video read: {len(video_content)} bytes")

            return video_content, manim_result.stdout, manim_result.stderr
        else:
            print("❌ No video file found")
            return None, manim_result.stdout, manim_result.stderr

    except Exception as e:
        print(f"❌ Error in execute_manim_code: {e}")
        import traceback
        traceback.print_exc()
        return None, "", str(e)
    finally:
        if sandbox:
            print("🛑 Killing sandbox...")
            sandbox.kill()

@app.route('/')
def home():
    """Render the main UI"""
    return render_template('index.html')

@app.route('/api')
def api_info():
    return jsonify({
        "service": "Manim Video Generator",
        "description": "Generate Manim animations from ClickHouse database",
        "endpoints": {
            "/prompts": "GET - List available prompts",
            "/generate": "POST - Generate video from prompt or get random",
            "/generate/random": "GET - Generate random video"
        }
    })

@app.route('/prompts', methods=['GET'])
def get_prompts():
    """Get list of available prompts"""
    limit = request.args.get('limit', type=int)  # No default, will get all if not specified
    prompts = list_available_prompts(limit)
    return jsonify({
        "count": len(prompts),
        "prompts": prompts
    })

@app.route('/generate', methods=['POST'])
def generate_video():
    """Generate video based on prompt or get random"""
    data = request.get_json()
    prompt = data.get('prompt') if data else None

    # Get Manim code from ClickHouse
    prompt_text, manim_code = get_manim_code_from_clickhouse(prompt)

    if not manim_code:
        return jsonify({
            "error": "No matching code found in database"
        }), 404

    # Execute the code and generate video
    video_content, stdout, stderr = execute_manim_code(manim_code)

    if video_content:
        # Save to temporary file
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, f"manim_{int(time.time())}.mp4")

        with open(video_path, 'wb') as f:
            f.write(video_content)

        return send_file(
            video_path,
            mimetype='video/mp4',
            as_attachment=True,
            download_name=f'manim_animation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4'
        )
    else:
        return jsonify({
            "error": "Failed to generate video",
            "prompt": prompt_text,
            "code": manim_code,
            "stdout": stdout,
            "stderr": stderr
        }), 500

@app.route('/generate/random', methods=['GET'])
def generate_random_video():
    """Generate a random video from the database"""
    # Get random Manim code
    prompt_text, manim_code = get_manim_code_from_clickhouse()

    if not manim_code:
        return jsonify({
            "error": "No code found in database"
        }), 404

    # Execute the code and generate video
    video_content, stdout, stderr = execute_manim_code(manim_code)

    if video_content:
        # Save to temporary file
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, f"manim_{int(time.time())}.mp4")

        with open(video_path, 'wb') as f:
            f.write(video_content)

        return send_file(
            video_path,
            mimetype='video/mp4',
            as_attachment=True,
            download_name=f'manim_animation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4'
        )
    else:
        return jsonify({
            "error": "Failed to generate video",
            "prompt": prompt_text,
            "code": manim_code,
            "stdout": stdout,
            "stderr": stderr
        }), 500

@app.route('/code', methods=['POST'])
def get_code():
    """Get Manim code for a prompt without generating video"""
    data = request.get_json()
    prompt = data.get('prompt') if data else None

    prompt_text, manim_code = get_manim_code_from_clickhouse(prompt)

    if manim_code:
        return jsonify({
            "code": manim_code,
            "prompt": prompt_text
        })
    else:
        return jsonify({
            "error": "No matching code found"
        }), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
