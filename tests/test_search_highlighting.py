"""
Tests for search highlighting template tags.
"""
from django.test import TestCase
from django.template import Context, Template
from forums.templatetags.search_tags import (
    highlight_search_terms, 
    highlight_in_suggestions,
    truncate_and_highlight,
    search_result_snippet
)


class SearchHighlightingTests(TestCase):
    """Tests for search result highlighting functionality."""
    
    def test_highlight_search_terms_basic(self):
        """Test basic search term highlighting."""
        text = "This is a test of JavaScript programming"
        query = "JavaScript"
        result = highlight_search_terms(text, query)
        
        expected = 'This is a test of <mark class="search-highlight">JavaScript</mark> programming'
        self.assertEqual(result, expected)
    
    def test_highlight_search_terms_multiple_terms(self):
        """Test highlighting multiple search terms."""
        text = "JavaScript and Python are programming languages"
        query = "JavaScript Python"
        result = highlight_search_terms(text, query)
        
        self.assertIn('<mark class="search-highlight">JavaScript</mark>', result)
        self.assertIn('<mark class="search-highlight">Python</mark>', result)
    
    def test_highlight_search_terms_case_insensitive(self):
        """Test case-insensitive highlighting."""
        text = "JavaScript is awesome"
        query = "javascript"
        result = highlight_search_terms(text, query)
        
        expected = '<mark class="search-highlight">JavaScript</mark> is awesome'
        self.assertEqual(result, expected)
    
    def test_highlight_search_terms_partial_words(self):
        """Test highlighting partial word matches."""
        text = "JavaScript development and scripting"
        query = "script"
        result = highlight_search_terms(text, query)
        
        # Should highlight 'script' in both 'JavaScript' and 'scripting'
        self.assertIn('<mark class="search-highlight">script</mark>', result)
    
    def test_highlight_search_terms_html_escaping(self):
        """Test that HTML in text is properly escaped."""
        text = "<script>alert('test')</script> JavaScript"
        query = "JavaScript"
        result = highlight_search_terms(text, query)
        
        # HTML should be escaped, JavaScript should be highlighted
        self.assertIn('&lt;script&gt;', result)
        self.assertIn('<mark class="search-highlight">JavaScript</mark>', result)
        self.assertNotIn('<script>', result)  # Ensure no unescaped HTML
    
    def test_highlight_search_terms_empty_query(self):
        """Test highlighting with empty query."""
        text = "Some text here"
        query = ""
        result = highlight_search_terms(text, query)
        
        # Should return escaped text without highlighting
        self.assertEqual(result, text)
    
    def test_highlight_search_terms_empty_text(self):
        """Test highlighting with empty text."""
        text = ""
        query = "test"
        result = highlight_search_terms(text, query)
        
        self.assertEqual(result, "")
    
    def test_highlight_search_terms_special_regex_chars(self):
        """Test highlighting with special regex characters in query."""
        text = "Testing [brackets] and (parentheses) plus + signs"
        query = "[brackets] +"
        result = highlight_search_terms(text, query)
        
        # Should properly escape regex special characters
        self.assertIn('<mark class="search-highlight">[brackets]</mark>', result)
        self.assertIn('<mark class="search-highlight">+</mark>', result)
    
    def test_highlight_in_suggestions_basic(self):
        """Test suggestion highlighting."""
        text = "JavaScript Programming"
        query = "Java"
        result = highlight_in_suggestions(text, query)
        
        expected = '<strong class="text-primary">Java</strong>Script Programming'
        self.assertEqual(result, expected)
    
    def test_truncate_and_highlight(self):
        """Test truncation with highlighting."""
        text = "JavaScript programming is a very long piece of text that should be truncated for testing purposes"
        args = "50,JavaScript"
        result = truncate_and_highlight(text, args)
        
        # Should be truncated and have highlighting
        self.assertLess(len(result.replace('<mark class="search-highlight">', '').replace('</mark>', '')), len(text))
        self.assertIn('<mark class="search-highlight">JavaScript</mark>', result)
        self.assertIn('...', result)
    
    def test_truncate_and_highlight_invalid_args(self):
        """Test truncate and highlight with invalid arguments."""
        text = "Some text"
        args = "invalid"
        result = truncate_and_highlight(text, args)
        
        # Should return escaped text without processing
        self.assertEqual(result, text)
    
    def test_search_result_snippet_basic(self):
        """Test search result snippet generation."""
        content = "This is a long article about JavaScript programming and web development practices"
        query = "JavaScript"
        result = search_result_snippet(content, query, 50)
        
        # Should center around the search term
        self.assertIn('<mark class="search-highlight">JavaScript</mark>', result)
        self.assertLessEqual(len(result.replace('<mark class="search-highlight">', '').replace('</mark>', '')), 60)  # Account for HTML tags
    
    def test_search_result_snippet_term_at_beginning(self):
        """Test snippet when search term is at the beginning."""
        content = "JavaScript is a programming language used for web development"
        query = "JavaScript"
        result = search_result_snippet(content, query, 30)
        
        # Should start from beginning, no leading ellipsis
        self.assertNotIn('...', result[:3])
        self.assertIn('<mark class="search-highlight">JavaScript</mark>', result)
    
    def test_search_result_snippet_term_at_end(self):
        """Test snippet when search term is at the end."""
        content = "Web development involves many technologies including JavaScript"
        query = "JavaScript"
        result = search_result_snippet(content, query, 30)
        
        # Should include the term even if at the end
        self.assertIn('<mark class="search-highlight">JavaScript</mark>', result)
    
    def test_search_result_snippet_no_query(self):
        """Test snippet with no query."""
        content = "This is some content without highlighting"
        query = ""
        result = search_result_snippet(content, query, 20)
        
        # Should return truncated content without highlighting
        self.assertLessEqual(len(result), 25)  # Account for ellipsis
        self.assertNotIn('<mark', result)
    
    def test_search_result_snippet_query_not_found(self):
        """Test snippet when query term is not in content."""
        content = "This content doesn't contain the search term"
        query = "Python"
        result = search_result_snippet(content, query, 20)
        
        # Should return truncated content from beginning
        self.assertTrue(result.startswith("This content"))
        self.assertNotIn('<mark', result)


class SearchHighlightingTemplateTests(TestCase):
    """Tests for search highlighting in templates."""
    
    def test_highlight_search_terms_in_template(self):
        """Test highlight_search_terms filter in template context."""
        template = Template(
            '{% load search_tags %}'
            '{{ text|highlight_search_terms:query }}'
        )
        context = Context({
            'text': 'JavaScript is awesome',
            'query': 'JavaScript'
        })
        result = template.render(context)
        
        expected = '<mark class="search-highlight">JavaScript</mark> is awesome'
        self.assertEqual(result, expected)
    
    def test_search_result_snippet_in_template(self):
        """Test search_result_snippet tag in template context."""
        template = Template(
            '{% load search_tags %}'
            '{% search_result_snippet content query 50 %}'
        )
        context = Context({
            'content': 'This is a long article about JavaScript programming and development',
            'query': 'JavaScript'
        })
        result = template.render(context)
        
        self.assertIn('<mark class="search-highlight">JavaScript</mark>', result)
    
    def test_truncate_and_highlight_in_template(self):
        """Test truncate_and_highlight filter in template context.""" 
        template = Template(
            '{% load search_tags %}'
            '{{ text|truncate_and_highlight:"30,Python" }}'
        )
        context = Context({
            'text': 'Python is a great programming language for beginners and experts alike'
        })
        result = template.render(context)
        
        self.assertIn('<mark class="search-highlight">Python</mark>', result)
        self.assertIn('...', result)
    
    def test_highlight_in_suggestions_in_template(self):
        """Test highlight_in_suggestions filter in template context."""
        template = Template(
            '{% load search_tags %}'
            '{{ text|highlight_in_suggestions:query }}'
        )
        context = Context({
            'text': 'JavaScript Framework',
            'query': 'Java'
        })
        result = template.render(context)
        
        expected = '<strong class="text-primary">Java</strong>Script Framework'
        self.assertEqual(result, expected)