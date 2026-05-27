"""
STEP 1: CLEAN SUBMISSIONS
==========================
What this does:
- Reads all student folders from input/submissions
- Extracts all zip files (including nested zips inside zips)
- Copies all files into cleaned_submissions/{student_id}/
- Keeps original files untouched

Run: python scripts/01_clean_submissions.py
"""

import sys
from pathlib import Path

# Add project root to Python path so we can import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import config, get_path
from utils.file_handlers import unzip_recursive
from tqdm import tqdm


def clean_submissions_folder(submissions_dir: Path, cleaned_dir: Path):
    """
    For each student folder:
    1. Create matching folder in cleaned_dir
    2. Extract all zips (recursively) directly into that folder
    3. Copy all non-zip files as-is
    """
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    
    student_folders = [d for d in submissions_dir.iterdir() if d.is_dir()]
    
    if not student_folders:
        print(f"ERROR: No student folders found in {submissions_dir}")
        print("Make sure you've placed student folders inside input/submissions/")
        return
    
    print(f"\n{'='*60}")
    print(f"STEP 1: Cleaning Submissions")
    print(f"{'='*60}")
    print(f"Found {len(student_folders)} student folders")
    print(f"Source: {submissions_dir}")
    print(f"Output: {cleaned_dir}")
    print(f"\nProcessing...")
    
    for student_folder in tqdm(student_folders, desc="Cleaning"):
        student_id = student_folder.name
        dest_student = cleaned_dir / student_id
        dest_student.mkdir(exist_ok=True)

        # Process every file in the student's folder
        for file_path in student_folder.iterdir():
            if file_path.is_file():
                if file_path.suffix.lower() == '.zip':
                    # Extract zip (handles nested zips internally)
                    unzip_recursive(file_path, dest_student)
                else:
                    # Copy non-zip files directly
                    shutil.copy2(file_path, dest_student / file_path.name)
    
    # Count results
    total_files = sum(1 for d in cleaned_dir.iterdir() if d.is_dir() 
                      for f in d.iterdir())
    print(f"\n✅ Done! Created {len(student_folders)} folders with {total_files} total files")
    print(f"Check the 'cleaned_submissions' folder to verify\n")


def main():
    # Get paths from config
    submissions_dir = get_path(config["paths"]["submissions_dir"])
    cleaned_dir = get_path(config["paths"]["cleaned_dir"])
    
    # Check if source exists
    if not submissions_dir.exists():
        print(f"ERROR: Submissions folder not found at {submissions_dir}")
        print("Create the folder and add student submissions first!")
        return
    
    # Run cleaning
    clean_submissions_folder(submissions_dir, cleaned_dir)


if __name__ == "__main__":
    import shutil  # Needed here for the copy operation
    main()