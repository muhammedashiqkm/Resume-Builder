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

env = Environment(loader=FileSystemLoader("app/templates"))
template = env.get_template("report_template.html")
executor = ThreadPoolExecutor()

REPORTS_DIR = "static/reports"

def format_date(date_str: str) -> str:
    """Converts ISO date '2024-06-01T00:00:00' to 'Jun 2024'."""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime("%b %Y")
    except:
        return date_str # Return original if parse fails

def save_pdf_report(student_data: StudentPortfolioInput, ai_content: AIContentOutput) -> str:
    # 1. Bucketing Logic with Date Formatting
    projects = []
    internships = []
    certificates = []

    for item in student_data.StudentProjectInternshipCertificationDetailsForPortfolio:
        # Create a dict to allow adding the 'formatted_date_range' field
        item_dict = item.model_dump()
        
        # Format dates
        start = format_date(item.FromDate)
        end = format_date(item.ToDate)
        item_dict['formatted_date_range'] = f"{start} - {end}"

        if item.Type == "Project":
            projects.append(item_dict)
        elif item.Type == "Internship":
            internships.append(item_dict)
        elif item.Type == "Certificate":
            certificates.append(item_dict)

    context = {
        "student": student_data,
        "ai": ai_content,
        "projects": projects,
        "internships": internships,
        "certificates": certificates,
    }

    html_out = template.render(context)

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