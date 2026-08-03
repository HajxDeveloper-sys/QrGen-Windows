import urllib.parse
import re
import datetime

def validate_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme in ["http", "https"] and bool(parsed.netloc)

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\/:*?"<>|]', '_', name)

def get_timestamp_string() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
