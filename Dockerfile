# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5167 available to the world outside this container
EXPOSE 5167

# Define environment variable for base directory
ENV BASE_DIRECTORY=/data

# Run app.py when the container launches on port 5167
CMD ["flask", "run", "--host=0.0.0.0", "--port=5167"]
