import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Settings:
    # Database configuration
    db_user: str = os.environ.get("DB_USER")
    db_password: str = os.environ.get("DB_PW")
    db_host: str = os.environ.get("DB_HOST")
    db_port: str = os.environ.get("DB_PORT", "1433")
    db_self_name: str = os.environ.get("DB_HISTORY_NAME")
    db_target_name: str = os.environ.get("DB_NAME")

    # Azure OpenAI Configuration
    azure_openai_endpoint: str = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = os.environ.get("AZURE_OPENAI_API_KEY")
    azure_openai_deployment_name: str = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
    azure_openai_api_version: str = os.environ.get("AZURE_OPENAI_API_VERSION")

    # Model configuration
    model_to_use_main: str = os.environ.get("MODEL_TO_USE_MAIN", "GPT 4")
    model_to_use_additional_questions_generation: str = os.environ.get("MODEL_TO_USE_ADDITIONAL_QUESTIONS_GENERATION", "GPT 4")
    model_to_use_output_formatting: str = os.environ.get("MODEL_TO_USE_OUTPUT_FORMATTING", "GPT 4")

    # SQL retries
    max_sql_retries: int = int(os.environ.get("MAX_SQL_RETRIES", "3"))

    # Production settings - LLM
    llm_timeout_seconds: int = int(os.environ.get("LLM_TIMEOUT_SECONDS", "60"))
    llm_max_retries: int = int(os.environ.get("LLM_MAX_RETRIES", "3"))

    # Production settings - Caching
    enable_sql_caching: bool = os.environ.get("ENABLE_SQL_CACHING", "true").lower() == "true"
    cache_ttl_seconds: int = int(os.environ.get("CACHE_TTL_SECONDS", "3600"))

    # Production settings - Validation
    enable_query_validation: bool = os.environ.get("ENABLE_QUERY_VALIDATION", "true").lower() == "true"
    max_query_complexity: str = os.environ.get("MAX_QUERY_COMPLEXITY", "medium")  # simple, medium, complex

    # Production settings - Monitoring
    enable_detailed_logging: bool = os.environ.get("ENABLE_DETAILED_LOGGING", "true").lower() == "true"
    log_llm_prompts: bool = os.environ.get("LOG_LLM_PROMPTS", "false").lower() == "true"

    @property
    def self_database_url(self) -> str:
        return f"mssql+pyodbc://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_self_name}?driver=ODBC+Driver+17+for+SQL+Server"

    @property
    def target_database_url(self) -> str:
        return f"mssql+pyodbc://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_target_name}?driver=ODBC+Driver+17+for+SQL+Server"

settings = Settings()
