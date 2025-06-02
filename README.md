# web-file-viewer

A modern, Dockerized web application for browsing, searching, and managing files and directories through a user-friendly interface.

## Features

- **Interactive File Browser:** Navigate directories, view files, and see folder/file icons.
- **Real-Time Search:** Search for files and folders recursively, with results showing name, path, size, and last modified date.
- **Sortable Columns:** Sort files and folders by name, size, type, or last modified date.
- **Detailed Metadata:** View file size (with human-readable units) and last accessed/modified times.
- **Responsive UI:** Clean, modern interface styled with CSS.
- **Performance Optimizations:** Uses caching and multi-threading for fast directory access.
- **Cross-Platform:** Works on Windows and Linux.
- **Production-Ready:** Runs on Waitress WSGI server; fully containerized with Docker and Docker Compose.
- **Custom Favicon:** Includes a favicon for a polished browser experience.

## Technologies Used

Python 3.9, Flask, Waitress, ThreadPoolExecutor, LRU Cache, HTML5, CSS3, JavaScript, Docker, Docker Compose, Jinja2, Werkzeug, Blinker, Click, Colorama, MarkupSafe, Git

## Setup

### Prerequisites

- Python 3.9+
- pip
- Docker (optional, for containerized deployment)
- Docker Compose (optional)

### Local Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/web-file-viewer.git
   cd web-file-viewer
   ```

2. **Install dependencies:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the application:**

   ```bash
   python run.py
   ```

   The app will be available at [http://localhost:5167](http://localhost:5167).

### Docker Deployment

1. **Copy the example Docker Compose file:**

   ```bash
   cp example-docker-compose.yml docker-compose.yml
   ```

2. **Edit `docker-compose.yml`** to set the correct host directory for your files:

   ```yaml
   volumes:
     - /absolute/path/to/your/files:/data
   ```

3. **Start the service (this will pull the image from Docker Hub if needed):**

   ```bash
   docker compose up
   ```

   The app will be available at [http://localhost:5167](http://localhost:5167).

4. **(Optional) To update to the latest image:**

   ```bash
   docker compose pull
   docker compose up -d
   ```

## Usage

- **Browse:** Click folders to navigate, click "Up One Directory" to go back.
- **Search:** Use the search bar to find files/folders by name.
- **Sort:** Click table headers to sort by type, name, size, or last modified.
- **View Details:** See file size and last modified date in the table.
