# DataSense Deployment Guide

This guide provides step-by-step instructions for deploying and running the DataSense application.

## Prerequisites

**Required Software:**
- Python 3.10.4
- Node.js 20.9.0
- SQL Server (or access to one)
- ODBC Driver 17 for SQL Server

**Required API Keys:**
- OpenAI API key (for GPT-4/GPT-3.5)
- Google Palm API key (optional, for Gemini)

---

## Deployment Options

### Option 1: Local Development (Recommended for Testing)

#### Step 1: Backend Setup

```bash
# Navigate to backend directory
cd "C:\Users\ddunga\Downloads\DataSense 1\DataSense\API\testgenai-master"

# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
# Edit .env file with your credentials
```

**Update `.env` file:**
```env
# AI Models Configuration
MODEL_TO_USE_MAIN="GPT 4"
MODEL_TO_USE_ADDITIONAL_QUESTIONS_GENERATION="GPT 4"
MODEL_TO_USE_OUTPUT_FORMATTING="GPT 3.5"
MAX_SQL_RETRIES=3

# API Keys - REPLACE WITH YOUR KEYS
OPENAI_API_KEY_DFZ=sk-your-openai-api-key-here
GooglePalmIsHere=your-google-palm-api-key-here

# Database Configuration
DB_USER=your-sql-server-username
DB_PW=your-sql-server-password
DB_HOST=your-sql-server-host
DB_NAME=your-target-database-name
DB_HISTORY_NAME=your-history-database-name
```

**Start the backend:**
```bash
# Option A: Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Option B: Using Python
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run on: `http://localhost:8000`

---

#### Step 2: Frontend Setup

```bash
# Navigate to frontend directory
cd "C:\Users\ddunga\Downloads\DataSense 1\DataSense\genaifrontend"

# Install Node dependencies
npm install

# Start development server
npm start
```

Frontend will run on: `http://localhost:4200`

---

### Option 2: Docker Deployment

```bash
# Navigate to backend directory
cd "C:\Users\ddunga\Downloads\DataSense 1\DataSense\API\testgenai-master"

# Build Docker image
docker build -t datasense-backend .

# Run container
docker run -p 8000:8000 --env-file .env datasense-backend
```

---

### Option 3: Azure Web App Deployment

The project includes GitHub Actions workflow (`master_data-sense.yml`) for automatic deployment to Azure:

1. **Setup Azure Web App** - Create Azure Web App for Python
2. **Configure Secrets** - Add `AZUREAPPSERVICE_PUBLISHPROFILE` to GitHub secrets
3. **Push to master** - Automatic deployment triggers on push to master branch

---

## Important Configuration Notes

### Security Alert:
The `.env` file contains hardcoded credentials. **You must change these before deploying:**

1. **Database credentials** (config.py:7-8) - Currently has hardcoded Azure SQL credentials
2. **OpenAI API keys** (`.env` file) - Replace expired keys with valid ones
3. **SQL user permissions** - Ensure DB user has only SELECT permissions (read-only)

### Database Setup:

You need **two SQL Server databases**:
1. **Target Database** (`DB_NAME`) - Your data source for queries
2. **History Database** (`DB_HISTORY_NAME`) - Stores user questions and analytics

The config.py:31-34 includes a security note that the DB user should have LIMITED permissions (SELECT only, no DELETE/UPDATE).

---

## Verify Setup

Once running, test the connection:

1. **Backend Health Check:**
   - Visit: `http://localhost:8000/docs`
   - You should see the FastAPI Swagger documentation

2. **Frontend:**
   - Visit: `http://localhost:4200`
   - You should see the DataSense login page

3. **API Test:**
   - Use the test API keys configured in the backend for authentication

---

## Troubleshooting

**Backend won't start:**
- Check Python version: `python --version` (needs 3.10.4)
- Verify ODBC Driver 17 is installed
- Check database connectivity

**Frontend won't start:**
- Check Node version: `node --version` (needs 20.9.0)
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`

**API Key Errors:**
- Update `.env` with valid OpenAI API keys
- The keys in the file are expired/invalid

---

## Quick Start Commands

For the fastest local setup:

```bash
# Terminal 1 - Backend
cd "API/testgenai-master"
pip install -r requirements.txt
# Update .env with your credentials
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd "genaifrontend"
npm install
npm start
```

Then open your browser to `http://localhost:4200`
