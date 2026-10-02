import hashlib
import json
import os
import sys

BASELINE_FILE = "baseline.json"
WATCH_DIR = "watched_files"

def calculate_sha256(filepath):
    """Generate SHA-256 hash for a given file."""
    hasher = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(4096):
                hasher.update(chunk)
        return hasher.hexdigest()
    except FileNotFoundError:
        return None

def scan_directory(directory):
    """Walk through the directory and hash every file."""
    file_hashes = {}
    for root, _, files in os.walk(directory):
        for file in files:
            full_path = os.path.join(root, file)
            norm_path = os.path.normpath(full_path)
            file_hashes[norm_path] = calculate_sha256(norm_path)
    return file_hashes

def create_baseline():
    """Create a new baseline of file hashes."""
    print(f"[*] Scanning '{WATCH_DIR}' to generate baseline...")
    snapshot = scan_directory(WATCH_DIR)
    with open(BASELINE_FILE, "w") as f:
        json.dump(snapshot, f, indent=4)
    print(f"[+] Baseline saved to '{BASELINE_FILE}' with {len(snapshot)} files.")

def verify_integrity():
    """Compare current directory state against baseline."""
    if not os.path.exists(BASELINE_FILE):
        print(f"[-] Baseline file '{BASELINE_FILE}' not found! Run with '--init' first.")
        return

    with open(BASELINE_FILE, "r") as f:
        baseline = json.load(f)

    current = scan_directory(WATCH_DIR)
    
    baseline_files = set(baseline.keys())
    current_files = set(current.keys())

    added = current_files - baseline_files
    deleted = baseline_files - current_files
    common = baseline_files.intersection(current_files)

    modified = [f for f in common if baseline[f] != current[f]]

    print("\n--- Integrity Report ---")
    if not added and not deleted and not modified:
        print("[OK] All files match baseline. No tampering detected.")
        return

    for f in added:
        print(f"[ALERT: ADDED] New file detected: {f}")
    for f in deleted:
        print(f"[ALERT: DELETED] File removed: {f}")
    for f in modified:
        print(f"[ALERT: MODIFIED] Content changed: {f}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--init":
        create_baseline()
    elif len(sys.argv) > 1 and sys.argv[1] == "--check":
        verify_integrity()
    else:
        print("Usage:")
        print("  python fim.py --init   (Create initial baseline)")
        print("  python fim.py --check  (Run integrity verification)")
