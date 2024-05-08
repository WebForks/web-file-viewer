from flask import Flask, render_template, request, redirect, url_for
import os
import time

app = Flask(__name__)
# example gui https://alchemist.cyou
# https://stackoverflow.com/questions/49770999/docker-env-for-python-variables
base_directory = 'C:/Users/Ethan/Downloads'


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
    directories = {}
    files = {}
    for path, dirs, file_list in os.walk(rootdir):
        for name in sorted(dirs):
            full_path = os.path.join(path, name)
            size_bytes = get_directory_size(full_path)
            size = scale_size(size_bytes)
            mtime = os.path.getmtime(full_path)
            formatted_mtime = time.strftime(
                '%m/%d/%Y %I:%M %p', time.localtime(mtime))
            directories[name] = {'is_directory': True,
                                 'size': size, 'last_modified': formatted_mtime}

        for name in sorted(file_list):
            full_path = os.path.join(path, name)
            size_bytes = os.path.getsize(full_path)
            size = scale_size(size_bytes)
            mtime = os.path.getmtime(full_path)
            # print(f"mtime: {mtime}")
            # Adjusting the format string to Month/Day/Year Hour:Minute AM/PM
            formatted_mtime = time.strftime(
                '%m/%d/%Y %I:%M %p', time.localtime(mtime))
            # print(f"formatted_mtime: {formatted_mtime}")
            files[name] = {'is_directory': False,
                           'size': size, 'last_modified': formatted_mtime}

        break
    combined = {**directories, **files}
    # print(f"Combined: {combined}")
    return combined


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
    search_results = search_files(base_directory, search_query)
    search_results = [{
        'name': os.path.basename(path),
        'path': path,
        'type': 'Directory' if os.path.isdir(path) else 'File',
        'size': scale_size(os.path.getsize(path)),
        'last_modified': time.strftime('%m/%d/%Y %I:%M %p', time.localtime(os.path.getmtime(path))),
        'parent_directory': os.path.dirname(path)
    } for path in search_results]
    results_count = len(search_results)  # Calculate the number of results
    return render_template('search_results.html', search_query=search_query, search_results=search_results, results_count=results_count, base_directory=base_directory)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET'])  # Removed 'POST'
def index(path):
    current_directory = os.path.join(
        base_directory, path) if path else base_directory
    is_base_directory = (current_directory == base_directory)

    directory_structure = get_directory_structure(current_directory)
    sort_by = request.args.get('sort', 'name')
    order = request.args.get('order', 'asc')
    type_sort = request.args.get('type_sort', 'folder_top')

    if type_sort == 'folder_top':
        sorted_directory_structure = dict(sorted(directory_structure.items(),
                                                 key=lambda item: (
                                                     not item[1]['is_directory'], item[0] if sort_by == 'name' else item[1][sort_by]),
                                                 reverse=(order == 'desc')))
    else:
        sorted_directory_structure = dict(sorted(directory_structure.items(),
                                                 key=lambda item: (
                                                     item[1]['is_directory'], item[0] if sort_by == 'name' else item[1][sort_by]),
                                                 reverse=(order == 'desc')))

    return render_template('index.html', directory_structure=sorted_directory_structure,
                           root_directory=current_directory, is_base_directory=is_base_directory)


if __name__ == '__main__':
    app.run(debug=True)
