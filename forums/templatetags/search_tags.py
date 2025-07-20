"""
Template tags for search functionality.
"""
import re
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape

register = template.Library()


@register.filter
def highlight_search_terms(text, query):
    """
    Highlight search terms in text with HTML markup.
    
    Args:
        text: The text to highlight terms in
        query: The search query containing terms to highlight
        
    Returns:
        HTML-safe string with highlighted terms
    """
    if not text or not query:
        return escape(text) if text else ''
    
    # Split query into individual terms
    query_terms = query.strip().split()
    if not query_terms:
        return escape(text)
    
    # Escape the text to prevent XSS
    escaped_text = escape(text)
    
    # Create regex pattern for all terms (case-insensitive)
    pattern_parts = []
    for term in query_terms:
        # Escape special regex characters in the search term
        escaped_term = re.escape(term)
        pattern_parts.append(f'({escaped_term})')
    
    if not pattern_parts:
        return escaped_text
    
    # Combine all terms with OR operator
    pattern = '|'.join(pattern_parts)
    
    try:
        # Highlight matching terms
        def highlight_match(match):
            matched_text = match.group(0)
            return f'<mark class="search-highlight">{matched_text}</mark>'
        
        # Apply highlighting
        highlighted = re.sub(pattern, highlight_match, escaped_text, flags=re.IGNORECASE)
        
        return mark_safe(highlighted)
    
    except re.error:
        # If regex fails, return escaped text without highlighting
        return escaped_text


@register.filter
def highlight_in_suggestions(text, query):
    """
    Highlight search terms in autocomplete suggestions.
    Similar to highlight_search_terms but optimized for shorter text.
    
    Args:
        text: The text to highlight terms in
        query: The search query containing terms to highlight
        
    Returns:
        HTML-safe string with highlighted terms
    """
    if not text or not query:
        return escape(text) if text else ''
    
    # For suggestions, only highlight if query is a subset of the text
    escaped_text = escape(text)
    escaped_query = escape(query.strip())
    
    if not escaped_query:
        return escaped_text
    
    try:
        # Case-insensitive replacement
        pattern = re.escape(escaped_query)
        
        def highlight_match(match):
            matched_text = match.group(0)
            return f'<strong class="text-primary">{matched_text}</strong>'
        
        highlighted = re.sub(pattern, highlight_match, escaped_text, flags=re.IGNORECASE)
        
        return mark_safe(highlighted)
    
    except re.error:
        return escaped_text


@register.filter  
def truncate_and_highlight(text, args):
    """
    Truncate text and highlight search terms.
    
    Args:
        text: The text to process
        args: String containing "length,query" separated by comma
        
    Returns:
        Truncated and highlighted text
    """
    if not text or not args:
        return escape(text) if text else ''
    
    try:
        parts = args.split(',', 1)
        if len(parts) != 2:
            return escape(text)
        
        length = int(parts[0])
        query = parts[1].strip()
        
        # First truncate, then highlight
        if len(text) > length:
            # Try to truncate at word boundary near the target length
            truncated = text[:length].rsplit(' ', 1)[0] + '...'
        else:
            truncated = text
        
        # Apply highlighting
        return highlight_search_terms(truncated, query)
        
    except (ValueError, IndexError):
        return escape(text)


@register.simple_tag
def search_result_snippet(content, query, max_length=200):
    """
    Generate a smart snippet from content that includes the search query.
    
    Args:
        content: The full content text
        query: Search query terms
        max_length: Maximum length of snippet
        
    Returns:
        HTML-safe snippet with highlighted terms
    """
    if not content or not query:
        return escape(content[:max_length] + '...' if len(content) > max_length else content)
    
    escaped_content = escape(content)
    query_terms = query.strip().split()
    
    if not query_terms:
        return escaped_content[:max_length] + ('...' if len(escaped_content) > max_length else '')
    
    # Find the first occurrence of any search term
    best_start = 0
    for term in query_terms:
        pos = escaped_content.lower().find(term.lower())
        if pos != -1:
            # Center the snippet around the found term
            start = max(0, pos - max_length // 2)
            # Try to start at word boundary
            if start > 0:
                space_pos = escaped_content.find(' ', start)
                if space_pos != -1 and space_pos - start < 20:
                    start = space_pos + 1
            best_start = start
            break
    
    # Extract snippet
    snippet = escaped_content[best_start:best_start + max_length]
    
    # Add ellipsis if truncated
    prefix = '...' if best_start > 0 else ''
    suffix = '...' if best_start + max_length < len(escaped_content) else ''
    
    snippet = prefix + snippet + suffix
    
    # Apply highlighting
    return highlight_search_terms(snippet, query)