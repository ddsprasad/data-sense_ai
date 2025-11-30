from fastapi import FastAPI, HTTPException, Request, Depends, Header, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from models.request_models import QuestionRequestModel, FollowUpQuestionRequestModel, UserHistoryRequestModel, UserHistoryQuestionRequestModel, RelatedQuestionRequestModel, DislikeQuestionRequestModel, DeleteQuestionRequestModel, RenameQuestionRequestModel, SharedHistoryQuestionRequestModel, UserValidationRequestModel, QuestionTagsRequestModel, ChartsRequestModel, ChartEditRequestModel, ChartOptionsRequestModel, ChartOptionsEditRequestModel, ChartOptionsSaveEditedRequestModel, TrendingQuestionsRequestModel
from self_db import create_question, get_user_history_question, get_user_history, update_question, set_answer_dislike, get_shared_story_history_question, rename_question, delete_question, get_trending_questions, get_user_details, update_question_tags, update_question_updated_at, update_question_chart_info, get_all_databases, get_trending_questions_by_database
from app_init.init_app import create_vector_store, create_rag_vector_store
from llm import api_handlers
from llm.response_cache import get_response_cache
from llm.async_handlers import run_in_executor, get_tags_async, get_related_questions_async, get_additional_insights_async
from self_db import get_db
import asyncio
import time, json
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader
import shutil
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
import logging

# Initialize logging system FIRST (before any other initialization)
from logging_setup.logging_config import setup_logging, get_logger
from middleware.logging_middleware import LoggingMiddleware, PerformanceLoggingMiddleware

# Setup logging
setup_logging(
    log_dir="logs",
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    enable_console=True,
    enable_json=True,
    enable_colored_console=True
)

# Get logger for this module
logger = get_logger(__name__)

#RAG = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")
RAG = ""




# Using Smart Vector Store V2 with automated schema discovery
logger.info("Initializing DataSense with Smart Schema Discovery...")
vector_store_from_metadata_two, create_statement_dict_two = create_vector_store('data/table_keywords.json')

rag_vector_store = create_rag_vector_store()

def select_vector_version(version: str):
    if version == 'v2' or version == 'v3' or version == 'v4':
        return vector_store_from_metadata_two, create_statement_dict_two
    else:
        # Default to v2 for any other version (v1, etc.)
        return vector_store_from_metadata_two, create_statement_dict_two
    
def select_model(version: str):
    if version == 'v1' or version == 'v2':
        return 'GPT 4'
    elif version == 'v3':
        return 'GPT 3.5'
    elif version == 'v4':
        return 'Deep Seek 33B'
   
    
# TEMP api keys until we implement proper auth

# Assuming we already have the 30 API keys from the previous response
api_keys_30 = [
    'f655b043c9291c2122e6648f0056da0c', 'abb7275d95dae5bd158f80c4b4dc6441',
    '281fbd6804764772b030a966637b2c8c', 'bbcb930f579ab9bcd374a0d2951eee64',
    'a71fdfe3f59c9b193f44d0e7a5a24af8', '4c8fb0021457984d047a570dd8d787ad',
    'ec5b214fcbc4278bd67003e0b7826eca', 'b1903de458444b447a0efa5eb17d8463',
    'a4f7557724a66152f14a127c2d3a66be', 'c1aaa7e34391f4746e351f3e583b050d',
    '1a2f5ac902134feb505a665d5e97a815', 'd1042993fccd77b8a0c3d5d96e269ecd',
    '265dae51964f74d397daed555708c3ff', '4c05156c16741e93743af7a32c29051e',
    '8d6a5cc2553aa94e0d8f3f5d4972569c', '032bd43b675077765426282b4e934c7d',
    'dd4aaf8a0ea83a893ec277e9bcc3fdb2', '2fc7e9bf1c5b5cae80dead115d0d387e',
    '8d28b4456b13d0a6c3fe29baaebe7b1a', '1603dba958ce506e2091184aa086b43f',
    '2a9c810721d3ce47309189732a907390', 'fa9015ea78e1cc14a77802070a65d760',
    '085a36ceb8c4fa396fd22c3312b414ec', '6345bbc0f9813930d4c829e7a41544d2',
    '832d6a7bf3c480ac893334de82a08f6f', '257e9a8fd9af8e411ad07230fd23820a',
    'dcb6e2c29b7da9a6da5351bbdb9156ee', '4ae1a8e7fb3c7a3fed4b121f2ff7be6e',
    '3e4826dda68ea51c22ae3009cbd54699', '81d09bf751a61f2304fb71e74e5f2aec'
]

# Create a mapping between user IDs and API keys
user_ids = range(300, 330 + 1)  # User IDs from 300 to 330
user_api_map = dict(zip(user_ids, api_keys_30))

# To create a reverse mapping (API key to user ID)
api_user_map = {v: k for k, v in user_api_map.items()}

# Function to get API key by user ID
def get_api_key_for_user(user_id):
    return user_api_map.get(user_id)

# Function to get user ID by API key
def get_user_id(api_key):
    return api_user_map.get(api_key)

def get_api_key(authorization: str = Header(None)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="API key missing or invalid")
    api_key = authorization[7:]  # Extract the key part from "Bearer YOUR_API_KEY"
    user_id = get_user_id(api_key)
    if user_id is None or user_id < 300 or user_id > 330:
        raise HTTPException(status_code=401, detail="API key invalid")    
    return api_key

# End of temp auth



app = FastAPI(
    title="DataSense API",
    description="AI-powered data analysis and SQL query generation",
    version="2.0.0"
)

origins = ["*"]

# Add CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Add performance monitoring middleware (logs slow requests > 1000ms)
app.add_middleware(PerformanceLoggingMiddleware, slow_request_threshold_ms=1000.0)

logger.info("FastAPI application initialized with logging middleware")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 404:
        # For a JSON response
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    elif exc.status_code == 401:
        # For a JSON response
        return JSONResponse({"detail": "API key missing or invalid"}, status_code=401)

    #return await request.app.default_exception_handler(request, exc)
    return JSONResponse({"detail": "Something went wrong!"}, status_code=exc.status_code)

# Handle h11 protocol errors gracefully (client disconnections)
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Check if it's an h11 LocalProtocolError (client disconnected)
    if "h11" in str(type(exc).__module__) or "LocalProtocolError" in str(type(exc).__name__):
        logger.warning(f"Client disconnected during request: {request.url.path}")
        # Don't try to send a response - client is gone
        return None

    # For other exceptions, log and return error
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        {"detail": "Internal server error"},
        status_code=500
    )


@app.post("/{version}/original-question")
async def answer_original_question(request_data: QuestionRequestModel, version: str, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    try:
        start_time = time.time()
        user_id = request_data.user_id
        question_id = str(request_data.question_id)
        question_asked = request_data.question_asked
        question_type = "Original-Question"

        # Check cache first for faster response
        cache = get_response_cache()
        cached_response = cache.get(question_asked, "original")
        if cached_response:
            logger.info(f"Cache hit for question: {question_asked[:50]}...")
            answered_at = datetime.now().strftime("%B %d, %Y, %H:%M:%S")
            return {
                "question_id": question_id,
                "sql": cached_response.get("sql"),
                "answer": cached_response.get("answer"),
                "answered_at": answered_at,
                "show_chart": cached_response.get("show_chart", 0),
                "show_sql": cached_response.get("show_sql", 0),
                "cached": True
            }

        # Insert the question first for logging purposes
        try:
            create_question(db, user_id, question_id, question_type, None, question_asked)
        except ValueError as e:
            logger.error(f"Error saving question: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error while saving question: {str(e)}")

        vector_store_from_metadata, create_statement_dict = select_vector_version(version)
        model_to_use = select_model(version)

        # Run the question processing in executor (non-blocking)
        extracted_sql, formatted_output, found_matching_sql, show_chart, show_sql = await run_in_executor(
            api_handlers.original_question_response,
            question_id, question_type, question_asked,
            vector_store_from_metadata, create_statement_dict,
            True,  # Enable SQL reuse
            model_to_use, rag_vector_store
        )

        # Check if the final database response is an error
        if formatted_output and 'ran into error' in formatted_output:
            logger.error(f"Query execution failed for question_id {question_id}: {formatted_output}")
            raise HTTPException(status_code=500, detail=f"Failed to execute query: {formatted_output}")

        time_taken = time.time() - start_time

        # Update the question with the time_taken now
        answered_at = datetime.now().strftime("%B %d, %Y, %H:%M:%S")
        try:
            update_question(user_id, question_id, question_type, round(time_taken, 2), found_matching_sql, formatted_output, extracted_sql, answered_at, show_chart, show_sql)
        except ValueError as e:
            logger.error(f"Error updating question: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error while updating question: {str(e)}")

        # Cache the successful response
        cache.set(question_asked, {
            "sql": extracted_sql,
            "answer": formatted_output,
            "show_chart": show_chart,
            "show_sql": show_sql
        }, "original", ttl=3600)

        return {"question_id": question_id, "sql": extracted_sql, "answer": formatted_output, "answered_at": answered_at, "show_chart": show_chart, "show_sql": show_sql}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in original-question endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    
@app.post("/{version}/additional-insights")
async def answer_additional_insights(request_data: QuestionRequestModel, version: str, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    try:
        start_time = time.time()
        user_id = request_data.user_id
        question_id = str(request_data.question_id)
        question_asked = request_data.question_asked
        question_type = "Additional-Insights"

        # Check cache first
        cache = get_response_cache()
        cached_response = cache.get(question_asked, "insights")
        if cached_response:
            logger.info(f"Cache hit for insights: {question_asked[:50]}...")
            answered_at = datetime.now().strftime("%B %d, %Y, at %H:%M:%S")
            return {
                "question_id": question_id,
                "sql": cached_response.get("sql"),
                "answer": cached_response.get("answer"),
                "answered_at": answered_at,
                "cached": True
            }

        try:
            create_question(db, user_id, question_id, question_type, None, question_asked)
        except ValueError as e:
            logger.error(f"Error saving question for insights: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error while saving question: {str(e)}")

        vector_store_from_metadata, create_statement_dict = select_vector_version(version)
        model_to_use = select_model(version)

        # Run async
        extracted_sql, formatted_output = await run_in_executor(
            api_handlers.additional_insights_response,
            question_id, question_type, question_asked,
            vector_store_from_metadata, create_statement_dict, model_to_use
        )

        # Check if the final database response is an error
        if formatted_output and 'ran into error' in formatted_output:
            raise HTTPException(status_code=500, detail="Failed to execute query after several attempts.")

        time_taken = time.time() - start_time

        # Update the question with the time_taken now
        answered_at = datetime.now().strftime("%B %d, %Y, at %H:%M:%S")
        try:
            update_question(user_id, question_id, question_type, round(time_taken, 2), False, formatted_output, extracted_sql, answered_at, None, None)
        except ValueError as e:
            logger.error(f"Error updating question for insights: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error while updating question: {str(e)}")

        # Cache the response
        cache.set(question_asked, {"sql": extracted_sql, "answer": formatted_output}, "insights", ttl=3600)

        return {"question_id": question_id, "sql": extracted_sql, "answer": formatted_output, "answered_at": answered_at}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in additional-insights endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.post("/{version}/related-questions")
async def get_related_questions(request_data: RelatedQuestionRequestModel, version: str, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    start_time = time.time()
    user_id = request_data.user_id
    question_id = str(request_data.question_id)
    question_asked = request_data.question_asked
    question_type = "Related Questions"

    # Check cache first
    cache = get_response_cache()
    cached_response = cache.get(question_asked, "related")
    if cached_response:
        logger.info(f"Cache hit for related questions: {question_asked[:50]}...")
        return {"related_questions": cached_response, "cached": True}

    try:
        create_question(db, user_id, question_id, question_type, None, question_asked)
    except ValueError as e:
        return {"message": "Error while saving question", "error": str(e)}

    vector_store_from_metadata, create_statement_dict = select_vector_version(version)
    model_to_use = select_model(version)

    # Run async
    related_questions = await run_in_executor(
        api_handlers.related_questions_response,
        question_id, question_type, question_asked,
        vector_store_from_metadata, create_statement_dict, model_to_use
    )

    time_taken = time.time() - start_time

    try:
        update_question(user_id, question_id, question_type, round(time_taken, 2), False, None, None, None, None, None)
    except ValueError as e:
        return {"message": "Error while updating question", "error": str(e)}

    # Cache the response
    cache.set(question_asked, related_questions, "related", ttl=3600)

    return {"related_questions": related_questions}


@app.post("/{version}/follow-up-question")
async def answer_follow_up_question(request_data: FollowUpQuestionRequestModel, version: str, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    start_time = time.time()
    user_id = request_data.user_id
    parent_question_id = str(request_data.parent_question_id)
    question_id = str(request_data.question_id)
    question_asked = request_data.question_asked
    question_type = "Follow-Up-Question"

    # Insert the question first for logging purposes
    try:
        create_question(db, user_id, question_id, question_type, parent_question_id, question_asked)
    except ValueError as e:
        return {"message": "Error while saving question", "error": str(e)}

    vector_store_from_metadata, create_statement_dict = select_vector_version(version)
    model_to_use = select_model(version)

    # Run async
    extracted_sql, formatted_output, show_chart, show_sql = await run_in_executor(
        api_handlers.followup_question_response,
        question_id, question_type, parent_question_id, question_asked,
        vector_store_from_metadata, create_statement_dict, model_to_use, rag_vector_store
    )

    # Check if the final database response is an error
    if formatted_output and 'ran into error' in formatted_output:
        raise HTTPException(status_code=500, detail="Failed to execute query after several attempts.")

    time_taken = time.time() - start_time

    # Update the question with the time_taken now
    answered_at = datetime.now().strftime("%B %d, %Y, at %H:%M:%S")
    try:
        update_question(user_id, question_id, question_type, round(time_taken, 2), False, formatted_output, extracted_sql, answered_at, show_chart, show_sql)
        update_question_updated_at(parent_question_id, user_id)
    except ValueError as e:
        return {"message": "Error while updating question", "error": str(e)}

    return {"question_id": question_id, "parent_question_id": parent_question_id, "sql": extracted_sql, "answer": formatted_output, "answered_at": answered_at, "show_chart": show_chart, "show_sql": show_sql}


@app.post("/{version}/get-tags")
async def get_question_tags(request_data: QuestionTagsRequestModel, api_key: str = Depends(get_api_key)):
    question_id = request_data.question_id

    # Check cache
    cache = get_response_cache()
    cached_tags = cache.get(question_id, "tags")
    if cached_tags:
        return cached_tags

    tags = await run_in_executor(api_handlers.get_tags, question_id)

    try:
        update_question_tags(question_id, tags)
    except ValueError as e:
        return {"message": "Error while updating question", "error": str(e)}

    # Cache the tags
    if tags:
        cache.set(question_id, tags, "tags", ttl=7200)

    return tags


@app.post("/{version}/user-history")
def read_user_history(request_data: UserHistoryRequestModel, api_key: str = Depends(get_api_key)):  
    user_id = request_data.user_id
    history = get_user_history(user_id)   
    return history

@app.post("/{version}/user-history-question")
def read_history_for_question_id(request_data: UserHistoryQuestionRequestModel, api_key: str = Depends(get_api_key)):
    user_id = request_data.user_id
    question_id = request_data.question_id
    history = get_user_history_question(user_id, question_id)   
    return history

@app.post("/{version}/shared-story-history-question")
def read_shared_story_history_for_question_id(request_data: SharedHistoryQuestionRequestModel, api_key: str = Depends(get_api_key)):    
    question_id = request_data.question_id
    story = get_shared_story_history_question(question_id)   
    return story

@app.post("/{version}/trending-questions")
def read_trending_questions(request_data: TrendingQuestionsRequestModel = None, api_key: str = Depends(get_api_key)):
    if request_data and request_data.database_name:
        trending_questions = get_trending_questions_by_database(request_data.database_name)
    else:
        trending_questions = get_trending_questions()
    return trending_questions


@app.get("/{version}/databases")
def list_databases(api_key: str = Depends(get_api_key)):
    """
    Get all available databases from SQL Server.
    Returns a list of database names that users can query.
    """
    databases = get_all_databases()
    return {"databases": databases}

@app.post("/{version}/rename")
def read_history_for_question_id(request_data: RenameQuestionRequestModel, api_key: str = Depends(get_api_key)):     
    new_name = request_data.new_name
    user_id = request_data.user_id
    question_id = request_data.question_id    
    rename_question(user_id, question_id, new_name)   
    return 'ok'

@app.post("/{version}/delete")
def read_history_for_question_id(request_data: DeleteQuestionRequestModel, api_key: str = Depends(get_api_key)):         
    user_id = request_data.user_id
    question_id = request_data.question_id
    delete_question(user_id, question_id)   
    return 'ok'

@app.post("/{version}/dislike")
def read_history_for_question_id(request_data: DislikeQuestionRequestModel, api_key: str = Depends(get_api_key)):     
    dislike = request_data.dislike
    user_id = request_data.user_id
    question_id = request_data.question_id

    if dislike not in [0, 1]:
        raise HTTPException(status_code=404, detail="Invalid value for dislike")
    
    set_answer_dislike(user_id, question_id, dislike)   
    return 'ok'

@app.post("/{version}/validate-user")
def check_user_is_valid(request_data: UserValidationRequestModel):
    username = request_data.username
    password = request_data.password
    user_details = get_user_details(username, password)
    user_details["api_key"] = get_api_key_for_user(user_details["user_id"])
    return user_details


@app.get("/{version}/cache-stats")
def get_cache_stats(api_key: str = Depends(get_api_key)):
    """Get cache statistics for monitoring performance."""
    cache = get_response_cache()
    stats = cache.get_stats()
    # Cleanup expired entries
    cleaned = cache.cleanup_expired()
    stats["cleaned_expired"] = cleaned
    return stats


@app.post("/{version}/cache-clear")
def clear_cache(api_key: str = Depends(get_api_key)):
    """Clear all cached responses."""
    cache = get_response_cache()
    cache.clear()
    return {"message": "Cache cleared successfully"}


@app.post("/{version}/get-chart-img")
def get_chart_img(request_data: ChartsRequestModel, api_key: str = Depends(get_api_key)):    
    question_id = request_data.question_id    
    file_id = request_data.file_id 
    chart_img = api_handlers.get_charts(question_id, file_id)
    return chart_img

@app.post("/{version}/edit-chart-img")
def edit_chart_img(request_data: ChartEditRequestModel, api_key: str = Depends(get_api_key)): 
    question_id = request_data.question_id     
    file_id = request_data.file_id 
    code = request_data.code 
    library = request_data.library 
    instructions = request_data.instructions    
    chart_img = api_handlers.edit_chart(question_id, file_id, code, library, instructions)   
    return chart_img

@app.post("/{version}/get-charts")
def get_chart(request_data: ChartOptionsRequestModel, version: str, api_key: str = Depends(get_api_key)):
    """Generate chart options for a given question's result set"""
    try:
        question_id = str(request_data.question_id)
        user_id = request_data.user_id

        logger.info(f"Chart request for question_id: {question_id}, user_id: {user_id}")

        # First check if chart already exists in database
        from self_db import get_question_chart_info
        saved_chart = get_question_chart_info(question_id)
        if saved_chart:
            logger.info(f"Chart loaded from database for question_id: {question_id}")
            # Parse chart_data if it's a string
            chart_data = saved_chart.get('chart_data', '[]')
            if isinstance(chart_data, str):
                try:
                    chart_data = json.loads(chart_data)
                except json.JSONDecodeError:
                    chart_data = []
            return {
                "chart_type": saved_chart['chart_type'],
                "chart_options": saved_chart['chart_options'],
                "chart_data": chart_data,
                "from_cache": True
            }

        # Generate chart configuration if not found in database
        chart_info = api_handlers.get_charts_code(question_id)

        # Check if chart generation resulted in an error
        if chart_info.get("chart_type") == "error":
            logger.error(f"Chart generation failed for question_id {question_id}: {chart_info.get('error')}")
            return {
                "message": "Chart generation failed",
                "error": chart_info.get('error'),
                "chart_type": "error"
            }

        # Save chart info to database
        try:
            chart_type = chart_info["chart_type"]
            chart_options = chart_info["chart_options"]
            chart_data = json.dumps(chart_info["chart_data"])
            update_question_chart_info(question_id, chart_type, chart_options, chart_data)
            logger.info(f"Chart info saved successfully for question_id: {question_id}")
        except (ValueError, KeyError) as e:
            logger.error(f"Error updating chart info for question_id {question_id}: {e}")
            return {"message": "Error while saving chart", "error": str(e)}

        return chart_info

    except Exception as e:
        logger.error(f"Unexpected error in get_chart endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate chart: {str(e)}")


@app.post("/{version}/edit-charts")
def edit_chart(request_data: ChartOptionsEditRequestModel, version: str, api_key: str = Depends(get_api_key)):                 
    question_id = str(request_data.question_id)   
    user_id = request_data.user_id        
    code = request_data.code
    instructions = request_data.instructions    
    apex_chart_options = api_handlers.edit_charts_code(question_id, code, instructions)       
    return apex_chart_options


@app.post("/{version}/save-edited-charts")
def save_edited_chart(request_data: ChartOptionsSaveEditedRequestModel, version: str, api_key: str = Depends(get_api_key)):                 
    question_id = str(request_data.question_id)   
    user_id = request_data.user_id        
    chart_type = request_data.chart_type
    chart_options = request_data.chart_options     
    chart_data = "[]"
    
    try:               
        update_question_chart_info(question_id, chart_type, chart_options, chart_data)  
    except ValueError as e:
        return {"message": "Error while updating question", "error": str(e)}
        
    return 'ok'

    
    
#RAG
@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    with open(f"/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    loader = PyPDFLoader(file.filename)
    pages = loader.load_and_split()

    len(pages)
    full_document = ""

    for page in pages:
        full_document += page.page_content

    RAG.index(
        collection=[full_document],
        index_name="msc",
        max_document_length=512,
        split_documents=True,
    )
    return {"filename": file.filename}


@app.post("/{version}/original-question-rag")
def answer_original_question(request_data: QuestionRequestModel): 
    try:
        question_asked = request_data.question_asked 
        question_id = request_data.question_id
        retriever = RAG.as_langchain_retriever(k=10)
        prompt = ChatPromptTemplate.from_template(
        """Answer the following question in html format inside para tag, based only on the provided context:

        <context>
        {context}
        </context>

        Question: {input}"""
        )

        llm = ChatOpenAI(model='gpt-4-turbo-2024-04-09', temperature=0) #ChatOpenAI(model='gpt-4-0125-preview', temperature=0)
        

        document_chain = create_stuff_documents_chain(llm, prompt)


        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        response = retrieval_chain.invoke({"input": question_asked})
        answered_at = datetime.now().strftime("%B %d, %Y, %H:%M:%S")
        return {"question_id": question_id, "answer": response["answer"], "answered_at": answered_at}
    except Exception as e:
        detail = f"An error occurred: {str(e)}"
        raise HTTPException(status_code=500, detail=detail)

@app.get("/")
def read_history_for_question_id():      
    return "welcome"