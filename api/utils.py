import re

# Regex to match internal refs like GEN-VIS-1, SW-14.1, etc.
# Pattern: One or more uppercase letters, followed by a hyphen, 
# followed by uppercase letters or numbers, and potentially more hyphens/dots/numbers.
INTERNAL_REF_PATTERN = re.compile(r'\b[A-Z]+(?:-[A-Z0-9]+)+(?:\.[0-9]+)?\b')

ROUTE_DISPLAY_NAMES = {
    "SKILLED_WORKER": "Skilled Worker",
    "VISITOR": "Visitor Visa",
    "HEALTH_AND_CARE": "Health and Care Worker",
    "GRADUATE": "Graduate Visa",
    "GLOBAL_TALENT": "Global Talent",
    "HPI": "High Potential Individual",
    "SCALE_UP": "Scale-up Worker",
    "APPENDIX_FM": "Family Visa",
    "STUDENT": "Student Visa",
}

def get_route_display_name(route_key: str) -> str:
    return ROUTE_DISPLAY_NAMES.get(route_key, route_key.replace('_', ' ').title())

def strip_internal_refs(data):
    """
    Recursively strips internal refs from strings, lists, and dictionaries.
    """
    if isinstance(data, str):
        # If the entire string is just a ref, return empty or a placeholder if needed
        # But usually we just want to remove it from text.
        # The requirement says "must never appear", so we replace with empty string.
        return INTERNAL_REF_PATTERN.sub('', data).strip()
    elif isinstance(data, list):
        return [strip_internal_refs(item) for item in data if strip_internal_refs(item)]
    elif isinstance(data, dict):
        return {k: strip_internal_refs(v) for k, v in data.items()}
    return data
