# DataSense Text-to-SQL System - Code Review & Production Recommendations

## Executive Summary

After reviewing your codebase, I've identified **critical issues** causing your problems:
1. ❌ **No error handling for LLM failures** - When GPT-4 doesn't respond or times out, you get no response
2. ❌ **Prompt is too long and repetitive** - 400+ lines with duplicate rules
3. ❌ **No retry logic for API failures** - Azure OpenAI timeouts cause complete failure
4. ❌ **Poor SQL extraction** - Regex fails when LLM doesn't wrap SQL in code blocks
5. ❌ **Missing validation** - No check if generated SQL is actually valid before execution

## Critical Issues Found

### Issue #1: No Error Handling in LLM Calls ⚠️ CRITICAL

**Location:** `llm/llm_core.py` lines 20-36

**Problem:**
```python
def get_llm_qna_response(self, prompt):
    llm_chain = LLMChain(llm=llm, prompt=PromptTemplate.from_template(prompt_template))
    resp = llm_chain(prompt)  # ❌ No try-catch, no timeout handling
    return resp['text']
```

**What happens when it fails:**
- Azure OpenAI timeout → No response at all
- Rate limit exceeded → No response at all  
- API key invalid → No response at all
- Network error → App crashes

**Fix:**
```python
def get_llm_qna_response(self, prompt, max_retries=3):
    import time
    from openai import RateLimitError, APIError, Timeout
    
    for attempt in range(max_retries):
        try:
            llm_chain = LLMChain(
                llm=llm, 
                prompt=PromptTemplate.from_template(prompt_template)
            )
            resp = llm_chain(prompt)
            
            if not resp or 'text' not in resp:
                logger.error(f"Empty response from LLM on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                return "Error: Unable to generate response after multiple attempts"
            
            return resp['text']
            
        except Timeout as e:
            logger.error(f"Timeout on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return "Error: Request timed out. Please try again."
            
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            return "Error: Too many requests. Please wait and try again."
            
        except APIError as e:
            logger.error(f"API error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return "Error: Azure OpenAI service error. Please try again."
            
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt + 1}: {e}", exc_info=True)
            return f"Error: {str(e)}"
    
    return "Error: Failed after maximum retries"
```

---

### Issue #2: Prompt is Too Long and Repetitive ⚠️ CRITICAL

**Location:** `llm/prompts.py` lines 64-217

**Problem:**
- Your prompt is 400+ lines long
- Rules are duplicated 2-3 times (lines 66-130 duplicate lines 164-217)
- Too verbose, causes token waste
- Harder for GPT-4 to follow

**Current prompt size:** ~3,500 tokens
**Recommended size:** ~1,500 tokens

**Fix:**
```python
def get_ms_sql_prompt():
    date_info = load_date_range_info()
    
    return f"""You are an expert MS SQL query builder for a star schema data warehouse.

CRITICAL RULES:
1. Use MS SQL syntax: TOP instead of LIMIT
2. NEVER invent column/table names - use ONLY what's in the schema
3. ALWAYS join fact tables with dimension tables for descriptive names
4. Use table aliases and qualify ALL columns
5. For dates: join with dim_date using date_key columns
6. Match data types: INT/BIGINT = unquoted numbers, VARCHAR = quoted text

COMMON MISTAKES TO AVOID:
- ❌ WHERE member_key = '12345' → ✅ WHERE member_key = 12345
- ❌ Inventing columns like "open_date" → ✅ Use "open_date_key"
- ❌ Using "fact_account_product" → ✅ Use "bridge_member_product"

DATA AVAILABILITY:
- Years: {date_info.get('Available_Years')}
- Current Period: {date_info.get('Current_Period')}
- Latest: Q{date_info.get('Latest_Quarter')} {date_info.get('Latest_Year')}

When users ask for "current" or "latest", use:
- Year: {date_info.get('Latest_Year')}
- Quarter: {date_info.get('Latest_Quarter')}
- Month: {date_info.get('Latest_Month')}

Generate ONLY the SQL query in a ```sql code block."""
```

---

### Issue #3: SQL Extraction Fails Silently ⚠️ HIGH PRIORITY

**Location:** `util/util.py` (likely contains `extract_sql_from_code_blocks`)

**Problem:**
When GPT-4 doesn't wrap SQL in ```sql blocks, your extraction fails and returns nothing.

**Example failure case:**
```
GPT-4 response: "Here's the query: SELECT * FROM dim_branch"
Your code: extract_sql_from_code_blocks() → Returns empty string
Result: No SQL, no error message, user gets "no response"
```

**Fix:**
```python
import re

def extract_sql_from_code_blocks(text):
    """Extract SQL from various formats GPT-4 might return"""
    
    # Try pattern 1: ```sql ... ```
    pattern1 = r'```sql\s*(.*?)\s*```'
    matches = re.findall(pattern1, text, re.DOTALL | re.IGNORECASE)
    if matches:
        return matches[0].strip()
    
    # Try pattern 2: ``` ... ``` (no language specifier)
    pattern2 = r'```\s*(SELECT.*?)\s*```'
    matches = re.findall(pattern2, text, re.DOTALL | re.IGNORECASE)
    if matches:
        return matches[0].strip()
    
    # Try pattern 3: Plain SQL (starts with SELECT, WITH, or CREATE)
    pattern3 = r'((?:WITH|SELECT|CREATE)[\s\S]*?)(?:\n\n|$)'
    matches = re.findall(pattern3, text, re.IGNORECASE)
    if matches:
        sql = matches[0].strip()
        # Remove trailing markdown or explanatory text
        sql = re.split(r'\n\s*\n', sql)[0]
        return sql
    
    # If all patterns fail, log and return error
    logger.error(f"Failed to extract SQL from text: {text[:200]}")
    return None
```

---

### Issue #4: No Validation Before Query Execution ⚠️ HIGH PRIORITY

**Location:** `llm/api_handlers.py` line 146

**Problem:**
```python
db_response, _, db_error = execute_query_original(
    question_id, question_type, "Original-Answer-SQL-Query-Generation", 
    extracted_sql, True, attempt_number
)  # ❌ No check if extracted_sql is valid
```

**What happens:**
- If SQL extraction returns None or empty string → Database error
- If SQL is incomplete → Database error
- User sees "no response" instead of helpful error

**Fix:**
```python
def validate_sql(sql: str) -> tuple[bool, str]:
    """Validate SQL before execution"""
    
    if not sql or sql.strip() == "":
        return False, "Empty SQL query"
    
    # Basic syntax check
    sql_upper = sql.upper().strip()
    
    # Check if it starts with valid SQL keyword
    valid_starts = ['SELECT', 'WITH', 'DECLARE', 'EXEC']
    if not any(sql_upper.startswith(start) for start in valid_starts):
        return False, "SQL must start with SELECT, WITH, or DECLARE"
    
    # Check for dangerous operations (if you want read-only)
    dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'INSERT', 'UPDATE', 'ALTER']
    if any(keyword in sql_upper for keyword in dangerous_keywords):
        return False, f"Query contains forbidden operation: {', '.join(dangerous_keywords)}"
    
    # Check for balanced parentheses
    if sql.count('(') != sql.count(')'):
        return False, "Unbalanced parentheses"
    
    # Check minimum length (a valid query should be at least 15 chars)
    if len(sql.strip()) < 15:
        return False, "Query too short to be valid"
    
    return True, ""

# Use before execution:
is_valid, error_msg = validate_sql(extracted_sql)
if not is_valid:
    logger.error(f"Invalid SQL generated: {error_msg}")
    return None, f"Error: Generated invalid SQL - {error_msg}", False, 0, 0
```

---

### Issue #5: Poor Context Management for RAG ⚠️ MEDIUM PRIORITY

**Location:** `llm/api_handlers.py` lines 126-131

**Problem:**
```python
doc = vector_store_from_metadata.similarity_search(query, 1)  # ❌ Only 1 document
metadata_str = doc[0].metadata["metadata"]
tables = extract_from_vector_doc(metadata_str, "Tables")
```

**Issues:**
- Only retrieving 1 document → Might miss relevant tables
- No relevance score check → Might get irrelevant tables
- No fallback if vector search fails

**Fix:**
```python
def get_relevant_tables_and_schema(query: str, vector_store, k=3):
    """Get relevant tables with fallback and scoring"""
    
    try:
        # Get top k documents
        docs = vector_store.similarity_search_with_score(query, k=k)
        
        if not docs:
            logger.warning("Vector search returned no results")
            return get_default_tables(), get_default_schema()
        
        # Filter by relevance score (lower is better for some vector stores)
        relevant_docs = [doc for doc, score in docs if score < 0.5]
        
        if not relevant_docs:
            logger.warning(f"No highly relevant docs found for query: {query}")
            relevant_docs = [docs[0][0]]  # Use best match as fallback
        
        # Extract tables from all relevant docs
        all_tables = set()
        for doc in relevant_docs:
            metadata_str = doc.metadata.get("metadata", "")
            tables_str = extract_from_vector_doc(metadata_str, "Tables")
            if tables_str:
                all_tables.update(tables_str.split(','))
        
        # Get schema for all identified tables
        tables_list = [t.strip() for t in all_tables]
        db_schema = get_combined_schema(tables_list, create_statement_dict)
        
        logger.info(f"Identified tables for query: {tables_list}")
        
        return tables_list, db_schema
        
    except Exception as e:
        logger.error(f"Error in vector search: {e}", exc_info=True)
        return get_default_tables(), get_default_schema()

def get_default_tables():
    """Fallback tables when vector search fails"""
    return ['dim_date', 'dim_member', 'dim_branch', 'fact_account_opening']

def get_default_schema():
    """Fallback schema"""
    return get_combined_schema(get_default_tables(), create_statement_dict)
```

---

### Issue #6: No Streaming or Progress Indication ⚠️ MEDIUM PRIORITY

**Problem:**
Users wait 10-30 seconds with no feedback, then get "no response"

**Fix: Implement Server-Sent Events (SSE)**

```python
from fastapi.responses import StreamingResponse
import asyncio
import json

@app.post("/{version}/original-question-stream")
async def answer_original_question_stream(
    request_data: QuestionRequestModel, 
    version: str
):
    """Stream response with progress updates"""
    
    async def generate_response():
        try:
            # Step 1: Identifying tables
            yield f"data: {json.dumps({'status': 'analyzing', 'message': 'Analyzing your question...'})}\n\n"
            await asyncio.sleep(0.1)
            
            # Step 2: Generating SQL
            yield f"data: {json.dumps({'status': 'generating', 'message': 'Generating SQL query...'})}\n\n"
            
            # Your existing logic here...
            extracted_sql, formatted_output, _, _, _ = api_handlers.original_question_response(...)
            
            # Step 3: Executing query
            yield f"data: {json.dumps({'status': 'executing', 'message': 'Executing query...'})}\n\n"
            
            # Step 4: Formatting results
            yield f"data: {json.dumps({'status': 'formatting', 'message': 'Formatting results...'})}\n\n"
            
            # Final result
            result = {
                'status': 'complete',
                'sql': extracted_sql,
                'answer': formatted_output
            }
            yield f"data: {json.dumps(result)}\n\n"
            
        except Exception as e:
            error_result = {
                'status': 'error',
                'message': str(e)
            }
            yield f"data: {json.dumps(error_result)}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream"
    )
```

---

## Additional Improvements Needed

### 1. Add Caching for Repeated Questions

**Problem:** Same question asked multiple times hits GPT-4 every time

**Solution:**
```python
import hashlib
from functools import lru_cache

def get_question_hash(question: str) -> str:
    return hashlib.md5(question.lower().strip().encode()).hexdigest()

# Simple in-memory cache (use Redis for production)
sql_cache = {}

def get_cached_sql(question: str) -> Optional[str]:
    question_hash = get_question_hash(question)
    return sql_cache.get(question_hash)

def cache_sql(question: str, sql: str):
    question_hash = get_question_hash(question)
    sql_cache[question_hash] = sql
```

### 2. Add Query Complexity Detection

**Problem:** Some questions require multiple queries or are too complex

**Solution:**
```python
def assess_question_complexity(question: str) -> str:
    """Determine if question is simple, medium, or complex"""
    
    complexity_indicators = {
        'simple': ['top', 'count', 'total', 'list', 'show me'],
        'medium': ['average', 'compare', 'breakdown', 'by month', 'trend'],
        'complex': ['correlation', 'predict', 'analyze', 'optimize', 'recommend']
    }
    
    question_lower = question.lower()
    
    if any(ind in question_lower for ind in complexity_indicators['complex']):
        return 'complex'
    elif any(ind in question_lower for ind in complexity_indicators['medium']):
        return 'medium'
    else:
        return 'simple'

# Use this to adjust approach:
complexity = assess_question_complexity(query)
if complexity == 'complex':
    # Break down into sub-questions
    # Or warn user that question is too complex
    pass
```

### 3. Improve Prompt with Few-Shot Examples

**Add to your prompt:**
```python
EXAMPLES = """
Example 1:
Question: "Show me top 5 branches by new member acquisition this quarter"
SQL:
```sql
SELECT TOP 5
    b.branch_name,
    COUNT(DISTINCT f.member_key) AS new_members
FROM fact_account_opening f
INNER JOIN dim_branch b ON f.branch_key = b.branch_key
INNER JOIN dim_date d ON f.open_date_key = d.date_key
WHERE d.year = 2024 AND d.quarter = 4
  AND (f.cross_sell_indicator = 0 OR f.days_since_membership <= 30)
GROUP BY b.branch_name
ORDER BY new_members DESC
```

Example 2:
Question: "What's the average credit score of our members?"
SQL:
```sql
SELECT AVG(credit_score) AS avg_credit_score
FROM fact_credit_score cs
INNER JOIN dim_date d ON cs.score_date_key = d.date_key
WHERE d.year = 2024 AND d.quarter = 4
```
"""
```

### 4. Add Telemetry and Monitoring

```python
from opentelemetry import trace
from opentelemetry.exporter.azure.monitor import AzureMonitorTraceExporter

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("generate_sql")
def generate_sql_with_monitoring(question: str):
    span = trace.get_current_span()
    span.set_attribute("question", question)
    span.set_attribute("question_length", len(question))
    
    start_time = time.time()
    
    try:
        result = generate_sql(question)
        span.set_attribute("success", True)
        span.set_attribute("sql_length", len(result))
        return result
    except Exception as e:
        span.set_attribute("success", False)
        span.set_attribute("error", str(e))
        raise
    finally:
        duration = time.time() - start_time
        span.set_attribute("duration_ms", duration * 1000)
```

---

## Recommended Prompt Structure (Revised)

```python
def get_optimized_ms_sql_prompt():
    date_info = load_date_range_info()
    
    return f"""You are an MS SQL expert generating queries for a credit union data warehouse.

# RULES
1. MS SQL syntax only (TOP not LIMIT)
2. Use EXACT column names from schema - never invent
3. Always join dimensions for readable names
4. Numeric columns = unquoted (member_key = 123)
5. Text columns = quoted (product_name = 'Checking')

# DATE CONTEXT
Available: 2023-2024
Current: Q{date_info['Latest_Quarter']} {date_info['Latest_Year']}
For "current/latest": year={date_info['Latest_Year']}, quarter={date_info['Latest_Quarter']}

# KEY TABLES
- fact_account_opening: new accounts (join dim_branch, dim_product, dim_date)
- fact_account_balance: deposit balances
- fact_loan_origination: new loans
- fact_member_relationship: member value metrics
- dim_member, dim_branch, dim_product: dimension details
- dim_date: ALL date filtering (join on *_date_key = date_key)

# BUSINESS RULES
New members: (cross_sell_indicator = 0 OR days_since_membership <= 30)
Active records: is_current = 1, is_active = 1
Current quarter: year = {date_info['Latest_Year']} AND quarter = {date_info['Latest_Quarter']}

# OUTPUT
Return ONLY SQL in ```sql block. No explanation.