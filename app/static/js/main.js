const fileList = document
  .getElementById("file-list")
  .getElementsByTagName("tbody")[0];
const breadcrumb = document.getElementById("breadcrumb");
const searchInput = document.getElementById("search-input");
const backButton = document.getElementById("back-button");
const rescanButton = document.getElementById("rescan-button");
const clearSearchButton = document.getElementById("clear-search-button");

let rootPath = null; // Will be set from server
let currentPath = null; // Will be set from server
let isSearchMode = false;
let currentData = [];
let sortColumn = "name";
let sortDirection = "asc";

const fetchAndDisplay = async (path) => {
  // Ensure we have a valid path
  if (!path) {
    console.error("Cannot fetch: path is null or empty");
    return;
  }

  try {
    console.log(`Fetching path: ${path}`);
    const response = await fetch(
      `/api/browse?path=${encodeURIComponent(path)}`
    );
    if (!response.ok) {
      throw new Error("Network response was not ok");
    }
    const data = await response.json();
    currentData = data;
    currentPath = path;
    renderFileList();
    renderBreadcrumb();
  } catch (error) {
    console.error("Error fetching data:", error);
  }
};

const renderFileList = () => {
  fileList.innerHTML = "";
  sortData();
  currentData.forEach((item) => {
    const row = fileList.insertRow();
    const icon = item.type === "directory" ? "📁" : "📄";

    // Create the name cell with path information for search results
    const nameCell = document.createElement("td");

    // Create the link element
    const link = document.createElement("a");
    link.href = "#";
    link.dataset.path = item.path;
    link.dataset.type = item.type;
    link.textContent = item.name;

    // Add icon and link to the name cell
    nameCell.appendChild(document.createTextNode(icon + " "));
    nameCell.appendChild(link);

    // Add file path for search results
    if (isSearchMode) {
      const pathInfo = document.createElement("span");
      pathInfo.className = "file-path";

      // Get the parent directory path
      const parentPath = item.path.substring(0, item.path.lastIndexOf("/"));
      pathInfo.textContent = `in ${parentPath}`;

      nameCell.appendChild(pathInfo);
    }

    row.appendChild(nameCell);

    // Add the rest of the cells
    const sizeCell = document.createElement("td");
    sizeCell.textContent = item.size;
    row.appendChild(sizeCell);

    const typeCell = document.createElement("td");
    typeCell.textContent = item.type;
    row.appendChild(typeCell);

    const dateCell = document.createElement("td");
    dateCell.textContent = item.last_modified;
    row.appendChild(dateCell);
  });
};

const renderBreadcrumb = () => {
  // Don't update breadcrumb in search mode
  if (isSearchMode) return;

  breadcrumb.innerHTML = "";
  const parts = currentPath.split(/[\\/]/).filter(Boolean);
  let path = "";

  // Add Root link
  const rootLink = document.createElement("a");
  rootLink.href = "#";
  rootLink.textContent = "Root";
  rootLink.addEventListener("click", (e) => {
    e.preventDefault();
    fetchAndDisplay(rootPath);
  });
  breadcrumb.appendChild(rootLink);

  // Add path parts
  parts.forEach((part, index) => {
    // Add separator
    const separator = document.createElement("span");
    separator.className = "separator";
    separator.textContent = " / ";
    breadcrumb.appendChild(separator);

    // Build the full path correctly with leading slash
    if (index === 0) {
      path = `/${part}`;
    } else {
      path = `${path}/${part}`;
    }

    const link = document.createElement("a");
    link.href = "#";
    link.textContent = part;
    link.addEventListener("click", (e) => {
      e.preventDefault();
      fetchAndDisplay(path);
    });
    breadcrumb.appendChild(link);
  });
};

const sortData = () => {
  currentData.sort((a, b) => {
    const aValue = a[sortColumn];
    const bValue = b[sortColumn];
    let comparison = 0;
    if (aValue > bValue) {
      comparison = 1;
    } else if (aValue < bValue) {
      comparison = -1;
    }
    return sortDirection === "desc" ? comparison * -1 : comparison;
  });
};

fileList.addEventListener("click", (e) => {
  if (e.target.tagName === "A" && e.target.dataset.type === "directory") {
    e.preventDefault();
    searchInput.value = "";
    fetchAndDisplay(e.target.dataset.path);
  }
});

document
  .getElementById("file-list")
  .querySelector("thead")
  .addEventListener("click", (e) => {
    if (e.target.tagName === "TH") {
      const newSortColumn = e.target.dataset.sort;
      if (sortColumn === newSortColumn) {
        sortDirection = sortDirection === "asc" ? "desc" : "asc";
      } else {
        sortColumn = newSortColumn;
        sortDirection = "asc";
      }
      renderFileList();
    }
  });

async function performSearch() {
  const query = searchInput.value;
  if (query) {
    try {
      const response = await fetch(
        `/api/search?q=${encodeURIComponent(query)}&path=${encodeURIComponent(
          currentPath
        )}`
      );
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      const data = await response.json();
      currentData = data;
      isSearchMode = true;
      breadcrumb.innerHTML = `Search results for: "${query}"`;
      renderFileList();

      // Show the clear search button
      clearSearchButton.style.display = "inline-block";
    } catch (error) {
      console.error("Error searching:", error);
    }
  } else {
    clearSearch();
  }
}

function clearSearch() {
  isSearchMode = false;
  searchInput.value = "";
  clearSearchButton.style.display = "none";
  fetchAndDisplay(currentPath);
}

searchInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    performSearch();
  }
});

// Initialize back button functionality
backButton.addEventListener("click", () => {
  if (isSearchMode) {
    clearSearch();
    return;
  }

  if (currentPath === rootPath) {
    return; // Already at root
  }

  // Get parent directory
  const parentPath = currentPath.substring(0, currentPath.lastIndexOf("/"));
  fetchAndDisplay(parentPath || rootPath);
});

// Initialize rescan button functionality
rescanButton.addEventListener("click", () => {
  if (isSearchMode) {
    clearSearch();
  } else {
    fetchAndDisplay(currentPath);
  }
});

// Hide clear search button initially
clearSearchButton.style.display = "none";

// Fetch configuration from server
async function fetchConfig() {
  try {
    console.log("Fetching configuration from server...");
    const response = await fetch("/api/config");
    if (!response.ok) {
      throw new Error("Failed to fetch configuration");
    }
    const config = await response.json();
    rootPath = config.rootPath;
    currentPath = rootPath;
    console.log(`Root path set to: ${rootPath}`);

    // Only start loading data after we have the configuration
    fetchAndDisplay(currentPath);
  } catch (error) {
    console.error("Error fetching configuration:", error);
    // If we can't get the config, use a default value
    rootPath = "/host/documents";
    currentPath = rootPath;
    console.log(`Using default root path: ${rootPath}`);
    fetchAndDisplay(currentPath);
  }
}

// Start the application by fetching config first
fetchConfig();
