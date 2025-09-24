#!/usr/bin/env python3
"""
Setup script for Knowledge Capture MVP
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"\n{description}...")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {description}: {e}")
        return False
    return True

def setup_database():
    """Setup database and create tables"""
    print("\n🗄️ Setting up database...")

    # Check if PostgreSQL is running
    try:
        subprocess.run("psql --version", shell=True, check=True, capture_output=True)
        print("✅ PostgreSQL found")
    except subprocess.CalledProcessError:
        print("❌ PostgreSQL not found. Please install PostgreSQL first.")
        return False

    # Create database (this might fail if database exists)
    print("Creating database...")
    subprocess.run("createdb knowledge_capture", shell=True, capture_output=True)

    return True

def setup_python_environment():
    """Setup Python virtual environment and install requirements"""
    print("\n🐍 Setting up Python environment...")

    # Create virtual environment
    if not Path("venv").exists():
        if not run_command("python3 -m venv venv", "Creating virtual environment"):
            return False

    # Activate and install requirements
    activate_cmd = ". venv/bin/activate" if os.name != 'nt' else "venv\\Scripts\\activate"
    pip_cmd = f"{activate_cmd} && pip install -r requirements.txt"

    if not run_command(pip_cmd, "Installing Python requirements"):
        return False

    return True

def setup_redis():
    """Check Redis installation"""
    print("\n🔴 Checking Redis...")

    try:
        subprocess.run("redis-cli ping", shell=True, check=True, capture_output=True)
        print("✅ Redis is running")
        return True
    except subprocess.CalledProcessError:
        print("❌ Redis not running. Please start Redis server.")
        print("Install Redis: https://redis.io/docs/getting-started/installation/")
        return False

def create_env_file():
    """Create .env file from template"""
    print("\n⚙️ Setting up environment configuration...")

    env_file = Path(".env")
    template_file = Path(".env.template")

    if not env_file.exists() and template_file.exists():
        # Copy template to .env
        with open(template_file, 'r') as template:
            content = template.read()

        with open(env_file, 'w') as env:
            env.write(content)

        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your actual API keys and configuration!")
    else:
        print("✅ .env file already exists")

    return True

def main():
    """Main setup function"""
    print("🚀 Setting up Knowledge Capture MVP...")

    # Change to project directory
    os.chdir(Path(__file__).parent)

    success = True

    # Setup steps
    success &= create_env_file()
    success &= setup_python_environment()
    success &= setup_database()
    success &= setup_redis()

    if success:
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your API keys")
        print("2. Start the backend: python main.py")
        print("3. Start the frontend: streamlit run frontend/streamlit_app.py")
    else:
        print("\n❌ Setup encountered errors. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
