
from datetime import datetime
import json
import os

def load_verified_queries():
    """Load verified working SQL queries from knowledge base"""
    try:
        queries_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'verified_queries.json'
        )
        with open(queries_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  WARNING: Could not load verified_queries.json: {e}")
        return {}

def load_sql_generation_rules():
    """Load SQL generation rules from JSON knowledge base"""
    try:
        rules_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'sql_generation_rules.json'
        )
        with open(rules_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  WARNING: Could not load sql_generation_rules.json: {e}")
        return {}

def load_business_logic_rules():
    """Load business logic rules from JSON knowledge base"""
    try:
        rules_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'business_logic_rules.json'
        )
        with open(rules_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  WARNING: Could not load business_logic_rules.json: {e}")
        return {}

def load_date_range_info():
    """
    Load date range information from JSON file.
    Returns dict with available years, months, quarters, and latest values.
    """
    try:
        date_range_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'date_range.json'
        )
        with open(date_range_path, 'r') as f:
            date_info = json.load(f)

        return date_info
    except Exception as e:
        print(f"⚠️  CRITICAL WARNING: Could not load date_range.json: {e}")
        print(f"⚠️  Using HARDCODED fallback values. UPDATE date_range.json to fix this!")
        return {
            'Latest_Year': '2024',
            'Latest_Month': '12',
            'Latest_Quarter': '4',
            'Available_Years': '2023, 2024',
            'Current_Period': 'Q4 2024 (October, November, December)',
            'Notes': 'FALLBACK VALUES - date_range.json failed to load'
        }


def _get_core_sql_rules():
    """Core SQL generation rules - loaded from knowledge base"""
    sql_rules = load_sql_generation_rules()

    if not sql_rules:
        return "ERROR: Could not load SQL generation rules"

    # Build rules from JSON knowledge base
    rules_text = "CORE RULES:\n"

    # Generic syntax rules
    if 'generic_rules' in sql_rules:
        for category, rules in sql_rules['generic_rules'].items():
            for rule in rules:
                rules_text += f"• {rule}\n"

    # Date handling rules
    if 'date_handling' in sql_rules:
        rules_text += "\nCRITICAL - DATE HANDLING:\n"
        for rule in sql_rules['date_handling']['critical_rules']:
            rules_text += f"❌ " if "NEVER" in rule else f"✅ "
            rules_text += f"{rule}\n"

        pattern = sql_rules['date_handling']['correct_pattern_for_date_filtering']
        rules_text += f"\nCORRECT DATE PATTERN:\n{pattern['sql']}\n"

    # Common mistakes from knowledge base
    if 'common_mistakes' in sql_rules:
        rules_text += "\nCOMMON MISTAKES TO AVOID:\n"

        # Data type errors
        if 'data_type_errors' in sql_rules['common_mistakes']:
            dt_error = sql_rules['common_mistakes']['data_type_errors']
            rules_text += f"❌ WRONG: {dt_error['wrong_pattern']}\n"
            rules_text += f"✅ CORRECT: {dt_error['correct_pattern']}\n"

        # Datetime errors
        if 'datetime_overflow_errors' in sql_rules['common_mistakes']:
            dt_error = sql_rules['common_mistakes']['datetime_overflow_errors']
            rules_text += f"❌ WRONG: {dt_error['wrong_pattern']}\n"
            rules_text += f"✅ CORRECT: {dt_error['correct_pattern']}\n"

        # Column invention
        if 'column_invention' in sql_rules['common_mistakes']:
            col_error = sql_rules['common_mistakes']['column_invention']
            rules_text += f"\nCRITICAL - COLUMN VALIDATION:\n{col_error['rule']}\n"
            rules_text += "Common hallucinations:\n"
            for hallucination in col_error['common_hallucinations']:
                rules_text += f"  • {hallucination}\n"

        # Table invention
        if 'table_invention' in sql_rules['common_mistakes']:
            table_error = sql_rules['common_mistakes']['table_invention']
            rules_text += f"\nCRITICAL - TABLE VALIDATION:\n{table_error['rule']}\n"
            if 'common_hallucinations' in table_error:
                rules_text += "Common table hallucinations:\n"
                for hallucination in table_error['common_hallucinations']:
                    rules_text += f"  • {hallucination}\n"

        # Invalid date joins
        if 'invalid_date_joins' in sql_rules['common_mistakes']:
            date_join_error = sql_rules['common_mistakes']['invalid_date_joins']
            rules_text += f"\n❌ CRITICAL - INVALID DATE JOINS:\n{date_join_error['critical_rule']}\n"
            rules_text += f"✅ {date_join_error['correct_approach']}\n"

        # Date key column validation - prevent hallucination
        if 'date_key_column_validation' in sql_rules['common_mistakes']:
            date_col_error = sql_rules['common_mistakes']['date_key_column_validation']
            rules_text += f"\n❌ CRITICAL - EXACT COLUMN NAMES:\n"
            rules_text += "DO NOT GUESS column names! Common WRONG guesses:\n"
            for hallucination in date_col_error.get('common_hallucinations', []):
                rules_text += f"  ❌ {hallucination}\n"
            if 'correct_column_names' in date_col_error:
                rules_text += "CORRECT column names:\n"
                for table, info in date_col_error['correct_column_names'].items():
                    rules_text += f"  ✅ {table}: use '{info['date_column']}'\n"

        # Date integer arithmetic - prevent type clash errors
        if 'date_integer_arithmetic' in sql_rules['common_mistakes']:
            date_arith_error = sql_rules['common_mistakes']['date_integer_arithmetic']
            rules_text += f"\n❌ CRITICAL - DATE ARITHMETIC:\n{date_arith_error['critical_rule']}\n"
            rules_text += "WRONG: date_column - 0, CAST('2024-12-31' AS DATE) - 0\n"
            rules_text += "CORRECT: Use DATEADD(day, 0, date_column) instead\n"

    return rules_text


def get_output_format_prompt(db_output, user_query):
    return f"Given that for the question '{user_query}', database output is '{db_output}', provide the answer in HTML format without any css code. Add a 'highlight' class to the metrics, column names and any other key entities in the answer. Include a table with the given data with improved names for the column headings. IMPORTANT: Return ONLY the raw HTML content without wrapping it in code blocks or markdown. Do NOT use ```html or ``` tags."


def _get_verified_query_examples():
    """Get relevant verified query examples for the prompt"""
    verified = load_verified_queries()
    if not verified:
        return ""

    # Get critical patterns
    critical_patterns = verified.get('critical_patterns', {})
    column_ref = verified.get('column_reference', {})

    text = "\n🔑 CRITICAL COLUMN REFERENCE (USE EXACT NAMES FROM SCHEMA):\n"
    for table, info in column_ref.items():
        if isinstance(info, dict):
            if 'date_key' in info:
                pk = info.get('primary_key', 'N/A')
                text += f"  • {table}: date_key='{info['date_key']}', primary_key='{pk}'\n"

    # Add hallucination warnings
    hallucinations = verified.get('common_hallucinations', {})
    if hallucinations:
        # Wrong tables
        if 'wrong_tables' in hallucinations:
            text += "\n❌ TABLES THAT DO NOT EXIST:\n"
            for wrong, correct in hallucinations['wrong_tables'].items():
                text += f"  • '{wrong}' ❌ → {correct}\n"

        # Wrong columns
        if 'wrong_columns' in hallucinations:
            text += "\n❌ COMMON WRONG COLUMN NAMES (DO NOT USE):\n"
            for wrong, correct in list(hallucinations['wrong_columns'].items())[:6]:
                text += f"  • '{wrong}' ❌ → {correct}\n"

        # Critical table-column mapping
        if 'critical_table_column_mapping' in hallucinations:
            text += "\n⚠️ CRITICAL - COLUMNS EXIST ONLY IN SPECIFIC TABLES:\n"
            for col, location in hallucinations['critical_table_column_mapping'].items():
                text += f"  • {col}: {location}\n"

    # Add a few verified example queries
    queries = verified.get('verified_queries', [])
    if queries:
        text += "\n📋 VERIFIED WORKING QUERY EXAMPLES:\n"
        # Include first 2 examples as reference
        for q in queries[:2]:
            text += f"\nExample ({q['category']}): {q['question']}\n"
            # Show just key pattern hints
            if 'key_patterns' in q:
                text += f"Key patterns: {', '.join(q['key_patterns'][:2])}\n"

    return text


def get_ms_sql_prompt():
    date_info = load_date_range_info()
    business_rules = load_business_logic_rules()

    # Build business rules from knowledge base
    business_rules_text = ""
    if 'business_rules' in business_rules:
        business_rules_text = "BUSINESS RULES (from knowledge base):\n"
        for rule_name, rule_data in business_rules['business_rules'].items():
            business_rules_text += f"• {rule_data['description']}: {rule_data['sql_pattern']}\n"

    # Build organization identity rules
    org_identity_text = ""
    if 'organization_identity' in business_rules:
        org = business_rules['organization_identity']
        org_identity_text = f"""
🏦 ORGANIZATION IDENTITY:
Our organization is called "{org.get('our_name', 'Our Credit Union')}"
When user says "us", "our", "we", "with us" → they mean Our Credit Union

SQL PATTERNS FOR "US" vs "COMPETITORS":
• Loans WITH us: resulted_in_our_loan = 1
• Loans NOT with us: resulted_in_our_loan = 0
• Lost to competitor: resulted_in_our_loan = 0 AND competitor_key IS NOT NULL
• Still shopping: resulted_in_our_loan = 0 AND competitor_key IS NULL
• Our lender name in data: inquiring_lender = 'Our Credit Union'
"""

    # Build example pattern from knowledge base
    example_pattern = ""
    if 'example_patterns' in load_sql_generation_rules():
        example_pattern = load_sql_generation_rules()['example_patterns'].get('basic_join', '')

    # Get verified query reference
    verified_examples = _get_verified_query_examples()

    return f"""You are an MS SQL expert for a credit union data warehouse.

{_get_core_sql_rules()}
{verified_examples}
{org_identity_text}

DATA PERIOD:
Years: {date_info.get('Available_Years')}
Current: Q{date_info.get('Latest_Quarter')} {date_info.get('Latest_Year')}
Latest Date: {date_info.get('Latest_Year')}-{date_info.get('Latest_Month')}-31

❌ CRITICAL - NEVER USE GETDATE():
- Data ONLY exists through December 31, 2024
- GETDATE() returns current system date (beyond available data)
- For "last N days/months" use: DATEADD(day/month, -N, CAST('2024-12-31' AS DATE))
- WRONG: WHERE d.full_date >= DATEADD(month, -1, GETDATE())
- CORRECT: WHERE d.full_date >= DATEADD(month, -1, CAST('2024-12-31' AS DATE))

When user says "current" or "latest":
- WHERE d.year = {date_info.get('Latest_Year')} AND d.quarter = {date_info.get('Latest_Quarter')}

{business_rules_text}

EXAMPLE PATTERN:
```sql
{example_pattern}
```

IMPORTANT - NEVER SHOW IDs IN RESULTS:
- NEVER return _key or _id columns in SELECT - always JOIN to dimension tables and show descriptive names
- Instead of member_key → JOIN dim_member and show member_name
- Instead of branch_key → JOIN dim_branch and show branch_name
- Instead of product_key → JOIN dim_product and show product_name or product_type
- Instead of competitor_key → JOIN dim_competitor and show competitor_name
- Instead of date_key → JOIN dim_date and show full_date
- Final SELECT must contain human-readable values, NOT numeric IDs/keys

OUTPUT: Return ONLY SQL in ```sql code block. No explanation."""


def get_ms_sql_prompt_for_follow_up():
    date_info = load_date_range_info()

    return f"""Answer the current user question using conversation history and provided schema.

{_get_core_sql_rules()}

DATA PERIOD:
Years: {date_info.get('Available_Years')}
Current: Q{date_info.get('Latest_Quarter')} {date_info.get('Latest_Year')}
Latest Date: {date_info.get('Latest_Year')}-{date_info.get('Latest_Month')}-31

❌ CRITICAL - NEVER USE GETDATE():
- Data ONLY exists through December 31, 2024
- GETDATE() returns current system date (beyond available data)
- For "last N days/months" use: DATEADD(day/month, -N, CAST('2024-12-31' AS DATE))

When user says "current" or "latest":
- WHERE d.year = {date_info.get('Latest_Year')} AND d.quarter = {date_info.get('Latest_Quarter')}

BUSINESS RULES:
- New members: (cross_sell_indicator = 0 OR days_since_membership <= 30)
- Active records: is_current = 1, is_active = 1

IMPORTANT - NEVER SHOW IDs IN RESULTS:
- NEVER return _key or _id columns in SELECT - always JOIN to dimension tables and show descriptive names
- Instead of member_key → JOIN dim_member and show member_name
- Instead of branch_key → JOIN dim_branch and show branch_name
- Instead of product_key → JOIN dim_product and show product_name or product_type
- Instead of competitor_key → JOIN dim_competitor and show competitor_name
- Instead of date_key → JOIN dim_date and show full_date
- Final SELECT must contain human-readable values, NOT numeric IDs/keys

OUTPUT: Return ONLY SQL in ```sql code block. No explanation."""


def get_sql_error_resolve_prompt(db_error, extracted_sql, db_schema):
    sql_rules = load_sql_generation_rules()
    verified = load_verified_queries()

    # Build error-specific guidance from knowledge base
    error_guidance = ""
    if 'error_resolution_patterns' in sql_rules:
        for error_type, pattern in sql_rules['error_resolution_patterns'].items():
            error_guidance += f"\n{pattern['error_pattern']}:\n"
            if 'root_cause' in pattern:
                error_guidance += f"Root cause: {pattern['root_cause']}\n"
            error_guidance += "Fix steps:\n"
            for step in pattern['resolution_steps']:
                error_guidance += f"  {step}\n"

    # Add column reference from verified queries
    column_ref_text = "\n🔑 CORRECT DATE KEY COLUMN NAMES (from verified queries):\n"
    column_ref = verified.get('column_reference', {})
    for table, info in column_ref.items():
        if 'date_key' in info:
            column_ref_text += f"  • {table}: '{info['date_key']}'\n"

    return f"""Fix the SQL error below. Generate ONLY corrected MS SQL query in ```sql code block.

{_get_core_sql_rules()}
{column_ref_text}

ERROR RESOLUTION PATTERNS (from knowledge base):
{error_guidance}

ACTUAL ERROR DETAILS:
Error: {db_error}
Failed Query: {extracted_sql}
DB Schema: {db_schema}

⚠️ IMPORTANT: Check the schema for EXACT column names. Do NOT guess column names.
Common mistakes: account_opening_date_key ❌ → open_date_key ✅

IMPORTANT - NEVER SHOW IDs IN RESULTS:
- NEVER return _key or _id columns in SELECT - JOIN to dimension tables and show descriptive names
- Final SELECT must contain human-readable values, NOT numeric IDs/keys

OUTPUT: Return ONLY corrected SQL in ```sql code block."""


def get_additional_insights_question_generation_prompt(user_query, additional_insights_keywords, db_schema_add):
    return f"""Given user's question: {user_query}

Generate ONE additional insight question related to: {additional_insights_keywords}

CRITICAL: Question MUST be answerable using ONLY tables/columns in this schema: {db_schema_add}

Rules:
- NEVER suggest questions requiring columns not in schema
- Schema shows ALL available columns - don't assume more exist
- Question should be simple and directly answerable

Generate simple, answerable question based on available schema."""


def get_related_questions_generation_prompt(user_query, additional_insights_keywords, db_schema_add):
    return f"""Given user's question: {user_query}

Generate THREE easy follow-up questions related to: {additional_insights_keywords}

CRITICAL: Questions MUST be answerable using ONLY tables/columns in this schema: {db_schema_add}

Rules:
- NEVER suggest questions requiring columns not in schema
- Schema shows ALL available columns
- Questions should be simple and SQL-friendly
- Related to {additional_insights_keywords}

Return as: ["question one", "question two", "question three"]"""
