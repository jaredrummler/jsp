#!/usr/bin/env python3
"""
Script to publish the jsp package to PyPI.

Usage:
    python scripts/publish.py [--test]
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, check=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=check, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result

def clean_build_dirs():
    """Remove build directories."""
    print("Cleaning build directories...")
    dirs_to_remove = ["build", "dist", "*.egg-info", "src/*.egg-info"]
    for pattern in dirs_to_remove:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                run_command(["rm", "-rf", str(path)])

def build_package():
    """Build the package."""
    print("\nBuilding package...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "build"])
    run_command([sys.executable, "-m", "build"])

def check_package():
    """Check the package with twine."""
    print("\nChecking package...")
    run_command([sys.executable, "-m", "pip", "install", "--upgrade", "twine"])
    run_command([sys.executable, "-m", "twine", "check", "dist/*"])

def upload_package(test=False):
    """Upload the package to PyPI."""
    if test:
        print("\nUploading to TestPyPI...")
        repository_url = "https://test.pypi.org/legacy/"
        cmd = [sys.executable, "-m", "twine", "upload", "--repository-url", repository_url, "dist/*"]
    else:
        print("\nUploading to PyPI...")
        cmd = [sys.executable, "-m", "twine", "upload", "dist/*"]
    
    # Check for credentials
    if not any([
        os.environ.get("TWINE_USERNAME"),
        os.path.exists(os.path.expanduser("~/.pypirc")),
        os.path.exists(".pypirc")
    ]):
        print("\n⚠️  No PyPI credentials found!")
        print("Please set up one of the following:")
        print("  1. Environment variables: TWINE_USERNAME and TWINE_PASSWORD")
        print("  2. ~/.pypirc file with your API token")
        print("  3. Use: twine upload --username __token__ --password <your-token> dist/*")
        return False
    
    run_command(cmd)
    return True

def main():
    parser = argparse.ArgumentParser(description="Publish jsp package to PyPI")
    parser.add_argument("--test", action="store_true", help="Upload to TestPyPI instead")
    parser.add_argument("--skip-build", action="store_true", help="Skip building (use existing dist)")
    args = parser.parse_args()
    
    if not args.skip_build:
        # Clean previous builds
        clean_build_dirs()
        
        # Build the package
        build_package()
        
        # Check the package
        check_package()
    
    # Upload the package
    success = upload_package(test=args.test)
    
    if success:
        if args.test:
            print("\n✅ Package uploaded to TestPyPI!")
            print("Install with: pip install -i https://test.pypi.org/simple/ jsp")
        else:
            print("\n✅ Package uploaded to PyPI!")
            print("Install with: pip install jsp")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())