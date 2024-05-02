from flask import Flask, render_template, request
import os
from functools import reduce

app = Flask(__name__)


def get_directory_structure(rootdir):
    """
    Creates a nested dictionary that represents the folder structure of rootdir.
    """
    dir = {}
    rootdir = rootdir.rstrip(os.sep)
    start = rootdir.rfind(os.sep) + 1
    for path, dirs, files in os.walk(rootdir):
        folders = path[start:].split(os.sep)
        subdir = dict.fromkeys(files)
        parent = reduce(dict.get, folders[:-1], dir)
        parent[folders[-1]] = subdir
    return dir


def search_files(directory, search_query):
    """
    Search for files and directories that match the search_query within 'directory'.
    """
    matches = []
    for root, dirs, files in os.walk(directory):
        for dir in dirs:
            if search_query.lower() in dir.lower():
                matches.append(os.path.join(root, dir))
        for file in files:
            if search_query.lower() in file.lower():
                matches.append(os.path.join(root, file))
    return matches


@app.route('/', methods=['GET', 'POST'])
def index():
    root_directory = request.form.get('directory', 'path/to/your/directory')
    search_query = request.form.get('search_query', '')
    if request.method == 'POST':
        directory_structure = get_directory_structure(root_directory)
        search_results = search_files(
            root_directory, search_query) if search_query else []
    else:
        directory_structure = {}
        search_results = []
    return render_template('index.html', directory_structure=directory_structure, root_directory=root_directory, search_query=search_query, search_results=search_results)


if __name__ == '__main__':
    app.run(debug=True)
