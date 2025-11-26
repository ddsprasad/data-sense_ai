# DataSense Knowledge Base

This directory contains the centralized knowledge base for DataSense's T-SQL generation system. All SQL generation rules, business logic, and error patterns are stored here in JSON format for easy maintenance and growth.

## 📁 Knowledge Base Files

### 1. `sql_generation_rules.json`
**Purpose:** Core T-SQL generation rules, common mistakes, and error resolution patterns

**When to update:**
- Adding new T-SQL syntax rules
- Discovering new common errors and their fixes
- Adding datetime handling patterns
- Documenting column/table naming conventions

**Structure:**
```json
{
  "generic_rules": {
    "syntax": [...],
    "schema_validation": [...],
    "data_types": [...],
    "joins": [...],
    "best_practices": [...]
  },
  "common_mistakes": {
    "data_type_errors": {...},
    "datetime_overflow_errors": {...},
    "column_invention": {...}
  },
  "date_handling": {...},
  "error_resolution_patterns": {...}
}
```

### 2. `business_logic_rules.json`
**Purpose:** Domain-specific business rules for credit union banking

**When to update:**
- Adding new business definitions (e.g., "active member")
- Updating date period rules
- Adding new metrics formulas
- Documenting table usage patterns

**Structure:**
```json
{
  "business_rules": {
    "new_member_acquisition": {...},
    "active_members": {...}
  },
  "date_patterns": {...},
  "common_metrics": {...},
  "table_usage_patterns": {...}
}
```

### 3. `table_keywords.json`
**Purpose:** Keyword-to-table mapping for vector search

**When to update:**
- Adding new tables to the database
- Adding synonyms for existing tables
- Improving keyword matching

### 4. `date_range.json`
**Purpose:** Current data period information

**When to update:**
- When new data is loaded (update Latest_Year, Latest_Quarter, etc.)
- At the start of each quarter/year

## 🔄 How to Grow the Knowledge Base

### Adding New Error Patterns

When you encounter a new SQL error that LLM struggles with:

1. Open `sql_generation_rules.json`
2. Add to `error_resolution_patterns`:
```json
"error_resolution_patterns": {
  "new_error_type": {
    "error_pattern": "Exact error message pattern",
    "root_cause": "Why this error happens",
    "resolution_steps": [
      "1. First step to fix",
      "2. Second step to fix"
    ]
  }
}
```

### Adding New Business Rules

When you add a new business metric or definition:

1. Open `business_logic_rules.json`
2. Add to `business_rules` or `common_metrics`:
```json
"business_rules": {
  "your_new_rule": {
    "description": "What this rule defines",
    "sql_pattern": "WHERE condition here",
    "table": "relevant_table_name"
  }
}
```

### Adding Date Handling Rules

For new date-related patterns:

1. Open `sql_generation_rules.json`
2. Add to `date_handling.critical_rules` array
3. Update `correct_pattern_for_date_filtering` if needed

## ⚠️ Important Rules

### DO NOT hardcode in prompts.py:
- ❌ Specific column names (e.g., `member_name`, `is_active`)
- ❌ Specific table names (e.g., `fact_account_opening`)
- ❌ Business logic SQL patterns
- ❌ Error resolution steps

### DO put in JSON knowledge base:
- ✅ Generic patterns (e.g., "Check CREATE TABLE for column names")
- ✅ Error types and resolution processes
- ✅ Business rule patterns
- ✅ Common mistakes and fixes

## 📝 Maintenance Best Practices

1. **Version Control:** Always commit changes to knowledge base with clear messages
2. **Testing:** After updating JSON files, test with relevant queries
3. **Documentation:** Add comments in JSON using "description" fields
4. **Patterns over Examples:** Use generic patterns, not specific column names
5. **Validation:** Ensure JSON is valid before committing

## 🚀 How Prompts Use Knowledge Base

The system loads knowledge base at runtime:

```python
# In prompts.py
sql_rules = load_sql_generation_rules()
business_rules = load_business_logic_rules()

# Rules are dynamically injected into prompts
prompt = f"""
{_get_core_sql_rules()}  # Loads from sql_generation_rules.json
{business_rules_text}     # Loads from business_logic_rules.json
"""
```

**Benefits:**
- No code changes needed to update rules
- Easy to grow knowledge base
- Centralized source of truth
- Testable and version-controlled

## 📊 Example: Adding a New Error Pattern

**Scenario:** You discover LLMs are generating queries with `ORDER BY` on non-selected columns

1. Open `sql_generation_rules.json`
2. Add to `error_resolution_patterns`:
```json
"order_by_non_selected_column": {
  "error_pattern": "ORDER BY items must appear in the select list",
  "root_cause": "Attempted to ORDER BY a column not in SELECT clause",
  "resolution_steps": [
    "1. Check ORDER BY clause",
    "2. Add missing columns to SELECT list",
    "3. Or remove ORDER BY clause if not needed"
  ]
}
```
3. Test with a failing query
4. Commit changes

## 🎯 Knowledge Base Growth Goals

- **Completeness:** Cover all common SQL errors
- **Clarity:** Clear, actionable resolution steps
- **Maintainability:** Generic patterns, not hardcoded specifics
- **Testability:** Validate rules work with real queries
- **Documentation:** Every rule has a description

---

**Last Updated:** 2025-11-23
**Maintainer:** DataSense Team
