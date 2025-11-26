import logging
import time
from functools import wraps
from typing import Any, Callable
import json

logger = logging.getLogger(__name__)


class QueryMetrics:
    """Track query generation metrics"""

    def __init__(self):
        self.metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "total_time": 0,
            "avg_time": 0,
            "llm_errors": 0,
            "sql_extraction_failures": 0,
            "validation_failures": 0,
            "db_execution_errors": 0
        }

    def record_success(self, duration: float):
        self.metrics["total_queries"] += 1
        self.metrics["successful_queries"] += 1
        self.metrics["total_time"] += duration
        self.metrics["avg_time"] = self.metrics["total_time"] / self.metrics["total_queries"]

    def record_failure(self, failure_type: str, duration: float):
        self.metrics["total_queries"] += 1
        self.metrics["failed_queries"] += 1
        self.metrics["total_time"] += duration
        if failure_type in self.metrics:
            self.metrics[failure_type] += 1

    def get_metrics(self) -> dict:
        return self.metrics.copy()

    def log_metrics(self):
        logger.info(f"Query Metrics: {json.dumps(self.metrics, indent=2)}")


# Global metrics instance
metrics = QueryMetrics()


def track_query_generation(func: Callable) -> Callable:
    """Decorator to track query generation metrics"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        question_id = kwargs.get("question_id", args[0] if args else "unknown")

        try:
            logger.info(f"Starting query generation for question_id: {question_id}")
            result = func(*args, **kwargs)

            duration = time.time() - start_time

            # Check if generation was successful
            if result and len(result) >= 2:
                sql, output = result[0], result[1]
                if sql and not (isinstance(output, str) and output.startswith("Error")):
                    metrics.record_success(duration)
                    logger.info(f"Query generation successful in {duration:.2f}s for question_id: {question_id}")
                else:
                    metrics.record_failure("failed_queries", duration)
                    logger.warning(f"Query generation failed in {duration:.2f}s for question_id: {question_id}")

            return result

        except Exception as e:
            duration = time.time() - start_time
            metrics.record_failure("failed_queries", duration)
            logger.error(f"Query generation exception in {duration:.2f}s for question_id: {question_id}: {e}", exc_info=True)
            raise

    return wrapper


def log_llm_call(question_id: str, prompt_length: int, response_length: int, duration: float, success: bool):
    """Log LLM API call details"""
    logger.info(f"""LLM Call Summary:
    Question ID: {question_id}
    Prompt Length: {prompt_length} chars
    Response Length: {response_length} chars
    Duration: {duration:.2f}s
    Success: {success}
    Tokens Est: {(prompt_length + response_length) / 4:.0f}
    """)


def log_sql_generation(question_id: str, question: str, sql: str, success: bool, error: str = None):
    """Log SQL generation details"""
    log_data = {
        "question_id": question_id,
        "question": question[:200],  # Truncate for logging
        "sql_length": len(sql) if sql else 0,
        "success": success,
        "error": error
    }

    if success:
        logger.info(f"SQL Generated: {json.dumps(log_data)}")
    else:
        logger.error(f"SQL Generation Failed: {json.dumps(log_data)}")
