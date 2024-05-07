from flask import Flask, render_template, request
import os
import time

app = Flask(__name__)


def get_directory_size(path):
    """ Returns the total size of all files in the directory tree. """
    total_size = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            total_size += os.path.getsize(file_path)
    return total_size


def get_directory_structure(rootdir):
    directories = {}
    files = {}
    for path, dirs, file_list in os.walk(rootdir):
        for name in sorted(dirs):
            full_path = os.path.join(path, name)
            size_bytes = get_directory_size(full_path)  # Get cumulative size
            size = scale_size(size_bytes)
            mtime = os.path.getmtime(full_path)
            formatted_mtime = time.strftime(
                '%Y-%m-%d %H:%M:%S', time.localtime(mtime))
            directories[name] = {'is_directory': True,
                                 'size': size, 'last_modified': formatted_mtime}
        for name in sorted(file_list):
            full_path = os.path.join(path, name)
            size_bytes = os.path.getsize(full_path)
            size = scale_size(size_bytes)
            mtime = os.path.getmtime(full_path)
            formatted_mtime = time.strftime(
                '%Y-%m-%d %H:%M:%S', time.localtime(mtime))
            files[name] = {'is_directory': False,
                           'size': size, 'last_modified': formatted_mtime}
        break
    combined = {**directories, **files}
    print(combined)
    return combined


def scale_size(size_bytes):
    """Scale size to appropriate measurement (Bytes, KB, MB, GB, TB)."""
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


def search_files(directory, search_query):
    """
    Search for files and directories that match the search_query within 'directory',
    but only within the immediate subdirectories and files of the root.
    """
    matches = []
    for path, dirs, files in os.walk(directory):
        # Check directories and files only in the root
        for dir in dirs:
            if search_query.lower() in dir.lower():
                matches.append(os.path.join(path, dir))
        for file in files:
            if search_query.lower() in file.lower():
                matches.append(os.path.join(path, file))
        # Stop after checking the root directory
        break
    return matches


@app.route('/', methods=['GET', 'POST'])
def index():
    hardcoded_root_directory = '/'
    search_query = request.form.get('search_query', '')
    sort_by = request.args.get('sort', 'name')
    order = request.args.get('order', 'asc')
    type_sort = request.args.get('type_sort', 'folder_top')

    directory_structure = get_directory_structure(hardcoded_root_directory)

    # Sort based on type if requested
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

    search_results = []
    if request.method == 'POST' and search_query:
        search_results = search_files(hardcoded_root_directory, search_query)
    return render_template('index.html', directory_structure=sorted_directory_structure,
                           root_directory=hardcoded_root_directory, search_query=search_query,
                           search_results=search_results, type_sort=type_sort)


if __name__ == '__main__':
    app.run(debug=True)
