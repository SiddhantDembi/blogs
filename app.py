from flask import Flask, render_template_string, abort, request
import os
import markdown
from functools import lru_cache
from datetime import datetime
import yaml
import logging

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
        .post-list, .subcategory-list { padding-left: 20px; }
        .post-item { margin: 5px 0; }
        .category { color: #666; font-size: 0.9em; }
        .breadcrumbs { padding: 10px 0; font-size: 0.9em; }
        .breadcrumbs a { color: #666; }
        .error { color: #cc0000; padding: 20px; }
        .subcategory-list { list-style-type: circle; margin: 10px 0; }
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
            {% if breadcrumbs %}
            <div class="breadcrumbs">
                {% for part in breadcrumbs %}
                    {% if not loop.last %}
                        <a href="{{ part.url }}">{{ part.name }}</a> /
                    {% else %}
                        <span>{{ part.name }}</span>
                    {% endif %}
                {% endfor %}
            </div>
            {% endif %}
            
            {% if error %}
                <div class="error">
                    <h2>{{ error.title }}</h2>
                    <p>{{ error.description }}</p>
                </div>
            {% else %}
                {{ content|safe }}
            {% endif %}
        </div>
        <footer>
            <p>Blogs by Siddhant Dembi</p>
        </footer>
    </body>
    </html>
    """

    @classmethod
    def render_page(cls, title, content, breadcrumbs=None, error=None):
        """Render a page with common layout"""
        return render_template_string(
            cls.BASE_TEMPLATE,
            title=title,
            styles=BlogConfig.STYLES,
            social_links=BlogConfig.SOCIAL_LINKS,
            content=content,
            breadcrumbs=breadcrumbs,
            error=error
        )

class BlogManager:
    """Handles blog post operations with metadata support"""
    def __init__(self, md_folder):
        self.md_folder = md_folder
        os.makedirs(self.md_folder, exist_ok=True)

    @lru_cache(maxsize=128)
    def get_post(self, filename):
        """Retrieve and convert a markdown post with metadata"""
        parts = filename.split('/')
        file_path = os.path.join(self.md_folder, *parts) + '.md'
        
        if not os.path.isfile(file_path):
            return None
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Parse front matter
                metadata = {}
                if content.startswith('---\n'):
                    parts = content.split('---\n', 2)
                    if len(parts) > 2:
                        metadata = yaml.safe_load(parts[1]) or {}
                        content = parts[2]
                
                # Default metadata
                metadata.setdefault('title', filename.split('/')[-1])
                metadata.setdefault('date', datetime.fromtimestamp(os.path.getctime(file_path)))
                
                return {
                    'html': markdown.markdown(content),
                    'metadata': metadata
                }
        except Exception as e:
            logging.error(f"Error loading post {filename}: {str(e)}")
            return None

    @lru_cache(maxsize=128)
    def list_posts(self):
        """List all available blog posts with metadata, sorted by date"""
        posts = []
        for root, dirs, files in os.walk(self.md_folder):
            for file in files:
                if file.endswith(".md"):
                    full_path = os.path.join(root, file)
                    if os.path.getsize(full_path) == 0:
                        continue  # Skip empty files
                    
                    relative_path = os.path.relpath(full_path, self.md_folder)
                    post_name = relative_path[:-3].replace("\\", "/")
                    
                    # Get creation date for sorting
                    stat = os.stat(full_path)
                    posts.append({
                        'path': post_name,
                        'date': datetime.fromtimestamp(stat.st_ctime)
                    })
        
        # Sort by date descending, then by path
        return sorted(posts, 
                     key=lambda x: (-x['date'].timestamp(), x['path'].lower()))

# Initialize application components
app = Flask(__name__)
config = BlogConfig()
blog_manager = BlogManager(config.MD_FOLDER)
app.logger.setLevel(logging.DEBUG if config.DEBUG else logging.ERROR)

@app.before_request
def before_request():
    """Clear cache in development mode"""
    if app.debug:
        blog_manager.get_post.cache_clear()
        blog_manager.list_posts.cache_clear()

def generate_breadcrumbs(path):
    """Generate breadcrumb navigation for a given path"""
    parts = path.split('/')
    breadcrumbs = []
    accumulated = []
    for i, part in enumerate(parts):
        accumulated.append(part)
        breadcrumbs.append({
            'name': part,
            'url': '/category/' + '/'.join(accumulated) if i < len(parts)-1 else f"/{'/'.join(accumulated)}"
        })
    return breadcrumbs

@app.route("/category/<path:category>")
def category_posts(category):
    """Show posts in a specific category"""
    try:
        all_posts = blog_manager.list_posts()
        filtered_posts = [p for p in all_posts if p['path'].startswith(f"{category}/")]
        
        subcategories = set()
        immediate_posts = []
        
        for post in filtered_posts:
            post_path = post['path']
            remaining_path = post_path[len(category)+1:]
            
            if '/' in remaining_path:
                subcategory = remaining_path.split('/')[0]
                subcategories.add(f"{category}/{subcategory}")
            else:
                immediate_posts.append(post)
        
        content = f"<h1>{category}</h1>"
        
        # Display subcategories
        if subcategories:
            content += "<h2>Subcategories</h2><ul class='subcategory-list'>"
            for sub in sorted(subcategories):
                sub_name = sub.split('/')[-1]
                content += f"<li><a href='/category/{sub}'>{sub_name.capitalize()}</a></li>"
            content += "</ul>"
        
        # Display immediate posts
        if immediate_posts:
            content += "<h2>Posts</h2><ul class='post-list'>"
            for post in immediate_posts:
                name = post['path'].split('/')[-1]
                content += f"""
                    <li class='post-item'>
                        <a href="/{post['path']}">{name}</a>
                        <div class='category'>{post['date'].strftime('%Y-%m-%d')}</div>
                    </li>
                """
            content += "</ul>"
        
        return TemplateRenderer.render_page(
            title=f"Category: {category}",
            content=content,
            breadcrumbs=generate_breadcrumbs(category)
        )
    except Exception as e:
        app.logger.error(f"Category error: {str(e)}")
        return TemplateRenderer.render_page(
            title="Error",
            content="",
            error={'title': 'Category Error', 'description': str(e)}
        )

@app.route("/<path:filename>")
def serve_post(filename):
    """Serve individual blog post"""
    try:
        post_data = blog_manager.get_post(filename)
        if not post_data:
            abort(404)
        
        metadata = post_data['metadata']
        breadcrumbs = generate_breadcrumbs(filename)
        
        content = f"""
            <h1>{metadata.get('title', filename)}</h1>
            <div class='post-meta'>
                <small>{metadata['date'].strftime('%B %d, %Y')}</small>
            </div>
            {post_data['html']}
        """
        
        return TemplateRenderer.render_page(
            title=metadata.get('title', filename),
            content=content,
            breadcrumbs=breadcrumbs
        )
    except Exception as e:
        app.logger.error(f"Post error: {str(e)}")
        return TemplateRenderer.render_page(
            title="Error",
            content="",
            error={'title': 'Post Error', 'description': str(e)}
        )

@app.route("/")
def home():
    """Render home page with categorized post list"""
    try:
        posts = blog_manager.list_posts()
        categories = {}
        
        # Organize posts by top-level category
        for post in posts:
            parts = post['path'].split('/')
            if len(parts) == 1:
                category = '_root'
            else:
                category = parts[0]
            
            if category not in categories:
                categories[category] = []
            categories[category].append(post)
        
        # Generate content
        content = "<h1>Blog Posts</h1>"
        for category_name, posts_in_category in sorted(categories.items()):
            if category_name != '_root':
                content += f"<h2><a href='/category/{category_name}'>{category_name.capitalize()}</a></h2>"
            else:
                content += "<h2>Uncategorized</h2>"
            
            content += "<ul class='post-list'>"
            for post in posts_in_category:
                if len(post['path'].split('/')) == 1 or category_name == '_root':
                    name = post['path'].split('/')[-1]
                    content += f"""
                        <li class='post-item'>
                            <a href="/{post['path']}">{name}</a>
                            <div class='category'>{post['date'].strftime('%Y-%m-%d')}</div>
                        </li>
                    """
            content += "</ul>"
        
        return TemplateRenderer.render_page(
            title="Blog Home",
            content=content
        )
    except Exception as e:
        app.logger.error(f"Home error: {str(e)}")
        return TemplateRenderer.render_page(
            title="Error",
            content="",
            error={'title': 'Home Error', 'description': str(e)}
        )

@app.errorhandler(404)
def page_not_found(e):
    return TemplateRenderer.render_page(
        title="Not Found",
        content="",
        error={'title': '404 Not Found', 'description': e.description}
    ), 404

@app.errorhandler(500)
def internal_error(e):
    return TemplateRenderer.render_page(
        title="Server Error",
        content="",
        error={'title': '500 Server Error', 'description': e.description}
    ), 500

if __name__ == "__main__":
    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT
    )