# Use a slim Python 3.9 base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app


# Copy the requirements file into the container
COPY requirements.txt requirements.txt

# Upgrade pip to the latest version and install Python dependencies with a higher timeout
RUN pip install --upgrade pip
RUN pip --default-timeout=100 install -r requirements.txt

# Copy the entire application code into the container
COPY . .

# Expose port 3000 to allow external access
EXPOSE 3000

# Run database setup and then start Flask application
CMD ["sh", "-c", "python db_setup.py && python app.py"]
