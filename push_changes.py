#!/usr/bin/env python3
import subprocess
import sys

try:
    # Add files
    result = subprocess.run(
        ["git", "add", "backend/app/main.py", "backend/app/database.py"],
        cwd="c:\\Users\\kavya\\OneDrive\\Desktop\\Mini",
        capture_output=True,
        text=True,
        timeout=10
    )
    print("Add:", result.returncode, result.stdout, result.stderr)
    
    # Commit
    result = subprocess.run(
        ["git", "commit", "-m", "Fix: Make database initialization non-blocking to handle missing drivers gracefully"],
        cwd="c:\\Users\\kavya\\OneDrive\\Desktop\\Mini",
        capture_output=True,
        text=True,
        timeout=10
    )
    print("Commit:", result.returncode, result.stdout, result.stderr)
    
    # Push
    result = subprocess.run(
        ["git", "push", "origin", "main"],
        cwd="c:\\Users\\kavya\\OneDrive\\Desktop\\Mini",
        capture_output=True,
        text=True,
        timeout=30
    )
    print("Push:", result.returncode, result.stdout, result.stderr)
    
    if result.returncode == 0:
        print("\n✓ Changes pushed successfully!")
    else:
        print(f"\n✗ Push failed: {result.stderr}")
        sys.exit(1)
        
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
