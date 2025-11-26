from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Annoy
from config import settings
from llm import get_ms_sql_prompt, get_ms_sql_prompt_for_follow_up, get_additional_insights_question_generation_prompt, get_llm_response,  format_db_output, get_related_questions_generation_prompt, get_sql_error_resolve_prompt, get_chart_image, get_edited_chart
from llm.llm_core import llm_qna_response
from llm.schema_intelligence import SchemaIntelligence
from llm.two_stage_sql import two_stage_sql_generation, validate_and_fix_sql
from self_db.crud import get_conversation_history, get_existing_sql_query_if_match_found, get_previous_response, get_extracted_sql, get_result_set
from target_db import execute_query_original
from util.util import extract_from_vector_doc, add_additional_column_css, validate_extracted_sql
import re
import json
import logging
from ast import literal_eval

logger = logging.getLogger(__name__)

# Global schema intelligence instance (initialized on first use)
_schema_intelligence = None

def get_schema_intelligence(create_statement_dict):
    """Get or create SchemaIntelligence instance."""
    global _schema_intelligence
    if _schema_intelligence is None:
        logger.info("Initializing SchemaIntelligence with FAISS index...")
        _schema_intelligence = SchemaIntelligence(create_statement_dict)
        logger.info("SchemaIntelligence initialized successfully")
    return _schema_intelligence

def get_combined_schema(tables_list, create_statement_dict):
    create_stmts_combined = ''
    processed_tables = set()  # Set to keep track of processed tables

    for table in tables_list:
        table_name = table.strip().upper()
        # Check if the table has already been processed
        if table_name not in processed_tables:
            this_tables_create_stmt = create_statement_dict.get(table_name, '')
            create_stmts_combined = create_stmts_combined + "\n" + this_tables_create_stmt
            processed_tables.add(table_name)  # Add the table to the set of processed tables

    return create_stmts_combined

def convert_to_html_table(db_response):   

    # Start of the HTML table
    html_table = "<table>"

    # Add table headers
    headers = db_response[0].keys()
    html_table += "<tr>" + "".join(f"<th>{header}</th>" for header in headers) + "</tr>"

    # Add table rows
    for row in db_response:
        html_table += "<tr>" + "".join(f"<td>{value}</td>" for value in row.values()) + "</tr>"

    # End of the HTML table
    html_table += "</table>"

    return html_table

def handle_too_many_rows(db_response, db_error):
    if db_error or db_response is None:
        return db_response, False, ""
    
    rows_count_before = len(db_response)
    max_allowed_rows = 30
    if isinstance(db_response, list) and rows_count_before <= max_allowed_rows:
        return db_response, False, ""                
    elif isinstance(db_response, list) and rows_count_before > max_allowed_rows: 
        note = f"<p><span class='highlight'>Note</span>: The complete dataset contains a total of {rows_count_before} rows. To provide a concise overview, only the top {max_allowed_rows} rows are displayed below.</p>"                    
        return db_response[:max_allowed_rows], True, note
    
    
def extract_html_block(text):
    # Pattern to match HTML block wrappers
    pattern = r"```html\s*(.*?)\s*```"
    
    # Find all matches using regex
    matches = re.findall(pattern, text, re.DOTALL)
    
    # If matches are found, return the first match, otherwise return the original text
    return matches[0].strip() if matches else text

def remove_specific_html_elements(text):
    text = extract_html_block(text)

    # Remove <html>, </html>, <body>, and </body> tags
    # Remove <!DOCTYPE html> and variations
    text = re.sub(r'<!DOCTYPE html[^>]*>', '', text, flags=re.IGNORECASE)

    # Remove <html> with attributes and <html> tags
    text = re.sub(r'<html[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'```html[\s\S]*?```', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<\/?html>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<\/?body>', '', text, flags=re.IGNORECASE)

    # Remove everything inside <head>...</head>
    text = re.sub(r'<head>.*?<\/head>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Remove heading tags (h1, h2, h3, etc.) and their contents
    text = re.sub(r'<h[1-6]>.*?<\/h[1-6]>', '', text, flags=re.DOTALL | re.IGNORECASE)

    return text

    
def original_question_response(question_id, question_type, query, vector_store_from_metadata, create_statement_dict, bool_exact_question_reuse, model_to_use, rag_vector_store):
    extracted_sql = None
    if bool_exact_question_reuse:
        extracted_sql = get_existing_sql_query_if_match_found(query)

    prompt = "You are an expert in classifying whether the question is related to fetching sql results or fetching information from the documentation about the database, table schemas, column definitions, relations between tables. If the CURRENT QUESTION needs to run some sql query, then respond with exactly and only 'sql' and nothing else at all. If the CURRENT QUESTION needs to fetch from the database definition documentation, then respond with exactly and only 'rag' and nothing else at all. ALWAYS the answer should depend on the CURRENT QUESTION only. Question - "
    prompt_final = prompt + "[Current Question]: " + query
    llm_response, _ = get_llm_response(question_id, question_type, prompt_final, "GPT 4", "SQL-RAG-Switch-Original-Question", None, None, None, None, False)
    sql_or_rag = "RAG"
    if "sql".lower() in llm_response.lower():
        sql_or_rag = "SQL"
    elif "rag".lower() in llm_response.lower():
        sql_or_rag = "RAG"

    if sql_or_rag == "RAG":
        rag_docs = rag_vector_store.similarity_search(query, 3)

        # Safely extract metadata from available docs
        doc_contents = []
        for i, doc in enumerate(rag_docs):
            if i < 3 and doc and hasattr(doc, 'metadata') and 'metadata' in doc.metadata:
                doc_contents.append(doc.metadata["metadata"])

        if not doc_contents:
            return None, "<p>Unable to find relevant documentation for this question.</p>", False, 0, 0

        combined_docs = " \n\n ".join(doc_contents)
        prompt = f"Answer only the user question in HTML format - {query} - using this documentation - {combined_docs}"

        initial_output, _ = get_llm_response(question_id, question_type, prompt, "GPT 3.5 0125", "RAG-Response-Generation-Original-Question", None, None, None, None, False)

        formatted_output = remove_specific_html_elements(initial_output)

        return None, formatted_output, False, 0, 0

    attempt_number = 1
    found_matching_sql = False
    if extracted_sql is None:
        # Initialize schema intelligence for FAISS-based retrieval and validation
        schema_intel = get_schema_intelligence(create_statement_dict)

        logger.info(f"Using two-stage SQL generation for question_id: {question_id}")

        # Two-stage SQL generation with FAISS-based schema retrieval and validation
        extracted_sql, is_valid, validation_msg = two_stage_sql_generation(
            question_id,
            question_type,
            query,
            schema_intel,
            model_to_use
        )

        logger.info(f"Two-stage SQL result - Valid: {is_valid}, Message: {validation_msg}")

        if not extracted_sql or 'SQL Extraction Failed' in str(extracted_sql):
            logger.error(f"Two-stage SQL generation failed: {extracted_sql}")
            return None, "I encountered an error generating the SQL query. Please try again.", False, 0, 0

        # Get tables for logging
        relevant_schemas = schema_intel.get_relevant_schemas(query, top_k=5)
        tables = ",".join([s["table_name"] for s in relevant_schemas])

        # Execute the generated SQL
        db_response, _, db_error = execute_query_original(question_id, question_type, "Original-Answer-SQL-Query-Generation", extracted_sql, True, attempt_number)

        db_response, has_too_many_rows, too_many_rows_note = handle_too_many_rows(db_response, db_error)

        # Retry loop with schema-aware error fixing
        while db_error and attempt_number < settings.max_sql_retries:
            attempt_number += 1

            extracted_sql, is_valid, fix_msg = validate_and_fix_sql(
                extracted_sql,
                schema_intel,
                question_id,
                question_type,
                query,
                model_to_use
            )
            logger.info(f"SQL fix attempt {attempt_number} - Valid: {is_valid}, Message: {fix_msg}")

            if 'SQL Extraction Failed' not in str(extracted_sql):
                db_response, _, db_error = execute_query_original(question_id, question_type, "Original-Answer-SQL-Query-Generation", extracted_sql, True, attempt_number)
                db_response, has_too_many_rows, too_many_rows_note = handle_too_many_rows(db_response, db_error)
    else:
        # Reuse existing SQL query that was found
        found_matching_sql = True
        db_response, _, db_error = execute_query_original(question_id, question_type, "Original-Answer-SQL-Query-Found", extracted_sql, True, attempt_number)
        db_response, has_too_many_rows, too_many_rows_note = handle_too_many_rows(db_response, db_error)

    if db_error:
        return None, db_error, found_matching_sql, 0, 0

    formatted_output = format_db_output(question_id, question_type, db_response, query, "Original-Answer-Output-Formatting")

    if has_too_many_rows:
        formatted_output = too_many_rows_note + formatted_output

    show_chart = 0
    if db_response is not None:
        resultset_rows_count = len(db_response)
        if resultset_rows_count >= 5 and resultset_rows_count <= 30:
            show_chart = 1

    return extracted_sql, formatted_output, found_matching_sql, show_chart, 1
    

def additional_insights_response(question_id, question_type, query, vector_store_from_metadata, create_statement_dict, model_to_use):
    # Initialize schema intelligence for FAISS-based retrieval
    schema_intel = get_schema_intelligence(create_statement_dict)

    # Get relevant schemas for insight generation
    relevant_schemas = schema_intel.get_relevant_schemas(query, top_k=5)
    db_schema_add = schema_intel.get_schema_context_for_tables([s["table_name"] for s in relevant_schemas])

    # Extract keywords from metadata for insight question generation
    doc = vector_store_from_metadata.similarity_search(query, 1)
    metadata_str = doc[0].metadata["metadata"]
    additional_insights_keywords = extract_from_vector_doc(metadata_str, "Related Keywords")

    prompt_for_getting_query_add = get_additional_insights_question_generation_prompt(query, additional_insights_keywords, db_schema_add)

    ms_sql_prompt = get_ms_sql_prompt()
    query_add, _ = get_llm_response(question_id, question_type, prompt_for_getting_query_add, model_to_use, "Additional-Insights-Question-Generation", None, db_schema_add, query, ms_sql_prompt, extract_sql=False)

    logger.info(f"ADDITIONAL INSIGHTS - Original: {query}, Generated: {query_add}")

    # Use two-stage SQL generation for the insight question
    attempt_number = 1
    extracted_sql, is_valid, validation_msg = two_stage_sql_generation(
        question_id,
        question_type,
        query_add,
        schema_intel,
        model_to_use
    )

    logger.info(f"ADDITIONAL INSIGHTS SQL - Valid: {is_valid}, Message: {validation_msg}")

    if not extracted_sql or 'SQL Extraction Failed' in str(extracted_sql):
        logger.info(f"Additional insights SQL generation failed for question_id: {question_id}")
        return None, "<p>Unable to generate additional insights for this question. The insight may require data not available in the current schema.</p>"

    db_response, _, db_error = execute_query_original(question_id, question_type, "Additional-Insights-SQL-Query-Generation", extracted_sql, True, attempt_number)

    db_response, has_too_many_rows, too_many_rows_note = handle_too_many_rows(db_response, db_error)

    # Retry loop with schema-aware error fixing
    while db_error and attempt_number < settings.max_sql_retries:
        logger.info(f"ADDITIONAL INSIGHTS - SQL Error on Attempt {attempt_number}: {db_error}")
        attempt_number += 1

        extracted_sql, is_valid, fix_msg = validate_and_fix_sql(
            extracted_sql,
            schema_intel,
            question_id,
            question_type,
            query_add,
            model_to_use
        )
        logger.info(f"ADDITIONAL INSIGHTS - Fix attempt {attempt_number}: {fix_msg}")

        if 'SQL Extraction Failed' not in str(extracted_sql):
            db_response, _, db_error = execute_query_original(question_id, question_type, "Additional-Insights-SQL-Query-Generation", extracted_sql, True, attempt_number)
            db_response, has_too_many_rows, too_many_rows_note = handle_too_many_rows(db_response, db_error)

    if db_error:
        return None, db_error

    formatted_output = format_db_output(question_id, question_type, db_response, query_add, "Additional-Insights-Output-Formatting")

    if has_too_many_rows:
        formatted_output = too_many_rows_note + formatted_output

    return extracted_sql, formatted_output








def related_questions_response(question_id, question_type, query, vector_store_from_metadata, create_statement_dict, model_to_use):   
    
    doc = vector_store_from_metadata.similarity_search(query, 1)    
    metadata_str = doc[0].metadata["metadata"]        
    keywords = extract_from_vector_doc(metadata_str, "Keywords")     
    tables = extract_from_vector_doc(metadata_str, "Tables") 
    tables_list = tables.split(',')
    db_schema = get_combined_schema(tables_list, create_statement_dict)   

    # db_schema_add = extract_from_vector_doc(metadata_str_add, "CreateTableStatements")
    prompt_for_related_questions = get_related_questions_generation_prompt(query, keywords, db_schema)
    # Only for this GPT 4 is fixed to get the output in the correct format - until we have a 3.5 fine tuned version for this
    related_questions, _ = get_llm_response(question_id, question_type, prompt_for_related_questions, 'GPT 4', "Related-Questions-Generation", tables, db_schema, query, None, extract_sql=False)  
    
   
    
    return related_questions




    
    


def followup_question_response(question_id, question_type, parent_question_id, query, vector_store_from_metadata, create_statement_dict, model_to_use, rag_vector_store):
    get_history = get_conversation_history(parent_question_id)

    prompt = "You are an expert in classifying whether the question is related to fetching sql results or fetching information from the documentation about the database, table schemas, column definitions, relations between tables. If the CURRENT QUESTION needs to run some sql query, then respond with exactly and only 'sql' and nothing else at all. If the CURRENT QUESTION needs to fetch from the database definition documentation, then respond with exactly and only 'rag' and nothing else at all. ALWAYS the answer should depend on the CURRENT QUESTION only. Question - "
    history_rag = ""
    for conversation in get_history:
        history_rag += f"[Previous-Question]{conversation['question_asked']}[/Previous-Question]\n"

    prompt_final = (f"{prompt}\n"
             f"{history_rag}\n"
             f"[Current-Question]{query}[/Current-Question]")

    llm_response, _ = get_llm_response(question_id, question_type, prompt_final, "GPT 4", "SQL-RAG-Switch-Follow-Up-Question", None, None, None, None, False)
    sql_or_rag = "RAG"
    if "sql".lower() in llm_response.lower():
        sql_or_rag = "SQL"
    elif "rag".lower() in llm_response.lower():
        sql_or_rag = "RAG"

    if sql_or_rag == "RAG":
        rag_docs = rag_vector_store.similarity_search(query, 3)

        # Safely extract metadata from available docs
        doc_contents = []
        for i, doc in enumerate(rag_docs):
            if i < 3 and doc and hasattr(doc, 'metadata') and 'metadata' in doc.metadata:
                doc_contents.append(doc.metadata["metadata"])

        if not doc_contents:
            return None, "<p>Unable to find relevant documentation for this question.</p>", 0, 0

        combined_docs = " \n\n ".join(doc_contents)

        prompt_final = f"Answer only the user question in HTML format using the provide documentation. [Current Question]{query}[Current Question]. [Documenation]{combined_docs}[/Documenation]"
        initial_output, _ = get_llm_response(question_id, question_type, prompt_final, "GPT 3.5 0125", "RAG-Response-Generation-Follow-Up-Question", None, None, None, None, False)
        formatted_output = remove_specific_html_elements(initial_output)
        return None, formatted_output, 0, 0

    # Initialize schema intelligence for FAISS-based retrieval and validation
    schema_intel = get_schema_intelligence(create_statement_dict)

    # Build conversation history context for the LLM
    # Extract the original question and its SQL for context
    original_question = ""
    original_sql = ""
    history_content = ""

    for i, conversation in enumerate(get_history):
        if i == 0:
            # First question is the original question
            original_question = conversation['question_asked']
            original_sql = conversation.get('sql_query', '')
        history_content += f"[Previous-Question]{conversation['question_asked']}[/Previous-Question]\n[Previous-Response]```sql {conversation['sql_query']}``` \n Execution Result - {conversation['resultset']}[/Previous-Response]\n"

    # Build enhanced query that clearly connects follow-up to original question
    enhanced_query = f"""FOLLOW-UP QUESTION: {query}

ORIGINAL QUESTION: {original_question}

ORIGINAL SQL THAT WORKED:
```sql
{original_sql}
```

CONVERSATION HISTORY:
{history_content}

IMPORTANT: This is a FOLLOW-UP question. The user is asking about the same data context as the original question.
- Use the ORIGINAL SQL as a starting point and modify it to answer the FOLLOW-UP QUESTION
- Keep the same tables and joins from the original query where relevant
- Apply any filters, groupings, or modifications needed to answer the follow-up
- If the follow-up asks for a breakdown, add GROUP BY
- If the follow-up asks for a different time period, adjust the date filter
- If the follow-up asks for specific criteria, add WHERE conditions"""

    attempt_number = 1

    logger.info(f"Using two-stage SQL generation for follow-up question_id: {question_id}")
    logger.info(f"Original question: {original_question}")
    logger.info(f"Follow-up question: {query}")

    # Two-stage SQL generation with FAISS-based schema retrieval and validation
    extracted_sql, is_valid, validation_msg = two_stage_sql_generation(
        question_id,
        question_type,
        enhanced_query,
        schema_intel,
        model_to_use
    )

    logger.info(f"Follow-up SQL result - Valid: {is_valid}, Message: {validation_msg}")

    if not extracted_sql or 'SQL Extraction Failed' in str(extracted_sql):
        return None, "I couldn't generate a valid SQL query for this follow-up question.", 0, 0

    db_response, _, db_error = execute_query_original(question_id, question_type, "Original-Answer-SQL-Query-Generation", extracted_sql, True, attempt_number)

    db_response, has_too_many_rows, too_many_rows_note = handle_too_many_rows(db_response, db_error)

    # Retry loop with schema-aware error fixing
    while db_error and attempt_number < settings.max_sql_retries:
        attempt_number += 1

        extracted_sql, is_valid, fix_msg = validate_and_fix_sql(
            extracted_sql,
            schema_intel,
            question_id,
            question_type,
            enhanced_query,
            model_to_use
        )
        logger.info(f"Follow-up SQL fix attempt {attempt_number} - Valid: {is_valid}, Message: {fix_msg}")

        if 'SQL Extraction Failed' not in str(extracted_sql):
            db_response, _, db_error = execute_query_original(question_id, question_type, "Original-Answer-SQL-Query-Generation", extracted_sql, True, attempt_number)
            db_response, has_too_many_rows, too_many_rows_note = handle_too_many_rows(db_response, db_error)

    if db_error:
        return None, db_error, 0, 0

    formatted_output = format_db_output(question_id, question_type, db_response, query, "Original-Answer-Output-Formatting")

    if has_too_many_rows:
        formatted_output = too_many_rows_note + formatted_output

    show_chart = 0
    if db_response is not None:
        resultset_rows_count = len(db_response)
        if resultset_rows_count >= 5 and resultset_rows_count <= 30:
            show_chart = 1

    return extracted_sql, formatted_output, show_chart, 1


def get_tags(question_id):
    extracted_sql_resultset = get_extracted_sql(question_id)
    tags_prompt = "Provide business context tags for this SQL query. It should be as short as possible and only comma separated final business context tags. Give only the final business context tags like what the query related to, for example like for which period or to which product or category. Response should contain nothing else. SQL query - "    
    if extracted_sql_resultset is not None and len(extracted_sql_resultset) > 0:
        tags_prompt += extracted_sql_resultset[0]['sql_query_extracted']
        tags, _ = get_llm_response(question_id, None, tags_prompt, 'SQL-to-Tags', "SQL-to-Tags", None, None, None, None, extract_sql=False)          
        tags = tags.replace('.', '')
        return tags
    else:
        return None

def get_charts(question_id, file_id):
    result_set = get_result_set(question_id)
    rs_val = result_set[0]['resultset']

    # Generate a unique ID for the filename
    #unique_id = uuid.uuid4()

    # Define the directory to save the file, change as per your file system
    directory = "temp_data/"

    # Save the JSON data to a file with the unique ID
    file_path = f"{directory}{file_id}.json"
    with open(file_path, 'w') as file:
        file.write(rs_val)

    chrt_img_response = get_chart_image(file_path)

    return chrt_img_response

def edit_chart(question_id, file_id, code, library, instructions): 
    directory = "temp_data/"
    file_path = f"{directory}{file_id}.json"
    return get_edited_chart(question_id, file_path, code, library, instructions)


def get_charts_code(question_id):
    """
    Generate chart options for a given question's result set.
    Returns chart configuration for ApexCharts or Google Charts.
    """
    try:
        call_center_locations = {
                                    "San Francisco": {"lat": 37.773972, "long": -122.431297},
                                    "Salt Lake City": {"lat": 40.758701, "long": -111.876183},
                                    "Milwaukee": {"lat": 43.038902, "long": -87.906471},
                                    "New York": {"lat": 40.730610, "long": -73.935242},
                                    "New Orleans": {"lat": 29.954400, "long": -90.107500},
                                    "Miami": {"lat": 25.761681, "long": -80.191788},
                                    "Chicago": {"lat": 41.881832, "long": -87.623177},
                                    "San Diego": {"lat": 32.715736, "long": -117.161087},
                                    "Charleston": {"lat": 32.776566, "long": -79.930923},
                                    "Fargo": {"lat": 46.877186, "long": -96.789803},
                                    "Atlanta": {"lat": 33.753746, "long": -84.386330},
                                    "Seattle": {"lat": 47.608013, "long": -122.335167},
                                    "Memphis": {"lat": 35.117500, "long": -89.971107},
                                    "Washington, DC": {"lat": 38.895100, "long": -77.036400},
                                    "Boston": {"lat": 42.361145, "long": -71.057083}
                                }

        # Fetch result set from database
        result_set = get_result_set(question_id)

        # Validate result set exists
        if not result_set or len(result_set) == 0:
            logger.error(f"No result set found for question_id: {question_id}")
            return {
                "chart_type": "error",
                "chart_options": "{}",
                "chart_data": [],
                "error": "No data available for chart generation"
            }

        # Extract resultset from first record
        result_val = result_set[0].get('resultset')
        if not result_val:
            logger.error(f"Empty resultset for question_id: {question_id}")
            return {
                "chart_type": "error",
                "chart_options": "{}",
                "chart_data": [],
                "error": "Empty result set"
            }

        # Parse JSON result set
        try:
            parsed_json = json.loads(result_val)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON for question_id {question_id}: {e}")
            return {
                "chart_type": "error",
                "chart_options": "{}",
                "chart_data": [],
                "error": f"Invalid JSON in result set: {str(e)}"
            }

        # Validate parsed JSON is a list
        if not isinstance(parsed_json, list) or len(parsed_json) == 0:
            logger.error(f"Invalid or empty data structure for question_id: {question_id}")
            return {
                "chart_type": "error",
                "chart_options": "{}",
                "chart_data": [],
                "error": "Data is not in expected format"
            }

        # Check for geo chart data (call center names)
        has_call_center_name = any('call_center_name'.lower() in map(str.lower, item) for item in parsed_json)

        prompt_for_chart_options = ''
        if has_call_center_name:
            for item in parsed_json:
                call_center_name = item.get("call_center_name")
                if call_center_name in call_center_locations:
                    # Add latitude and longitude from the dictionary
                    item["latitude"] = call_center_locations[call_center_name]["lat"]
                    item["longitude"] = call_center_locations[call_center_name]["long"]

            prompt = """Provide 'drawChart' method for google geo chart to create a geo chart best suited for this dataset.

IMPORTANT CHART REQUIREMENTS:
- Chart should be large and fit the full container width (100%)
- Set height to at least 500px
- Legend should be positioned appropriately and readable
- Title should be clear, descriptive, and WRAP if too long (use \\n for line breaks if needed)
- Use appropriate colors for data visualization

Give only the 'drawChart' method and nothing else in code block. Dataset - """
            prompt_for_chart_options = prompt + json.dumps(parsed_json)
        else:
            prompt = """Provide apexcharts options value to create best suited chart for this dataset.

IMPORTANT CHART REQUIREMENTS:
1. CHART SIZE - Make it large and fit to page:
   - chart.height: '500' or '100%'
   - chart.width: '100%'

2. LEGEND - Position and style appropriately:
   - legend.position: 'bottom' or 'right' depending on data
   - legend.horizontalAlign: 'center'
   - legend.fontSize: '14px'
   - legend.itemMargin: { horizontal: 10, vertical: 5 }

3. TITLE - Clear, descriptive, and WRAP if too long:
   - title.text: descriptive title based on data
   - title.align: 'center'
   - title.style.fontSize: '18px'
   - title.style.cssClass: 'apexcharts-title-text'
   - title.floating: false
   - title.offsetY: 0
   - If title is long, use array format: title.text: ['Line 1', 'Line 2'] to wrap text
   - Or use \\n in string for line break: title.text: 'Long Title\\nContinued'

4. DATA LABELS - Readable:
   - dataLabels.enabled: true (for pie/donut)
   - dataLabels.style.fontSize: '12px'

5. RESPONSIVE - Add responsive breakpoints:
   - responsive: [{ breakpoint: 480, options: { chart: { width: '100%' }, legend: { position: 'bottom' } } }]

6. TOOLTIP - Enable and format nicely:
   - tooltip.enabled: true
   - tooltip.y.formatter for numbers

7. XAXIS/YAXIS LABELS - Wrap long labels:
   - xaxis.labels.rotate: -45 (for long category names)
   - xaxis.labels.rotateAlways: false
   - xaxis.labels.trim: true
   - xaxis.labels.maxHeight: 120

Give only the options value and nothing else in a code block. Dataset - """
            prompt_for_chart_options = prompt + result_val

        # Generate chart options using LLM
        logger.info(f"Generating chart options for question_id: {question_id}")
        chart_options, _ = get_llm_response(question_id, None, prompt_for_chart_options, 'GPT 4', "Apex-Chart-Options-Generation", None, None, None, None, extract_sql=False)

        # Extract content from code block
        extracted_content = re.search(r'```(?:\w+\n)?([\s\S]*?)\n```', chart_options)
        options = extracted_content.group(1) if extracted_content else chart_options

        if has_call_center_name:
            # Parse Google Charts format
            data_pattern = r"google\.visualization\.arrayToDataTable\((\[.*?\])\);"
            data_match = re.search(data_pattern, options, re.DOTALL)
            data_string = data_match.group(1) if data_match else None
            data_array = literal_eval(data_string) if data_string else []

            options_pattern = r"var options = (\{.*?\});"
            options_match = re.search(options_pattern, options, re.DOTALL)
            options_string = options_match.group(1) if options_match else "{}"

            response = {
                    "chart_type": "google",
                    "chart_options": options_string,
                    "chart_data": data_array
                }
        else:
            # ApexCharts format
            options = "this, this.chartOptions = " + options
            response = {
                    "chart_type": "apex",
                    "chart_options": options,
                    "chart_data": []
                }

        logger.info(f"Chart generated successfully for question_id: {question_id}, type: {response['chart_type']}")
        return response

    except Exception as e:
        logger.error(f"Unexpected error in get_charts_code for question_id {question_id}: {e}", exc_info=True)
        return {
            "chart_type": "error",
            "chart_options": "{}",
            "chart_data": [],
            "error": f"Failed to generate chart: {str(e)}"
        }


def edit_charts_code(question_id, code, instructions):        

    prompt = ""
    interaction_type = ""
    """
    if chart_type == 'google':
        prompt = "update this google chart 'drawChart' function to apply the given instructions. Give only the 'drawChart' method and nothing else."
        interaction_type = "Google-Chart-Code-Generation"
    elif chart_type == 'apex':
        prompt = "update apexcharts options value to apply the given instructions. Give only the options value and nothing else in a code block. Check JSON is valid once again." 
        interaction_type = "Apex-Chart-Options-Generation"
    else:
        return None
    """

    prompt = """Update apexcharts options value to apply the given instructions.

MAINTAIN THESE CHART REQUIREMENTS:
1. CHART SIZE - Keep it large and fit to page:
   - chart.height: '500' or '100%'
   - chart.width: '100%'

2. LEGEND - Position and style appropriately:
   - legend.position: 'bottom' or 'right'
   - legend.horizontalAlign: 'center'
   - legend.fontSize: '14px'

3. TITLE - Clear, descriptive, and WRAP if too long:
   - title.align: 'center'
   - title.style.fontSize: '18px'
   - If title is long, use array format: title.text: ['Line 1', 'Line 2'] to wrap text
   - Or use \\n in string for line break: title.text: 'Long Title\\nContinued'

4. XAXIS/YAXIS LABELS - Wrap long labels:
   - xaxis.labels.rotate: -45 (for long category names)
   - xaxis.labels.trim: true

5. RESPONSIVE - Keep responsive breakpoints

Give only the options value and nothing else in a code block. Check JSON is valid once again."""
    interaction_type = "Apex-Chart-Options-Generation"

    prompt_to_update_chart = f"{prompt}\n\nExisting code: {code}\n\nChange instructions: {instructions}"
    
    chart_options, _ = get_llm_response(question_id, None, prompt_to_update_chart, 'GPT 4', interaction_type, None, None, None, None, extract_sql=False)  
    
    # Extracting the content inside the code block, irrespective of its type
    extracted_content = re.search(r'```(?:\w+\n)?([\s\S]*?)\n```', chart_options)
    options = extracted_content.group(1) if extracted_content else chart_options

    # if chart_type == 'apex':
    options = "this, this.chartOptions = " + options 
    
    response = {
            "chart_type": "apex",
            "chart_options": options,
            "chart_data": []	
        }
    
    return response

