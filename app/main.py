import os
import platform
import logging
from flask import Flask, render_template, request, jsonify
from waitress import serve
import datetime
import mimetypes

# Get the root path from environment variable or use default
ROOT_PATH = os.environ.get('ROOT_PATH', '/host/documents')

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_folder_size(folder_path):
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(file_path)
                except (FileNotFoundError, PermissionError):
                    # Skip files that can't be accessed
                    pass
    except (PermissionError, FileNotFoundError):
        # Return 0 if folder can't be accessed
        pass
    return total_size

def get_file_metadata(path):
    try:
        stat = os.stat(path)
        size = stat.st_size
        if os.path.isdir(path):
            size = get_folder_size(path)
        return {
            "size": size,
            "last_modified": stat.st_mtime,
            "created": stat.st_ctime,
        }
    except FileNotFoundError:
        return None

def human_readable_size(size, decimal_places=2):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/browse')
def browse():
    path = request.args.get('path', ROOT_PATH)
    logger.debug(f"Browse request for path: {path}")
    
    if platform.system() == "Windows" and path == "/":
        # On Windows, default to the C drive or the first available drive
        drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:")]
        path = drives[0] if drives else "C:\\"
    
    logger.debug(f"Checking if path exists: {path}")
    if not os.path.exists(path):
        logger.error(f"Path does not exist: {path}")
        return jsonify({"error": f"Path not found: {path}"}), 404
    
    if not os.path.isdir(path):
        logger.error(f"Path is not a directory: {path}")
        return jsonify({"error": f"Not a directory: {path}"}), 404

    logger.debug(f"Listing directory: {path}")
    try:
        dir_contents = os.listdir(path)
        logger.debug(f"Directory contents: {dir_contents}")
    except Exception as e:
        logger.error(f"Error listing directory {path}: {str(e)}")
        return jsonify({"error": f"Error accessing directory: {str(e)}"}), 500

    items = []
    for item in dir_contents:
        item_path = os.path.join(path, item)
        logger.debug(f"Processing item: {item_path}")
        try:
            metadata = get_file_metadata(item_path)
            if metadata:
                item_type = "directory" if os.path.isdir(item_path) else "file"
                items.append({
                    "name": item,
                    "path": item_path,
                    "type": item_type,
                    "size": human_readable_size(metadata["size"]),
                    "last_modified": datetime.datetime.fromtimestamp(metadata["last_modified"]).strftime('%Y-%m-%d %H:%M:%S')
                })
        except Exception as e:
            logger.error(f"Error processing item {item_path}: {str(e)}")
    
    logger.debug(f"Returning {len(items)} items")
    return jsonify(items)

@app.route('/api/search')
def search():
    query = request.args.get('q', '')
    path = request.args.get('path', ROOT_PATH)
    logger.debug(f"Search request for query: '{query}' in path: {path}")
    
    if platform.system() == "Windows" and path == "/":
        drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:")]
        path = drives[0] if drives else "C:\\"
        logger.debug(f"Adjusted path for Windows: {path}")

    if not os.path.exists(path):
        logger.error(f"Search path does not exist: {path}")
        return jsonify({"error": f"Path not found: {path}"}), 404

    results = []
    try:
        logger.debug(f"Starting search in: {path}")
        for root, dirs, files in os.walk(path):
            logger.debug(f"Searching in directory: {root}")
            for name in files + dirs:
                if query.lower() in name.lower():
                    item_path = os.path.join(root, name)
                    logger.debug(f"Match found: {item_path}")
                    try:
                        metadata = get_file_metadata(item_path)
                        if metadata:
                            item_type = "directory" if os.path.isdir(item_path) else "file"
                            results.append({
                                "name": name,
                                "path": item_path,
                                "type": item_type,
                                "size": human_readable_size(metadata["size"]),
                                "last_modified": datetime.datetime.fromtimestamp(metadata["last_modified"]).strftime('%Y-%m-%d %H:%M:%S')
                            })
                    except Exception as e:
                        logger.error(f"Error processing search result {item_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Error during search in {path}: {str(e)}")
        return jsonify({"error": f"Search error: {str(e)}"}), 500
    
    logger.debug(f"Search complete. Found {len(results)} results")
    return jsonify(results)

@app.route('/api/config')
def get_config():
    """Return configuration information to the client"""
    return jsonify({
        "rootPath": ROOT_PATH
    })

if __name__ == '__main__':
    logger.info(f"Starting server with ROOT_PATH: {ROOT_PATH}")
    serve(app, host='0.0.0.0', port=8080)