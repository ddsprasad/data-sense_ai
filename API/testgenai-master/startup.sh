#!/bin/bash

# Install ODBC Driver 17 for SQL Server on Azure App Service Linux
echo "Installing ODBC Driver 17 for SQL Server..."

# Add Microsoft repository
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Update and install
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

echo "ODBC Driver installation complete!"

# Start the application with gunicorn
echo "Starting application..."
gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 main:app
