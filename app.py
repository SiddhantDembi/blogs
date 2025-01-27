from flask import Flask, render_template_string, abort
import os
import markdown
from functools import lru_cache

class BlogConfig:
    """Configuration settings for the blog"""
    MD_FOLDER = os.path.join(os.path.dirname(__file__), "md")
    HOST = "0.0.0.0"
    PORT = 5678
    DEBUG = True
    SOCIAL_LINKS = {
        "github": "https://github.com/siddhantdembi",
        "linkedin": "https://linkedin.com/in/siddhantdembi"
    }
    STYLES = """
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; 
               background-color: #f4f4f9; color: #333; padding-bottom: 40px; }
        h1, h2, h3 { color: #555; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .container { max-width: 800px; margin: 20px auto; background: #fff; 
                    padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); }
        .navbar { background-color: #0066cc; color: white; padding: 10px 20px; 
                 display: flex; align-items: center; justify-content: space-between; }
        .navbar a { color: white; margin-right: 20px; font-weight: bold; }
        .social-icons a { color: white; margin-left: 10px; font-size: 20px; }
        footer { 
            background-color: #0066cc; 
            color: white; 
            text-align: center; 
            padding: 10px 20px; 
            position: fixed; 
            left: 0; 
            bottom: 0; 
            width: 100%; 
            box-sizing: border-box; 
        }
        footer p { 
            margin: 0; 
            font-weight: bold; 
        }
        ul { list-style-type: none; padding: 0; }
        li { margin: 10px 0; }
    """

class TemplateRenderer:
    """Handles template rendering with proper HTML escaping"""
    BASE_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }}</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>{{ styles }}</style>
    </head>
    <body>
        <div class="navbar">
            <a href="/">Home</a>
            <div class="social-icons">
                <a href="{{ social_links.github }}" target="_blank" title="GitHub">
                    <i class="fab fa-github"></i>
                </a>
                <a href="{{ social_links.linkedin }}" target="_blank" title="LinkedIn">
                    <i class="fab fa-linkedin"></i>
                </a>
            </div>
        </div>
        <div class="container">
            {{ content|safe }}
        </div>
        <footer>
            <p>Blogs by Siddhant Dembi</p>
        </footer>
    </body>
    </html>
    """

    @classmethod
    def render_page(cls, title, content):
        """Render a page with common layout"""
        return render_template_string(
            cls.BASE_TEMPLATE,
            title=title,
            styles=BlogConfig.STYLES,
            social_links=BlogConfig.SOCIAL_LINKS,
            content=content
        )

class BlogManager:
    """Handles blog post operations"""
    def __init__(self, md_folder):
        self.md_folder = md_folder
        os.makedirs(self.md_folder, exist_ok=True)

    @lru_cache(maxsize=32)
    def get_post(self, filename):
        """Retrieve and convert a markdown post"""
        # Split filename into path components
        parts = filename.split('/')
        # Construct full file path with .md extension
        file_path = os.path.join(self.md_folder, *parts) + '.md'
        
        if not os.path.isfile(file_path):
            return None
        
        with open(file_path, "r", encoding="utf-8") as f:
            return markdown.markdown(f.read())

    def list_posts(self):
        """List all available blog posts with their relative paths"""
        posts = []
        for root, dirs, files in os.walk(self.md_folder):
            for file in files:
                if file.endswith(".md"):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, self.md_folder)
                    # Convert to URL-friendly path and remove .md extension
                    post_name = relative_path[:-3].replace("\\", "/")
                    posts.append(post_name)
        return posts

# Initialize application components
app = Flask(__name__)
config = BlogConfig()
blog_manager = BlogManager(config.MD_FOLDER)

@app.route("/<path:filename>")
def serve_post(filename):
    """Serve individual blog post"""
    content = blog_manager.get_post(filename)
    if not content:
        abort(404)
    
    return TemplateRenderer.render_page(
        title=filename,
        content=content
    )

@app.route("/")
def home():
    """Render home page with post list"""
    posts = blog_manager.list_posts()
    posts_list = "".join(
        f'<li><a href="/{post}">{post}</a></li>' 
        for post in posts
    )
    content = f"<h1>Blog Posts</h1><ul>{posts_list}</ul>"
    
    return TemplateRenderer.render_page(
        title="Blog Home",
        content=content
    )

if __name__ == "__main__":
    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT
    )