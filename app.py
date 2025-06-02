from flask import request  # Make sure to import request
from flask import Flask, render_template, request, redirect, url_for
import os
import time
import subprocess
from concurrent.futures import ThreadPoolExecutor
import threading
import logging
import math

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

executor = ThreadPoolExecutor(max_workers=4)
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

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

def get_directory_structure(rootdir, page=1, sort_by='name', order='asc'):
    """Get directory structure using native ls command with pagination"""
    try:
        # Use ls -la to get detailed listing
        result = subprocess.run(['ls', '-la', rootdir], capture_output=True, text=True)
        if result.returncode != 0:
            return {}, 0

        # Skip the first line (total) and process entries
        lines = result.stdout.strip().split('\n')[1:]
        entries = {}
        
        for line in lines:
            parts = line.split()
            if len(parts) < 9:  # Skip invalid lines
                continue
                
            name = ' '.join(parts[8:])  # Handle filenames with spaces
            if name in ['.', '..']:
                continue
                
            full_path = os.path.join(rootdir, name)
            is_directory = line.startswith('d')
            
            # Get size only if needed (for sorting by size)
            size_bytes = 0
            if sort_by == 'size':
                if is_directory:
                    size_bytes = get_directory_size(full_path)
                else:
                    size_bytes = int(parts[4])
            
            # Get modification time
            mtime = os.path.getmtime(full_path)
            formatted_mtime = time.strftime('%m/%d/%Y %I:%M %p', time.localtime(mtime))
            
            entries[name] = {
                'is_directory': is_directory,
                'size': scale_size(size_bytes) if size_bytes else '...',
                'size_bytes': size_bytes,
                'last_modified': formatted_mtime
            }

        # Sort entries
        sorted_items = sorted(entries.items(), 
                            key=lambda x: x[1]['size_bytes'] if sort_by == 'size' 
                                        else x[1]['last_modified'] if sort_by == 'last_modified'
                                        else x[0].lower(),
                            reverse=(order == 'desc'))
        
        # Calculate pagination
        total_items = len(sorted_items)
        total_pages = math.ceil(total_items / PAGE_SIZE)
        start_idx = (page - 1) * PAGE_SIZE
        end_idx = start_idx + PAGE_SIZE
        
        # Return paginated results
        paginated_entries = dict(sorted_items[start_idx:end_idx])
        return paginated_entries, total_pages

    except Exception as e:
        logging.error(f"Error in get_directory_structure: {e}")
        return {}, 0

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

    search_results = search_files(base_directory, search_query)
    search_results = [{
        'name': os.path.basename(path),
        'path': path,
        'type': 'Directory' if os.path.isdir(path) else 'File',
        'size': scale_size(os.path.getsize(path)),
        'last_modified': time.strftime('%m/%d/%Y %I:%M %p', time.localtime(os.path.getmtime(path))),
        'parent_directory': os.path.dirname(path)
    } for path in search_results]

    # Sort results
    search_results.sort(key=lambda x: x[sort_by], reverse=(order == 'desc'))

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
