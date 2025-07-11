from flask import request  # Make sure to import request
from flask import Flask, render_template, request, redirect, url_for
import os
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor
import threading
import logging
import math
from functools import lru_cache

app = Flask(__name__)
# example gui https://alchemist.cyou
# https://stackoverflow.com/questions/49770999/docker-env-for-python-variables

# # Build your Docker image
# docker build -t webfile-viewer .

# Run your Docker container
# docker run -p 5167:5167 -e BASE_DIRECTORY=/path/on/container webfile-viewer
# docker-compose up --build
# docker-compose down


base_directory = '/data'
PAGE_SIZE = 50  # Number of items per page

# Directories to exclude from caching
EXCLUDED_DIRS = {
    '/proc',
    '/sys',
    '/dev',
    '/run',
    '/var/run',
    '/tmp',
    '/var/tmp'
}

executor = ThreadPoolExecutor(max_workers=4)
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

# Cache for directory structures
directory_cache = {}
cache_lock = threading.Lock()

def should_cache_directory(path):
    """Check if a directory should be cached"""
    # Don't cache system directories
    if any(path.startswith(excluded) for excluded in EXCLUDED_DIRS):
        return False
    # Don't cache directories outside the base directory
    if not path.startswith(base_directory):
        return False
    return True

def get_directory_size(path):
    """Get directory size using native du command"""
    try:
        result = subprocess.run(['du', '-sb', path], capture_output=True, text=True)
        if result.returncode == 0:
            return int(result.stdout.split()[0])
    except Exception as e:
        logging.warning(f"Error getting size for {path}: {e}")
    return 0

def scale_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes / 1024**2:.2f} MB"
    elif size_bytes < 1024**4:
        return f"{size_bytes / 1024**3:.2f} GB"
    else:
        return f"{size_bytes / 1024**4:.2f} TB"

def get_directory_structure(rootdir, page=1, sort_by='name', order='asc', use_cache=True):
    """Get directory structure using native ls command with pagination and caching"""
    try:
        # Check if we should cache this directory
        if use_cache and not should_cache_directory(rootdir):
            use_cache = False

        # Check cache first if enabled
        if use_cache:
            with cache_lock:
                if rootdir in directory_cache:
                    entries, total_pages = directory_cache[rootdir]
                    # Apply pagination to cached results
                    start_idx = (page - 1) * PAGE_SIZE
                    end_idx = start_idx + PAGE_SIZE
                    paginated_entries = dict(list(entries.items())[start_idx:end_idx])
                    return paginated_entries, total_pages

        # Use ls -la to get detailed listing, following symlinks
        result = subprocess.run(['ls', '-la', '--time-style=full-iso', rootdir], 
                              capture_output=True, text=True, check=False)
        if result.returncode != 0:
            logging.warning(f"Error listing directory {rootdir}: {result.stderr}")
            return {}, 0

        # Skip the first line (total) and process entries
        lines = result.stdout.strip().split('\n')[1:]
        entries = {}
        
        for line in lines:
            try:
                parts = line.split()
                if len(parts) < 9:  # Skip invalid lines
                    continue
                    
                name = ' '.join(parts[8:])  # Handle filenames with spaces
                if name in ['.', '..']:
                    continue
                    
                full_path = os.path.join(rootdir, name)
                
                # Skip if path doesn't exist (broken symlink or deleted file)
                if not os.path.exists(full_path):
                    continue
                
                is_directory = line.startswith('d')
                
                # Get size for all entries
                size_bytes = 0
                try:
                    if is_directory:
                        size_bytes = get_directory_size(full_path)
                    else:
                        size_bytes = int(parts[4])
                except (ValueError, OSError) as e:
                    logging.warning(f"Error getting size for {full_path}: {e}")
                
                # Get modification time
                try:
                    mtime = os.path.getmtime(full_path)
                    formatted_mtime = time.strftime('%m/%d/%Y %I:%M %p', time.localtime(mtime))
                except OSError as e:
                    logging.warning(f"Error getting mtime for {full_path}: {e}")
                    mtime = 0
                    formatted_mtime = "Unknown"
                
                entries[name] = {
                    'is_directory': is_directory,
                    'size': scale_size(size_bytes) if size_bytes else '...',
                    'size_bytes': size_bytes,
                    'last_modified': formatted_mtime,
                    'last_modified_ts': mtime
                }
            except Exception as e:
                logging.warning(f"Error processing entry in {rootdir}: {e}")
                continue

        # Sort entries
        def sort_key(item):
            name, details = item
            if sort_by == 'size':
                return details['size_bytes']
            elif sort_by == 'last_modified':
                return details['last_modified_ts']
            elif sort_by == 'type_sort':
                return (0 if details['is_directory'] else 1, name.lower())
            else:
                return name.lower()

        reverse = (order == 'desc')
        if sort_by == 'type_sort':
            # Descending should show directories first
            reverse = (order == 'asc')

        sorted_items = sorted(entries.items(), key=sort_key, reverse=reverse)
        
        # Calculate pagination
        total_items = len(sorted_items)
        total_pages = math.ceil(total_items / PAGE_SIZE)
        start_idx = (page - 1) * PAGE_SIZE
        end_idx = start_idx + PAGE_SIZE
        
        # Cache the full directory structure
        if use_cache:
            with cache_lock:
                directory_cache[rootdir] = (dict(sorted_items), total_pages)
                
                # Cache parent directory if it exists
                parent_dir = os.path.dirname(rootdir)
                if parent_dir and parent_dir != rootdir and should_cache_directory(parent_dir):
                    if parent_dir not in directory_cache:
                        executor.submit(get_directory_structure, parent_dir, 1, sort_by, order)
                
                # Cache immediate children directories
                for name, details in entries.items():
                    if details['is_directory']:
                        child_path = os.path.join(rootdir, name)
                        if child_path not in directory_cache and should_cache_directory(child_path):
                            executor.submit(get_directory_structure, child_path, 1, sort_by, order)
        
        # Return paginated results
        paginated_entries = dict(sorted_items[start_idx:end_idx])
        return paginated_entries, total_pages

    except Exception as e:
        logging.error(f"Error in get_directory_structure: {e}")
        return {}, 0

def clear_directory_cache():
    """Clear the directory cache"""
    with cache_lock:
        directory_cache.clear()

def search_files(directory, search_query):
    """Search files using native find command"""
    try:
        result = subprocess.run(['find', directory, '-iname', f'*{search_query}*'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')
    except Exception as e:
        logging.error(f"Error in search_files: {e}")
    return []

@app.route('/search/<search_query>')
def search(search_query):
    page = int(request.args.get('page', 1))
    sort_by = request.args.get('sort', 'name')
    order = request.args.get('order', 'asc')

    search_results_raw = search_files(base_directory, search_query)

    search_results = []
    for path in search_results_raw:
        is_dir = os.path.isdir(path)
        size_bytes = get_directory_size(path) if is_dir else os.path.getsize(path)
        search_results.append({
            'name': os.path.basename(path),
            'path': path,
            'type': 'Directory' if is_dir else 'File',
            'size': scale_size(size_bytes),
            'size_bytes': size_bytes,
            'last_modified': time.strftime('%m/%d/%Y %I:%M %p', time.localtime(os.path.getmtime(path))),
            'last_modified_ts': os.path.getmtime(path),
            'parent_directory': os.path.dirname(path)
        })

    # Sort results with proper numeric handling
    def sort_key(item):
        if sort_by == 'size':
            return item['size_bytes']
        elif sort_by == 'last_modified':
            return item['last_modified_ts']
        else:
            return item[sort_by].lower() if isinstance(item[sort_by], str) else item[sort_by]

    search_results.sort(key=sort_key, reverse=(order == 'desc'))

    # Paginate results
    total_items = len(search_results)
    total_pages = math.ceil(total_items / PAGE_SIZE)
    start_idx = (page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    paginated_results = search_results[start_idx:end_idx]

    return render_template('search_results.html', 
                         search_query=search_query,
                         search_results=paginated_results,
                         results_count=total_items,
                         base_directory=base_directory,
                         sort_by=sort_by,
                         order=order,
                         current_page=page,
                         total_pages=total_pages)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET'])
def index(path):
    current_directory = os.path.join(base_directory, path) if path else base_directory
    parent_directory = os.path.dirname(current_directory) if current_directory != base_directory else None
    is_base_directory = (current_directory == base_directory)

    # Get pagination and sorting parameters
    page = int(request.args.get('page', 1))
    sort_by = request.args.get('sort', 'type_sort')
    order = request.args.get('order', 'desc')

    # Clear cache if rescan is requested
    if request.args.get('rescan'):
        clear_directory_cache()

    # Get directory structure with pagination
    directory_structure, total_pages = get_directory_structure(
        current_directory, 
        page=page,
        sort_by=sort_by,
        order=order
    )

    return render_template('index.html',
                         directory_structure=directory_structure,
                         root_directory=current_directory,
                         is_base_directory=is_base_directory,
                         sort_by=sort_by,
                         order=order,
                         current_page=page,
                         total_pages=total_pages)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5167, debug=True)
