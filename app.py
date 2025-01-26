from flask import Flask, render_template_string, abort
import os
import markdown

app = Flask(__name__)

# Path to the folder containing .md files
MD_FOLDER = os.path.join(os.path.dirname(__file__), "md")

# HTML Template for rendering Markdown files
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f4f4f9;
            color: #333;
        }
        h1, h2, h3 {
            color: #555;
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
        }
        .navbar a {
            color: white;
            margin-right: 20px;
            text-decoration: none;
            font-weight: bold;
        }
        .navbar a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <a href="/">Home</a>
    </div>
    <div class="container">
        {{ content|safe }}
    </div>
</body>
</html>
"""

# HTML Template for the Home Page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f4f4f9;
            color: #333;
            padding-bottom: 40px; /* Prevent content from being hidden behind footer */
        }
        h1, h2, h3 {
            color: #555;
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
        }
        .navbar a {
            color: white;
            margin-right: 20px;
            text-decoration: none;
            font-weight: bold;
        }
        .navbar a:hover {
            text-decoration: underline;
        }
        .navbar .social-icons a {
            color: white;
            margin-left: 10px;
            font-size: 20px;
        }
        .navbar .social-icons a:hover {
            color: #f1f1f1;
        }
        footer {
            background-color: #0066cc;
            color: white;
            text-align: center;
            padding: 10px;
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <a href="/">Home</a>
        <div class="social-icons">
            <a href="https://github.com/siddhantdembi" target="_blank" title="GitHub">
                <i class="fab fa-github"></i>
            </a>
            <a href="https://linkedin.com/in/siddhantdembi" target="_blank" title="LinkedIn">
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

HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blogs</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f4f4f9;
            color: #333;
            padding-bottom: 40px; /* Prevent content from being hidden behind footer */
        }
        h1, h2, h3 {
            color: #555;
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
        ul {
            list-style-type: none;
            padding: 0;
        }
        li {
            margin: 10px 0;
        }
        .navbar {
            background-color: #0066cc;
            color: white;
            padding: 10px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .navbar a {
            color: white;
            margin-right: 20px;
            text-decoration: none;
            font-weight: bold;
        }
        .navbar a:hover {
            text-decoration: underline;
        }
        .navbar .social-icons a {
            color: white;
            margin-left: 10px;
            font-size: 20px;
        }
        .navbar .social-icons a:hover {
            color: #f1f1f1;
        }
        footer {
            background-color: #0066cc;
            color: white;
            text-align: center;
            padding: 10px;
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <a href="/">Home</a>
        <div class="social-icons">
            <a href="https://github.com/siddhantdembi" target="_blank" title="GitHub">
                <i class="fab fa-github"></i>
            </a>
            <a href="https://linkedin.com/in/siddhantdembi" target="_blank" title="LinkedIn">
                <i class="fab fa-linkedin"></i>
            </a>
        </div>
    </div>
    <div class="container">
        <h1>Blogs</h1>
        <ul>
            {{ content|safe }}
        </ul>
    </div>
    <footer>
        <p>Blogs by Siddhant Dembi</p>
    </footer>
</body>
</html>
"""

@app.route("/<string:filename>")
def serve_markdown(filename):
    # Construct the full path to the markdown file
    file_path = os.path.join(MD_FOLDER, f"{filename}.md")

    # Check if the file exists
    if not os.path.isfile(file_path):
        abort(404)

    # Read and convert the Markdown content to HTML
    with open(file_path, "r", encoding="utf-8") as md_file:
        md_content = md_file.read()
        html_content = markdown.markdown(md_content)

    # Render the content with the HTML template
    return render_template_string(HTML_TEMPLATE, title=filename, content=html_content)

@app.route("/")
def list_files():
    # List all Markdown files in the folder
    files = [f[:-3] for f in os.listdir(MD_FOLDER) if f.endswith(".md")]

    # Generate a simple HTML list of links
    file_links = "".join(
        f'<li><a href="/{file}">{file}</a></li>' for file in files
    )

    return render_template_string(HOME_TEMPLATE, content=file_links)

if __name__ == "__main__":
    # Ensure the markdown folder exists
    if not os.path.exists(MD_FOLDER):
        os.makedirs(MD_FOLDER)

    app.run(debug=True, host="0.0.0.0", port=5678)