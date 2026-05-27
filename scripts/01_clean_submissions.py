"""
STEP 1: CLEAN SUBMISSIONS
==========================
What this does:
- Reads all student folders from input/submissions
- Extracts all zip files (including nested zips inside zips)
- FLATTENS all subfolders (no folders inside student folders)
- Copies all files into cleaned_submissions/{student_id}/
- Keeps original files untouched

Run: python scripts/01_clean_submissions.py
"""

import sys
from pathlib import Path

# Add project root to Python path so we can import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import config, get_path
from utils.file_handlers import flatten_directory
from tqdm import tqdm


def clean_submissions_folder(submissions_dir: Path, cleaned_dir: Path):
    """
    For each student folder:
    1. Create matching folder in cleaned_dir
    2. Recursively flatten ALL subfolders
    3. Extract ALL zips (including nested)
    4. ALL files end up directly in the student's folder (no subfolders)
    """
    # Remove old cleaned folder if it exists (to start fresh)
    if cleaned_dir.exists():
        print(f"Removing old cleaned submissions...")
        shutil.rmtree(cleaned_dir)
    
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
    print(f"\nFlattening folders & extracting zips...")
    
    for student_folder in tqdm(student_folders, desc="Cleaning"):
        student_id = student_folder.name
        dest_student = cleaned_dir / student_id
        dest_student.mkdir(exist_ok=True)

        # THE KEY CHANGE: Use flatten_directory instead of iterating files
        # This recursively digs into ALL subfolders
        flatten_directory(student_folder, dest_student)
    
    # Count results
    total_files = 0
    for student_dir in cleaned_dir.iterdir():
        if student_dir.is_dir():
            files_in_dir = list(student_dir.iterdir())
            total_files += len(files_in_dir)
            
            # Check if any subfolders remain (they shouldn't!)
            remaining_dirs = [f for f in files_in_dir if f.is_dir()]
            if remaining_dirs:
                print(f"  ⚠️  WARNING: {student_dir.name} still has subfolders: {[d.name for d in remaining_dirs]}")
    
    print(f"\n✅ Done! Created {len(student_folders)} student folders with {total_files} total files")
    
    # Show sample structure
    print(f"\nSample output structure:")
    for student_dir in list(cleaned_dir.iterdir())[:2]:
        if student_dir.is_dir():
            print(f"  {student_dir.name}/")
            for f in list(student_dir.iterdir())[:5]:
                print(f"    ├── {f.name}")
            remaining = len(list(student_dir.iterdir())) - 5
            if remaining > 0:
                print(f"    └── ... and {remaining} more files")
    
    print(f"\nCheck 'cleaned_submissions' folder to verify before running Step 2\n")


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
    import shutil  # Needed for rmtree
    main()