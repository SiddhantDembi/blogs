from flask import Flask, render_template_string, abort, request, Response
import os
import markdown
from functools import lru_cache
import yaml
import logging
import re
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as dateutil_parser
import xml.etree.ElementTree as ET


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
        /* ── Theme tokens ─────────────────────────────────────────── */
        :root {
            --bg:           #f0f2f5;
            --surface:      #ffffff;
            --surface2:     #f8f9fa;
            --text:         #1a1a2e;
            --text-muted:   #6c757d;
            --accent:       #0066cc;
            --accent-hover: #0052a3;
            --accent-light: #e8f0fe;
            --border:       #dee2e6;
            --nav-bg:       #0052a3;
            --nav-text:     #ffffff;
            --shadow:       0 2px 8px rgba(0,0,0,.10);
            --shadow-hover: 0 4px 16px rgba(0,0,0,.16);
            --radius:       10px;
            --code-bg:      #f6f8fa;
            --code-border:  #e1e4e8;
        }
        /* ── Base ──────────────────────────────────────────────────── */
        *, *::before, *::after { box-sizing: border-box; }
        html { scroll-behavior: smooth; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                         "Helvetica Neue", Arial, sans-serif;
            line-height: 1.7;
            margin: 0;
            padding: 0;
            background: var(--bg);
            color: var(--text);
            padding-bottom: 64px;
        }
        h1, h2, h3, h4 { color: var(--accent); margin-top: 1.4em; line-height: 1.3; }
        h1 { margin-top: 0; font-size: 1.8em; }
        h2 { font-size: 1.35em; }
        h3 { font-size: 1.1em; }
        a  { color: var(--accent); text-decoration: none; transition: color .15s; }
        a:hover { color: var(--accent-hover); text-decoration: underline; }
        p  { margin: .8em 0; }
        hr { border: none; border-top: 2px solid var(--border); margin: 1.4em 0; }

        /* ── Layout ────────────────────────────────────────────────── */
        .container {
            max-width: 860px;
            margin: 28px auto;
            background: var(--surface);
            padding: 28px 32px;
            border-radius: var(--radius);
            box-shadow: var(--shadow);
        }

        /* ── Navbar ────────────────────────────────────────────────── */
        .navbar {
            background: var(--nav-bg);
            color: var(--nav-text);
            padding: 0 20px;
            display: flex;
            align-items: center;
            gap: 16px;
            box-shadow: 0 2px 6px rgba(0,0,0,.25);
            position: sticky;
            top: 0;
            z-index: 100;
            min-height: 52px;
            flex-wrap: wrap;
        }
        .navbar-links { display: flex; align-items: center; gap: 4px; }
        .navbar-links a {
            color: var(--nav-text);
            font-weight: 600;
            font-size: .9em;
            padding: 6px 12px;
            border-radius: 6px;
            opacity: .9;
            transition: background .15s, opacity .15s;
        }
        .navbar-links a:hover { background: rgba(255,255,255,.15); opacity: 1; text-decoration: none; }
        .navbar-search {
            flex: 1;
            min-width: 140px;
            display: flex;
            align-items: center;
            background: rgba(255,255,255,.15);
            border-radius: 20px;
            padding: 0 12px;
            transition: background .2s;
        }
        .navbar-search:focus-within { background: rgba(255,255,255,.25); }
        .navbar-search i { color: rgba(255,255,255,.7); font-size: .85em; margin-right: 6px; }
        .navbar-search input {
            background: transparent;
            border: none;
            outline: none;
            color: white;
            font-size: .9em;
            padding: 7px 0;
            width: 100%;
        }
        .navbar-search input::placeholder { color: rgba(255,255,255,.6); }
        .navbar-right { display: flex; align-items: center; gap: 4px; margin-left: auto; }
        .social-icons { display: flex; gap: 2px; }
        .social-icons a {
            color: var(--nav-text);
            opacity: .85;
            font-size: 18px;
            padding: 6px 8px;
            border-radius: 6px;
            transition: background .15s, opacity .15s;
        }
        .social-icons a:hover { background: rgba(255,255,255,.15); opacity: 1; text-decoration: none; }

        /* ── Footer ────────────────────────────────────────────────── */
        footer {
            background: var(--nav-bg);
            color: rgba(255,255,255,.85);
            text-align: center;
            padding: 12px 20px;
            position: fixed;
            left: 0; bottom: 0; width: 100%;
            font-size: .85em;
            letter-spacing: .3px;
        }
        footer p { margin: 0; font-weight: 600; }

        /* ── Breadcrumbs ───────────────────────────────────────────── */
        .breadcrumbs {
            padding: 8px 0 16px;
            font-size: .85em;
            color: var(--text-muted);
            display: flex; flex-wrap: wrap; align-items: center; gap: 4px;
        }
        .breadcrumbs a { color: var(--text-muted); }
        .breadcrumbs a:hover { color: var(--accent); }
        .breadcrumbs .sep { color: var(--border); }

        /* ── Post list cards ───────────────────────────────────────── */
        .post-list { list-style: none; padding: 0; margin: 0; }
        .post-item {
            margin: 10px 0;
            padding: 14px 16px;
            background: var(--surface2);
            border-radius: 8px;
            border: 1px solid var(--border);
            transition: box-shadow .2s, transform .15s, background .2s;
        }
        .post-item:hover {
            box-shadow: var(--shadow-hover);
            transform: translateY(-2px);
        }
        .post-title {
            font-weight: 700;
            font-size: 1.05em;
            color: var(--accent);
        }
        .post-title:hover { text-decoration: underline; }
        .post-item-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin: 4px 0 6px;
            font-size: .82em;
            color: var(--text-muted);
        }
        .post-item-meta i { margin-right: 4px; }
        .post-excerpt {
            font-size: .9em;
            color: var(--text-muted);
            margin: 6px 0 4px;
            line-height: 1.5;
        }

        /* ── Single post meta ──────────────────────────────────────── */
        .post-meta {
            color: var(--text-muted);
            font-size: .88em;
            margin-top: -.3em;
            margin-bottom: 1em;
            display: flex; flex-wrap: wrap; gap: 12px; align-items: center;
        }
        .post-meta i { margin-right: 3px; }

        /* ── Category / subcategory section ────────────────────────── */
        .category-section { margin-bottom: 28px; }
        .category-header {
            display: flex; align-items: center; gap: 10px;
            padding-bottom: 8px;
            border-bottom: 2px solid var(--border);
            margin-bottom: 12px;
        }
        .category-header h2 { margin: 0; font-size: 1.15em; }
        .subcategory-list { list-style: none; padding: 0; }
        .category-badge {
            font-size: .78em;
            color: var(--text-muted);
            background: var(--surface2);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1px 8px;
        }

        /* ── Tags ──────────────────────────────────────────────────── */
        .tag {
            display: inline-block;
            background: var(--accent-light);
            color: var(--accent);
            border: 1px solid #c5d7f5;
            border-radius: 20px;
            padding: 1px 10px;
            font-size: .78em;
            margin: 2px;
            font-weight: 500;
            transition: background .15s, color .15s;
        }
        .tag:hover { background: var(--accent); color: #fff; text-decoration: none; }
        .tag-list { margin: 4px 0 2px; }
        .tag-grid { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 18px; }
        .tag-grid-item {
            background: var(--accent-light);
            border: 1px solid #c5d7f5;
            border-radius: 20px;
            padding: 5px 16px;
            font-size: .9em;
            transition: background .15s;
        }
        .tag-grid-item a { color: var(--accent); font-weight: 500; }
        .tag-grid-item:hover { background: var(--accent); }
        .tag-grid-item:hover a { color: #fff; text-decoration: none; }
        .tag-count { color: var(--text-muted); font-size: .82em; margin-left: 4px; }

        /* ── Table of contents ─────────────────────────────────────── */
        .toc {
            background: var(--surface2);
            border-left: 4px solid var(--accent);
            border-radius: 0 8px 8px 0;
            padding: 14px 20px;
            margin-bottom: 28px;
            font-size: .88em;
        }
        .toc strong { display: block; margin-bottom: 8px; color: var(--text); font-size: .95em; }
        .toc ul { margin: 0; padding-left: 18px; }
        .toc li { margin: 4px 0; }
        .toc a { color: var(--accent); }

        /* ── Related posts ─────────────────────────────────────────── */
        .related-posts { margin-top: 36px; padding-top: 20px; border-top: 2px solid var(--border); }
        .related-posts h3 { color: var(--text); font-size: 1.05em; margin: 0 0 12px; }

        /* ── Errors ────────────────────────────────────────────────── */
        .error {
            color: #c0392b;
            padding: 20px;
            background: #fdecea;
            border-radius: 8px;
            border: 1px solid #f5c6cb;
        }

        /* ── Code blocks ───────────────────────────────────────────── */
        pre {
            background: var(--code-bg);
            border: 1px solid var(--code-border);
            border-radius: 8px;
            padding: 16px;
            overflow-x: auto;
            font-size: .88em;
            line-height: 1.6;
        }
        code {
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: .9em;
        }
        :not(pre) > code {
            background: var(--code-bg);
            border: 1px solid var(--code-border);
            border-radius: 4px;
            padding: 1px 5px;
        }
        pre code { background: none; border: none; padding: 0; font-size: 1em; }

        /* ── Tables ────────────────────────────────────────────────── */
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
            font-size: .92em;
        }
        th, td { border: 1px solid var(--border); padding: 8px 12px; text-align: left; }
        th { background: var(--surface2); font-weight: 600; color: var(--text); }
        tr:nth-child(even) { background: var(--surface2); }

        /* ── Blockquotes ───────────────────────────────────────────── */
        blockquote {
            border-left: 4px solid var(--accent);
            margin: 1em 0;
            padding: 8px 16px;
            color: var(--text-muted);
            background: var(--surface2);
            border-radius: 0 6px 6px 0;
        }

        /* ── Responsive ────────────────────────────────────────────── */
        @media (max-width: 640px) {
            .navbar { gap: 10px; padding: 8px 12px; }
            .navbar-search { min-width: 0; }
            .container { margin: 12px 10px; padding: 16px; }
            h1 { font-size: 1.4em; }
            .post-item-meta { gap: 8px; }
        }
        @media (max-width: 420px) {
            .navbar-links a { padding: 5px 8px; font-size: .82em; }
            .social-icons a { font-size: 15px; padding: 5px 6px; }
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
        <link rel="alternate" type="application/rss+xml" title="Blog RSS Feed" href="/feed.xml">
        <!-- Syntax highlighting -->
        <link rel="stylesheet"
              href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
        <style>{{ styles }}</style>
    </head>
    <body>
        <nav class="navbar">
            <div class="navbar-links">
                <a href="/"><i class="fas fa-home"></i> Home</a>
                <a href="/tags"><i class="fas fa-tags"></i> Tags</a>
            </div>

            <form class="navbar-search" action="/search" method="GET">
                <i class="fas fa-search"></i>
                <input type="text" name="q" placeholder="Search posts…"
                       value="{{ request.args.get('q', '') }}" autocomplete="off">
            </form>

            <div class="navbar-right">
                <div class="social-icons">
                    <a href="{{ social_links.github }}" target="_blank" title="GitHub">
                        <i class="fab fa-github"></i>
                    </a>
                    <a href="{{ social_links.linkedin }}" target="_blank" title="LinkedIn">
                        <i class="fab fa-linkedin"></i>
                    </a>
                    <a href="/feed.xml" target="_blank" title="RSS Feed">
                        <i class="fas fa-rss"></i>
                    </a>
                </div>
            </div>
        </nav>

        <div class="container">
            {% if breadcrumbs %}
            <nav class="breadcrumbs" aria-label="Breadcrumb">
                <a href="/"><i class="fas fa-home"></i> Home</a>
                {% for part in breadcrumbs %}
                    <span class="sep">/</span>
                    {% if not loop.last %}
                        <a href="{{ part.url }}">{{ part.name }}</a>
                    {% else %}
                        <span>{{ part.name }}</span>
                    {% endif %}
                {% endfor %}
            </nav>
            {% endif %}

            {% if error %}
                <div class="error">
                    <h2>{{ error.title }}</h2>
                    <p>{{ error.description }}</p>
                    <a href="/">← Return Home</a>
                </div>
            {% else %}
                {{ content|safe }}
            {% endif %}
        </div>

        <footer>
            <p>Blogs by Siddhant Dembi</p>
        </footer>

        <!-- Syntax highlighting -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', function () {
                document.querySelectorAll('pre code').forEach(function (el) {
                    hljs.highlightElement(el);
                });
            });
        </script>
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
                    sections = content.split('---\n', 2)
                    if len(sections) > 2:
                        try:
                            metadata = yaml.safe_load(sections[1]) or {}
                        except yaml.YAMLError as e:
                            logging.error(f"YAML parsing error in {filename}: {str(e)}")
                            metadata = {}
                        content = sections[2]

                # Default metadata
                metadata.setdefault('title', filename.split('/')[-1])

                # Normalise tags to a list of strings
                raw_tags = metadata.get('tags', [])
                if isinstance(raw_tags, str):
                    raw_tags = [t.strip() for t in raw_tags.split(',') if t.strip()]
                metadata['tags'] = [str(t).strip() for t in raw_tags if str(t).strip()]

                # Convert markdown with TOC extension
                md_instance = markdown.Markdown(extensions=['extra', 'toc'])
                html_content = md_instance.convert(content)
                toc_raw = md_instance.toc  # '<div class="toc">...</div>' or empty

                # Build styled TOC block only when there are real entries
                if toc_raw and '<li>' in toc_raw:
                    inner = toc_raw.replace('<div class="toc">', '').replace('</div>', '').strip()
                    toc_html = f'<div class="toc"><strong>Contents</strong>{inner}</div>'
                else:
                    toc_html = ''

                # Reading time (≈200 wpm)
                word_count = len(BeautifulSoup(html_content, 'html.parser').get_text().split())
                reading_time = max(1, round(word_count / 200))

                sanitized_html = sanitize_html(html_content)

                return {
                    'html': sanitized_html,
                    'toc': toc_html,
                    'metadata': metadata,
                    'reading_time': reading_time,
                    'word_count': word_count,
                }
        except Exception as e:
            logging.error(f"Error loading post {filename}: {str(e)}")
            return None

    @lru_cache(maxsize=1)
    def get_tag_index(self):
        """Build a mapping of tag → list of post dicts"""
        tags = {}
        for post in self.list_posts():
            post_data = self.get_post(post['path'])
            if not post_data:
                continue
            for tag in post_data['metadata'].get('tags', []):
                key = tag.lower()
                if key not in tags:
                    tags[key] = []
                tags[key].append({'path': post['path'], 'title': post_data['metadata'].get('title', post['path'].split('/')[-1])})
        return tags

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

        return sorted(posts, key=lambda x: x['path'].lower())


# ---------------------------------------------------------------------------
# Application bootstrap
# ---------------------------------------------------------------------------

app = Flask(__name__)
config = BlogConfig()
blog_manager = BlogManager(config.MD_FOLDER)
app.logger.setLevel(logging.DEBUG if config.DEBUG else logging.ERROR)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def is_safe_path(path):
    """Reject paths with directory-traversal characters"""
    return re.match(r'^[a-zA-Z0-9_\-/]+$', path) is not None


def sanitize_html(html):
    """Remove dangerous tags to prevent XSS"""
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup.find_all():
        if tag.name in ['script', 'iframe', 'style']:
            tag.decompose()
    return str(soup)


def parse_date(date_val):
    """Return (datetime | None, display_str) for any date value from YAML metadata.

    Supports:
    - datetime.date / datetime objects produced by PyYAML
    - DD-MM-YYYY strings (existing format)
    - ISO 8601, human-readable strings, etc. via python-dateutil
    """
    if not date_val:
        return None, ''
    # PyYAML may yield a date/datetime object for ISO-format values
    if hasattr(date_val, 'strftime'):
        return datetime(date_val.year, date_val.month, date_val.day), date_val.strftime('%d-%m-%Y')
    date_str = str(date_val).strip()
    if not date_str:
        return None, ''
    try:
        dt = dateutil_parser.parse(date_str, dayfirst=True)
        return dt, date_str
    except Exception as e:
        logging.warning(f"Could not parse date '{date_str}': {e}")
        return None, date_str


def make_excerpt(text, max_chars=200):
    """Return a word-boundary-respecting excerpt"""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')
    return (truncated[:last_space] if last_space > 0 else truncated) + '...'


def render_tags(tags):
    """Return HTML badge links for a list of tag strings"""
    if not tags:
        return ''
    badges = ''.join(
        f'<a href="/tags/{t.lower().replace(" ", "-")}" class="tag">{t}</a>'
        for t in tags
    )
    return f'<div class="tag-list">{badges}</div>'


def get_related_posts(current_path, current_tags, limit=5):
    """Return up to `limit` related posts ranked by shared tags then same category"""
    current_category = current_path.split('/')[0] if '/' in current_path else None
    current_tags_set = {t.lower() for t in (current_tags or [])}

    scored = []
    for post in blog_manager.list_posts():
        if post['path'] == current_path:
            continue
        post_data = blog_manager.get_post(post['path'])
        if not post_data:
            continue
        metadata = post_data['metadata']
        post_tags = {t.lower() for t in metadata.get('tags', [])}
        score = len(current_tags_set & post_tags)
        post_category = post['path'].split('/')[0] if '/' in post['path'] else None
        if post_category and post_category == current_category:
            score += 0.5
        if score > 0:
            scored.append((score, post, metadata))

    scored.sort(key=lambda x: -x[0])
    return [(p, m) for _, p, m in scored[:limit]]


def generate_breadcrumbs(path):
    """Generate breadcrumb navigation for a given path"""
    parts = path.split('/')
    breadcrumbs = []
    accumulated = []
    for i, part in enumerate(parts):
        accumulated.append(part)
        breadcrumbs.append({
            'name': ' '.join(p.capitalize() for p in part.split('-')),
            'url': '/category/' + '/'.join(accumulated) if i < len(parts) - 1 else f"/{'/'.join(accumulated)}"
        })
    return breadcrumbs


def _build_dated_post_list(posts):
    """Enrich a list of post dicts with metadata, dates, reading time and excerpt; sort newest-first"""
    enriched = []
    for post in posts:
        post_data = blog_manager.get_post(post['path'])
        if not post_data:
            continue
        metadata = post_data['metadata']
        date_obj, date_str = parse_date(metadata.get('date', ''))
        plain = BeautifulSoup(post_data['html'], 'html.parser').get_text()
        enriched.append({
            'post': post,
            'title': metadata.get('title', post['path'].split('/')[-1]),
            'date_str': date_str,
            'date_obj': date_obj,
            'reading_time': post_data.get('reading_time', 1),
            'tags': metadata.get('tags', []),
            'excerpt': make_excerpt(plain, 160),
        })
    enriched.sort(key=lambda x: (x['date_obj'] is None, x['date_obj'] or datetime.min), reverse=True)
    return enriched


def _render_post_item(item):
    """Return the HTML for a single post list card"""
    tag_html = render_tags(item['tags'])
    date_part = (f"<span><i class='far fa-calendar-alt'></i> {item['date_str']}</span>"
                 if item['date_str'] else "")
    rt = f"<span><i class='far fa-clock'></i> {item['reading_time']} min read</span>"
    excerpt = (f"<p class='post-excerpt'>{item['excerpt']}</p>"
               if item.get('excerpt') else "")
    return f"""
        <li class='post-item'>
            <a class='post-title' href="/{item['post']['path']}">{item['title']}</a>
            <div class='post-item-meta'>{date_part}{rt}</div>
            {excerpt}
            {tag_html}
        </li>
    """


# ---------------------------------------------------------------------------
# Request hook
# ---------------------------------------------------------------------------

@app.before_request
def before_request():
    """Clear all caches in development mode so edits are reflected immediately"""
    if app.debug:
        blog_manager.get_post.cache_clear()
        blog_manager.list_posts.cache_clear()
        blog_manager.get_tag_index.cache_clear()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    """Render home page with categorised post list"""
    try:
        posts = blog_manager.list_posts()
        categories = {}

        for post in posts:
            parts = post['path'].split('/')
            category = '_root' if len(parts) == 1 else parts[0]
            categories.setdefault(category, []).append(post)

        content = "<h1>Home</h1><hr>"
        for category_name, cat_posts in sorted(categories.items()):
            display_name = "Uncategorized" if category_name == '_root' else \
                ' '.join(p.capitalize() for p in category_name.split('-'))
            cat_url = f"/category/{category_name}"
            count = len(cat_posts)
            content += f"""
                <div class='category-section'>
                    <div class='category-header'>
                        <h2><a href='{cat_url}'><i class='fas fa-folder-open'></i> {display_name}</a></h2>
                        <span class='category-badge'>{count} post{'s' if count != 1 else ''}</span>
                    </div>
                    <ul class='post-list'>
            """
            for item in _build_dated_post_list(cat_posts):
                content += _render_post_item(item)
            content += "</ul></div>"

        return TemplateRenderer.render_page(title="Blogs", content=content)
    except Exception as e:
        app.logger.error(f"Home error: {str(e)}")
        return TemplateRenderer.render_page(
            title="Error", content="",
            error={'title': 'Home Error', 'description': str(e)}
        )


@app.route("/search")
def search_posts():
    """Full-text search across titles, content, dates, authors and tags"""
    query = request.args.get("q", "").lower().strip()
    if not query or len(query) > 100:
        abort(400, description="Invalid search query")

    results = []
    for post in blog_manager.list_posts():
        post_data = blog_manager.get_post(post['path'])
        if not post_data:
            continue

        metadata = post_data['metadata']
        soup = BeautifulSoup(post_data['html'], 'html.parser')
        content_text = soup.get_text()
        tags_text = ' '.join(metadata.get('tags', [])).lower()
        _, date_str = parse_date(metadata.get('date', ''))

        haystack = ' '.join([
            metadata.get('title', '').lower(),
            content_text.lower(),
            post['path'].lower(),
            str(date_str).lower(),
            metadata.get('author', '').lower(),
            tags_text,
        ])

        if query in haystack:
            results.append({
                'path': post['path'],
                'title': metadata.get('title', post['path'].split('/')[-1]),
                'excerpt': make_excerpt(content_text),
                'date': date_str,
                'author': metadata.get('author', ''),
                'tags': metadata.get('tags', []),
                'reading_time': post_data.get('reading_time', 1),
            })

    content = "<h1>Search Results</h1>"
    if results:
        content += f'<p>Found {len(results)} match{"es" if len(results) != 1 else ""} for "<strong>{query}</strong>"</p>'
        content += "<ul class='post-list'>"
        for r in results:
            tag_html = render_tags(r['tags'])
            content += f"""
                <li class='post-item'>
                    <a href="/{r['path']}">{r['title']}</a>
                    <span class='reading-time'>· {r['reading_time']} min read</span>
                    <p class='post-meta'>Posted on {r['date']} by {r['author']}</p>
                    {tag_html}
                    <p>{r['excerpt']}</p>
                </li>
            """
        content += "</ul>"
    else:
        content += f'<div class="error"><p>No results found for "<strong>{query}</strong>"</p></div>'

    return TemplateRenderer.render_page(title=f"Search: {query}", content=content)


@app.route("/tags")
def tag_index():
    """Show all tags with post counts"""
    tag_map = blog_manager.get_tag_index()
    if not tag_map:
        content = "<h1>Tags</h1><p>No tags found. Add a <code>tags:</code> field to your post front matter.</p>"
        return TemplateRenderer.render_page(title="Tags", content=content)

    content = "<h1>Tags</h1><div class='tag-grid'>"
    for tag in sorted(tag_map):
        count = len(tag_map[tag])
        slug = tag.replace(' ', '-')
        content += f"""
            <div class='tag-grid-item'>
                <a href="/tags/{slug}">{tag}</a>
                <span class='tag-count'>({count})</span>
            </div>
        """
    content += "</div>"
    return TemplateRenderer.render_page(title="Tags", content=content)


@app.route("/tags/<path:tag>")
def tag_posts(tag):
    """List all posts for a given tag"""
    tag_key = tag.lower().replace('-', ' ')
    tag_map = blog_manager.get_tag_index()
    posts_for_tag = tag_map.get(tag_key, [])

    if not posts_for_tag:
        abort(404)

    enriched = _build_dated_post_list([{'path': p['path']} for p in posts_for_tag])
    content = f"<h1>Tag: {tag_key}</h1>"
    content += "<ul class='post-list'>"
    for item in enriched:
        content += _render_post_item(item)
    content += "</ul>"

    breadcrumbs = [
        {'name': 'Tags', 'url': '/tags'},
        {'name': tag_key, 'url': f'/tags/{tag}'},
    ]
    return TemplateRenderer.render_page(title=f"Tag: {tag_key}", content=content, breadcrumbs=breadcrumbs)


@app.route("/feed.xml")
def rss_feed():
    """Serve an RSS 2.0 feed of the latest 20 posts"""
    posts = blog_manager.list_posts()
    items = []
    for post in posts:
        post_data = blog_manager.get_post(post['path'])
        if not post_data:
            continue
        metadata = post_data['metadata']
        date_obj, _ = parse_date(metadata.get('date', ''))
        plain = BeautifulSoup(post_data['html'], 'html.parser').get_text()
        items.append({
            'path': post['path'],
            'title': metadata.get('title', post['path'].split('/')[-1]),
            'date': date_obj,
            'description': make_excerpt(plain, 500),
        })

    items.sort(key=lambda x: (x['date'] is None, x['date'] or datetime.min), reverse=True)
    items = items[:20]

    base_url = request.url_root.rstrip('/')
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = 'Blogs by Siddhant Dembi'
    ET.SubElement(channel, 'link').text = base_url
    ET.SubElement(channel, 'description').text = 'Latest blog posts'

    for item in items:
        entry = ET.SubElement(channel, 'item')
        ET.SubElement(entry, 'title').text = item['title']
        ET.SubElement(entry, 'link').text = f"{base_url}/{item['path']}"
        ET.SubElement(entry, 'description').text = item['description']
        if item['date']:
            ET.SubElement(entry, 'pubDate').text = item['date'].strftime('%a, %d %b %Y %H:%M:%S +0000')

    xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(rss, encoding='unicode')
    return Response(xml_str, mimetype='application/rss+xml')


@app.route("/category/<path:category>")
def category_posts(category):
    """Show posts and subcategories for a category"""
    try:
        if not is_safe_path(category):
            abort(404)

        all_posts = blog_manager.list_posts()
        filtered = [p for p in all_posts if p['path'].startswith(f"{category}/")]

        subcategories = {}
        immediate_posts = []

        for post in filtered:
            remaining = post['path'][len(category) + 1:]
            if '/' in remaining:
                subcat = remaining.split('/')[0]
                subcat_path = f"{category}/{subcat}"
                subcategories[subcat_path] = subcategories.get(subcat_path, 0) + 1
            else:
                immediate_posts.append(post)

        display_category = ' '.join(p.capitalize() for p in category.split('-'))
        content = f"<h1>{display_category}</h1>"

        if subcategories:
            content += "<h2>Subcategories</h2><ul class='subcategory-list'>"
            for sub, count in sorted(subcategories.items()):
                sub_display = ' '.join(p.capitalize() for p in sub.split('/')[-1].split('-'))
                content += f"""
                    <li class='post-item'>
                        <a href='/category/{sub}'>{sub_display}</a>
                        <span class='category'>({count} post{'s' if count != 1 else ''})</span>
                    </li>
                """
            content += "</ul>"

        if immediate_posts:
            content += "<h2>Posts</h2><ul class='post-list'>"
            for item in _build_dated_post_list(immediate_posts):
                content += _render_post_item(item)
            content += "</ul>"

        return TemplateRenderer.render_page(
            title=f"Category: {display_category}",
            content=content,
            breadcrumbs=generate_breadcrumbs(category)
        )
    except Exception as e:
        app.logger.error(f"Category error: {str(e)}")
        return TemplateRenderer.render_page(
            title="Error", content="",
            error={'title': 'Category Error', 'description': str(e)}
        )


@app.route("/<path:filename>")
def serve_post(filename):
    """Serve an individual blog post"""
    try:
        if not is_safe_path(filename):
            abort(404)

        post_data = blog_manager.get_post(filename)
        if not post_data:
            abort(404)

        metadata = post_data['metadata']
        date_obj, date_str = parse_date(metadata.get('date', ''))
        author = metadata.get('author', '')   # Fixed: was 'auther'
        tags = metadata.get('tags', [])
        reading_time = post_data.get('reading_time', 1)

        content = f"<h1>{metadata.get('title', filename)}</h1>"

        # Meta line: date · author · reading time
        meta_parts = []
        if date_str:
            meta_parts.append(f"<span><i class='far fa-calendar-alt'></i> {date_str}</span>")
        if author:
            meta_parts.append(f"<span><i class='far fa-user'></i> {author}</span>")
        meta_parts.append(f"<span><i class='far fa-clock'></i> {reading_time} min read</span>")
        content += f"<div class='post-meta'>{''.join(meta_parts)}</div>"

        # Tags
        content += render_tags(tags)

        # Table of contents (only shown when there are headings)
        if post_data.get('toc'):
            content += post_data['toc']

        # Post body
        content += post_data['html']

        # Related posts
        related = get_related_posts(filename, tags)
        if related:
            content += "<div class='related-posts'><h3>Related Posts</h3><ul class='post-list'>"
            for rel_post, rel_meta in related:
                _, rel_date_str = parse_date(rel_meta.get('date', ''))
                rel_title = rel_meta.get('title', rel_post['path'].split('/')[-1])
                content += f"""
                    <li class='post-item'>
                        <div class='post-header'>
                            <a href="/{rel_post['path']}">{rel_title}</a>
                            {f"<span class='post-date'>{rel_date_str}</span>" if rel_date_str else ""}
                        </div>
                        {render_tags(rel_meta.get('tags', []))}
                    </li>
                """
            content += "</ul></div>"

        return TemplateRenderer.render_page(
            title=metadata.get('title', filename),
            content=content,
            breadcrumbs=generate_breadcrumbs(filename)
        )
    except Exception as e:
        app.logger.error(f"Post error: {str(e)}")
        return TemplateRenderer.render_page(
            title="Error", content="",
            error={'title': 'Post Error', 'description': str(e)}
        )


@app.errorhandler(404)
def page_not_found(e):
    return TemplateRenderer.render_page(
        title="Not Found", content="",
        error={'title': '404 Not Found', 'description': e.description}
    ), 404


@app.errorhandler(500)
def internal_error(e):
    return TemplateRenderer.render_page(
        title="Server Error", content="",
        error={'title': '500 Server Error', 'description': e.description}
    ), 500


if __name__ == "__main__":
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)
