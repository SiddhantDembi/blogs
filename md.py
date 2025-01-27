from flask import Flask, render_template_string, request, send_file
import markdown
import os

app = Flask(__name__)

# HTML template with inline CSS and JavaScript
TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown Live Preview</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            background-color: #f9f9f9;
        }
        .container {
            width: 90%;
            max-width: 1200px;
        }
        textarea {
            width: 100%;
            height: 200px;
            margin-bottom: 20px;
            padding: 10px;
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 5px;
            resize: vertical;
        }
        .preview {
            padding: 20px;
            border: 1px solid #ccc;
            border-radius: 5px;
            background-color: #fff;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        .preview h1, .preview h2, .preview h3 {
            border-bottom: 1px solid #ddd;
        }
        .preview p {
            line-height: 1.6;
        }
        .preview code {
            background: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
        }
        .download-btn {
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 20px;
        }
        .download-btn:hover {
            background-color: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Markdown Live Preview</h1>
        <textarea id="markdown-input" placeholder="Enter Markdown content here...">{{ initial_content }}</textarea>
        <div class="preview" id="markdown-preview">{{ rendered_content|safe }}</div>
        <button class="download-btn" id="download-btn">Download</button>
    </div>

    <script>
        const inputField = document.getElementById('markdown-input');
        const previewDiv = document.getElementById('markdown-preview');
        const downloadBtn = document.getElementById('download-btn');

        inputField.addEventListener('input', () => {
            const markdownContent = inputField.value;
            fetch('/render', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ content: markdownContent })
            })
            .then(response => response.text())
            .then(html => {
                previewDiv.innerHTML = html;
            });
        });

        // Download Markdown file
        downloadBtn.addEventListener('click', () => {
            const markdownContent = inputField.value;
            const blob = new Blob([markdownContent], { type: 'text/markdown' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'content.md';
            link.click();
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    # Default content for the textarea
    initial_content = "# Welcome to Markdown Preview\n\nStart typing your markdown content here!"
    rendered_content = markdown.markdown(initial_content)
    return render_template_string(
        TEMPLATE,
        initial_content=initial_content,
        rendered_content=rendered_content
    )

@app.route("/render", methods=["POST"])
def render_markdown():
    data = request.get_json()
    markdown_content = data.get("content", "")
    rendered_content = markdown.markdown(markdown_content)
    return rendered_content

if __name__ == "__main__":
    app.run(debug=True)
