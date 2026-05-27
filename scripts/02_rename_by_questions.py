"""
STEP 2: RENAME FILES BY QUESTION NUMBER
========================================
What this does:
- Reads the cleaned submissions from Step 1
- Reads all question papers
- Uses AI to identify which question each file answers
- Renames files: "Q1.pdf", "Q2_Q3.docx", etc.
- Copies renamed files to renamed_submissions/

Run: python scripts/02_rename_by_questions.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import config, get_path, MAX_CHARS_ID
from utils.file_handlers import get_file_text, get_all_text_from_folder
from utils.ollama_helpers import ask_ollama, extract_list_from_response
from tqdm import tqdm


def identify_question(file_path: Path, question_papers_text: str) -> list:
    """
    Use AI to determine which question(s) from the paper this file answers.
    Returns list of question numbers, e.g. [1] or [2, 3]
    """
    # Get preview of student's file (first N characters)
    file_preview = get_file_text(file_path, max_chars=MAX_CHARS_ID)
    
    if not file_preview:
        print(f"  ⚠️  Could not read {file_path.name}, skipping")
        return []

    # Create prompt for AI
    prompt = f"""You are a teaching assistant. Below is the exam question paper content, 
followed by the beginning of a student's answer file.

Determine which question number(s) this file answers.
If it answers multiple questions, list all numbers.
Return ONLY a JSON list of integers, e.g. [1] or [2,3]. No other text.

QUESTION PAPER:
{question_papers_text[:3000]}

STUDENT FILE BEGINNING:
{file_preview}

Which question(s) does this file answer? JSON list:"""

    # Ask AI
    response = ask_ollama(prompt, temperature=0)
    questions = extract_list_from_response(response)
    
    # Convert to integers
    return [int(q) for q in questions if str(q).isdigit()]


def rename_student_files(student_dir: Path, question_papers_text: str, renamed_dir: Path):
    """
    For one student: identify questions for each file and copy with new names.
    """
    student_renamed = renamed_dir / student_dir.name
    student_renamed.mkdir(parents=True, exist_ok=True)
    
    files = [f for f in student_dir.iterdir() if f.is_file()]
    
    for file_path in files:
        # Ask AI which question(s) this file answers
        questions = identify_question(file_path, question_papers_text)
        
        if not questions:
            # Couldn't identify, keep original name with UNKNOWN prefix
            new_name = f"UNKNOWN_{file_path.name}"
        else:
            q_str = "_".join(f"Q{q}" for q in sorted(questions))
            new_name = f"{q_str}{file_path.suffix}"
        
        # Copy to renamed folder with new name
        new_path = student_renamed / new_name
        
        # Handle name collisions
        if new_path.exists():
            stem = new_path.stem
            suffix = new_path.suffix
            counter = 1
            while new_path.exists():
                new_path = student_renamed / f"{stem}_{counter}{suffix}"
                counter += 1
        
        shutil.copy2(file_path, new_path)


def main():
    print(f"\n{'='*60}")
    print(f"STEP 2: Identifying Questions & Renaming Files")
    print(f"{'='*60}")
    
    # Get paths
    questions_dir = get_path(config["paths"]["questions_dir"])
    cleaned_dir = get_path(config["paths"]["cleaned_dir"])
    renamed_dir = get_path(config["paths"]["renamed_dir"])
    
    # Validate input folders exist
    if not cleaned_dir.exists():
        print("ERROR: 'cleaned_submissions' folder not found!")
        print("Run Step 1 first: python scripts/01_clean_submissions.py")
        return
    
    if not questions_dir.exists():
        print("ERROR: 'questions' folder not found!")
        return
    
    # Combine all question papers into one text
    print("Reading question papers...")
    question_papers_text = get_all_text_from_folder(questions_dir)
    
    if not question_papers_text.strip():
        print("ERROR: Could not extract text from question papers!")
        return
    
    print(f"Question paper text extracted ({len(question_papers_text)} characters)")
    
    # Get student folders
    student_dirs = [d for d in cleaned_dir.iterdir() if d.is_dir()]
    
    if not student_dirs:
        print("ERROR: No student folders found in cleaned_submissions!")
        return
    
    print(f"\nProcessing {len(student_dirs)} students...")
    print("This uses AI and may take a while. Be patient! ⏳\n")
    
    for student_dir in tqdm(student_dirs, desc="Identifying questions"):
        rename_student_files(student_dir, question_papers_text, renamed_dir)
    
    # Summary
    total_files = sum(1 for d in renamed_dir.iterdir() if d.is_dir() 
                      for f in d.iterdir())
    print(f"\n✅ Done! Renamed {total_files} files across {len(student_dirs)} students")
    print(f"Check the 'renamed_submissions' folder to verify\n")
    
    # Show some examples
    print("Sample renamed files:")
    for student_dir in list(renamed_dir.iterdir())[:3]:
        if student_dir.is_dir():
            print(f"  {student_dir.name}/")
            for f in list(student_dir.iterdir())[:3]:
                print(f"    {f.name}")


if __name__ == "__main__":
    import shutil
    main()