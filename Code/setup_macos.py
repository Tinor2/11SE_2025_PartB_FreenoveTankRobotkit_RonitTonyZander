import os
import sys
import subprocess
import platform

def run_command(command, description):
    print(f"\nInstalling {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"Successfully installed {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing {description}:")
        print(f"Exit code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("Starting Freenove Tank Robot Kit setup...")
    print(f"Python version: {platform.python_version()}")
    print(f"System: {platform.system()} {platform.release()}")
    
    # Update pip first
    if not run_command("python3 -m pip install --upgrade pip", "pip"):
        print("Failed to update pip. Please check your internet connection and try again.")
        return
    
    # Install dependencies in the correct order
    dependencies = [
        ("numpy", "numpy"),
        ("Pillow", "Pillow"),
        ("opencv-python-headless", "OpenCV"),
        # Try PyQt5 5.15.10 which is compatible with Python 3.12
        ("PyQt5==5.15.10", "PyQt5"),
    ]
    
    all_installed = True
    for pkg, name in dependencies:
        if not run_command(f"pip3 install {pkg}", name):
            print(f"Failed to install {name}. Please check the error message above.")
            all_installed = False
    
    if all_installed:
        print("\nAll dependencies installed successfully!")
        print("You can now run the Freenove Tank Robot software.")
        # List installed packages for verification
        os.system("pip3 list | grep -E 'numpy|Pillow|opencv-python|PyQt5'")
    else:
        print("\nSome dependencies failed to install. Please check the error messages above.")
        print("You may need to install some system dependencies first.")
        if platform.system() == "Darwin":  # macOS
            print("\nOn macOS, you might need to install Qt5 first. Try running:")
            print("brew install qt@5")
            print("export PATH=\"/usr/local/opt/qt@5/bin:$PATH\"")

if __name__ == "__main__":
    main()


