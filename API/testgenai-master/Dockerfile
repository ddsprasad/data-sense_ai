# Use an official Python runtime as a parent image
FROM python:3.10.4

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Uvicorn for running the app
RUN pip install uvicorn

# Make port 5000 available to the world outside this container
EXPOSE 8000

# Run the app using Uvicorn on port 5000
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
