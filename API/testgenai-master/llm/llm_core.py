from abc import ABC, abstractmethod
from langchain.chains import LLMChain
from langchain_openai import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from llm.prompts import get_output_format_prompt
from config import settings
from self_db.crud import log_exception
from util.util import extract_sql_from_code_blocks
from self_db import create_interaction
import time
import logging
from openai import RateLimitError, APIError, Timeout

logger = logging.getLogger(__name__)


class LLMStrategy(ABC):
    @abstractmethod
    def get_llm_qna_response(self):
        pass


class GPT4Strategy(LLMStrategy):
    def get_llm_qna_response(self, prompt, max_retries=None):
        """Get LLM response with retry logic and error handling"""

        if max_retries is None:
            max_retries = settings.llm_max_retries

        for attempt in range(max_retries):
            try:
                prompt_template = """{question}"""

                llm = AzureChatOpenAI(
                    azure_endpoint=settings.azure_openai_endpoint,
                    api_key=settings.azure_openai_api_key,
                    deployment_name=settings.azure_openai_deployment_name,
                    api_version=settings.azure_openai_api_version,
                    temperature=0,
                    request_timeout=settings.llm_timeout_seconds
                )

                llm_chain = LLMChain(
                    llm=llm,
                    prompt=PromptTemplate.from_template(prompt_template)
                )

                resp = llm_chain(prompt)

                # Validate response
                if not resp or 'text' not in resp or not resp['text'].strip():
                    logger.error(f"Empty LLM response on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return "Error: Unable to generate response. Please try rephrasing your question."

                return resp['text']

            except Timeout as e:
                logger.error(f"Timeout on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return "Error: Request timed out. Please try again or simplify your question."

            except RateLimitError as e:
                logger.error(f"Rate limit on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)  # Wait longer for rate limits
                    continue
                return "Error: Too many requests. Please wait a moment and try again."

            except APIError as e:
                logger.error(f"API error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return "Error: Azure OpenAI service error. Please try again."

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return f"Error: {str(e)}"

        return "Error: Failed after maximum retries. Please contact support."


class GPT35Strategy(LLMStrategy):
    def get_llm_qna_response(self, prompt, max_retries=None):
        """Get LLM response with retry logic and error handling"""

        if max_retries is None:
            max_retries = settings.llm_max_retries

        for attempt in range(max_retries):
            try:
                prompt_template = """{question}"""

                llm = AzureChatOpenAI(
                    azure_endpoint=settings.azure_openai_endpoint,
                    api_key=settings.azure_openai_api_key,
                    deployment_name=settings.azure_openai_deployment_name,
                    api_version=settings.azure_openai_api_version,
                    temperature=0,
                    request_timeout=settings.llm_timeout_seconds
                )

                llm_chain = LLMChain(
                    llm=llm,
                    prompt=PromptTemplate.from_template(prompt_template)
                )

                resp = llm_chain(prompt)

                # Validate response
                if not resp or 'text' not in resp or not resp['text'].strip():
                    logger.error(f"Empty LLM response on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return "Error: Unable to generate response. Please try rephrasing your question."

                return resp['text']

            except Timeout as e:
                logger.error(f"Timeout on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return "Error: Request timed out. Please try again or simplify your question."

            except RateLimitError as e:
                logger.error(f"Rate limit on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)  # Wait longer for rate limits
                    continue
                return "Error: Too many requests. Please wait a moment and try again."

            except APIError as e:
                logger.error(f"API error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return "Error: Azure OpenAI service error. Please try again."

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}", exc_info=True)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return f"Error: {str(e)}"

        return "Error: Failed after maximum retries. Please contact support."


# Create a dictionary mapping model names to LLM strategy classes
llm_strategies = {
    'GPT 4': GPT4Strategy(),
    'GPT 3.5': GPT35Strategy(),
}


def llm_qna_response(model_to_use, prompt):
    llm_strategy = llm_strategies.get(model_to_use, GPT4Strategy())  # Default to GPT 4
    return llm_strategy.get_llm_qna_response(prompt)


def contains_table(llm_response, tables):
    tables_list = tables.split(',')
    for table in tables_list:
        if table.strip().lower() in llm_response.lower():
            return True
    return False


def get_llm_response(question_id, question_type, prompt, model_name, usage_type, tables, db_schema, query, ms_sql_prompt, extract_sql):
    start_time = time.time()
    llm_response = llm_qna_response(model_name, prompt)
    time_taken = time.time() - start_time

    is_valid_question = True

    if extract_sql == True:
        try:
            extracted_sql = extract_sql_from_code_blocks(llm_response)
        except Exception as e:
            log_exception(e, 'get_llm_response')
            extracted_sql = f"SQL Extraction Failed - LLM Response was  {llm_response}"

        try:
            create_interaction(
                interaction_type=usage_type,
                model=model_name,
                question_id=question_id,
                question_type=question_type,
                prompt=prompt,
                response=llm_response,
                sql_query_extracted=extracted_sql,
                tables=tables,
                db_schema=db_schema,
                query=query,
                ms_sql_prompt=ms_sql_prompt,
                time_taken=time_taken,
                is_valid_question=1 if is_valid_question else 0
            )
        except ValueError as e:
            return {"message": "Error while saving question", "error": str(e)}

        return extracted_sql,  is_valid_question
    else:
        try:
            create_interaction(
                interaction_type=usage_type,
                model=model_name,
                question_id=question_id,
                question_type=question_type,
                prompt=prompt,
                response=llm_response,
                sql_query_extracted='',
                tables=tables,
                db_schema=db_schema,
                query=query,
                ms_sql_prompt=ms_sql_prompt,
                time_taken=time_taken,
                is_valid_question=1 if is_valid_question else 0
            )
        except ValueError as e:
            return {"message": "Error while saving question", "error": str(e)}
        return llm_response, None


def format_db_output(question_id, question_type, db_output, user_query, usage_type):
    output_format_prompt = get_output_format_prompt(db_output, user_query)
    formatted_output, is_valid_question = get_llm_response(
        question_id, question_type, output_format_prompt,
        settings.model_to_use_output_formatting, usage_type,
        None, None, None, None, extract_sql=False
    )

    # Remove markdown code blocks if present
    import re
    formatted_output = re.sub(r'^```html\s*', '', formatted_output, flags=re.MULTILINE)
    formatted_output = re.sub(r'^```\s*', '', formatted_output, flags=re.MULTILINE)
    formatted_output = re.sub(r'\s*```$', '', formatted_output, flags=re.MULTILINE)
    formatted_output = formatted_output.strip()

    # Replace newline characters with <br>
    formatted_output = formatted_output.replace("\n", "")
    return formatted_output


def get_chart_image(file_path):
    import pandas as pd
    import json

    # Read the data
    df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_json(file_path)

    # Create data summary
    data_summary = {
        "columns": list(df.columns),
        "sample_data": df.head(5).to_dict('records'),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "row_count": len(df)
    }

    # Use Azure OpenAI to generate chart config
    prompt = f"""Given this data summary: {json.dumps(data_summary)}
    Generate a Python dictionary for an ApexCharts configuration that best visualizes this data.
    Return only valid Python dictionary code, no markdown or explanation."""

    chart_config_response = llm_qna_response("GPT 4", prompt)

    return {"code": chart_config_response, "library": "apex"}


def get_edited_chart(question_id, file_path, code, library, instructions):
    import pandas as pd
    import json

    df = pd.read_csv(file_path) if file_path.endswith('.csv') else pd.read_json(file_path)
    data_summary = {
        "columns": list(df.columns),
        "sample_data": df.head(5).to_dict('records')
    }

    prompt = f"""Given this existing chart code: {code}
    And this data: {json.dumps(data_summary)}
    Apply these instructions: {instructions}
    Return updated chart configuration as Python dictionary."""

    updated_config = llm_qna_response("GPT 4", prompt)

    return {"code": updated_config, "library": library}
