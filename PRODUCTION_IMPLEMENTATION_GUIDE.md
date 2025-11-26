# DataSense Production-Ready Implementation Guide

## Priority Fixes (Do These First)

### 🔴 Priority 1: Fix "No Response" Issues (Day 1)

#### Fix #1: Add Robust Error Handling to LLM Calls

**File:** `llm/llm_core.py`

Replace the entire `GPT4Strategy` class:

```python
from openai import RateLimitError, APIError, Timeout
import time
import logging

logger = logging.getLogger(__name__)

class GPT4Strategy(LLMStrategy):
    def get_llm_qna_response(self, prompt, max_retries=3):
        """Get LLM response with retry logic and error handling"""
        
        for attempt in range(max_retries):
            try:
                prompt_template = """{question}"""
                
                llm = AzureChatOpenAI(
                    azure_endpoint=settings.azure_openai_endpoint,
                    api_key=settings.azure_openai_api_key,
                    deployment_name=settings.azure_openai_deployment_name,
                    api_version=settings.azure_openai_api_version,
                    temperature=0,
                    request_timeout=60  # Add timeout
                )
                
                llm_chain = LLMChain(
                    llm=llm,
                    prompt=PromptTemplate.from_template(prompt_template)
                )
                
                resp = llm_chain(prompt)
                
                # Validate response
                if not resp or 'text' not in resp or not resp['text'].strip():
                    logger.error(f"Empty LLM response on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return "Error: Unable to generate response. Please try rephrasing your question."
                
                return resp['text']
                
            except Timeout as e:
                logger.error(f"Timeout on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return "Error: Request timed out. Please try again or simplify your question."
                
            except RateLimitError as e:
                logger.error(f"Rate limit on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)  # Wait longer for rate limits
                    continue
                return "Error: Too many requests. Please wait a moment and try again."
                
            except APIError as e:
                logger.error(f"API error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return "Error: Azure OpenAI service error. Please try again."
                
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return f"Error: {str(e)}"
        
        return "Error: Failed after maximum retries. Please contact support."
```

#### Fix #2: Improve SQL Extraction

**File:** `util/util.py`

Replace `extract_sql_from_code_blocks`:

```python
import re
import logging

logger = logging.getLogger(__name__)

def extract_sql_from_code_blocks(text):
    """
    Extract SQL from various LLM response formats.
    Handles: ```sql, ```, plain SQL, or SQL with explanations.
    """
    
    if not text or not isinstance(text, str):
        logger.error("Invalid input to extract_sql_from_code_blocks")
        return None
    
    # Pattern 1: ```sql ... ```
    pattern1 = r'```sql\s*(.*?)\s*```'
    matches = re.findall(pattern1, text, re.DOTALL | re.IGNORECASE)
    if matches:
        sql = matches[0].strip()
        logger.info("Extracted SQL from ```sql block")
        return sql
    
    # Pattern 2: ``` ... ``` (no language tag)
    pattern2 = r'```\s*(SELECT.*?)\s*```'
    matches = re.findall(pattern2, text, re.DOTALL | re.IGNORECASE)
    if matches:
        sql = matches[0].strip()
        logger.info("Extracted SQL from ``` block")
        return sql
    
    # Pattern 3: SQL starting with WITH (for CTEs)
    pattern3 = r'(WITH\s+\w+\s+AS\s*\([\s\S]*?SELECT[\s\S]*?)(?:\n\s*\n|$)'
    matches = re.findall(pattern3, text, re.IGNORECASE)
    if matches:
        sql = matches[0].strip()
        # Clean up trailing text
        sql = re.split(r'\n\s*(?:Explanation|Note|This query)', sql, flags=re.IGNORECASE)[0].strip()
        logger.info("Extracted CTE SQL from plain text")
        return sql
    
    # Pattern 4: Plain SELECT statement
    pattern4 = r'(SELECT[\s\S]*?)(?:\n\s*\n|$)'
    matches = re.findall(pattern4, text, re.IGNORECASE)
    if matches:
        sql = matches[0].strip()
        # Stop at common explanation markers
        sql = re.split(r'\n\s*(?:Explanation|Note|This query|--\s*Explanation)', sql, flags=re.IGNORECASE)[0].strip()
        # Remove trailing semicolons and whitespace
        sql = sql.rstrip(';').strip()
        logger.info("Extracted plain SELECT SQL")
        return sql
    
    # If nothing found, log the full response for debugging
    logger.error(f"Failed to extract SQL. Response preview: {text[:500]}")
    return None


def validate_extracted_sql(sql: str) -> tuple[bool, str]:
    """Validate extracted SQL before execution"""
    
    if not sql or not sql.strip():
        return False, "No SQL query extracted"
    
    sql_upper = sql.upper().strip()
    
    # Must start with valid keyword
    valid_starts = ['SELECT', 'WITH', 'DECLARE']
    if not any(sql_upper.startswith(start) for start in valid_starts):
        return False, f"SQL must start with SELECT, WITH, or DECLARE. Found: {sql[:50]}"
    
    # Check for dangerous operations (read-only protection)
    dangerous = ['DROP', 'DELETE', 'TRUNCATE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'EXEC']
    found_dangerous = [kw for kw in dangerous if kw in sql_upper]
    if found_dangerous:
        return False, f"Query contains forbidden operations: {', '.join(found_dangerous)}"
    
    # Check parentheses balance
    if sql.count('(') != sql.count(')'):
        return False, "Unbalanced parentheses in query"
    
    # Minimum length check
    if len(sql.strip()) < 20:
        return False, "Query too short to be valid"
    
    # Check if it contains FROM clause (basic SQL structure)
    if 'FROM' not in sql_upper and 'SELECT' in sql_upper:
        return False, "SELECT query missing FROM clause"
    
    return True, ""
```

#### Fix #3: Add Validation Before Execution

**File:** `llm/api_handlers.py`

Update `original_question_response` function around line 140:

```python
# After extracting SQL
extracted_sql, is_valid_question = get_llm_response(
    question_id, question_type, prompt, model_to_use, 
    "Original-Answer-SQL-Query-Generation", 
    tables, db_schema, query, ms_sql_prompt, extract_sql=True
)

# ADD THIS VALIDATION BLOCK
if not is_valid_question:
    logger.warning(f"Invalid question detected for question_id: {question_id}")
    return None, "I couldn't generate a valid SQL query for this question. Could you please rephrase it?", False, 0, 0

if not extracted_sql or extracted_sql.startswith("Error:"):
    logger.error(f"SQL extraction failed: {extracted_sql}")
    return None, "I encountered an error generating the SQL query. Please try again.", False, 0, 0

# Validate SQL structure
is_valid_sql, validation_error = validate_extracted_sql(extracted_sql)
if not is_valid_sql:
    logger.error(f"SQL validation failed: {validation_error}")
    logger.error(f"Attempted SQL: {extracted_sql[:500]}")
    
    # Try one more time with more explicit instructions
    retry_prompt = f"""The previous SQL generation failed validation: {validation_error}

Please generate a corrected SQL query following these requirements:
- Must start with SELECT or WITH
- Must include FROM clause
- Must have balanced parentheses
- Must use only tables from the schema

Original question: {query}
Schema: {db_schema}

Generate ONLY the SQL query in ```sql block."""
    
    extracted_sql, _ = get_llm_response(
        question_id, question_type, retry_prompt, model_to_use,
        "SQL-Validation-Retry", tables, db_schema, query, 
        ms_sql_prompt, extract_sql=True
    )
    
    # Validate again
    is_valid_sql, validation_error = validate_extracted_sql(extracted_sql)
    if not is_valid_sql:
        return None, f"Unable to generate valid SQL: {validation_error}", False, 0, 0

# Now execute (existing code continues)
db_response, _, db_error = execute_query_original(...)
```

---

### 🟡 Priority 2: Optimize Prompt (Day 2)

#### Simplified Prompt

**File:** `llm/prompts.py`

Replace `get_ms_sql_prompt()`:

```python
def get_ms_sql_prompt():
    date_info = load_date_range_info()
    
    # Load business rules for reference
    business_rules_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data',
        'business_logic_rules.json'
    )
    
    try:
        with open(business_rules_path, 'r') as f:
            business_rules = json.load(f)
    except:
        business_rules = {}
    
    return f"""You are an MS SQL expert for a credit union data warehouse.

## CORE RULES
1. MS SQL syntax: Use TOP not LIMIT
2. EXACT names only: Never invent column/table names
3. Always join dimensions: Get names not just IDs
4. Match data types: Numeric = no quotes, Text = quotes
5. Date filtering: ALWAYS use dim_date table

## CRITICAL COLUMN NAMING
✅ DO USE:
- open_date_key (in fact_account_opening)
- balance_date_key (in fact_account_balance)
- origination_date_key (in fact_loan_origination)
- member_key, branch_key, product_key (numeric IDs)

❌ NEVER USE:
- open_date (doesn't exist, use open_date_key)
- branch_id (doesn't exist, use branch_key)
- product_open_date_key (products don't have dates)

## DATA PERIOD
Years: {date_info.get('Available_Years')}
Current: Q{date_info.get('Latest_Quarter')} {date_info.get('Latest_Year')}

When user says "current" or "latest":
- WHERE d.year = {date_info.get('Latest_Year')} AND d.quarter = {date_info.get('Latest_Quarter')}

## BUSINESS RULES
New members: (cross_sell_indicator = 0 OR days_since_membership <= 30)
Active branches: is_current = 1 AND is_active = 1
Active members: is_current = 1

## EXAMPLE PATTERN
```sql
SELECT TOP 10
    b.branch_name,  -- name from dimension
    COUNT(DISTINCT f.member_key) AS new_members
FROM fact_account_opening f
INNER JOIN dim_branch b ON f.branch_key = b.branch_key
INNER JOIN dim_date d ON f.open_date_key = d.date_key
WHERE d.year = {date_info.get('Latest_Year')}
  AND d.quarter = {date_info.get('Latest_Quarter')}
  AND b.is_current = 1
GROUP BY b.branch_name
ORDER BY new_members DESC
```

OUTPUT: Return ONLY SQL in ```sql code block. No explanation before or after."""
```

---

### 🟢 Priority 3: Add Monitoring & Logging (Day 3)

#### Enhanced Logging

**File:** Create new `llm/monitoring.py`:

```python
import logging
import time
from functools import wraps
from typing import Any, Callable
import json

logger = logging.getLogger(__name__)

class QueryMetrics:
    """Track query generation metrics"""
    
    def __init__(self):
        self.metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_time': 0,
            'avg_time': 0,
            'llm_errors': 0,
            'sql_extraction_failures': 0,
            'validation_failures': 0,
            'db_execution_errors': 0
        }
    
    def record_success(self, duration: float):
        self.metrics['total_queries'] += 1
        self.metrics['successful_queries'] += 1
        self.metrics['total_time'] += duration
        self.metrics['avg_time'] = self.metrics['total_time'] / self.metrics['total_queries']
    
    def record_failure(self, failure_type: str, duration: float):
        self.metrics['total_queries'] += 1
        self.metrics['failed_queries'] += 1
        self.metrics['total_time'] += duration
        self.metrics[failure_type] += 1
    
    def get_metrics(self) -> dict:
        return self.metrics.copy()
    
    def log_metrics(self):
        logger.info(f"Query Metrics: {json.dumps(self.metrics, indent=2)}")

# Global metrics instance
metrics = QueryMetrics()

def track_query_generation(func: Callable) -> Callable:
    """Decorator to track query generation metrics"""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        question_id = kwargs.get('question_id', args[0] if args else 'unknown')
        
        try:
            logger.info(f"Starting query generation for question_id: {question_id}")
            result = func(*args, **kwargs)
            
            duration = time.time() - start_time
            
            # Check if generation was successful
            if result and len(result) >= 2:
                sql, output = result[0], result[1]
                if sql and not output.startswith("Error"):
                    metrics.record_success(duration)
                    logger.info(f"Query generation successful in {duration:.2f}s for question_id: {question_id}")
                else:
                    metrics.record_failure('failed_queries', duration)
                    logger.warning(f"Query generation failed in {duration:.2f}s for question_id: {question_id}")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            metrics.record_failure('failed_queries', duration)
            logger.error(f"Query generation exception in {duration:.2f}s for question_id: {question_id}: {e}", exc_info=True)
            raise
    
    return wrapper

def log_llm_call(question_id: str, prompt_length: int, response_length: int, duration: float, success: bool):
    """Log LLM API call details"""
    logger.info(f"""LLM Call Summary:
    Question ID: {question_id}
    Prompt Length: {prompt_length} chars
    Response Length: {response_length} chars
    Duration: {duration:.2f}s
    Success: {success}
    Tokens Est: {(prompt_length + response_length) / 4:.0f}
    """)

def log_sql_generation(question_id: str, question: str, sql: str, success: bool, error: str = None):
    """Log SQL generation details"""
    log_data = {
        'question_id': question_id,
        'question': question[:200],  # Truncate for logging
        'sql_length': len(sql) if sql else 0,
        'success': success,
        'error': error
    }
    
    if success:
        logger.info(f"SQL Generated: {json.dumps(log_data)}")
    else:
        logger.error(f"SQL Generation Failed: {json.dumps(log_data)}")
```

#### Use in api_handlers.py

```python
from llm.monitoring import track_query_generation, log_llm_call, log_sql_generation, metrics

@track_query_generation
def original_question_response(question_id, question_type, query, ...):
    # Your existing code
    
    # After LLM call, add logging:
    log_llm_call(
        question_id=question_id,
        prompt_length=len(prompt),
        response_length=len(llm_response),
        duration=time_taken,
        success=bool(extracted_sql)
    )
    
    # After SQL generation:
    log_sql_generation(
        question_id=question_id,
        question=query,
        sql=extracted_sql,
        success=bool(extracted_sql and not db_error),
        error=db_error if db_error else None
    )
```

---

## Configuration Changes

### Update config.py

Add these settings:

```python
class Settings:
    # Existing settings...
    
    # New settings for production
    enable_sql_caching: bool = os.environ.get("ENABLE_SQL_CACHING", "true").lower() == "true"
    cache_ttl_seconds: int = int(os.environ.get("CACHE_TTL_SECONDS", "3600"))
    
    llm_timeout_seconds: int = int(os.environ.get("LLM_TIMEOUT_SECONDS", "60"))
    llm_max_retries: int = int(os.environ.get("LLM_MAX_RETRIES", "3"))
    
    enable_query_validation: bool = os.environ.get("ENABLE_QUERY_VALIDATION", "true").lower() == "true"
    max_query_complexity: str = os.environ.get("MAX_QUERY_COMPLEXITY", "medium")  # simple, medium, complex
    
    # Monitoring
    enable_detailed_logging: bool = os.environ.get("ENABLE_DETAILED_LOGGING", "true").lower() == "true"
    log_llm_prompts: bool = os.environ.get("LOG_LLM_PROMPTS", "false").lower() == "true"
```

### Update .env

```bash
# LLM Configuration
LLM_TIMEOUT_SECONDS=60
LLM_MAX_RETRIES=3

# Caching
ENABLE_SQL_CACHING=true
CACHE_TTL_SECONDS=3600

# Validation
ENABLE_QUERY_VALIDATION=true
MAX_QUERY_COMPLEXITY=medium

# Monitoring
ENABLE_DETAILED_LOGGING=true
LOG_LLM_PROMPTS=false  # Set to true only for debugging

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

---

## Testing Strategy

### 1. Create Test Suite

**File:** `tests/test_sql_generation.py`:

```python
import pytest
from llm.api_handlers import original_question_response
from util.util import extract_sql_from_code_blocks, validate_extracted_sql

class TestSQLGeneration:
    
    def test_simple_query(self):
        """Test simple query generation"""
        question = "Show me top 10 branches"
        # Your test implementation
        assert sql is not None
        assert "SELECT" in sql.upper()
        assert "TOP 10" in sql.upper()
    
    def test_date_filtering(self):
        """Test that current quarter is correctly identified"""
        question = "Show me new members this quarter"
        # Test implementation
        assert "year = 2024" in sql.lower()
        assert "quarter = 4" in sql.lower()
    
    def test_error_handling(self):
        """Test that errors are handled gracefully"""
        question = "Invalid impossible question with tables that don't exist"
        result = original_question_response(...)
        # Should return error message, not crash
        assert result is not None
        
class TestSQLExtraction:
    
    def test_extract_from_code_block(self):
        text = "```sql\nSELECT * FROM table\n```"
        sql = extract_sql_from_code_blocks(text)
        assert sql == "SELECT * FROM table"
    
    def test_extract_plain_sql(self):
        text = "Here's the query: SELECT * FROM table"
        sql = extract_sql_from_code_blocks(text)
        assert sql is not None
    
    def test_validation(self):
        valid_sql = "SELECT * FROM dim_branch"
        is_valid, error = validate_extracted_sql(valid_sql)
        assert is_valid == True
        
        invalid_sql = "DROP TABLE dim_branch"
        is_valid, error = validate_extracted_sql(invalid_sql)
        assert is_valid == False
```

### 2. Run Tests

```bash
pytest tests/ -v --cov=llm --cov=util
```

---

## Deployment Checklist

- [ ] Update all files with error handling
- [ ] Test with 20+ sample questions
- [ ] Enable detailed logging
- [ ] Set up monitoring dashboard
- [ ] Configure alerting for failures
- [ ] Document common error patterns
- [ ] Create runbook for troubleshooting
- [ ] Set up automated health checks
- [ ] Test failover scenarios
- [ ] Load test with concurrent users

---

## Monitoring Dashboard (Application Insights)

### Key Metrics to Track

1. **Success Rate**
   - % of queries that generate valid SQL
   - % of queries that execute successfully
   - % of queries that return results

2. **Performance**
   - Average response time
   - P95 response time
   - LLM API latency
   - Database query execution time

3. **Errors**
   - LLM timeout count
   - SQL extraction failures
   - SQL validation failures
   - Database execution errors

4. **Usage**
   - Queries per minute
   - Unique users
   - Most common questions
   - Most problematic questions

### Sample Query (Application Insights)

```kusto
customEvents
| where name == "QueryGeneration"
| summarize 
    SuccessRate = avg(toreal(customDimensions.Success)),
    AvgDuration = avg(todouble(customDimensions.Duration)),
    ErrorCount = countif(customDimensions.Success == "false")
    by bin(timestamp, 1h)
| render timechart
```

---

## Next Steps

1. **Week 1**: Implement Priority 1 fixes (error handling, validation)
2. **Week 2**: Implement Priority 2 (prompt optimization)
3. **Week 3**: Add monitoring and testing
4. **Week 4**: Load testing and optimization

This should resolve your "no response" and "SQL not generating" issues while making the system production-ready.
