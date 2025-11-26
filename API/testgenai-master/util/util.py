import re
import logging
from bs4 import BeautifulSoup

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
        # Remove SQL comments
        sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
        logger.info("Extracted SQL from ```sql block")
        return sql.strip()

    # Pattern 2: ``` ... ``` (no language tag)
    pattern2 = r'```\s*(SELECT.*?)\s*```'
    matches = re.findall(pattern2, text, re.DOTALL | re.IGNORECASE)
    if matches:
        sql = matches[0].strip()
        # Remove SQL comments
        sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
        logger.info("Extracted SQL from ``` block")
        return sql.strip()

    # Pattern 3: SQL starting with WITH (for CTEs)
    pattern3 = r'(WITH\s+\w+\s+AS\s*\([\s\S]*?SELECT[\s\S]*?)(?:\n\s*\n|$)'
    matches = re.findall(pattern3, text, re.IGNORECASE)
    if matches:
        sql = matches[0].strip()
        # Clean up trailing text
        sql = re.split(r'\n\s*(?:Explanation|Note|This query)', sql, flags=re.IGNORECASE)[0].strip()
        # Remove SQL comments
        sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
        logger.info("Extracted CTE SQL from plain text")
        return sql.strip()

    # Pattern 4: Plain SELECT statement
    pattern4 = r'(SELECT[\s\S]*?)(?:\n\s*\n|$)'
    matches = re.findall(pattern4, text, re.IGNORECASE)
    if matches:
        sql = matches[0].strip()
        # Stop at common explanation markers
        sql = re.split(r'\n\s*(?:Explanation|Note|This query|--\s*Explanation)', sql, flags=re.IGNORECASE)[0].strip()
        # Remove trailing semicolons and whitespace
        sql = sql.rstrip(';').strip()
        # Remove SQL comments
        sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
        logger.info("Extracted plain SELECT SQL")
        return sql.strip()

    # If nothing found, log the full response for debugging
    logger.error(f"Failed to extract SQL. Response preview: {text[:500]}")
    return None


def validate_extracted_sql(sql):
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
        # Allow simple SELECT without FROM (like SELECT 1)
        if len(sql.strip()) < 30:
            return True, ""
        return False, "SELECT query missing FROM clause"

    return True, ""


def extract_from_vector_doc(metadata_str, extraction_key):
    # Split the metadata string into individual parts
    metadata_parts = metadata_str.split('; ')
    
    # Iterate through the parts and find the one that contains "Related Keywords"
    for part in metadata_parts:
        if part.startswith(f"[{extraction_key}] - "):            
            return part[len(f"[{extraction_key}] - "):]

    # Return None or an empty string if "Related Keywords" are not found
    return None

def tuple_to_dict(row, column_names):
    return {column_names[i]: row[i] for i in range(len(column_names))}


def add_additional_column_css(previous_html_response, new_html_response):      
  # Parse the HTML
  soup_previous = BeautifulSoup(previous_html_response, 'html.parser')
  soup_this = BeautifulSoup(new_html_response, 'html.parser')

  # Extract column headings
  previous_output_columns = [th.text.strip() for th in soup_previous.find_all('th')]
  this_output_columns = [th.text.strip() for th in soup_this.find_all('th')]

  # Find the extra column in formatted_output
  extra_column = None
  if len(this_output_columns) == len(previous_output_columns) + 1:
      extra_column = set(this_output_columns).difference(previous_output_columns).pop()

  # Add 'additional-column' class to the extra column's <th> element
  if extra_column:
      for th in soup_this.find_all('th'):
          if th.text.strip() == extra_column:
              th['class'] = th.get('class', []) + ['additional-column']
              break

  # Get the modified HTML
  modified_html = str(soup_this)
  return modified_html



def get_full_documentation_split_list():
    """
    Read database documentation from JSON file and convert to sections.
    JSON format: Array of objects with "section" and "content" keys
    This replaces the old CSV approach.
    """
    import os
    import json

    # Path to the documentation file (relative to project root)
    doc_file_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data',
        'database_documentation.json'
    )

    try:
        # Read the JSON file
        with open(doc_file_path, 'r') as f:
            docs_data = json.load(f)

        # Format each entry as "Section: Content"
        sections = []
        for entry in docs_data:
            section_text = f"{entry['section']}: {entry['content']}"
            sections.append(section_text)

        print(f"Loaded {len(sections)} documentation sections from: {doc_file_path}")
        return sections

    except FileNotFoundError:
        print(f"WARNING: Database documentation file not found at: {doc_file_path}")
        print("Using minimal fallback documentation.")
        return [
            "Process Flow: No documentation file found.",
            "Tables: Please create data/database_documentation.json with your database documentation.",
            "Documentation Format: JSON array with 'section' and 'content' keys"
        ]

    except Exception as e:
        print(f"ERROR reading documentation file: {e}")
        return ["Documentation unavailable due to error: " + str(e)]


