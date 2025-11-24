# app/services/pdf_service.py
import pdfkit
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import os
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.models.report import StudentPortfolioInput, AIContentOutput
from app.core.logging_config import error_logger

# Set up Jinja2 environment
env = Environment(loader=FileSystemLoader("app/templates"))
template = env.get_template("report_template.html")
executor = ThreadPoolExecutor()

REPORTS_DIR = "static/reports"

def format_date(date_str: str) -> str:
    """
    Converts ISO date '2023-06-01T00:00:00' to 'Jun 2023'.
    Robustly handles typos like '2023-08:25' (colon instead of hyphen).
    """
    if not date_str:
        return ""
    
    # --- FIX: Sanitize common typos ---
    # The user input had '2023-08:25', replacing colons in the date part (first 10 chars)
    clean_date = date_str
    if len(date_str) >= 10:
        date_part = date_str[:10].replace(':', '-')
        clean_date = date_part + date_str[10:]
        
    try:
        dt = datetime.fromisoformat(clean_date)
        return dt.strftime("%b %Y")
    except ValueError:
        # If it still fails, return original so we don't crash
        return date_str

def save_pdf_report(student_data: StudentPortfolioInput, ai_content: AIContentOutput) -> str:
    """
    Prepares data, formatting dates and titles, then generates the PDF.
    """
    # --- 1. Bucketing & Formatting Logic ---
    projects = []
    internships = []
    certificates = []

    for item in student_data.StudentProjectInternshipCertificationDetailsForPortfolio:
        # Convert Pydantic model to dict so we can modify fields
        item_dict = item.model_dump()
        
        # Format the dates (e.g., "Jun 2023 - Aug 2023")
        start = format_date(item.FromDate)
        end = format_date(item.ToDate)
        item_dict['formatted_date_range'] = f"{start} - {end}"

        # Sort into categories and apply specific formatting
        if item.Type == "Project":
            # Append SubType (Major/Minor) to the Title if valid
            if item.SubType and item.SubType.lower() != "none":
                item_dict['Title'] = f"{item.Title} ({item.SubType})"
            projects.append(item_dict)

        elif item.Type == "Internship":
            internships.append(item_dict)

        elif item.Type == "Certificate":
            certificates.append(item_dict)

    # --- 2. Prepare Context for Jinja2 ---
    context = {
        "student": student_data,
        "ai": ai_content,
        "projects": projects,
        "internships": internships,
        "certificates": certificates,
    }

    # --- 3. Render HTML ---
    html_out = template.render(context)

    # --- 4. Generate PDF ---
    try:
        pdf_bytes = pdfkit.from_string(html_out, False, options={
            "enable-local-file-access": "",
            "page-size": "A4",
            "margin-top": "0.75in",
            "margin-right": "0.75in",
            "margin-bottom": "0.75in",
            "margin-left": "0.75in",
        })
        
        safe_name = "".join(c for c in student_data.StudentName if c.isalnum() or c in " _-").rstrip()
        unique_id = str(uuid.uuid4()).split('-')[0]
        filename = f"{safe_name}_{unique_id}_Portfolio.pdf"
        file_path = os.path.join(REPORTS_DIR, filename)

        with open(file_path, 'wb') as f:
            f.write(pdf_bytes)

        # Return the URL path
        return f"static/reports/{filename}"
        
    except Exception as e:
        error_logger.error(f"PDF Error: {e}")
        raise

async def generate_portfolio_pdf_async(student_data: StudentPortfolioInput, ai_content: AIContentOutput) -> str:
    """
    Async wrapper to run the blocking PDF generation in a separate thread.
    """
    loop = asyncio.get_running_loop()
    url = await loop.run_in_executor(executor, save_pdf_report, student_data, ai_content)
    return url