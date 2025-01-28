from flask import Flask, render_template_string, abort, request, url_for
import os
import markdown
from functools import lru_cache
import yaml
import logging
import re
from bs4 import BeautifulSoup
from datetime import datetime  # Added import

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
        body { 
            font-family: Arial, sans-serif; 
            line-height: 1.6; 
            margin: 0; 
            padding: 0; 
            background-color: #f4f4f9; 
            color: #333; 
            padding-bottom: 60px; 
        }
        h1, h2, h3 { 
            color: #0066cc; 
            margin-top: 0; 
        }
        a { 
            color: #0066cc; 
            text-decoration: none; 
        }
        a:hover { 
            text-decoration: underline; 
        }
        .container { 
            max-width: 800px; 
            margin: 20px auto; 
            background: #fff; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); 
        }
        .navbar { 
            background-color: #0066cc; 
            color: white; 
            padding: 10px 20px; 
            display: flex; 
            align-items: center; 
            justify-content: space-between; 
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); 
        }
        .navbar a { 
            color: white; 
            margin-right: 20px; 
            font-weight: bold; 
        }
        .social-icons a { 
            color: white; 
            margin-left: 10px; 
            font-size: 20px; 
        }
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
        .post-list, .subcategory-list { 
            padding-left: 20px; 
        }
        .post-item { 
            margin: 10px 0; 
            padding: 10px; 
            background: #f9f9f9; 
            border-radius: 4px; 
            border: 1px solid #ddd; 
        }
        .post-item:hover { 
            background: #f1f1f1; 
        }
        .category { 
            color: #666; 
            font-size: 0.9em; 
        }
        .breadcrumbs { 
            padding: 10px 0; 
            font-size: 0.9em; 
        }
        .breadcrumbs a { 
            color: #666; 
        }
        .error { 
            color: #cc0000; 
            padding: 20px; 
            background: #ffe6e6; 
            border-radius: 4px; 
            border: 1px solid #ffcccc; 
        }
        .subcategory-list { 
            list-style-type: circle; 
            margin: 10px 0; 
        }
        .post-meta { 
            color: #666; 
            font-size: 0.9em; 
            margin-top: -0.5em; 
            margin-bottom: 1em; 
        }
        .post-date {
            color: #666;
            font-size: 0.9em;
            margin-left: 20px;
        }
        .post-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
        }
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
<link rel="icon" href="https://www.freeiconspng.com/uploads/notepad-icon-2.png">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
<style>{{ styles }}</style>

    </head>
    <body>
        <div class="navbar">
            <a href="/">Home</a>
            <form action="/search" method="GET" style="flex-grow: 1; margin: 0 20px;">
                <input type="text" name="q" placeholder="Search posts..." 
                    value="{{ request.args.get('q', '') }}" style="width: 100%; padding: 8px;">
            </form>
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
                <a href="/">Home</a> /
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
                    <div class="error-actions">
                        <a href="/">Return Home</a>
                    </div>
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
            error=error,
            request=request
        )

class BlogManager:
    """Handles blog post operations with metadata support"""
    def __init__(self, md_folder):
        self.md_folder = md_folder
        os.makedirs(self.md_folder, exist_ok=True)

    @lru_cache(maxsize=128)
    def get_post(self, filename):
        """Retrieve and convert a markdown post with metadata"""
        if not is_safe_path(filename):
            return None

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
                        try:
                            metadata = yaml.safe_load(parts[1]) or {}
                        except yaml.YAMLError as e:
                            logging.error(f"YAML parsing error in {filename}: {str(e)}")
                            metadata = {}
                        content = parts[2]
                
                # Default metadata
                metadata.setdefault('title', filename.split('/')[-1])
                
                # Sanitize HTML content
                html_content = markdown.markdown(content)
                sanitized_html = sanitize_html(html_content)
                
                return {
                    'html': sanitized_html,
                    'metadata': metadata
                }
        except Exception as e:
            logging.error(f"Error loading post {filename}: {str(e)}")
            return None

    @lru_cache(maxsize=128)
    def list_posts(self):
        """List all available blog posts"""
        posts = []
        for root, dirs, files in os.walk(self.md_folder):
            for file in files:
                if file.endswith(".md"):
                    full_path = os.path.join(root, file)
                    if os.path.getsize(full_path) == 0:
                        continue  # Skip empty files
                    
                    relative_path = os.path.relpath(full_path, self.md_folder)
                    post_name = relative_path[:-3].replace("\\", "/")
                    posts.append({'path': post_name})
        
        # Sort alphabetically by path
        return sorted(posts, key=lambda x: x['path'].lower())

# Initialize application components
app = Flask(__name__)
config = BlogConfig()
blog_manager = BlogManager(config.MD_FOLDER)
app.logger.setLevel(logging.DEBUG if config.DEBUG else logging.ERROR)

def is_safe_path(path):
    """Check if the path is safe and does not contain directory traversal attempts"""
    return re.match(r'^[a-zA-Z0-9_\-/]+$', path) is not None

def sanitize_html(html):
    """Sanitize HTML content to prevent XSS attacks"""
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup.find_all():
        if tag.name in ['script', 'iframe', 'style']:
            tag.decompose()
    return str(soup)

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
            'name': ' '.join([p.capitalize() for p in part.split('-')]),
            'url': '/category/' + '/'.join(accumulated) if i < len(parts)-1 else f"/{'/'.join(accumulated)}"
        })
    return breadcrumbs

@app.route("/search")
def search_posts():
    """Handle post search functionality with case insensitivity and proper excerpt casing"""
    query = request.args.get("q", "").lower().strip()
    if not query or len(query) > 100:
        abort(400, description="Invalid search query")
    
    posts = blog_manager.list_posts()
    results = []
    
    for post in posts:
        post_data = blog_manager.get_post(post['path'])
        if not post_data:
            continue
            
        metadata = post_data['metadata']
        content_html = post_data['html']
        soup = BeautifulSoup(content_html, 'html.parser')
        content_original = soup.get_text()
        content_lower = content_original.lower()  # Lowercase version for search
        title = metadata.get('title', '').lower()
        date = metadata.get('date', '').lower()
        author = metadata.get('author', '').lower()  # Fixed typo: 'auther' -> 'author'
        path = post['path'].lower()
        
        if (query in title or 
            query in content_lower or  # Search in lowercase content
            query in path or 
            query in date or 
            query in author):
            
            # Use original content for proper casing in excerpt
            excerpt = content_original[:200] + '...' if len(content_original) > 200 else content_original
            results.append({
                'path': post['path'],
                'title': metadata.get('title', post['path'].split('/')[-1]),
                'excerpt': excerpt,
                'date': metadata.get('date', ''),
                'author': metadata.get('author', '')  # Fixed typo here
            })
    
    content = "<h1>Search Results</h1>"
    if results:
        content += f'<p>Found {len(results)} matches for "{query}"</p>'
        content += "<ul class='post-list'>"
        for result in results:
            content += f"""
                <li class='post-item'>
                    <a href="/{result['path']}">{result['title']}</a>
                    <p class='post-meta'>Posted on {result['date']} by {result['author']}</p>
                    <p>{result['excerpt']}</p>
                </li>
            """
        content += "</ul>"
    else:
        content += f'<div class="error"><p>No results found for "{query}"</p></div>'
    
    return TemplateRenderer.render_page(
        title=f"Search: {query}",
        content=content
    )

@app.route("/category/<path:category>")
def category_posts(category):
    """Show posts in a specific category"""
    try:
        if not is_safe_path(category):
            abort(404)
        
        all_posts = blog_manager.list_posts()
        filtered_posts = [p for p in all_posts if p['path'].startswith(f"{category}/")]
        
        subcategories = {}
        immediate_posts = []
        
        for post in filtered_posts:
            post_path = post['path']
            remaining_path = post_path[len(category)+1:]
            
            if '/' in remaining_path:
                subcategory = remaining_path.split('/')[0]
                subcat_path = f"{category}/{subcategory}"
                if subcat_path not in subcategories:
                    subcategories[subcat_path] = 1
                else:
                    subcategories[subcat_path] += 1
            else:
                immediate_posts.append(post)
        
        # Process posts with dates
        posts_with_dates = []
        for post in immediate_posts:
            post_data = blog_manager.get_post(post['path'])
            if not post_data: continue
            metadata = post_data['metadata']
            date_str = metadata.get('date', '')
            date_obj = None
            if date_str:
                try:
                    day, month, year = map(int, date_str.split('-'))
                    date_obj = datetime(year, month, day)
                except: pass
            posts_with_dates.append({
                'post': post,
                'title': metadata.get('title', post['path'].split('/')[-1]),
                'date_str': date_str,
                'date_obj': date_obj
            })
        
        # Sort by date descending
        posts_with_dates.sort(
            key=lambda x: (x['date_obj'] is None, x['date_obj'] or datetime.min),
            reverse=True
        )
        
        # Generate display name for category
        display_category = ' '.join([part.capitalize() for part in category.split('-')])
        content = f"<h1>{display_category}</h1>"
        
        if subcategories:
            content += "<h2>Subcategories</h2><ul class='subcategory-list'>"
            for sub, count in sorted(subcategories.items()):
                sub_parts = sub.split('/')
                sub_display = ' '.join([p.capitalize() for p in sub_parts[-1].split('-')])
                content += f"""
                    <li class='post-item'>
                        <a href='/category/{sub}'>{sub_display}</a>
                        <span class='category'>({count} post{'s' if count != 1 else ''})</span>
                    </li>
                """
            content += "</ul>"
        
        if posts_with_dates:
            content += "<h2>Posts</h2><ul class='post-list'>"
            for item in posts_with_dates:
                content += f"""
                    <li class='post-item'>
                        <div class="post-header">
                            <a href="/{item['post']['path']}">{item['title']}</a>
                            {f"<span class='post-date'>{item['date_str']}</span>" if item['date_str'] else ""}
                        </div>
                    </li>
                """
            content += "</ul>"
        
        return TemplateRenderer.render_page(
            title=f"Category: {display_category}",
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
        if not is_safe_path(filename):
            abort(404)
        
        post_data = blog_manager.get_post(filename)
        if not post_data:
            abort(404)
        
        metadata = post_data['metadata']
        breadcrumbs = generate_breadcrumbs(filename)
        
        content = f"<h1>{metadata.get('title', filename)}</h1>"
        
        # Add date and author
        date = metadata.get('date', '')
        author = metadata.get('auther', '')
        if date or author:
            content += f"<p class='post-meta'>"
            if date:
                content += f"Posted on {date}"
            if author:
                if date:
                    content += " by "
                else:
                    content += "By "
                content += author
            content += "</p>"
        
        content += post_data['html']
        
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
        content = "<h1>Home</h1><hr style='margin-top: -20px; margin-bottom: 20px; border: 2px solid #000;'>"  # Updated <hr> tag
        for category_name, posts_in_category in sorted(categories.items()):
            # Generate display name for category
            if category_name == '_root':
                display_name = "Uncategorized"
            else:
                display_name = ' '.join([part.capitalize() for part in category_name.split('-')])
            
            content += f"<h2><a href='/category/{category_name}'>{display_name}</a></h2>"
            
            # Sort posts by date (newest first)
            dated_posts = []
            for post in posts_in_category:
                post_data = blog_manager.get_post(post['path'])
                if not post_data: continue
                metadata = post_data['metadata']
                date_str = metadata.get('date', '')
                date_obj = None
                if date_str:
                    try:
                        day, month, year = map(int, date_str.split('-'))
                        date_obj = datetime(year, month, day)
                    except: pass
                dated_posts.append({
                    'post': post,
                    'title': metadata.get('title', post['path'].split('/')[-1]),
                    'date_str': date_str,
                    'date_obj': date_obj
                })
            
            # Sort by date descending
            dated_posts.sort(
                key=lambda x: (x['date_obj'] is None, x['date_obj'] or datetime.min),
                reverse=True
            )
            
            content += "<ul class='post-list'>"
            for item in dated_posts:
                content += f"""
                    <li class='post-item'>
                        <div class="post-header">
                            <a href="/{item['post']['path']}">{item['title']}</a>
                            {f"<span class='post-date'>{item['date_str']}</span>" if item['date_str'] else ""}
                        </div>
                    </li>
                """
            content += "</ul>"
        
        return TemplateRenderer.render_page(
            title="Blogs",
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