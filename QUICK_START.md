# DataSense Quick Start Guide

I've created automated setup scripts to make deployment easy. Follow these steps:

---

## Prerequisites to Install

Before running the setup scripts, you need to install:

### 1. Python 3.10.4
- **Download**: https://www.python.org/ftp/python/3.10.4/python-3.10.4-amd64.exe
- **Installation**:
  - Run the installer
  - ✅ **IMPORTANT**: Check "Add Python 3.10 to PATH"
  - ✅ Check "Install launcher for all users"
  - Click "Install Now"
  - Restart your terminal after installation

### 2. Node.js 20.9.0 (for frontend)
- **Download**: https://nodejs.org/dist/v20.9.0/node-v20.9.0-x64.msi
- Run the installer with default settings

### 3. Configure API Keys and Database
Edit this file: `API\testgenai-master\.env`

**Required changes:**
```env
# Replace with your actual OpenAI API key
OPENAI_API_KEY_DFZ=sk-your-actual-openai-key-here

# Replace with your database credentials
DB_USER=your-sql-server-username
DB_PW=your-sql-server-password
DB_HOST=your-sql-server-host.database.windows.net
DB_NAME=your-target-database-name
DB_HISTORY_NAME=your-history-database-name
```

---

## Automated Setup (After Installing Prerequisites)

### Backend Setup

1. Navigate to the backend folder
2. Double-click: `setup.bat`
3. Wait for it to complete (may take 5-10 minutes)

**Or via command line:**
```bash
cd "C:\Users\ddunga\Downloads\DataSense 1\DataSense\API\testgenai-master"
setup.bat
```

### Frontend Setup

1. Navigate to the frontend folder
2. Double-click: `setup-frontend.bat`
3. Wait for it to complete (may take 5-10 minutes)

**Or via command line:**
```bash
cd "C:\Users\ddunga\Downloads\DataSense 1\DataSense\genaifrontend"
setup-frontend.bat
```

---

## Running the Application

### Start Backend Server

**Option 1 (Easy):** Double-click `start-server.bat` in the backend folder

**Option 2 (Command line):**
```bash
cd "C:\Users\ddunga\Downloads\DataSense 1\DataSense\API\testgenai-master"
start-server.bat
```

Backend will run at: **http://localhost:8000**
API docs at: **http://localhost:8000/docs**

### Start Frontend Server

Open a **NEW terminal window** and:

**Option 1 (Easy):** Double-click `start-frontend.bat` in the frontend folder

**Option 2 (Command line):**
```bash
cd "C:\Users\ddunga\Downloads\DataSense 1\DataSense\genaifrontend"
start-frontend.bat
```

Frontend will run at: **http://localhost:4200**

---

## Files Created for You

I've created these automation scripts:

**Backend:**
- `API/testgenai-master/setup.bat` - Sets up Python environment and installs packages
- `API/testgenai-master/start-server.bat` - Starts the FastAPI backend server

**Frontend:**
- `genaifrontend/setup-frontend.bat` - Installs Node.js dependencies
- `genaifrontend/start-frontend.bat` - Starts the Angular development server

---

## Troubleshooting

### "Python 3.10 is not installed"
- Make sure you installed Python 3.10.4 (not 3.13)
- Make sure you checked "Add Python to PATH" during installation
- Restart your terminal after installation

### "Could not parse vswhere.exe output" during package installation
Install Visual Studio Build Tools:
- Download: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
- Select "Desktop development with C++"
- Install and run setup.bat again

### Backend starts but gives database errors
- Check your `.env` file has correct database credentials
- Make sure your database server is accessible
- Verify the database user has proper permissions

### Frontend can't connect to backend
- Make sure backend is running first (http://localhost:8000)
- Check that no firewall is blocking port 8000

---

## Next Steps

1. Install Python 3.10.4 and Node.js 20.9.0
2. Configure the `.env` file with your credentials
3. Run `setup.bat` in the backend folder
4. Run `setup-frontend.bat` in the frontend folder
5. Start the backend with `start-server.bat`
6. Start the frontend with `start-frontend.bat`
7. Open your browser to http://localhost:4200

---

## Manual Commands (Alternative)

If you prefer manual setup:

**Backend:**
```bash
cd "API\testgenai-master"
py -3.10 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd genaifrontend
npm install
npm start
```
