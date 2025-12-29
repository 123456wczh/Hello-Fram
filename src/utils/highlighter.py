import pygments
from pygments import lexers, formatters
from pygments.styles import get_style_by_name

class SyntaxHighlighter:
    def __init__(self, style_name='monokai'):
        self.lexer = lexers.get_lexer_by_name("python")
        self.formatter = formatters.get_formatter_by_name("html", noclasses=True, style=style_name)

    def highlight(self, code, cursor_pos=None):
        """
        Convert python code to HTML with inline styles.
        pygame_gui supports a subset of HTML.
        """
        try:
            # Pygments generates a full <div>, we might need to strip it or just use the inner parts.
            # noclasses=True ensures inline styles which pygame_gui needs.
            html_content = pygments.highlight(code, self.lexer, self.formatter)
            
            # Formatting for pygame_gui:
            # Pygments wraps in <div class="highlight"><pre> ... </pre></div>
            # We likely just want the content inside <pre>
            
            start_tag = "<pre"
            end_tag = "</pre>"
            s_idx = html_content.find(start_tag)
            if s_idx != -1:
                s_idx = html_content.find(">", s_idx) + 1
                e_idx = html_content.rfind(end_tag)
                html_content = html_content[s_idx:e_idx]
            
            # Replace logic for cursor could go here, but doing it in raw text is easier 
            # before highlighting? No, syntax highlighting might break if we insert a char.
            # We will handle cursor rendering simply by appending it or using a separate overlay if possible.
            # For "Plan C", let's try appending a cursor character if it's at the end.
            
            html_content = html_content.replace("\n", "<br>")
            
            # Fix colors: pygame_gui might not support all span styles, but let's try.
            # It mainly supports <font color='#...'>
            # Pygments produces <span style="color: #...">
            # We need to replace span style with font color.
            
            # Simple parser to convert span style="color: #HEX" to font color="#HEX"
            # This is a bit hacky but strict regex should work for pygments output.
            # Parsing Strategy V2 (Robust)
            # 1. Replace <span style="color: #XYZ">Text</span> with <font color="#XYZ">Text</font>
            # 2. Strip any other spans
            
            import re
            
            # Match span with color style
            # Note: pygments uses double quotes for attributes usually
            # Captures: 1=ColorHex, 2=Content
            def color_replacer(match):
                color = match.group(1)
                content = match.group(2)
                return f"<font color='{color}'>{content}</font>"

            # Pattern finding: style="color: #..."
            html_content = re.sub(r'<span style="color:\s*([^"]+);?">([^<]*)</span>', color_replacer, html_content)
            
            # Clean up any remaining spans (those without color or nested in ways we didn't catch)
            # This loops until no spans are left to ensure nested spans are stripped
            while "<span" in html_content:
                html_content = re.sub(r'<span[^>]*>', '', html_content)
                html_content = html_content.replace('</span>', '')
            
            # Better approach: Custom Formatter? 
            # Or just string replacements for common tokens if regex is too risky.
            # Actually, let's try a regex loop.
            
            # Legacy regex removed
            
            # Font size standard
            html_content = f"<font face='Consolas' size='4' color='#F8F8F2'>{html_content}</font>"
            
            return html_content
            
        except Exception as e:
            print(f"Highlight Error: {e}")
            # Fallback to white text so it's visible on dark background
            return f"<font face='Consolas' size='4' color='#FFFFFF'>{code}</font>"
