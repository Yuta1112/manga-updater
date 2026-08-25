import re
from typing import Optional


def normalize_chapter_number(chapter_str: str) -> Optional[float]:
    """
    Normalize different chapter formats to comparable numbers
    
    Args:
        chapter_str: Chapter string in various formats like "第120話", "Chapter 12", "12.5話", etc.
    
    Returns:
        Normalized chapter number as float, or None if could not parse
    """
    if not chapter_str:
        return None
    
    # Remove common prefixes and suffixes
    cleaned = re.sub(r'^(第|Ch|chap|Chapter)', '', chapter_str, flags=re.IGNORECASE)
    cleaned = re.sub(r'(話|话|章)$', '', cleaned)
    cleaned = cleaned.strip()
    
    # Extract numeric part (including decimals)
    match = re.search(r'(\d+(?:\.\d+)?)', cleaned)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    
    # If we couldn't extract a number, return None
    return None


def compare_chapters(current: str, previous: str) -> int:
    """
    Compare two chapter strings
    
    Returns:
        1 if current > previous (newer)
        0 if equal
        -1 if current < previous (older)
        None if comparison is not possible
    """
    current_num = normalize_chapter_number(current)
    previous_num = normalize_chapter_number(previous)

    # If either side is not a parseable numbered chapter, we cannot reliably
    # tell what is newer. Only an exact string match means "no change".
    if current_num is None or previous_num is None:
        return 0 if current == previous else None

    if current_num > previous_num:
        return 1
    elif current_num < previous_num:
        return -1
    else:
        return 0


def is_newer_chapter(current: str, previous: str) -> bool:
    """
    Check if current chapter is newer than previous
    
    Returns:
        True if current is newer, False otherwise
    """
    comparison = compare_chapters(current, previous)
    return comparison == 1 if comparison is not None else False