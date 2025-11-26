# Prompt Enhancement Guide

## Overview

This guide documents the transformation of DataSense prompts from hard-coded to a fully data-driven, maintainable system.

---

## What Changed?

### **Before (prompts.py):**
- ❌ Hard-coded domain knowledge in Python code
- ❌ Repeated rules across multiple prompts
- ❌ Difficult to update (requires code changes)
- ❌ Not reusable for other domains

### **After (prompts_v3.py + JSON configs):**
- ✅ Domain knowledge in JSON files
- ✅ Single source of truth
- ✅ Easy to update (edit JSON, no code changes)
- ✅ Reusable template for any domain/database

---

## New File Structure

```
DataSense/API/testgenai-master/
├── data/
│   ├── date_range.json                      # Temporal context
│   ├── database_documentation.json          # Schema documentation
│   ├── table_keywords.json                  # Keyword → table mapping
│   ├── sql_generation_rules.json            # Generic SQL rules (NEW)
│   ├── business_logic_rules.json            # Business rules & metrics (NEW)
│   └── prompt_structure_template.json       # Prompt assembly guide (NEW)
│
└── llm/
    ├── prompts.py                           # Original (keep for now)
    ├── prompts_v2.py                        # Intermediate version
    └── prompts_v3.py                        # Production-ready (NEW)
```

---

## Key Improvements

### 1. **Separation of Concerns**

| Concern | File | Content |
|---------|------|---------|
| **Generic SQL Rules** | `sql_generation_rules.json` | Syntax, data types, joins, best practices |
| **Business Rules** | `business_logic_rules.json` | Domain-specific patterns, metrics, keyword mapping |
| **Date Context** | `date_range.json` | Available periods, current quarter/year |
| **Schema Details** | `database_documentation.json` | Tables, relationships, usage patterns |
| **Prompt Logic** | `prompts_v3.py` | Assembly only, no hard-coded domain knowledge |

### 2. **Better Structure** (inspired by industry best practices)

```
1. Role Definition          → Who the AI is
2. Database Context         → What data is available
3. Table Usage Patterns     → How to use tables
4. Business Logic Rules     → Domain-specific rules
5. Keyword Mapping          → Natural language → SQL
6. Common Metrics           → Pre-defined calculations
7. SQL Syntax Rules         → Database-specific syntax
8. Date Handling            → Temporal patterns
9. Query Generation Process → Step-by-step guide
10. Validation Checklist    → Quality assurance
11. Output Format           → Expected response structure
12. Error Handling          → How to handle ambiguity
```

### 3. **Dynamic Prompt Assembly**

```python
# OLD: Hard-coded
def get_ms_sql_prompt():
    return """You are an expert MS SQL query builder...
    NEVER INVENT COLUMN NAMES:
    - "open_date" does NOT exist → use "open_date_key"
    - "branch_id" does NOT exist → use "branch_key"
    ..."""

# NEW: Data-driven
def get_ms_sql_prompt():
    configs = load_all_configs()  # Load JSON files
    sections = [
        build_role_definition(configs),
        build_business_rules(configs),
        build_keyword_mapping(configs),
        # ... more sections
    ]
    return "\n\n".join(sections)
```

---

## How to Use the New System

### **Quick Start**

1. **Test the new prompts** (without changing code):
   ```python
   # In Python console
   from llm.prompts_v3 import preview_prompt
   preview_prompt()  # See the generated prompt
   ```

2. **Switch to new prompts**:
   ```python
   # In llm/__init__.py or wherever you import prompts

   # OLD:
   # from llm.prompts import get_ms_sql_prompt, get_sql_error_resolve_prompt

   # NEW:
   from llm.prompts_v3 import get_ms_sql_prompt, get_sql_error_resolve_prompt
   ```

3. **Restart your application**

---

## Configuration Files Guide

### 1. `sql_generation_rules.json`

**Purpose:** Generic SQL best practices (works for any domain)

**When to update:**
- Changing database type (SQL Server → PostgreSQL)
- Adding new SQL syntax rules
- Adding common error patterns

**Example:**
```json
{
  "database_type": "MS SQL Server",
  "schema_type": "Star Schema",
  "generic_rules": {
    "syntax": ["Use TOP instead of LIMIT"],
    "data_types": ["Never compare INT with quoted strings"]
  },
  "common_mistakes": {
    "data_type_errors": {
      "wrong_examples": ["WHERE id = '123'"],
      "correct_examples": ["WHERE id = 123"]
    }
  }
}
```

### 2. `business_logic_rules.json`

**Purpose:** Domain-specific knowledge (credit union banking)

**When to update:**
- Adding new business rules
- Defining new metrics
- Adding keyword mappings
- Updating table usage patterns

**Example:**
```json
{
  "domain": "Credit Union Banking",
  "business_rules": {
    "new_member_acquisition": {
      "description": "Identify new members",
      "sql_pattern": "(cross_sell_indicator = 0 OR days_since_membership <= 30)"
    }
  },
  "keyword_to_table_mapping": {
    "members": ["dim_member"],
    "loans": ["fact_loan_origination"]
  },
  "common_metrics": {
    "total_deposits": {
      "formula": "SUM(current_balance)",
      "from_table": "fact_account_balance"
    }
  }
}
```

### 3. `date_range.json`

**Purpose:** Available data periods

**When to update:** Monthly or when new data is loaded

**Example:**
```json
{
  "Latest_Year": "2024",
  "Latest_Month": "12",
  "Latest_Quarter": "4",
  "Available_Years": "2023, 2024",
  "Current_Period": "Q4 2024 (October, November, December)"
}
```

---

## Migration Checklist

- [ ] Review generated prompt using `preview_prompt()`
- [ ] Test with sample questions
- [ ] Compare results with old prompts
- [ ] Update imports to use `prompts_v3`
- [ ] Test error resolution with known failing queries
- [ ] Monitor for any regressions
- [ ] Update business logic in JSON as needed
- [ ] Remove old `prompts.py` after validation (optional)

---

## Benefits of New System

### For Developers:
- ✅ **Faster updates**: Edit JSON, not Python code
- ✅ **No code changes**: Update business rules without touching code
- ✅ **Better testing**: Preview prompts without running full app
- ✅ **Version control**: Easy to track changes in JSON files

### For Product/Business:
- ✅ **Domain experts can update**: JSON is human-readable
- ✅ **Faster iteration**: Change metrics without developer involvement
- ✅ **Documentation**: JSON files serve as business logic documentation
- ✅ **Audit trail**: See what rules changed over time

### For Maintenance:
- ✅ **Single source of truth**: One place to update each rule
- ✅ **Consistency**: Same rules applied across all prompts
- ✅ **Extensibility**: Easy to add new sections
- ✅ **Reusability**: Template works for other domains

---

## Common Tasks

### Update a Business Rule

```json
// In business_logic_rules.json
{
  "business_rules": {
    "active_accounts": {
      "sql_pattern": "account_status = 'Active' AND close_date IS NULL"
      // Changed from: "account_status = 'Active'"
    }
  }
}
```

### Add a New Metric

```json
// In business_logic_rules.json
{
  "common_metrics": {
    "loan_approval_rate": {
      "description": "Percentage of loan applications approved",
      "formula": "COUNT(approved) / COUNT(total) * 100",
      "from_table": "fact_loan_origination"
    }
  }
}
```

### Add New Keyword Mapping

```json
// In business_logic_rules.json
{
  "keyword_to_table_mapping": {
    "delinquent loans": ["fact_loan_payment"],
    "past due": ["fact_loan_payment"]
  }
}
```

### Update Date Range (Monthly Task)

```json
// In date_range.json
{
  "Latest_Year": "2025",
  "Latest_Month": "1",
  "Latest_Quarter": "1",
  "Current_Period": "Q1 2025 (January, February, March)"
}
```

---

## Testing

```python
# Test prompt generation
from llm.prompts_v3 import preview_prompt
preview_prompt()

# Test individual sections
from llm.prompts_v3 import load_all_configs, build_business_rules
configs = load_all_configs()
print(build_business_rules(configs))

# Test with actual query generation
from llm.prompts_v3 import get_ms_sql_prompt
prompt = get_ms_sql_prompt()
# Use this prompt with your LLM
```

---

## Troubleshooting

### Issue: Prompt looks incomplete

**Solution:** Check that all JSON files are present and valid JSON

```bash
# Validate JSON files
cd data/
python -m json.tool sql_generation_rules.json
python -m json.tool business_logic_rules.json
```

### Issue: Missing sections in prompt

**Solution:** Check section builders in `prompts_v3.py`. Each JSON field should have a corresponding builder function.

### Issue: Error loading JSON files

**Solution:** Check file paths and permissions

```python
from llm.prompts_v3 import load_all_configs
configs = load_all_configs()
print(configs)  # Should show loaded data, not empty dicts
```

---

## Next Steps

1. **Review** the generated prompt
2. **Test** with sample questions
3. **Migrate** production to use `prompts_v3.py`
4. **Monitor** performance and accuracy
5. **Iterate** on business rules in JSON
6. **Document** any domain-specific patterns you discover

---

## Questions?

- Check `prompt_structure_template.json` for the overall design
- See `prompts_v3.py` for implementation details
- Review JSON files in `data/` for configuration examples

---

**Version:** 3.0
**Last Updated:** 2025-01-22
**Author:** Claude Code
