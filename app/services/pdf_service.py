# app/services/pdf_service.py
import pdfkit
from jinja2 import Environment, FileSystemLoader
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.models.report import StudentPortfolioInput, AIContentOutput
from app.core.logging_config import error_logger
from app.core.utils import format_date_str

# Setup Jinja2
env = Environment(loader=FileSystemLoader("app/templates"))
template = env.get_template("report_template.html")
executor = ThreadPoolExecutor()

REPORTS_DIR = "static/reports"
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

def sanitize_filename(text: str) -> str:
    """
    Removes special characters to make strings safe for filenames.
    Replaces spaces with underscores.
    """
    if not text:
        return "unknown"
    # Keep alphanumeric, underscores, hyphens. Replace spaces with _.
    safe_text = "".join(c for c in text if c.isalnum() or c in " _-").strip()
    return safe_text.replace(" ", "_")

def save_pdf_report(student_data: StudentPortfolioInput, ai_content: AIContentOutput) -> str:
    """
    Generates a PDF. 
    Filename is based on Name + Institution + Email.
    Writing to the same filename automatically overwrites the previous version.
    """
    # --- 1. Bucketing & Formatting Logic ---
    projects = []
    internships = []
    certificates = []

    for item in student_data.details_list:
        item_dict = item.model_dump()
        
        start = format_date_str(item.from_date)
        end = format_date_str(item.to_date)
        item_dict['formatted_date_range'] = f"{start} - {end}"

        if item.type == "Project":
            if item.sub_type and item.sub_type.lower() != "none":
                item_dict['title'] = f"{item.title} ({item.sub_type})"
            projects.append(item_dict)

        elif item.type == "Internship":
            internships.append(item_dict)

        elif item.type == "Certificate":
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
        
        # --- NEW FILENAME LOGIC (Static & Unique) ---
        
        # 1. Sanitize the Name and Institution
        safe_name = sanitize_filename(student_data.student_name)
        safe_institute = sanitize_filename(student_data.institution_name)
        
        # 2. Sanitize Email (Replace @ and . to avoid filesystem issues)
        # e.g., user@gmail.com -> user_at_gmail_com
        safe_email = sanitize_filename(student_data.email.replace("@", "_at_").replace(".", "_"))

        # 3. Combine: Name_Institute_Email.pdf
        # Because there is no timestamp, this filename is constant for this user.
        filename = f"{safe_name}_{safe_institute}_{safe_email}.pdf"
        
        file_path = os.path.join(REPORTS_DIR, filename)

        # 4. Write File (Overwrites existing file automatically)
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