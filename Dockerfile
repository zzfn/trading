# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install pip and setuptools first
RUN pip install --no-cache-dir setuptools==78.1.1

# Install numpy explicitly
RUN pip install --no-cache-dir numpy==1.26.4

# Install the rest of the requirements.txt
# pip will see numpy==1.26.4 is already installed and skip it.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run the application
CMD ["gunicorn", "main:app", "-b", "0.0.0.0:5000", "--workers", "4"]
