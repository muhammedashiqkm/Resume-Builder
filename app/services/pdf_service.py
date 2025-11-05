# app/services/pdf_service.py
import pdfkit
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from app.models.report import AIReportOutput
from app.core.logging_config import error_logger

# Set up Jinja2 environment
env = Environment(loader=FileSystemLoader("app/templates"))
template = env.get_template("report_template.html")

def generate_pdf_from_data(report_data: AIReportOutput) -> bytes:
    """
    Renders an HTML report template with AI-generated data and converts it to a PDF.
    """
    data_dict = {
        "portfolio": report_data.model_dump(),
        "generation_date": datetime.now().strftime("%B %d, %Y")
    }
    
    html_out = template.render(data_dict)
    
    try:
        pdf_bytes = pdfkit.from_string(html_out, False, options={"enable-local-file-access": ""})
        if not pdf_bytes:
            raise ValueError("pdfkit returned empty content.")
        return pdf_bytes
    except Exception as e:
        error_logger.error(f"An error occurred during PDF generation: {e}")
        raise