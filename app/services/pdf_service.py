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
    Converts ISO date strings to 'Month Year' format (e.g., 'Jun 2023').
    Includes logic to fix common data typos (like 2023-08:25 -> 2023-08-25).
    """
    if not date_str:
        return ""
    
    try:
        # 1. Try standard parsing
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%b %Y")
    except ValueError:
        try:
            # 2. Fallback: Fix dirty data (e.g., "2023-08:25" typo in input)
            # Remove time component and fix separators
            clean_date = date_str.split('T')[0].replace(':', '-')
            dt = datetime.fromisoformat(clean_date)
            return dt.strftime("%b %Y")
        except ValueError:
            # 3. If completely unparseable, return original so data isn't lost
            return date_str

def save_pdf_report(student_data: StudentPortfolioInput, ai_content: AIContentOutput) -> str:
    # --- 1. Bucketing & Formatting Logic ---
    projects = []
    internships = []
    certificates = []

    for item in student_data.StudentProjectInternshipCertificationDetailsForPortfolio:
        item_dict = item.model_dump()
        
        # Format the dates
        start = format_date(item.FromDate)
        end = format_date(item.ToDate)
        item_dict['formatted_date_range'] = f"{start} - {end}"

        if item.Type == "Project":
            # Add (Major/Minor) to title if it exists
            if item.SubType and item.SubType.lower() != "none":
                # Capitalize nicely: "major" -> "Major"
                item_dict['Title'] = f"{item.Title} ({item.SubType.capitalize()})"
            projects.append(item_dict)

        elif item.Type == "Internship":
            internships.append(item_dict)

        elif item.Type == "Certificate":
            certificates.append(item_dict)

    # --- 2. Prepare Context ---
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

        return f"static/reports/{filename}"
        
    except Exception as e:
        error_logger.error(f"PDF Error: {e}")
        raise

async def generate_portfolio_pdf_async(student_data: StudentPortfolioInput, ai_content: AIContentOutput) -> str:
    loop = asyncio.get_running_loop()
    url = await loop.run_in_executor(executor, save_pdf_report, student_data, ai_content)
    return url