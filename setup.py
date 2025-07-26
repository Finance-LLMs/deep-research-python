#!/usr/bin/env python3
"""
Setup script for Deep Research Python
"""
import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False
    return True

def check_env_file():
    """Check if .env.local file exists"""
    if not os.path.exists(".env.local"):
        print("⚠️  .env.local file not found!")
        print("Please create a .env.local file with your API keys:")
        print("""
# Example .env.local file:
FIRECRAWL_KEY="your_firecrawl_key"
NVIDIA_API_KEY="your_nvidia_api_key"
# OR
OPENAI_KEY="your_openai_key" 
# OR
FIREWORKS_KEY="your_fireworks_key"
        """)
        return False
    else:
        print("✅ .env.local file found!")
        return True

def main():
    print("🔬 Deep Research Python Setup")
    print("=" * 40)
    
    # Install requirements
    if not install_requirements():
        return 1
    
    # Check environment file
    env_exists = check_env_file()
    
    print("\n🎉 Setup complete!")
    if env_exists:
        print("You can now run:")
        print("  python -m src.run          # Interactive research")
        print("  python -m src.api          # API server")
    else:
        print("Please create .env.local file first, then run the commands above.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
