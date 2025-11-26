# app/core/utils.py
from datetime import datetime

def format_date_str(date_str: str) -> str:
    """
    Parses ISO dates (and sanitizes typos like '2023-08:25') 
    Returns format 'Jun 2023'. Returns original string if parsing fails.
    """
    if not date_str:
        return ""
    
    clean_date = date_str
    if len(date_str) >= 10:
        date_part = date_str[:10].replace(':', '-')
        clean_date = date_part + date_str[10:]
        
    try:
        dt = datetime.fromisoformat(clean_date)
        return dt.strftime("%b %Y")
    except ValueError:
        return date_str