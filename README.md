# Blogs Application
This Blogs Application, is a dynamic blogging platform built using Docker and Python (Flask), with the frontend developed using HTML and CSS within Flask (app.py) to keep it a single-file project. It allows users to create, manage, and publish blog posts through a user-friendly interface. The application is designed for easy setup and maintenance, leveraging Docker for seamless deployment.
## Prerequisites

- Docker installed on your machine.
- Python 3.9 or later installed (if you want to run locally without Docker).

## Setup

1. **Clone the repository**:

   ```sh
   git clone https://github.com/siddhantdembi/blogs.git
   ```

2. **Navigate to the project directory**:

   ```sh
   cd blogs
   ```

3. **Build the Docker image**:

   ```sh
   docker build -t blogs .
   ```
4. **Spin up the Docker container**:

   ```sh
   docker compose up
   ```
   
5. **Access the application**:
   Open your web browser and go to [http://localhost:5678](http://localhost:5678) (or the IP address of the machine running Docker).

## Project Structure

- **/md**: This folder contains all your markdown files categorized into subfolders.
  Each file should follow this format at the top:

  ```yaml
  ---
  title: "Write-The-Title"
  date: "28-01-2025"
  author: "Name"
  ---
  # Start Here
  This is an example.
  ```

## Docker Compose File

```yaml
version: "3.9"
services:
  blogs:
    image: blogs
    ports:
      - "5678:5678"
    volumes:
      - /path/to/blogs:/app/md

```

This setup should help you get started with your blogging application!
