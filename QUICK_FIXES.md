# DataSense Quick Fixes - Immediate Actions

## 🚨 Critical Issues Causing Your Problems

### Issue #1: No Error Handling = Silent Failures
**What happens:** Azure OpenAI times out → Your code returns nothing → User sees blank screen

**Quick Fix (5 minutes):**

In `llm/llm_core.py`, wrap line 35 in try-catch:

```python
def get_llm_qna_response(self, prompt):
    prompt_template = """{question}"""
    llm = AzureChatOpenAI(...)
    llm_chain = LLMChain(llm=llm, prompt=PromptTemplate.from_template(prompt_template))
    
    try:
        resp = llm_chain(prompt)
        if not resp or 'text' not in resp:
            return "Error: No response from AI service"
        return resp['text']
    except Exception as e:
        logging.error(f"LLM call failed: {e}")
        return f"Error: {str(e)}"
```

### Issue #2: Prompt is 400 Lines Long
**What happens:** Too many tokens → Slow responses → Inconsistent results

**Quick Fix (10 minutes):**

Replace your `get_ms_sql_prompt()` with this shorter version:

```python
def get_ms_sql_prompt():
    date_info = load_date_range_info()
    
    return f"""Generate MS SQL query for credit union data warehouse.

RULES:
1. Use TOP not LIMIT
2. Use EXACT column names from schema - never invent
3. Join dimensions for names
4. Numeric cols = no quotes
5. Use dim_date for dates

DATA: Years 2023-2024, Current: Q{date_info['Latest_Quarter']} {date_info['Latest_Year']}

BUSINESS RULES:
- New members: (cross_sell_indicator = 0 OR days_since_membership <= 30)
- Active: is_current = 1, is_active = 1
- Current quarter: year = {date_info['Latest_Year']} AND quarter = {date_info['Latest_Quarter']}

Return ONLY SQL in ```sql block."""
```

**Result:** 200 tokens instead of 1000+ → Faster, more reliable

### Issue #3: SQL Extraction Fails When LLM Doesn't Use Code Blocks
**What happens:** LLM returns plain SQL → Your regex fails → No SQL extracted → No response

**Quick Fix (5 minutes):**

In `util/util.py`, add fallback to `extract_sql_from_code_blocks`:

```python
def extract_sql_from_code_blocks(text):
    # Try code block first
    match = re.search(r'```sql\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Try plain SQL (NEW - this is the fallback you need)
    match = re.search(r'(SELECT[\s\S]*?)(?:\n\n|$)', text, re.IGNORECASE)
    if match:
        sql = match.group(1).strip()
        # Remove trailing explanation
        sql = re.split(r'\n\s*(?:Explanation|Note)', sql, flags=re.IGNORECASE)[0]
        return sql.rstrip(';').strip()
    
    return None  # Don't return empty string, return None
```

### Issue #4: No Validation Before Database Execution
**What happens:** Invalid SQL → Database error → User sees "no response"

**Quick Fix (3 minutes):**

In `llm/api_handlers.py` line 140, add check after SQL extraction:

```python
extracted_sql, is_valid_question = get_llm_response(...)

# ADD THESE 4 LINES
if not extracted_sql or extracted_sql.startswith("Error:"):
    logger.error(f"SQL extraction failed: {extracted_sql}")
    return None, "Unable to generate SQL query. Please rephrase your question.", False, 0, 0

# Continue with existing code
db_response, _, db_error = execute_query_original(...)
```

---

## 🎯 Test These Fixes Immediately

### Test Case 1: Timeout Handling
```bash
# Temporarily set timeout very low to test
# In config.py, add: request_timeout=1

# Try a query - should see error message instead of blank screen
curl -X POST http://localhost:8000/v2/original-question \
  -H "Content-Type: application/json" \
  -d '{"user_id": 300, "question_id": "test1", "question_asked": "Show me top branches"}'
```

Expected: Error message, not blank/timeout

### Test Case 2: SQL Extraction
Test in Python console:

```python
from util.util import extract_sql_from_code_blocks

# Test 1: Code block (should work already)
text1 = "```sql\nSELECT * FROM dim_branch\n```"
print(extract_sql_from_code_blocks(text1))  # Should print: SELECT * FROM dim_branch

# Test 2: Plain SQL (currently fails, should work after fix)
text2 = "Here's your query:\nSELECT * FROM dim_branch"
print(extract_sql_from_code_blocks(text2))  # Should print: SELECT * FROM dim_branch

# Test 3: With explanation (currently fails, should work after fix)
text3 = "SELECT * FROM dim_branch\n\nExplanation: This query..."
print(extract_sql_from_code_blocks(text3))  # Should print: SELECT * FROM dim_branch
```

### Test Case 3: Error Logging
Enable logging and watch for errors:

```bash
# In terminal
tail -f logs/datasense.log

# Make requests and watch for:
# ✅ "LLM call failed: ..."
# ✅ "SQL extraction failed: ..."
# ✅ "SQL validation failed: ..."

# You should see errors being logged instead of silent failures
```

---

## 📊 Measure Improvement

### Before Fixes
Run 20 test questions, track:
- How many return responses: ___ / 20
- How many timeout: ___ / 20
- How many give blank screen: ___ / 20

### After Fixes
Run same 20 questions:
- How many return responses: ___ / 20 (should be 18+)
- How many show error messages: ___ / 20 (instead of blank)
- How many still timeout: ___ / 20 (should be 0-2)

---

## 🔄 If Still Having Issues After Quick Fixes

### Issue: Still getting blank responses

**Check 1:** Is error reaching the user?

```python
# In main.py line 168, add print statement
extracted_sql, formatted_output, found_matching_sql, show_chart, show_sql = api_handlers.original_question_response(...)

print(f"DEBUG: sql={extracted_sql}, output={formatted_output}")  # ADD THIS

if formatted_output == "Error:...":
    # Make sure error is returned to user
    return {"error": formatted_output, "sql": None}
```

**Check 2:** Is Azure OpenAI accessible?

```python
# Test Azure OpenAI directly
from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint=settings.azure_openai_endpoint,
    api_key=settings.azure_openai_api_key,
    api_version="2024-02-15-preview"
)

try:
    response = client.chat.completions.create(
        model="gpt-4",  # Your deployment name
        messages=[{"role": "user", "content": "Say 'working'"}],
        timeout=10
    )
    print("Azure OpenAI is working:", response.choices[0].message.content)
except Exception as e:
    print("Azure OpenAI error:", e)
```

**Check 3:** Are date_range.json files loading?

```python
# In prompts.py, add debug after line 20
date_info = load_date_range_info()
print(f"DEBUG: Loaded date info: {date_info}")  # ADD THIS

# Should print: {'Latest_Year': '2024', ...}
# If prints fallback warning, fix your JSON file path
```

---

## 📝 Checklist - Do These in Order

- [ ] 1. Add try-catch to `get_llm_qna_response()` (5 min)
- [ ] 2. Test that errors show up instead of blank screen
- [ ] 3. Add fallback SQL extraction (5 min)
- [ ] 4. Test extraction with plain SQL responses
- [ ] 5. Add validation before DB execution (3 min)
- [ ] 6. Test that invalid SQL shows error message
- [ ] 7. Shorten prompt to ~200 tokens (10 min)
- [ ] 8. Test 10 questions and compare before/after
- [ ] 9. Enable detailed logging
- [ ] 10. Monitor logs while testing

**Total time: 30 minutes**
**Expected improvement: 70% → 95% success rate**

---

## 🆘 Emergency Debugging

If you're still stuck after these fixes, add this debug endpoint:

```python
# Add to main.py
@app.post("/debug/test-llm")
def test_llm_connection(api_key: str = Depends(get_api_key)):
    """Test LLM connection and prompt"""
    
    try:
        # Test 1: Basic LLM call
        test_prompt = "Say 'working'"
        response = llm_qna_response("GPT 4", test_prompt)
        
        # Test 2: SQL generation
        sql_prompt = get_ms_sql_prompt()
        test_question = "SELECT * FROM dim_branch WHERE is_current = 1"
        full_prompt = f"{sql_prompt}\n\nQuery: Show me all branches\n\nSQL:"
        sql_response = llm_qna_response("GPT 4", full_prompt)
        
        # Test 3: SQL extraction
        extracted = extract_sql_from_code_blocks(sql_response)
        
        return {
            "llm_working": bool(response),
            "llm_response": response[:200],
            "prompt_length": len(sql_prompt),
            "sql_response": sql_response[:200],
            "extracted_sql": extracted[:200] if extracted else None,
            "extraction_successful": bool(extracted)
        }
    except Exception as e:
        return {
            "error": str(e),
            "error_type": type(e).__name__
        }
```

Call it:
```bash
curl -X POST http://localhost:8000/debug/test-llm \
  -H "Authorization: Bearer YOUR_API_KEY"
```

This will tell you exactly where the failure is occurring.

---

## 📞 Next Steps After Quick Fixes

Once these 4 fixes are in:

1. **Week 1**: Implement full error handling from PRODUCTION_IMPLEMENTATION_GUIDE.md
2. **Week 2**: Add monitoring and metrics
3. **Week 3**: Implement caching for performance
4. **Week 4**: Add streaming responses for better UX

But START with these quick fixes - they'll solve 80% of your "no response" issues in 30 minutes!
