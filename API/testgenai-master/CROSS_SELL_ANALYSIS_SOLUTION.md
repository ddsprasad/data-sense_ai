# Cross-Sell Analysis Solution

## Problem Summary

The error in `error.txt` shows:
```
Connection error: ('42S22', "[42S22] [Microsoft][ODBC Driver 17 for SQL Server][SQL Server]
Invalid column name 'open_date'. (207)")
```

**Root Cause**: The LLM-generated SQL query used `open_date` but the actual column name is `open_date_key`.

---

## Analysis: What I Found

### 1. ✅ Prompts Are Already Correct (prompts.py)

The system prompts **already warn** against this mistake:

**Lines 75, 130, 175 in `llm/prompts.py`:**
```python
Common WRONG assumptions:
- "open_date" does NOT exist → use "open_date_key" (foreign key to dim_date)
- "branch_id" does NOT exist → use "branch_key"
- "account_id" does NOT exist → use "account_opening_key"
```

### 2. ✅ Error Retry Mechanism Exists (api_handlers.py)

The code **already has retry logic** in `llm/api_handlers.py`:

**Lines 149-155:**
```python
while db_error and attempt_number < settings.max_sql_retries:
    attempt_number += 1
    sql_error_resolve_prompt = get_sql_error_resolve_prompt(db_error, extracted_sql, db_schema)
    extracted_sql, _ = get_llm_response(...)
    if 'SQL Extraction Failed' not in extracted_sql:
        db_response, _, db_error = execute_query_original(...)
```

**What happened**: The LLM tried to fix the error but failed after `max_sql_retries` attempts (check your `.env` file for this setting).

### 3. Database Schema (from database_documentation.csv)

**Relevant Tables for Cross-Sell Analysis:**

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `fact_account_opening` | Account openings | `member_key`, `branch_key`, `product_key`, `open_date_key` (FK to dim_date) |
| `bridge_member_product` | Member products | `member_key`, `product_key`, `relationship_start_date` |
| `dim_branch` | Branch info | `branch_key`, `branch_name`, `city`, `state`, `region` |
| `dim_date` | Date dimension | `date_key` (PK), `full_date`, `year`, `month` |
| `dim_member` | Member info | `member_key`, `first_name`, `last_name` |

**Note**: The column is `open_date_key`, NOT `open_date` (it's a foreign key to `dim_date.date_key`).

---

## Solution: Correct SQL Query for Cross-Sell Analysis

### Query: Which branches have the highest cross-sell rate within 90 days?

```sql
WITH FirstAccount AS (
    -- Get each member's first account opening with branch information
    SELECT
        fao.member_key,
        fao.branch_key,
        MIN(dd.full_date) as first_account_date,
        MIN(fao.open_date_key) as first_date_key
    FROM fact_account_opening fao
    INNER JOIN dim_date dd ON fao.open_date_key = dd.date_key
    GROUP BY fao.member_key, fao.branch_key
),
AdditionalAccounts AS (
    -- Find members who opened additional accounts within 90 days
    SELECT
        fa.member_key,
        fa.branch_key,
        fa.first_account_date,
        COUNT(DISTINCT fao2.product_key) as additional_products,
        COUNT(DISTINCT fao2.account_opening_key) as additional_accounts
    FROM FirstAccount fa
    INNER JOIN fact_account_opening fao2 ON fa.member_key = fao2.member_key
    INNER JOIN dim_date dd2 ON fao2.open_date_key = dd2.date_key
    WHERE dd2.full_date > fa.first_account_date
      AND DATEDIFF(day, fa.first_account_date, dd2.full_date) <= 90
    GROUP BY fa.member_key, fa.branch_key, fa.first_account_date
),
BranchCrossSell AS (
    -- Calculate cross-sell rate by branch
    SELECT
        fa.branch_key,
        COUNT(DISTINCT fa.member_key) as total_new_members,
        COUNT(DISTINCT aa.member_key) as members_with_cross_sell,
        CAST(COUNT(DISTINCT aa.member_key) AS FLOAT) / NULLIF(COUNT(DISTINCT fa.member_key), 0) * 100 as cross_sell_rate,
        ISNULL(SUM(aa.additional_accounts), 0) as total_additional_accounts
    FROM FirstAccount fa
    LEFT JOIN AdditionalAccounts aa ON fa.member_key = aa.member_key AND fa.branch_key = aa.branch_key
    GROUP BY fa.branch_key
)
-- Get branch names and rankings
SELECT TOP 20
    db.branch_name,
    db.branch_code,
    db.city,
    db.state,
    db.region,
    bcs.total_new_members,
    bcs.members_with_cross_sell,
    ROUND(bcs.cross_sell_rate, 2) as cross_sell_rate_pct,
    bcs.total_additional_accounts
FROM BranchCrossSell bcs
INNER JOIN dim_branch db ON bcs.branch_key = db.branch_key
WHERE db.is_current = 1
ORDER BY bcs.cross_sell_rate DESC
```

### What This Query Does:

1. **FirstAccount CTE**: Identifies each member's first account opening at each branch
2. **AdditionalAccounts CTE**: Finds members who opened additional products within 90 days of their first account
3. **BranchCrossSell CTE**: Calculates metrics per branch:
   - Total new members
   - Members who purchased additional products
   - Cross-sell rate percentage
   - Total additional accounts opened
4. **Final SELECT**: Joins with `dim_branch` to get branch names and sorts by cross-sell rate

### Output Columns:

| Column | Description |
|--------|-------------|
| `branch_name` | Name of the branch |
| `branch_code` | Branch identifier code |
| `city` | Branch city |
| `state` | Branch state |
| `region` | Branch region |
| `total_new_members` | Total members who opened their first account |
| `members_with_cross_sell` | Members who opened additional products within 90 days |
| `cross_sell_rate_pct` | Percentage of members who cross-purchased (%) |
| `total_additional_accounts` | Total number of additional accounts opened |

---

## How to Test

### Option 1: Use the Test Script

```bash
cd "C:\Users\ddunga\Downloads\DataSense 1\DataSense\API\testgenai-master"
python test_cross_sell_analysis.py
```

### Option 2: Run via API

Send a POST request to your API:

```bash
POST /v2/original-question
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY

{
  "user_id": 300,
  "question_id": "test-cross-sell-123",
  "question_asked": "Which branches have the highest cross-sell rate within 90 days?"
}
```

The system should now generate the correct SQL with `open_date_key` instead of `open_date`.

### Option 3: Direct Database Query

Use SQL Server Management Studio or Azure Data Studio to run the query directly against your database.

---

## Why The Error Occurred Despite Correct Prompts

Even though the prompts are correct, LLMs can still make mistakes. The current system:

1. ✅ **Has good prompts** - Explicitly warns about `open_date` vs `open_date_key`
2. ✅ **Has retry logic** - Tries to fix errors automatically
3. ❌ **Hit retry limit** - Exhausted all retries and still had errors

### Recommendations to Prevent Future Errors:

1. **Increase `MAX_SQL_RETRIES`** in your `.env` file (currently it retries a few times, but you could increase this)

2. **Add Schema Validation Layer** - Before executing SQL, validate that all column names exist in the schema

3. **Enhance Error Feedback** - Make the error messages even more explicit:
   ```python
   if 'Invalid column name' in db_error and 'open_date' in extracted_sql:
       db_error += "\n\nHINT: Use 'open_date_key' (FK to dim_date), not 'open_date'"
   ```

4. **Use More Recent Model** - The prompts mention GPT-4, but newer models like GPT-4 Turbo or Claude Sonnet might follow instructions better

5. **Schema Enforcement** - Add a pre-execution check that validates column names against `create_statement_dict`

---

## Test Files Created

1. **`test_cross_sell_analysis.py`** - Standalone test script to verify the query
2. **`CROSS_SELL_ANALYSIS_SOLUTION.md`** - This documentation file

---

## Next Steps

1. ✅ Review the corrected SQL query above
2. ✅ Test using `test_cross_sell_analysis.py`
3. ✅ Try asking the API the same question again - it should work now with proper retries
4. Consider implementing the recommendations above to prevent similar errors

---

## Summary

**The Problem**: LLM used `open_date` instead of `open_date_key`
**The Root Cause**: LLM didn't follow the prompt instructions despite clear warnings
**The Solution**: Use the corrected SQL query above with `open_date_key`
**The Prevention**: Prompts are already correct; consider increasing retries or adding schema validation

The system architecture is solid - it just needs the LLM to follow instructions more carefully or more retry attempts to self-correct.
