"""
Schema Intelligence Module
--------------------------
Provides intelligent schema retrieval and SQL validation to prevent column/table hallucinations.

Components:
1. FAISS-based schema retrieval - finds relevant tables/columns for a query
2. SQL Validator - validates SQL against actual schema before execution
3. Column extractor - extracts columns from SQL to validate
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Set
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document


class SchemaIntelligence:
    """Manages schema knowledge and provides intelligent retrieval and validation."""

    def __init__(self, create_statement_dict: Dict[str, str]):
        """
        Initialize with schema dictionary.

        Args:
            create_statement_dict: Dict mapping table names to CREATE TABLE statements
        """
        self.schema_dict = create_statement_dict
        self.table_columns = self._extract_all_columns()
        self.embeddings = HuggingFaceEmbeddings()
        self.faiss_index = self._build_faiss_index()

    def _extract_all_columns(self) -> Dict[str, List[str]]:
        """Extract column names from all CREATE TABLE statements."""
        table_columns = {}

        for table_name, create_stmt in self.schema_dict.items():
            columns = self._extract_columns_from_create(create_stmt)
            table_columns[table_name.upper()] = columns
            # Also store lowercase version for matching
            table_columns[table_name.lower()] = columns

        return table_columns

    def _extract_columns_from_create(self, create_stmt: str) -> List[str]:
        """Extract column names from a CREATE TABLE statement."""
        columns = []

        # Find content between parentheses
        match = re.search(r'\((.*?)\)(?:\s*/\*|$)', create_stmt, re.DOTALL)
        if not match:
            return columns

        columns_section = match.group(1)

        # Split by comma and newline, extract column names
        for line in columns_section.split('\n'):
            line = line.strip().strip(',')
            if line and not line.startswith('--'):
                # First word is column name
                parts = line.split()
                if parts and not parts[0].upper() in ('PRIMARY', 'FOREIGN', 'CONSTRAINT', 'INDEX', 'UNIQUE'):
                    col_name = parts[0].strip('`"[]')
                    columns.append(col_name.lower())

        return columns

    def _build_faiss_index(self) -> FAISS:
        """Build FAISS index for semantic schema search."""
        documents = []

        for table_name, create_stmt in self.schema_dict.items():
            # Create searchable document with table info
            columns = self.table_columns.get(table_name.upper(), [])

            # Build rich description for semantic search
            doc_content = f"""
Table: {table_name}
Columns: {', '.join(columns)}
Schema: {create_stmt[:500]}
"""
            documents.append(Document(
                page_content=doc_content,
                metadata={
                    "table_name": table_name,
                    "columns": columns,
                    "create_statement": create_stmt
                }
            ))

        return FAISS.from_documents(documents, self.embeddings)

    def get_relevant_schemas(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve most relevant table schemas for a query using semantic search.

        Args:
            query: User's natural language question
            top_k: Number of tables to retrieve

        Returns:
            List of dicts with table_name, columns, create_statement
        """
        results = self.faiss_index.similarity_search(query, k=top_k)

        schemas = []
        for doc in results:
            schemas.append({
                "table_name": doc.metadata["table_name"],
                "columns": doc.metadata["columns"],
                "create_statement": doc.metadata["create_statement"]
            })

        return schemas

    def validate_sql(self, sql: str) -> Tuple[bool, List[str]]:
        """
        Validate SQL against actual schema.

        Args:
            sql: SQL query to validate

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        # Extract tables used in SQL
        tables_used = self._extract_tables_from_sql(sql)

        # Extract columns used in SQL
        columns_used = self._extract_columns_from_sql(sql)

        # Validate tables exist
        for table in tables_used:
            table_upper = table.upper()
            if table_upper not in self.table_columns and table.lower() not in self.table_columns:
                errors.append(f"Table '{table}' does not exist. Available tables: {', '.join(list(self.schema_dict.keys())[:10])}")

        # Validate columns exist in their tables
        for table, columns in columns_used.items():
            table_upper = table.upper()
            if table_upper in self.table_columns:
                valid_columns = set(self.table_columns[table_upper])
                for col in columns:
                    col_lower = col.lower()
                    if col_lower not in valid_columns:
                        # Find similar columns
                        similar = self._find_similar_columns(col_lower, valid_columns)
                        suggestion = f" Did you mean: {similar}?" if similar else ""
                        errors.append(f"Column '{col}' does not exist in table '{table}'.{suggestion} Valid columns: {', '.join(list(valid_columns)[:15])}")

        # Validate subqueries don't return multiple values with = operator
        subquery_errors = self._validate_subqueries(sql)
        errors.extend(subquery_errors)

        return len(errors) == 0, errors

    def _validate_subqueries(self, sql: str) -> List[str]:
        """
        Validate subqueries to prevent 'Subquery returned more than 1 value' errors.

        Returns:
            List of subquery-related errors/warnings
        """
        errors = []
        sql_upper = sql.upper()

        # Pattern 1: = (SELECT without TOP 1 or MAX/MIN/COUNT)
        # Find subqueries used with = operator
        eq_subquery_pattern = r'=\s*\(\s*SELECT\s+(?!TOP\s+1)(?!MAX\s*\()(?!MIN\s*\()(?!COUNT\s*\()(?!SUM\s*\()(?!AVG\s*\()'
        if re.search(eq_subquery_pattern, sql_upper):
            # Check if it's a potentially problematic subquery
            # Look for patterns like: = (SELECT column FROM table WHERE ...)
            detailed_pattern = r'=\s*\(\s*SELECT\s+([^)]+?)\s+FROM'
            matches = re.findall(detailed_pattern, sql_upper)
            for match in matches:
                # If selecting a non-aggregated column, it might return multiple values
                if not any(agg in match for agg in ['MAX(', 'MIN(', 'COUNT(', 'SUM(', 'AVG(', 'TOP 1']):
                    errors.append(
                        f"SUBQUERY WARNING: Subquery with '=' may return multiple values. "
                        f"Use 'TOP 1' or aggregate functions (MAX, MIN) in subquery, or use 'IN' instead of '='."
                    )
                    break

        # Pattern 2: Nested subqueries that could cause issues
        # WHERE col = (SELECT ... WHERE col2 = (SELECT ...))
        nested_eq_subquery = r'=\s*\(\s*SELECT[^)]+WHERE[^)]+\(\s*SELECT'
        if re.search(nested_eq_subquery, sql_upper):
            errors.append(
                f"SUBQUERY WARNING: Nested subqueries with '=' operator detected. "
                f"Consider using JOINs or ensure each subquery returns exactly one value with TOP 1."
            )

        # Pattern 3: GROUP BY in subquery used with = (without HAVING that limits to 1)
        group_subquery = r'=\s*\(\s*SELECT[^)]+GROUP\s+BY[^)]+\)'
        if re.search(group_subquery, sql_upper):
            # Check if there's a TOP 1 or aggregate
            if 'TOP 1' not in sql_upper:
                errors.append(
                    f"SUBQUERY WARNING: Subquery with GROUP BY used with '=' operator may return multiple values. "
                    f"Add 'TOP 1' or use 'IN' operator instead."
                )

        return errors

    def _extract_tables_from_sql(self, sql: str) -> Set[str]:
        """Extract table names from SQL query."""
        tables = set()

        # Pattern for FROM and JOIN clauses
        patterns = [
            r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bINTO\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            tables.update(matches)

        return tables

    def _extract_columns_from_sql(self, sql: str) -> Dict[str, Set[str]]:
        """
        Extract columns and their associated tables from SQL.
        Returns dict mapping table alias/name to set of columns.
        """
        columns_by_table = {}

        # Build alias mapping
        alias_map = self._build_alias_map(sql)

        # Find table.column or alias.column references
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\b'
        matches = re.findall(pattern, sql)

        for table_or_alias, column in matches:
            # Resolve alias to actual table name
            actual_table = alias_map.get(table_or_alias.lower(), table_or_alias)

            if actual_table.upper() not in columns_by_table:
                columns_by_table[actual_table.upper()] = set()
            columns_by_table[actual_table.upper()].add(column)

        return columns_by_table

    def _build_alias_map(self, sql: str) -> Dict[str, str]:
        """Build mapping from table aliases to actual table names."""
        alias_map = {}

        # Pattern: table_name alias or table_name AS alias
        patterns = [
            r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+(?:AS\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\b',
            r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+(?:AS\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\b',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            for table, alias in matches:
                # Make sure alias is not a keyword
                if alias.upper() not in ('ON', 'WHERE', 'AND', 'OR', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'CROSS', 'JOIN'):
                    alias_map[alias.lower()] = table

        return alias_map

    def _find_similar_columns(self, column: str, valid_columns: Set[str]) -> Optional[str]:
        """Find similar column names using simple string matching."""
        column = column.lower()

        # Direct substring match
        for valid in valid_columns:
            if column in valid or valid in column:
                return valid

        # Word overlap
        col_words = set(re.split(r'[_\s]', column))
        best_match = None
        best_score = 0

        for valid in valid_columns:
            valid_words = set(re.split(r'[_\s]', valid))
            overlap = len(col_words & valid_words)
            if overlap > best_score:
                best_score = overlap
                best_match = valid

        return best_match if best_score > 0 else None

    def get_schema_context_for_tables(self, table_names: List[str]) -> str:
        """Get formatted schema context for specific tables."""
        context_parts = []

        for table in table_names:
            table_upper = table.upper()
            if table_upper in self.schema_dict:
                context_parts.append(self.schema_dict[table_upper])

        return "\n\n".join(context_parts)

    def fix_invalid_sql(self, sql: str, errors: List[str]) -> Tuple[str, List[str]]:
        """
        Attempt to automatically fix invalid SQL based on errors.

        Args:
            sql: Original SQL with errors
            errors: List of validation errors

        Returns:
            Tuple of (fixed_sql, remaining_errors)
        """
        fixed_sql = sql
        remaining_errors = []

        for error in errors:
            # Try to extract column fix suggestion
            match = re.search(r"Column '([^']+)' does not exist.*Did you mean: ([^?]+)\?", error)
            if match:
                wrong_col = match.group(1)
                suggested_col = match.group(2).strip()
                # Replace wrong column with suggested
                fixed_sql = re.sub(
                    rf'\b{re.escape(wrong_col)}\b',
                    suggested_col,
                    fixed_sql,
                    flags=re.IGNORECASE
                )
            elif "SUBQUERY WARNING" in error:
                # Try to fix subquery issues
                fixed_sql = self._fix_subquery_issues(fixed_sql)
            else:
                remaining_errors.append(error)

        return fixed_sql, remaining_errors

    def _fix_subquery_issues(self, sql: str) -> str:
        """
        Attempt to fix subquery issues that could cause 'more than 1 value' errors.

        Args:
            sql: SQL with potential subquery issues

        Returns:
            Fixed SQL
        """
        fixed_sql = sql

        # Fix 1: Add TOP 1 to subqueries used with = that don't have aggregates
        # Pattern: = (SELECT column FROM ... without TOP 1 or aggregate)
        def add_top_1_to_subquery(match):
            full_match = match.group(0)
            # Check if already has TOP or aggregate
            if 'TOP' in full_match.upper() or any(agg in full_match.upper() for agg in ['MAX(', 'MIN(', 'COUNT(', 'SUM(', 'AVG(']):
                return full_match
            # Add TOP 1 after SELECT
            return re.sub(r'(SELECT\s+)', r'\1TOP 1 ', full_match, flags=re.IGNORECASE)

        # Find = (SELECT ... FROM ...) patterns and add TOP 1
        pattern = r'=\s*\(\s*SELECT\s+[^)]+\s+FROM\s+[^)]+\)'
        fixed_sql = re.sub(pattern, add_top_1_to_subquery, fixed_sql, flags=re.IGNORECASE)

        # Fix 2: For nested subqueries, ensure inner ones have TOP 1
        # This is a more aggressive fix for deeply nested subqueries
        def fix_nested_subquery(match):
            inner_sql = match.group(0)
            # Add TOP 1 to inner SELECT if missing
            if 'TOP' not in inner_sql.upper():
                inner_sql = re.sub(r'(SELECT\s+)', r'\1TOP 1 ', inner_sql, count=1, flags=re.IGNORECASE)
            return inner_sql

        # Look for subqueries within WHERE clauses of other subqueries
        nested_pattern = r'\(\s*SELECT\s+(?!TOP)[^)]+WHERE[^)]+\(\s*SELECT\s+(?!TOP)[^)]+\)\s*\)'
        fixed_sql = re.sub(nested_pattern, fix_nested_subquery, fixed_sql, flags=re.IGNORECASE)

        # Fix 3: Add ORDER BY with TOP 1 for date-related subqueries if missing
        # Pattern: TOP 1 ... FROM DIM_DATE ... without ORDER BY
        def add_order_by_for_dates(match):
            full_match = match.group(0)
            if 'ORDER BY' not in full_match.upper() and 'DIM_DATE' in full_match.upper():
                # Add ORDER BY full_date DESC before the closing paren
                return full_match.rstrip(')') + ' ORDER BY full_date DESC)'
            return full_match

        date_subquery_pattern = r'\(\s*SELECT\s+TOP\s+1[^)]+DIM_DATE[^)]+\)'
        fixed_sql = re.sub(date_subquery_pattern, add_order_by_for_dates, fixed_sql, flags=re.IGNORECASE)

        return fixed_sql


def create_schema_intelligence(create_statement_dict: Dict[str, str]) -> SchemaIntelligence:
    """Factory function to create SchemaIntelligence instance."""
    return SchemaIntelligence(create_statement_dict)
