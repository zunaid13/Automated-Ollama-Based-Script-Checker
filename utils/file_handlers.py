"""
File handling utilities: unzipping, text extraction, file operations.
Used by cleaning and renaming scripts.
"""

import os
import shutil
import zipfile
import tempfile
from pathlib import Path
import pdfplumber
from docx import Document


# ---------- ZIP HANDLING ----------
def unzip_recursive(zip_path: Path, extract_to: Path):
    """
    Extract a zip file. If any extracted files are also zips,
    extract them too. All files end up directly in extract_to.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Extract main zip
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(tmpdir)

        # Walk through extracted files AND folders
        for root, dirs, files in os.walk(tmpdir):
            root_path = Path(root)
            for file in files:
                file_path = root_path / file
                
                # If nested zip, extract it recursively
                if file_path.suffix.lower() == '.zip':
                    unzip_recursive(file_path, extract_to)
                else:
                    # Copy to destination, handle name collisions
                    dest = extract_to / file_path.name
                    if dest.exists():
                        stem = dest.stem
                        suffix = dest.suffix
                        counter = 1
                        while dest.exists():
                            dest = extract_to / f"{stem}_{counter}{suffix}"
                            counter += 1
                    shutil.copy2(file_path, dest)


# ---------- FOLDER FLATTENING (NEW!) ----------
def flatten_directory(source_dir: Path, dest_dir: Path):
    """
    Recursively copy all files from source_dir (including subfolders)
    directly into dest_dir. No subfolders in the output.
    
    Example:
        source_dir/
        ├── Assignment1/
        │   ├── answer.pdf
        │   └── code.py
        └── notes.docx
        
        becomes:
        dest_dir/
        ├── answer.pdf
        ├── code.py
        └── notes.docx
    """
    # Walk through ALL subdirectories
    for root, dirs, files in os.walk(source_dir):
        root_path = Path(root)
        for file in files:
            file_path = root_path / file
            
            # Handle zip files
            if file_path.suffix.lower() == '.zip':
                unzip_recursive(file_path, dest_dir)
            else:
                # Handle name collisions (files from different subfolders
                # might have the same name)
                dest = dest_dir / file_path.name
                if dest.exists():
                    stem = dest.stem
                    suffix = dest.suffix
                    counter = 1
                    while dest.exists():
                        dest = dest_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                shutil.copy2(file_path, dest)


# ---------- TEXT EXTRACTION ----------
def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"  Warning: Could not read PDF {pdf_path.name}: {e}")
    return text


def extract_text_from_docx(docx_path: Path) -> str:
    """Extract all text from a DOCX file."""
    try:
        doc = Document(docx_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"  Warning: Could not read DOCX {docx_path.name}: {e}")
        return ""


def extract_text_from_txt(txt_path: Path) -> str:
    """Read plain text file."""
    try:
        with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        print(f"  Warning: Could not read file {txt_path.name}: {e}")
        return ""


def get_file_text(file_path: Path, max_chars: int = None) -> str:
    """
    Extract text from various file formats.
    Returns up to max_chars characters if specified.
    """
    suffix = file_path.suffix.lower()
    
    if suffix == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif suffix == '.docx':
        text = extract_text_from_docx(file_path)
    elif suffix in ['.txt', '.py', '.java', '.c', '.cpp', '.js', '.html', '.css', '.ipynb', 
                    '.md', '.json', '.xml', '.yaml', '.yml', '.sql', '.r', '.rb']:
        text = extract_text_from_txt(file_path)
    else:
        # Try plain text as fallback for unknown types
        try:
            text = extract_text_from_txt(file_path)
        except Exception:
            text = ""
    
    if max_chars and len(text) > max_chars:
        text = text[:max_chars]
    
    return text.strip()


def get_all_text_from_folder(folder_path: Path) -> str:
    """
    Combine all readable files in a folder into one text string.
    Useful for combining all question papers or solutions.
    """
    all_text = ""
    for file_path in folder_path.iterdir():
        if file_path.is_file():
            text = get_file_text(file_path)
            if text:
                all_text += text + "\n\n"
    return all_text