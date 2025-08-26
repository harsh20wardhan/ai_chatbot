"""
Common Utility Functions

Helper functions used across the application for common operations.
"""

import uuid
import hashlib
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import re

def generate_uuid() -> str:
    """Generate a new UUID string"""
    return str(uuid.uuid4())

def generate_short_id(length: int = 8) -> str:
    """Generate a short random ID"""
    return str(uuid.uuid4()).replace('-', '')[:length]

def hash_string(text: str) -> str:
    """Generate SHA256 hash of a string"""
    return hashlib.sha256(text.encode()).hexdigest()

def current_timestamp() -> datetime:
    """Get current UTC timestamp"""
    return datetime.now(timezone.utc)

def format_timestamp(dt: datetime) -> str:
    """Format datetime as ISO string"""
    return dt.isoformat()

def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO timestamp string to datetime"""
    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]
    return filename

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks"""
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Only keep chunks that are reasonably sized
        if len(chunk) >= chunk_size // 2:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = end - overlap
        
        # Break if we've reached the end
        if end >= len(text):
            break
    
    return chunks

def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL"""
    import re
    pattern = r'https?://([^/]+)'
    match = re.match(pattern, url)
    return match.group(1) if match else None

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON string with fallback"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """Safely serialize object to JSON with fallback"""
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return default

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def paginate_results(items: List[Any], page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """Paginate a list of items"""
    total_items = len(items)
    total_pages = (total_items + page_size - 1) // page_size
    
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    return {
        "items": items[start_idx:end_idx],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

def filter_ai_response(content: str) -> str:
    """Remove hidden meta-thinking blocks from AI responses"""
    if not content or not isinstance(content, str):
        return content

    # Tags to strip completely (case-insensitive)
    removable_tags = [
        'thinking', 'reasoning', 'reflection', 'tool_call', 'tool_output',
        'analysis', 'chain_of_thought', 'cot', 'scratchpad'
    ]

    for tag in removable_tags:
        pattern = rf'<{tag}[^>]*>[\s\S]*?</{tag}>'
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)

    # Also remove self-closing variants
    content = re.sub(r'<(?:' + '|'.join(removable_tags) + r')(?:\s[^>]*)?\s*/>', '', content, flags=re.IGNORECASE)

    # Normalize excess blank lines
    content = re.sub(r'\n\s*\n', '\n', content)

    return content.strip()

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix