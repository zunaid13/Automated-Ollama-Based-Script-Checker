# Automated Exam Grading Pipeline

An AI-powered exam grading system that automates the entire workflow from messy student submissions to a polished grade report. Using **Ollama** with locally running open-source models (like **Qwen 2.5 32B**), the pipeline handles nested zip files, identifies which question each file answers, grades against solutions and marking rubrics, and generates a detailed Excel report—all on your machine with complete privacy.

## What It Does

1. **Cleans** — Extracts zipped submissions (even zips inside zips), flattens nested folders, and organizes everything into a clean structure.

2. **Renames** — Uses AI to read each student file and match it to the correct question(s), renaming them to `Q1.pdf`, `Q2_Q3.docx`, etc.

3. **Grades** — Evaluates each answer against your solution key and marking criteria, providing marks and point-by-point deduction reasons.

4. **Reports** — Outputs a formatted Excel file with per-student totals, per-question breakdowns, and deduction summaries.

## Perfect For

- Programming or written exam grading
- Courses with 20–40+ students
- TAs and instructors who want consistent, fast feedback
- Anyone who wants AI grading without sending data to the cloud
