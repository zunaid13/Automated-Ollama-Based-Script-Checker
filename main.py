"""
AUTOMATED ANSWER SCRIPT GRADING PIPELINE
========================================
1. Extracts nested zips, flattens student folders.
2. Uses Ollama (Qwen 32B) to identify which question(s) each file answers.
3. Renames files to "Q1.pdf", "Q2_Q3.docx", etc.
4. Grades each answer using the solutions & marking criteria via AI.
5. Produces an Excel report with marks and deduction details.

Run: python main.py
"""

import os
import json
import shutil
import zipfile
import tempfile
import re
from pathlib import Path
from typing import List, Dict, Any

import pdfplumber
from docx import Document
import openpyxl
from openpyxl.styles import Font, Alignment
import ollama
from tqdm import tqdm

# -------------------------- LOAD CONFIG --------------------------
def load_config(config_path: str = "config.json") -> dict:
    """Read the configuration file and return as dictionary."""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

config = load_config()
OLLAMA_MODEL = config["ollama"]["model"]
OLLAMA_TIMEOUT = config["ollama"]["timeout"]
MAX_CHARS_ID = config["max_chars_for_question_id"]
MAX_MARKS_DEFAULT = config["max_marks_per_question"]

# Helper to get absolute paths relative to the script's location
BASE_DIR = Path(__file__).parent
def get_path(relative_path: str) -> Path:
    return BASE_DIR / relative_path

# -------------------------- 1. UNZIP & FLATTEN --------------------------
def unzip_recursive(zip_path: Path, extract_to: Path):
    """
    Extract a zip file. If extracted items contain further zips, extract them too.
    All final files end up directly in 'extract_to' (flattened).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Extract main zip
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(tmpdir)

        # Now walk through everything extracted
        for root, dirs, files in os.walk(tmpdir):
            root_path = Path(root)
            for file in files:
                file_path = root_path / file
                # If it's another zip, extract it recursively into the same temp area
                if file_path.suffix.lower() == '.zip':
                    unzip_recursive(file_path, extract_to)
                else:
                    # Copy non-zip files to final destination, avoiding name collisions
                    dest = extract_to / file_path.name
                    if dest.exists():
                        # Append a number if file already exists
                        stem = dest.stem
                        suffix = dest.suffix
                        counter = 1
                        while dest.exists():
                            dest = extract_to / f"{stem}_{counter}{suffix}"
                            counter += 1
                    shutil.copy2(file_path, dest)

def clean_submissions_folder(submissions_dir: Path, cleaned_dir: Path):
    """
    For each student folder in submissions_dir:
      - Create corresponding folder in cleaned_dir.
      - Unzip all zip files (including nested) directly inside it.
      - Copy all other files as-is.
    """
    cleaned_dir.mkdir(parents=True, exist_ok=True)

    student_folders = [d for d in submissions_dir.iterdir() if d.is_dir()]
    print(f"Found {len(student_folders)} student folders. Cleaning submissions...")

    for student_folder in tqdm(student_folders, desc="Unzipping & flattening"):
        student_id = student_folder.name
        dest_student = cleaned_dir / student_id
        dest_student.mkdir(exist_ok=True)

        # Process every file inside the student's raw folder
        for file_path in student_folder.iterdir():
            if file_path.is_file():
                if file_path.suffix.lower() == '.zip':
                    unzip_recursive(file_path, dest_student)
                else:
                    shutil.copy2(file_path, dest_student / file_path.name)
            # Ignore subdirectories (we flatten everything)

# -------------------------- 2. TEXT EXTRACTION --------------------------
def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF using pdfplumber."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_text_from_docx(docx_path: Path) -> str:
    """Extract all text from a DOCX file."""
    doc = Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_txt(txt_path: Path) -> str:
    """Read plain text file."""
    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def get_file_text(file_path: Path, max_chars: int = None) -> str:
    """
    Extract text from a file (PDF, DOCX, TXT, common code files).
    Returns up to 'max_chars' characters if specified.
    """
    suffix = file_path.suffix.lower()
    if suffix == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif suffix == '.docx':
        text = extract_text_from_docx(file_path)
    elif suffix in ['.txt', '.py', '.java', '.c', '.cpp', '.js', '.html', '.css', '.ipynb']:
        # For code files, just read as text
        text = extract_text_from_txt(file_path)
    else:
        # Try reading as plain text anyway
        try:
            text = extract_text_from_txt(file_path)
        except Exception:
            text = ""
    if max_chars and len(text) > max_chars:
        text = text[:max_chars]
    return text.strip()

# -------------------------- 3. QUESTION IDENTIFICATION (AI) --------------------------
def identify_question(file_path: Path, question_papers_text: str) -> List[int]:
    """
    Use Ollama to read the file content and decide which question(s) from the
    question paper it answers. Returns a list of question numbers (e.g. [1] or [2,3]).
    """
    # Extract a preview of the student's file
    file_preview = get_file_text(file_path, max_chars=MAX_CHARS_ID)
    if not file_preview:
        return []   # Cannot determine

    # Construct a prompt for the AI
    prompt = f"""
You are a teaching assistant. Below is the full content of the exam question paper (maybe several questions). 
Then you see the beginning of a student's answer file. 
Determine which question number(s) this file answers. 
If it clearly answers multiple questions, list all numbers. 
Return ONLY a JSON list of integers, e.g. [1] or [2,3]. Do not add any extra text.

QUESTION PAPER CONTENT:
{question_papers_text[:3000]}   # limit context size

BEGINNING OF STUDENT FILE:
{file_preview}

Which question(s) does this file answer? Output JSON list:
"""

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0}  # deterministic
        )
        # Parse the response
        content = response['message']['content'].strip()
        # Extract list from possible markdown fences
        json_match = re.search(r'\[.*?\]', content, re.DOTALL)
        if json_match:
            numbers = json.loads(json_match.group(0))
            if isinstance(numbers, list):
                return [int(n) for n in numbers if str(n).isdigit()]
        return []
    except Exception as e:
        print(f"  AI error for {file_path.name}: {e}")
        return []

def rename_files_by_question(student_dir: Path, question_papers_text: str):
    """
    For every file in a student's cleaned folder, ask AI for question number(s)
    and rename it accordingly (e.g. 'Q1.pdf').
    """
    files = list(student_dir.iterdir())
    for file_path in files:
        if file_path.is_file():
            questions = identify_question(file_path, question_papers_text)
            if not questions:
                # If AI failed, keep original name but add prefix "UNKNOWN_"
                new_name = f"UNKNOWN_{file_path.name}"
            else:
                q_str = "_".join(f"Q{q}" for q in sorted(questions))
                new_name = f"{q_str}{file_path.suffix}"
            new_path = student_dir / new_name
            # Avoid overwriting; if exists, add a counter
            if new_path.exists() and new_path != file_path:
                stem = new_path.stem
                suffix = new_path.suffix
                counter = 1
                while new_path.exists():
                    new_path = student_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
            file_path.rename(new_path)

def identify_all_questions(cleaned_dir: Path, questions_dir: Path):
    """
    Build a single string of all question papers and then rename files for every student.
    """
    # Combine all question papers into one text
    all_questions_text = ""
    for q_file in questions_dir.iterdir():
        if q_file.suffix.lower() == '.pdf':
            all_questions_text += extract_text_from_pdf(q_file) + "\n\n"
        else:
            all_questions_text += get_file_text(q_file) + "\n\n"

    if not all_questions_text.strip():
        print("WARNING: No question paper text found. File renaming will likely fail.")

    student_dirs = [d for d in cleaned_dir.iterdir() if d.is_dir()]
    print("Identifying questions for each file (this may take a while due to AI calls)...")
    for student_dir in tqdm(student_dirs, desc="Renaming by question"):
        rename_files_by_question(student_dir, all_questions_text)

# -------------------------- 4. GRADING --------------------------
def parse_question_papers(questions_dir: Path) -> Dict[int, str]:
    """
    Try to split the question paper into separate questions (simple heuristic: numbered lines).
    Returns dict {question_number: "question text"}.
    If cannot split, returns {1: entire_text}.
    """
    all_text = ""
    for qf in questions_dir.iterdir():
        if qf.suffix.lower() == '.pdf':
            all_text += extract_text_from_pdf(qf) + "\n\n"
        else:
            all_text += get_file_text(qf) + "\n\n"

    # Simple splitting: look for lines starting with a number followed by dot or parenthesis
    # e.g., "1.", "1)", "Question 1"
    pattern = r'(?:^|\n)\s*(\d+)[\.\)]\s+'
    parts = re.split(pattern, all_text)
    questions = {}
    # parts[0] is anything before first question number; ignore
    for i in range(1, len(parts), 2):
        q_num = int(parts[i])
        q_text = parts[i+1].strip() if i+1 < len(parts) else ""
        questions[q_num] = q_text

    if not questions:
        questions[1] = all_text.strip()   # fallback: whole paper as Q1
    return questions

def parse_solutions(solutions_dir: Path) -> str:
    """Combine all solution files into one text."""
    text = ""
    for sol_file in solutions_dir.iterdir():
        if sol_file.suffix.lower() == '.pdf':
            text += extract_text_from_pdf(sol_file) + "\n\n"
        else:
            text += get_file_text(sol_file) + "\n\n"
    return text

def parse_marking_criteria(marking_dir: Path) -> str:
    """Combine all marking criteria files into one text."""
    text = ""
    for mc_file in marking_dir.iterdir():
        if mc_file.suffix.lower() == '.pdf':
            text += extract_text_from_pdf(mc_file) + "\n\n"
        else:
            text += get_file_text(mc_file) + "\n\n"
    return text

def grade_answer(question_text: str, solution_text: str, marking_text: str,
                 student_answer: str, max_marks: int) -> dict:
    """
    Use Ollama to grade a single answer. Returns a dict with:
    - marks_awarded (float)
    - deductions (list of strings explaining point cuts)
    """
    prompt = f"""
You are a strict but fair examiner. You will evaluate a student's answer to a question.

QUESTION:
{question_text}

MODEL SOLUTION (correct answer):
{solution_text if solution_text else "Not provided."}

MARKING CRITERIA / DEDUCTION RULES:
{marking_text if marking_text else "General: deduct for syntax errors, logical mistakes, incomplete answers."}

STUDENT'S ANSWER:
{student_answer}

The question is worth {max_marks} marks.
Please return a JSON object with two fields:
- "marks_awarded": a number between 0 and {max_marks}
- "deductions": a list of strings, each describing a specific mistake and how many marks were deducted.

Output ONLY the JSON, no other text.
"""

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0}
        )
        content = response['message']['content'].strip()
        # Extract JSON from possible markdown fences
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            return result
        else:
            return {"marks_awarded": 0, "deductions": ["AI grading failed to parse."]}
    except Exception as e:
        return {"marks_awarded": 0, "deductions": [f"Grading error: {e}"]}

def grade_all_students(cleaned_dir: Path, questions_dir: Path,
                       solutions_dir: Path, marking_dir: Path) -> List[dict]:
    """
    For each student, find their answer files (now named Qx...), match to a question,
    grade each, and aggregate results.
    Returns list of dicts ready for Excel.
    """
    questions = parse_question_papers(questions_dir)
    solutions_text = parse_solutions(solutions_dir)
    marking_text = parse_marking_criteria(marking_dir)
    max_marks = MAX_MARKS_DEFAULT

    all_results = []
    student_dirs = [d for d in cleaned_dir.iterdir() if d.is_dir()]

    print("Grading student submissions...")
    for student_dir in tqdm(student_dirs, desc="Grading"):
        student_id = student_dir.name
        student_total = 0
        details = {}

        # For each file, extract question number(s) from filename
        for file_path in student_dir.iterdir():
            if not file_path.is_file():
                continue
            # Expected filename: "Q1.pdf", "Q2_Q3.docx", etc.
            stem = file_path.stem  # e.g., "Q1" or "Q2_Q3" or "UNKNOWN_..."
            q_matches = re.findall(r'Q(\d+)', stem)
            if not q_matches:
                continue  # skip files we couldn't identify

            student_answer_text = get_file_text(file_path)
            for q_str in q_matches:
                q_num = int(q_str)
                if q_num not in questions:
                    continue
                question_text = questions[q_num]
                # Grade this particular question
                result = grade_answer(question_text, solutions_text, marking_text,
                                      student_answer_text, max_marks)
                marks = float(result.get("marks_awarded", 0))
                deductions = result.get("deductions", [])
                student_total += marks
                # Store per-question details
                if q_num not in details:
                    details[q_num] = {"marks": marks, "deductions": deductions}
                else:
                    # If a file answers the same question multiple times? Take best.
                    if marks > details[q_num]["marks"]:
                        details[q_num] = {"marks": marks, "deductions": deductions}

        # Build summary string of deductions
        deduction_summary = ""
        for q_num, info in sorted(details.items()):
            deduction_summary += f"Q{q_num} ({info['marks']}/{max_marks}): "
            deduction_summary += "; ".join(info['deductions']) + " | "

        all_results.append({
            "student_id": student_id,
            "total_marks": student_total,
            "per_question": details,
            "deduction_summary": deduction_summary.strip(" | ")
        })

    return all_results

# -------------------------- 5. EXCEL REPORT --------------------------
def generate_excel(results: List[dict], output_path: Path):
    """Create a formatted Excel file from the grading results."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Grades"

    # Headers
    headers = ["Student ID", "Total Marks", "Deduction Details"]
    ws.append(headers)

    # Style headers
    for col in range(1, len(headers)+1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    # Populate rows
    for result in results:
        ws.append([
            result["student_id"],
            result["total_marks"],
            result["deduction_summary"]
        ])

    # Adjust column widths
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 80

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    print(f"Excel report saved to {output_path}")

# -------------------------- MAIN PIPELINE --------------------------
def main():
    # Step 1: Clean submissions (unzip, flatten)
    submissions_dir = get_path(config["paths"]["submissions_dir"])
    cleaned_dir = get_path(config["paths"]["cleaned_dir"])
    clean_submissions_folder(submissions_dir, cleaned_dir)

    # Step 2: Rename files based on question numbers using AI
    questions_dir = get_path(config["paths"]["questions_dir"])
    identify_all_questions(cleaned_dir, questions_dir)

    # Step 3: Grade all students
    solutions_dir = get_path(config["paths"]["solutions_dir"])
    marking_dir = get_path(config["paths"]["marking_criteria_dir"])
    results = grade_all_students(cleaned_dir, questions_dir, solutions_dir, marking_dir)

    # Step 4: Generate Excel
    output_excel = get_path(config["paths"]["output_excel"])
    generate_excel(results, output_excel)

    print("\nAll done! Check the 'cleaned_submissions' folder and the Excel report.")

if __name__ == "__main__":
    main()