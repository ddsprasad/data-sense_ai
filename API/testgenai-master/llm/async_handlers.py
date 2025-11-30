"""
Async handlers for parallel processing of LLM requests.
Enables concurrent execution of related questions, insights, and tags.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Tuple, Dict, Any
import logging
from functools import partial

logger = logging.getLogger(__name__)

# Thread pool for running sync functions in async context
_executor = ThreadPoolExecutor(max_workers=10)


async def run_in_executor(func, *args, **kwargs):
    """Run a synchronous function in the thread pool executor."""
    loop = asyncio.get_event_loop()
    partial_func = partial(func, *args, **kwargs)
    return await loop.run_in_executor(_executor, partial_func)


async def get_parallel_responses(
    question_id: str,
    question_type: str,
    query: str,
    vector_store_from_metadata,
    create_statement_dict,
    model_to_use: str,
    rag_vector_store,
    get_related: bool = True,
    get_insights: bool = True
) -> Dict[str, Any]:
    """
    Get original answer, related questions, and additional insights in parallel.

    Args:
        question_id: Unique question identifier
        question_type: Type of question
        query: The user's question
        vector_store_from_metadata: Vector store for metadata
        create_statement_dict: Dictionary of table create statements
        model_to_use: LLM model to use
        rag_vector_store: RAG vector store
        get_related: Whether to fetch related questions
        get_insights: Whether to fetch additional insights

    Returns:
        Dictionary containing all responses
    """
    from llm.api_handlers import (
        original_question_response,
        related_questions_response,
        additional_insights_response
    )
    from llm.response_cache import get_response_cache

    cache = get_response_cache()

    # Check cache first for the main response
    cached_main = cache.get(query, "original")
    if cached_main:
        logger.info(f"Using cached main response for: {query[:50]}...")
        return cached_main

    # Create tasks for parallel execution
    tasks = []

    # Main question task (always run)
    main_task = run_in_executor(
        original_question_response,
        question_id,
        question_type,
        query,
        vector_store_from_metadata,
        create_statement_dict,
        True,  # bool_exact_question_reuse
        model_to_use,
        rag_vector_store
    )
    tasks.append(("main", main_task))

    # Related questions task (run in parallel)
    if get_related:
        related_task = run_in_executor(
            related_questions_response,
            question_id,
            question_type,
            query,
            vector_store_from_metadata,
            create_statement_dict,
            model_to_use
        )
        tasks.append(("related", related_task))

    # Execute all tasks in parallel
    results = {}
    task_names = [t[0] for t in tasks]
    task_futures = [t[1] for t in tasks]

    completed = await asyncio.gather(*task_futures, return_exceptions=True)

    for name, result in zip(task_names, completed):
        if isinstance(result, Exception):
            logger.error(f"Task {name} failed: {result}")
            results[name] = None
        else:
            results[name] = result

    # Process main response
    main_result = results.get("main")
    if main_result:
        extracted_sql, formatted_output, found_matching_sql, show_chart, show_sql = main_result

        response = {
            "sql": extracted_sql,
            "answer": formatted_output,
            "found_matching_sql": found_matching_sql,
            "show_chart": show_chart,
            "show_sql": show_sql,
            "related_questions": results.get("related")
        }

        # Cache the response
        cache.set(query, response, "original", ttl=3600)

        return response

    return {
        "sql": None,
        "answer": "Unable to process your question. Please try again.",
        "found_matching_sql": False,
        "show_chart": 0,
        "show_sql": 0,
        "related_questions": None
    }


async def get_additional_insights_async(
    question_id: str,
    question_type: str,
    query: str,
    vector_store_from_metadata,
    create_statement_dict,
    model_to_use: str
) -> Tuple[Optional[str], str]:
    """
    Get additional insights asynchronously.

    Returns:
        Tuple of (sql, formatted_output)
    """
    from llm.api_handlers import additional_insights_response
    from llm.response_cache import get_response_cache

    cache = get_response_cache()

    # Check cache
    cached = cache.get(query, "insights")
    if cached:
        return cached.get("sql"), cached.get("answer")

    result = await run_in_executor(
        additional_insights_response,
        question_id,
        question_type,
        query,
        vector_store_from_metadata,
        create_statement_dict,
        model_to_use
    )

    if result:
        sql, answer = result
        cache.set(query, {"sql": sql, "answer": answer}, "insights", ttl=3600)
        return sql, answer

    return None, "Unable to generate additional insights."


async def get_related_questions_async(
    question_id: str,
    question_type: str,
    query: str,
    vector_store_from_metadata,
    create_statement_dict,
    model_to_use: str
) -> Optional[str]:
    """
    Get related questions asynchronously.

    Returns:
        JSON string of related questions
    """
    from llm.api_handlers import related_questions_response
    from llm.response_cache import get_response_cache

    cache = get_response_cache()

    # Check cache
    cached = cache.get(query, "related")
    if cached:
        return cached

    result = await run_in_executor(
        related_questions_response,
        question_id,
        question_type,
        query,
        vector_store_from_metadata,
        create_statement_dict,
        model_to_use
    )

    if result:
        cache.set(query, result, "related", ttl=3600)

    return result


async def get_tags_async(question_id: str) -> Optional[str]:
    """Get tags for a question asynchronously."""
    from llm.api_handlers import get_tags
    from llm.response_cache import get_response_cache

    cache = get_response_cache()

    # Check cache by question_id
    cached = cache.get(question_id, "tags")
    if cached:
        return cached

    result = await run_in_executor(get_tags, question_id)

    if result:
        cache.set(question_id, result, "tags", ttl=7200)  # 2 hour cache for tags

    return result


def run_async(coro):
    """
    Run an async coroutine from sync code.
    Creates a new event loop if needed.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(coro)
