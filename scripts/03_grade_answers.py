"""
STEP 3: GRADE ANSWERS
=====================
What this does:
- Reads renamed submissions from Step 2
- Reads solutions and marking criteria
- Uses AI to grade each answer
- Saves grading results as JSON for Step 4

Run: python scripts/03_grade_answers.py
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config_loader import config, get_path, MAX_MARKS_DEFAULT
from utils.file_handlers import get_file_text, get_all_text_from_folder
from utils.ollama_helpers import ask_ollama, extract_json_from_response
from tqdm import tqdm


def parse_question_papers(questions_dir: Path) -> Dict[int, str]:
    """
    Try to split question paper into individual questions.
    Uses simple heuristic: looks for "1.", "2)", "Question 1", etc.
    Returns {question_number: "question text"}
    """
    all_text = get_all_text_from_folder(questions_dir)
    
    # Pattern: number followed by . or ) at start of line
    pattern = r'(?:^|\n)\s*(\d+)[\.\)]\s+'
    parts = re.split(pattern, all_text)
    
    questions = {}
    # parts[0] is anything before first number, skip it
    for i in range(1, len(parts), 2):
        q_num = int(parts[i])
        q_text = parts[i+1].strip() if i+1 < len(parts) else ""
        questions[q_num] = q_text
    
    # If splitting failed, treat whole paper as Q1
    if not questions:
        questions[1] = all_text.strip()
    
    return questions


def grade_single_answer(question_text: str, solution_text: str, 
                        marking_text: str, student_answer: str,
                        max_marks: int, question_num: int) -> dict:
    """
    Use AI to grade one student answer.
    Returns: {"marks_awarded": float, "deductions": [str, ...]}
    """
    if not student_answer.strip():
        return {
            "marks_awarded": 0, 
            "deductions": ["No answer submitted or file was empty."]
        }
    
    prompt = f"""You are a strict but fair programming exam grader. Evaluate this student's answer.

QUESTION {question_num}:
{question_text}

MODEL SOLUTION:
{solution_text if solution_text else "Not provided"}

MARKING SCHEME & DEDUCTION RULES:
{marking_text if marking_text else "General: deduct for syntax errors, logic errors, incomplete solutions. Give partial credit where appropriate."}

STUDENT'S ANSWER:
{student_answer[:5000]}

This question is worth {max_marks} marks.

Grade strictly according to the marking criteria. Provide:
- "marks_awarded": a number between 0 and {max_marks}
- "deductions": list of strings explaining each deduction with marks cut

Return ONLY a JSON object. No other text."""

    response = ask_ollama(prompt, temperature=0)
    result = extract_json_from_response(response)
    
    if not result:
        return {
            "marks_awarded": 0,
            "deductions": ["AI grading failed. Manual review needed."]
        }
    
    return result


def grade_all_students(renamed_dir: Path, questions_dir: Path,
                       solutions_dir: Path, marking_dir: Path) -> List[dict]:
    """
    Grade every student's answers and return results list.
    """
    # Parse reference materials
    print("Loading reference materials...")
    questions = parse_question_papers(questions_dir)
    solutions_text = get_all_text_from_folder(solutions_dir)
    marking_text = get_all_text_from_folder(marking_dir)
    max_marks = MAX_MARKS_DEFAULT
    
    print(f"Questions identified: {sorted(questions.keys())}")
    print(f"Solutions text: {len(solutions_text)} characters")
    print(f"Marking criteria: {len(marking_text)} characters\n")
    
    student_dirs = [d for d in renamed_dir.iterdir() if d.is_dir()]
    all_results = []
    
    for student_dir in tqdm(student_dirs, desc="Grading students"):
        student_id = student_dir.name
        student_total = 0
        per_question_details = {}
        
        # Grade each file
        for file_path in student_dir.iterdir():
            if not file_path.is_file():
                continue
            
            # Extract question numbers from filename
            stem = file_path.stem  # e.g., "Q1", "Q2_Q3"
            q_matches = re.findall(r'Q(\d+)', stem)
            
            if not q_matches:
                continue  # Skip UNKNOWN files
            
            student_answer = get_file_text(file_path)
            
            for q_str in q_matches:
                q_num = int(q_str)
                
                if q_num not in questions:
                    print(f"  ⚠️  Q{q_num} not found in question paper, skipping")
                    continue
                
                # Grade this answer
                question_text = questions[q_num]
                result = grade_single_answer(
                    question_text, solutions_text, marking_text,
                    student_answer, max_marks, q_num
                )
                
                marks = float(result.get("marks_awarded", 0))
                deductions = result.get("deductions", [])
                
                student_total += marks
                
                # Store in per_question_details (take best if same question appears twice)
                if q_num not in per_question_details or marks > per_question_details[q_num]["marks"]:
                    per_question_details[q_num] = {
                        "marks": marks,
                        "max_marks": max_marks,
                        "deductions": deductions
                    }
        
        # Build summary
        deduction_summary = ""
        for q_num in sorted(per_question_details.keys()):
            info = per_question_details[q_num]
            deduction_summary += f"Q{q_num} ({info['marks']}/{info['max_marks']}): "
            deduction_summary += "; ".join(info['deductions']) + " | "
        
        result_entry = {
            "student_id": student_id,
            "total_marks": round(student_total, 1),
            "per_question": per_question_details,
            "deduction_summary": deduction_summary.strip(" | ")
        }
        
        all_results.append(result_entry)
        
        # Print per-student summary
        print(f"\n  {student_id}: {student_total}/{max_marks * len(questions)} marks")
    
    return all_results


def main():
    print(f"\n{'='*60}")
    print(f"STEP 3: Grading Answers")
    print(f"{'='*60}")
    
    # Get paths
    renamed_dir = get_path(config["paths"]["renamed_dir"])
    questions_dir = get_path(config["paths"]["questions_dir"])
    solutions_dir = get_path(config["paths"]["solutions_dir"])
    marking_dir = get_path(config["paths"]["marking_criteria_dir"])
    
    # Validate inputs
    if not renamed_dir.exists():
        print("ERROR: 'renamed_submissions' folder not found!")
        print("Run Step 2 first: python scripts/02_rename_by_questions.py")
        return
    
    for dir_path, name in [(questions_dir, "questions"), 
                           (solutions_dir, "solutions"),
                           (marking_dir, "marking criteria")]:
        if not dir_path.exists():
            print(f"ERROR: '{name}' folder not found at {dir_path}")
            return
    
    # Grade all students
    print("Starting grading... This will take a while. ⏳\n")
    results = grade_all_students(renamed_dir, questions_dir, solutions_dir, marking_dir)
    
    # Save results for next step
    output_path = get_path("grading_output/grading_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Grading complete! Results saved to {output_path}")
    print(f"Total students graded: {len(results)}")
    print(f"Ready for Step 4: Generate Excel report\n")


if __name__ == "__main__":
    main()