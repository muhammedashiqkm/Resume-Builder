import pdfkit
import json
from jinja2 import Environment, FileSystemLoader
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.core.config import settings

from app.models.report import StudentPortfolioInput, AIContentOutput
from app.core.logging_config import error_logger
from app.core.utils import format_date_str

env = Environment(loader=FileSystemLoader("app/templates"))
template = env.get_template("report_template.html")
executor = ThreadPoolExecutor()

REPORTS_DIR = "media/reports"
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

def sanitize_filename(text: str) -> str:
    """
    Removes special characters to make strings safe for filenames.
    Replaces spaces with underscores.
    """
    if not text:
        return "unknown"
    safe_text = "".join(c for c in text if c.isalnum() or c in " _-").strip()
    return safe_text.replace(" ", "_")

def save_pdf_report(student_data: StudentPortfolioInput, ai_content: AIContentOutput) -> str:
    """
    Generates a PDF. 
    Filename is based on Name + Institution + Email.
    Writing to the same filename automatically overwrites the previous version.
    """
    
    processed_projects = []
    for item in student_data.projects:
        item_dict = item.model_dump()
        start = format_date_str(item.from_date)
        end = format_date_str(item.to_date)
        item_dict['formatted_date_range'] = f"{start} - {end}"
        
        if item.sub_type and item.sub_type.lower() != "none":
            item_dict['title'] = f"{item.title} ({item.sub_type})"
            
        processed_projects.append(item_dict)

    processed_internships = []
    for item in student_data.internships:
        item_dict = item.model_dump()
        start = format_date_str(item.from_date)
        end = format_date_str(item.to_date)
        item_dict['formatted_date_range'] = f"{start} - {end}"
        processed_internships.append(item_dict)

    processed_certs = []
    for item in student_data.certifications:
        item_dict = item.model_dump()
        start = format_date_str(item.from_date)
        end = format_date_str(item.to_date)
        item_dict['formatted_date_range'] = f"{start} - {end}"
        processed_certs.append(item_dict)

    psychometric_data = []
    if student_data.psychometric_details:
        for item in student_data.psychometric_details:
            try:
                if item.json_result:
                    parsed_result = json.loads(item.json_result)
                    sections = parsed_result.get("sections", [])
                    
                    for section in sections:
                        psychometric_data.append({
                            "category": item.category,      
                            "test_name": section.get("section", ""), 
                            "description": section.get("description", ""),
                            "representation": section.get("representation", "")
                        })
            except Exception as e:
                error_logger.warning(f"Error parsing psychometric JSON for category {item.category}: {e}")
                continue

    context = {
        "student": student_data,
        "ai": ai_content,
        "projects": processed_projects,
        "internships": processed_internships,
        "certificates": processed_certs,
        "psychometric_data": psychometric_data,
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
        
        safe_name = sanitize_filename(student_data.student_name)
        safe_institute = sanitize_filename(student_data.institution_name)
        safe_email = sanitize_filename(student_data.email.replace("@", "_at_").replace(".", "_"))

        filename = f"{safe_name}_{safe_institute}_{safe_email}.pdf"
        file_path = os.path.join(REPORTS_DIR, filename)

        with open(file_path, 'wb') as f:
            f.write(pdf_bytes)

        return f"{settings.BASE_URL}/media/reports/{filename}"
        
    except Exception as e:
        error_logger.error(f"PDF Error: {e}")
        raise

async def generate_portfolio_pdf_async(student_data: StudentPortfolioInput, ai_content: AIContentOutput) -> str:
    loop = asyncio.get_running_loop()
    url = await loop.run_in_executor(executor, save_pdf_report, student_data, ai_content)
    return url