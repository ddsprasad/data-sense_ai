"""
Two-Stage SQL Generation
------------------------
Stage 1: Identify relevant tables and columns for the query
Stage 2: Generate SQL using ONLY those validated tables/columns

This prevents hallucination by constraining the LLM to use only verified schema elements.
"""

import json
from typing import Dict, List, Tuple, Optional
from llm.schema_intelligence import SchemaIntelligence
from llm.llm_core import get_llm_response


def get_table_column_selection_prompt(query: str, available_schemas: List[Dict]) -> str:
    """
    Generate prompt for Stage 1: Table and column selection.
    """
    schema_info = ""
    for schema in available_schemas:
        schema_info += f"""
TABLE: {schema['table_name']}
COLUMNS: {', '.join(schema['columns'])}
---
"""

    return f"""You are a database schema expert. Your task is to identify which tables and columns are needed to answer a question.

AVAILABLE TABLES AND COLUMNS:
{schema_info}

USER QUESTION: {query}

TASK: Identify the EXACT tables and columns needed. ONLY use columns that exist in the list above.

NOTE: If this is a FOLLOW-UP question with an ORIGINAL SQL provided, make sure to include all tables from the original SQL plus any additional tables needed for the follow-up.

Return your answer as JSON:
{{
    "tables": ["table1", "table2"],
    "columns": {{
        "table1": ["col1", "col2"],
        "table2": ["col3", "col4"]
    }},
    "joins": [
        {{"from": "table1.col", "to": "table2.col"}}
    ],
    "reasoning": "Brief explanation"
}}

CRITICAL: Only include columns that EXACTLY match the available columns listed above. Do not invent or guess column names."""


def get_constrained_sql_prompt(
    query: str,
    selected_tables: List[str],
    selected_columns: Dict[str, List[str]],
    join_info: List[Dict],
    full_schemas: str
) -> str:
    """
    Generate prompt for Stage 2: Constrained SQL generation.
    """
    columns_list = ""
    for table, cols in selected_columns.items():
        columns_list += f"  {table}: {', '.join(cols)}\n"

    joins_list = ""
    for join in join_info:
        joins_list += f"  - {join.get('from', '')} = {join.get('to', '')}\n"

    return f"""You are an MS SQL expert. Generate a SQL query using ONLY the pre-selected tables and columns below.

CONSTRAINT: You MUST use ONLY these tables and columns. Do NOT use any other columns.

SELECTED TABLES: {', '.join(selected_tables)}

SELECTED COLUMNS (use ONLY these):
{columns_list}

SUGGESTED JOINS:
{joins_list}

FULL SCHEMA REFERENCE:
{full_schemas}

USER QUESTION: {query}

FOLLOW-UP QUESTION HANDLING:
- If this contains "FOLLOW-UP QUESTION" and "ORIGINAL SQL", use the ORIGINAL SQL as your starting point
- Modify the original SQL to answer the follow-up question
- Keep the same table joins and structure where applicable
- Add/modify GROUP BY, WHERE, or SELECT as needed for the follow-up

CRITICAL RULES:
1. Use ONLY columns from the SELECTED COLUMNS list above
2. Use date_key columns to join with dim_date (e.g., open_date_key, inquiry_date_key)
3. For date filtering use: DATEADD(day, -N, CAST('2024-12-31' AS DATE))
4. NEVER use GETDATE()
5. For "with us" or "our": resulted_in_our_loan = 1 (only in fact_credit_inquiry)
6. For active members: is_current = 1 (only in dim_member)

IMPORTANT - NEVER SHOW IDs IN RESULTS:
7. NEVER return _key or _id columns in SELECT - always JOIN to dimension tables and show the descriptive name/value instead
8. Instead of member_key → JOIN dim_member and show member_name or relevant member info
9. Instead of branch_key → JOIN dim_branch and show branch_name
10. Instead of product_key → JOIN dim_product and show product_name or product_type
11. Instead of competitor_key → JOIN dim_competitor and show competitor_name
12. Instead of date_key → JOIN dim_date and show full_date or formatted date
13. The final SELECT should contain human-readable values, NOT numeric IDs/keys

Return ONLY the SQL query in a ```sql code block. No explanation."""


def two_stage_sql_generation(
    question_id: str,
    question_type: str,
    query: str,
    schema_intelligence: SchemaIntelligence,
    model: str = "GPT 4"
) -> Tuple[str, bool, str]:
    """
    Two-stage SQL generation process.

    Args:
        question_id: Unique question identifier
        question_type: Type of question
        query: User's natural language query
        schema_intelligence: SchemaIntelligence instance
        model: LLM model to use

    Returns:
        Tuple of (generated_sql, is_valid, validation_message)
    """
    # Stage 1: Get relevant schemas using FAISS
    relevant_schemas = schema_intelligence.get_relevant_schemas(query, top_k=6)

    # Stage 1: Ask LLM to select tables and columns
    selection_prompt = get_table_column_selection_prompt(query, relevant_schemas)

    selection_response, _ = get_llm_response(
        question_id,
        question_type,
        selection_prompt,
        "GPT 4",  # Use GPT-4 for better reasoning
        "Schema-Selection-Stage-1",
        None, None, query, None,
        extract_sql=False
    )

    # Parse the selection response
    try:
        # Extract JSON from response
        json_match = selection_response
        if "```json" in selection_response:
            json_match = selection_response.split("```json")[1].split("```")[0]
        elif "```" in selection_response:
            json_match = selection_response.split("```")[1].split("```")[0]

        selection = json.loads(json_match.strip())
        selected_tables = selection.get("tables", [])
        selected_columns = selection.get("columns", {})
        join_info = selection.get("joins", [])
    except (json.JSONDecodeError, IndexError) as e:
        # Fallback: use all relevant tables from FAISS
        selected_tables = [s["table_name"] for s in relevant_schemas]
        selected_columns = {s["table_name"]: s["columns"] for s in relevant_schemas}
        join_info = []

    # Validate selected columns actually exist
    validated_columns = {}
    for table, columns in selected_columns.items():
        table_upper = table.upper()
        if table_upper in schema_intelligence.table_columns:
            valid_cols = set(schema_intelligence.table_columns[table_upper])
            validated_columns[table] = [c for c in columns if c.lower() in valid_cols]

    # Get full schema for selected tables
    full_schemas = schema_intelligence.get_schema_context_for_tables(selected_tables)

    # Stage 2: Generate SQL with constraints
    sql_prompt = get_constrained_sql_prompt(
        query,
        selected_tables,
        validated_columns,
        join_info,
        full_schemas
    )

    sql_response, _ = get_llm_response(
        question_id,
        question_type,
        sql_prompt,
        model,
        "Constrained-SQL-Generation-Stage-2",
        ",".join(selected_tables),
        full_schemas,
        query,
        None,
        extract_sql=True
    )

    # Validate the generated SQL
    is_valid, errors = schema_intelligence.validate_sql(sql_response)

    if not is_valid:
        # Try to auto-fix
        fixed_sql, remaining_errors = schema_intelligence.fix_invalid_sql(sql_response, errors)

        if remaining_errors:
            # Re-validate fixed SQL
            is_valid, errors = schema_intelligence.validate_sql(fixed_sql)
            if is_valid:
                return fixed_sql, True, "SQL auto-corrected and validated"
            else:
                return fixed_sql, False, f"Validation errors: {'; '.join(errors)}"
        else:
            return fixed_sql, True, "SQL auto-corrected and validated"

    return sql_response, True, "SQL validated successfully"


def validate_and_fix_sql(
    sql: str,
    schema_intelligence: SchemaIntelligence,
    question_id: str,
    question_type: str,
    query: str,
    model: str = "GPT 4"
) -> Tuple[str, bool, str]:
    """
    Validate SQL and attempt to fix if invalid.

    Args:
        sql: SQL to validate
        schema_intelligence: SchemaIntelligence instance
        question_id: Question ID for logging
        question_type: Question type
        query: Original user query
        model: LLM model for regeneration

    Returns:
        Tuple of (sql, is_valid, message)
    """
    is_valid, errors = schema_intelligence.validate_sql(sql)

    if is_valid:
        return sql, True, "SQL is valid"

    # Try auto-fix first
    fixed_sql, remaining_errors = schema_intelligence.fix_invalid_sql(sql, errors)

    if not remaining_errors:
        # Verify the fix worked
        is_valid, new_errors = schema_intelligence.validate_sql(fixed_sql)
        if is_valid:
            return fixed_sql, True, "SQL auto-corrected"

    # Auto-fix didn't work, regenerate with error context
    error_context = "\n".join(errors)

    # Get relevant schemas for the query
    relevant_schemas = schema_intelligence.get_relevant_schemas(query, top_k=5)
    full_schemas = schema_intelligence.get_schema_context_for_tables(
        [s["table_name"] for s in relevant_schemas]
    )

    fix_prompt = f"""The following SQL has validation errors. Fix it using ONLY valid columns.

ORIGINAL SQL:
{sql}

ERRORS:
{error_context}

VALID SCHEMA:
{full_schemas}

IMPORTANT - NEVER SHOW IDs IN RESULTS:
- NEVER return _key or _id columns in SELECT - JOIN to dimension tables and show descriptive names
- Instead of member_key → JOIN dim_member and show member_name
- Instead of branch_key → JOIN dim_branch and show branch_name
- Instead of product_key → JOIN dim_product and show product_name or product_type
- Instead of competitor_key → JOIN dim_competitor and show competitor_name
- Instead of date_key → JOIN dim_date and show full_date
- Final SELECT must contain human-readable values, NOT numeric IDs/keys

Generate corrected SQL using ONLY columns that exist in the schema above.
Return ONLY the corrected SQL in a ```sql code block."""

    fixed_response, _ = get_llm_response(
        question_id,
        question_type,
        fix_prompt,
        model,
        "SQL-Validation-Fix",
        None, full_schemas, query, None,
        extract_sql=True
    )

    # Validate the fixed SQL
    is_valid, new_errors = schema_intelligence.validate_sql(fixed_response)

    if is_valid:
        return fixed_response, True, "SQL regenerated and validated"
    else:
        return fixed_response, False, f"Still has errors: {'; '.join(new_errors)}"
