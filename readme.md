# File Explorer Web Application

This is a simple, dockerized web application for browsing, searching, and managing files on your local machine through a web interface.

## Features

- **Interactive File Browser**: Navigate through your file system with ease.
- **Real-time Search**: Quickly find files and folders within the current directory and its subdirectories.
- **Sortable Columns**: Sort files and folders by name, size, type, or last modified date.
- **Detailed Metadata**: View detailed information for each file and folder, including size and last modified date.
- **Folder Size Calculation**: Folder sizes are calculated recursively to show the total size of all their contents.
- **Breadcrumb Navigation**: Easily navigate back to parent directories using the clickable breadcrumb trail.
- **Back and Rescan Buttons**: A dedicated back button to go to the parent directory and a rescan button to refresh the current view.
- **Configurable Root Directory**: The application can be configured to start in any directory on your machine.
- **Responsive UI**: The user interface is designed with Monokai, Segoe UI, and Consolas for a clean and modern look.
- **Cross-Platform Compatibility**: The application is containerized with Docker, so it can run on any system that supports Docker.

## Requirements

- Docker
- Docker Compose

## How to Run

1.  **Clone the repository** to your local machine.

2.  **Configure the root directory** by editing the `docker-compose.yml` file.
    -   Update the `source` under `volumes` to the directory you want to browse.
    -   Update the `ROOT_PATH` environment variable to match the `target` path in the volume mount.

    For example, to browse your Documents folder:

    ```yaml
    services:
      webapp:
        build: .
        ports:
          - "8081:8080"
        environment:
          - ROOT_PATH=/host/documents
        volumes:
          - type: bind
            source: C:\Users\YourUser\Documents # Change this to your Documents path
            target: /host/documents
    ```

3.  **Build and run the application** using Docker Compose:

    ```bash
    docker-compose up --build
    ```

4.  **Open your web browser** and navigate to `http://localhost:8081` to access the application.

## Project Structure

- `app/`: Contains the Flask application.
  - `main.py`: The main Flask application file.
  - `static/`: Contains static assets like CSS, JavaScript, and images.
  - `templates/`: Contains the HTML templates for the web interface.
- `Dockerfile`: The Dockerfile for building the application image.
- `docker-compose.yml`: The Docker Compose file for running the application.
- `requirements.txt`: The Python dependencies for the application.
- `readme.txt`: This file.
