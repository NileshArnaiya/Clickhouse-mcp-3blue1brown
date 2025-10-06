#!/usr/bin/env python3
"""Test E2B Manim video generation"""

import os
from dotenv import load_dotenv
from e2b import Sandbox

load_dotenv()

# Simple Manim code to test
test_code = """from manim import *

class SimpleCircle(Scene):
    def construct(self):
        circle = Circle(radius=1, color=BLUE)
        self.play(Create(circle))
        self.wait(1)
"""

print("🚀 Starting E2B sandbox...")
sandbox = Sandbox.create()

try:
    print("📦 Installing system dependencies...")
    sys_install = sandbox.commands.run("sudo apt-get update && sudo apt-get install -y libcairo2-dev libpango1.0-dev ffmpeg pkg-config")
    print(f"System deps exit code: {sys_install.exit_code}")

    print("📦 Installing Manim...")
    install = sandbox.commands.run("pip install manim")
    print(f"Manim install exit code: {install.exit_code}")
    if install.exit_code != 0:
        print(f"Error: {install.stderr[:1000]}")

    print("\n📝 Writing code to file...")
    sandbox.files.write("scene.py", test_code)

    print("\n🎬 Running Manim...")
    manim = sandbox.commands.run("manim -ql scene.py --media_dir media")
    print(f"Manim exit code: {manim.exit_code}")
    print(f"\nManim stdout:\n{manim.stdout[:1000]}")
    print(f"\nManim stderr:\n{manim.stderr[:1000]}")

    print("\n🔍 Finding video files...")
    find = sandbox.commands.run("find media -name '*.mp4'")
    print(f"Found files:\n{find.stdout}")

    if find.stdout.strip():
        video_path = find.stdout.strip().split('\n')[0]
        print(f"\n✅ Video generated at: {video_path}")

        # Try to read the file
        video_content = sandbox.files.read(video_path)
        print(f"✅ Video size: {len(video_content)} bytes")

        # Save locally for testing
        with open("test_output.mp4", "wb") as f:
            f.write(video_content)
        print("✅ Saved to test_output.mp4")
    else:
        print("❌ No video file found")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    sandbox.kill()
    print("\n🛑 Sandbox killed")
