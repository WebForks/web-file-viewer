from flask import request  # Make sure to import request
from flask import Flask, render_template, request, redirect, url_for
import os
import time

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


def get_directory_size(path):
    total_size = 0
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_file():
                total_size += entry.stat().st_size
            elif entry.is_dir():
                total_size += get_directory_size(entry.path)
    return total_size


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


def get_directory_structure(rootdir):
    entries = {}
    for name in sorted(os.listdir(rootdir)):
        full_path = os.path.join(rootdir, name)
        if os.path.isdir(full_path):
            size_bytes = get_directory_size(full_path)
            is_directory = True
        else:
            size_bytes = os.path.getsize(full_path)
            is_directory = False
        size = scale_size(size_bytes)
        mtime = os.path.getmtime(full_path)
        formatted_mtime = time.strftime(
            '%m/%d/%Y %I:%M %p', time.localtime(mtime))
        entries[name] = {
            'is_directory': is_directory,
            'size': size,
            'size_bytes': size_bytes,
            'last_modified': formatted_mtime
        }
    return entries


def search_files(directory, search_query):
    """
    Search recursively for files and directories that match the search_query within 'directory'.
    """
    matches = []
    for path, dirs, files in os.walk(directory):
        for dir_name in dirs:
            if search_query.lower() in dir_name.lower():
                full_path = os.path.join(path, dir_name)
                matches.append(full_path)
        for file_name in files:
            if search_query.lower() in file_name.lower():
                full_path = os.path.join(path, file_name)
                matches.append(full_path)
    return matches


@app.route('/search/<search_query>')
def search(search_query):
    # Retrieve sort parameters from the URL query string, default to 'name' and 'asc'
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

    # Sorting function using lambda based on sort_by and order
    search_results.sort(key=lambda x: x[sort_by], reverse=(order == 'desc'))

    results_count = len(search_results)  # Calculate the number of results
    return render_template('search_results.html', search_query=search_query, search_results=search_results, results_count=results_count, base_directory=base_directory, sort_by=sort_by, order=order)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET'])
def index(path):
    current_directory = os.path.join(
        base_directory, path) if path else base_directory
    is_base_directory = (current_directory == base_directory)
    print(current_directory, is_base_directory)

    # Retrieve sorting parameters with defaults set to sort by type descending
    sort_by = request.args.get('sort', 'type_sort')
    order = request.args.get('order', 'desc')

    directory_structure = get_directory_structure(current_directory)

    # Define the sorting key based on the parameter
    def sort_key(item):
        if sort_by == 'size':
            return item[1]['size_bytes']
        elif sort_by == 'last_modified':
            return time.mktime(time.strptime(item[1]['last_modified'], '%m/%d/%Y %I:%M %p'))
        elif sort_by == 'name':
            return item[0]
        elif sort_by == 'type_sort':
            # Directories first if descending
            return item[1]['is_directory']
        else:
            # Default to sorting by name if unrecognized sort type
            return item[0]

    reverse_order = (order == 'desc')
    sorted_directory_structure = dict(
        sorted(directory_structure.items(), key=sort_key, reverse=reverse_order))

    return render_template('index.html', directory_structure=sorted_directory_structure,
                           root_directory=current_directory, is_base_directory=is_base_directory,
                           sort_by=sort_by, order=order)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5167, debug=True)
