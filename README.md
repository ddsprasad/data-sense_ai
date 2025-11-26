# DataSense

**AI-Powered Natural Language to SQL Query Generator for Business Intelligence**

DataSense is an intelligent business intelligence platform that converts natural language questions into SQL queries, enabling non-technical users to extract insights from databases without writing code.

## 🚀 Features

- **Natural Language Processing**: Ask questions in plain English
- **Intelligent SQL Generation**: Converts questions to optimized SQL queries
- **Multiple LLM Support**: GPT-4, GPT-3.5, Claude, Gemini
- **Smart Schema Discovery**: Automatically discovers and understands database structure
- **Follow-up Questions**: Contextual conversation support
- **Chart Generation**: Automatic visualization recommendations
- **Query History**: Track and reuse previous queries
- **Comprehensive Logging**: Full request/response logging for debugging

## 🏗️ Architecture

```
DataSense/
├── API/testgenai-master/          # Backend API
│   ├── llm/                        # LLM integration (prompts, handlers)
│   ├── self_db/                    # History database
│   ├── target_db/                  # Target database connector
│   ├── models/                     # Request/response models
│   ├── middleware/                 # Logging middleware
│   ├── logging_setup/              # Logging configuration
│   ├── data/                       # Configuration & schema files
│   └── main.py                     # FastAPI application
├── genaifrontend/                  # Angular frontend
└── docs/                           # Documentation & fine-tuning data
```

## 📋 Prerequisites

- **Python**: 3.10+
- **Node.js**: 16+ (for frontend)
- **SQL Server**: Database instance
- **API Keys**: Azure OpenAI or OpenAI API key

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/datasense.git
cd datasense
```

### 2. Backend Setup

```bash
cd API/testgenai-master

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your credentials
```

### 3. Frontend Setup

```bash
cd genaifrontend

# Install dependencies
npm install

# Start development server
npm start
```

## 🔧 Configuration

### Environment Variables (.env)

Create a `.env` file in `API/testgenai-master/` with the following:

```env
# Azure OpenAI
USE_AZURE_OPENAI=true
AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# Database
DB_USER=your-db-username
DB_PW=your-db-password
DB_HOST=your-db-host.database.windows.net
DB_NAME=DataSense
DB_HISTORY_NAME=genaipoc_history

# Models
MODEL_TO_USE_MAIN="GPT 4"
MODEL_TO_USE_ADDITIONAL_QUESTIONS_GENERATION="GPT 4"
MODEL_TO_USE_OUTPUT_FORMATTING="GPT 4"
MAX_SQL_RETRIES=3
```

## 🚀 Running the Application

### Start Backend

```bash
cd API/testgenai-master
python main.py
```

Server will start at `http://localhost:8000`

### Start Frontend

```bash
cd genaifrontend
npm start
```

Frontend will start at `http://localhost:4200`

## 📚 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v2/original-question` | POST | Submit a new question |
| `/v2/follow-up-question` | POST | Ask follow-up question |
| `/v2/additional-insights` | POST | Get additional insights |
| `/v2/related-questions` | POST | Get related questions |
| `/v2/user-history` | POST | Get user query history |
| `/v2/get-charts` | POST | Generate chart configuration |

## 🔐 Security

- **Never commit `.env` files** containing credentials
- All API keys are loaded from environment variables
- Database credentials are stored securely in `.env`
- `.gitignore` prevents sensitive files from being committed

## 📊 Logging

The application includes comprehensive logging:

- **General logs**: `logs/datasense.log`
- **Error logs**: `logs/error.log`
- **API requests**: `logs/api_requests.log`
- **SQL queries**: `logs/sql_queries.log`
- **Performance**: `logs/performance.log`

See [LOGGING_GUIDE.md](API/testgenai-master/LOGGING_GUIDE.md) for details.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Your Name** - *Initial work* - [ddsprasad](https://github.com/ddsprasad)

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- LangChain for LLM integration
- OpenAI/Azure for AI models
- All contributors who have helped this project

## 📧 Support

For questions or support, please open an issue on GitHub or contact [your-email@example.com](mailto:your-email@example.com)
