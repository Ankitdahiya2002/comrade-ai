# =============================================================
# src/file_reader.py
# Extracts readable text from uploaded files.
# Supported formats: PDF, TXT, Excel (.xlsx / .xls), CSV
# =============================================================

import io

import pandas as pd
import fitz  # PyMuPDF — for PDF extraction


def extract_pdf(uploaded_file) -> str:
    """
    Extract all text from a PDF file.
    Each page is labelled [Page N] so the AI can reference pages.
    """
    data = uploaded_file.read()
    doc  = fitz.open(stream=data, filetype="pdf")

    pages = []
    for i, page in enumerate(doc):
        text = page.get_text().strip()
        if text:
            pages.append(f"[Page {i + 1}]\n{text}")

    return "\n\n".join(pages)


def extract_txt(uploaded_file) -> str:
    """
    Read a plain-text file.
    Tries UTF-8 first, falls back to latin-1 for older files.
    """
    raw = uploaded_file.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="replace")


def extract_excel(uploaded_file) -> str:
    """
    Convert an Excel file to a readable text table.
    Each sheet is shown with its name as a header.
    """
    data = uploaded_file.read()
    xl   = pd.ExcelFile(io.BytesIO(data))

    sheets = []
    for sheet_name in xl.sheet_names:
        df = xl.parse(sheet_name).fillna("")
        sheets.append(f"[Sheet: {sheet_name}]\n{df.to_string(index=False)}")

    return "\n\n".join(sheets)


def extract_csv(uploaded_file) -> str:
    """
    Convert a CSV file to a readable text table.
    Shows row and column counts in a header line.
    """
    data = uploaded_file.read()
    try:
        df = pd.read_csv(io.BytesIO(data))
    except Exception:
        df = pd.read_csv(io.BytesIO(data), encoding="latin-1")

    df = df.fillna("")
    rows, cols = df.shape
    header = f"[CSV: {rows} rows × {cols} columns]\n"
    return header + df.to_string(index=False)


def extract_file(uploaded_file) -> str:
    """
    Public entry point — dispatches to the correct extractor
    based on the file's MIME type or extension.

    Raises ValueError for unsupported file types.
    """
    mime = uploaded_file.type or ""
    name = uploaded_file.name.lower()

    if mime == "application/pdf" or name.endswith(".pdf"):
        return extract_pdf(uploaded_file)

    if mime == "text/plain" or name.endswith(".txt"):
        return extract_txt(uploaded_file)

    if (
        mime in (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
        )
        or name.endswith((".xlsx", ".xls"))
    ):
        return extract_excel(uploaded_file)

    if mime == "text/csv" or name.endswith(".csv"):
        return extract_csv(uploaded_file)

    raise ValueError(
        f"Unsupported file type: {mime or name}. "
        "Please upload a PDF, TXT, XLSX, XLS, or CSV file."
    )
