"""
API Request/Response Logging Middleware for FastAPI
Logs all incoming requests and outgoing responses with timing information
"""

import time
import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message
from typing import Callable
import logging

logger = logging.getLogger('api')


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all API requests and responses
    Captures request details, response status, and execution time
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()

        # Extract request details
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)

        # Get user_id from headers if available
        user_id = request.headers.get('user-id', None)

        # Log request
        logger.info(
            f"Request: {method} {path}",
            extra={
                'event': 'request_started',
                'method': method,
                'endpoint': path,
                'client_ip': client_ip,
                'query_params': query_params,
                'user_id': user_id,
                'user_agent': request.headers.get('user-agent', 'unknown')
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000  # Convert to ms

            # Log response
            logger.info(
                f"Response: {method} {path} - {response.status_code}",
                extra={
                    'event': 'request_completed',
                    'method': method,
                    'endpoint': path,
                    'client_ip': client_ip,
                    'status_code': response.status_code,
                    'execution_time': execution_time,
                    'user_id': user_id
                }
            )

            # Add custom header with execution time
            response.headers['X-Execution-Time'] = f"{execution_time:.2f}ms"

            return response

        except Exception as e:
            # Calculate execution time even for errors
            execution_time = (time.time() - start_time) * 1000

            # Log error
            logger.error(
                f"Request Failed: {method} {path} - {str(e)}",
                extra={
                    'event': 'request_failed',
                    'method': method,
                    'endpoint': path,
                    'client_ip': client_ip,
                    'execution_time': execution_time,
                    'error': str(e),
                    'user_id': user_id
                },
                exc_info=True
            )

            # Re-raise the exception to be handled by FastAPI
            raise


class RequestBodyLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log request bodies (use with caution for sensitive data)
    Only logs if LOG_REQUEST_BODIES environment variable is set
    """

    async def set_body(self, request: Request):
        """Read and cache the request body"""
        receive_ = await request._receive()

        async def receive() -> Message:
            return receive_

        request._receive = receive

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only log request bodies if explicitly enabled
        import os
        if os.getenv('LOG_REQUEST_BODIES', 'false').lower() == 'true':
            try:
                # Read request body
                await self.set_body(request)
                body = await request.body()

                # Try to parse as JSON
                try:
                    body_json = json.loads(body.decode('utf-8'))
                    # Mask sensitive fields
                    masked_body = self.mask_sensitive_data(body_json)

                    logger.debug(
                        f"Request Body: {request.url.path}",
                        extra={
                            'event': 'request_body',
                            'endpoint': request.url.path,
                            'body': masked_body
                        }
                    )
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Not JSON or can't decode
                    logger.debug(
                        f"Request Body (non-JSON): {request.url.path}",
                        extra={
                            'event': 'request_body',
                            'endpoint': request.url.path,
                            'body_size': len(body)
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to log request body: {e}")

        response = await call_next(request)
        return response

    @staticmethod
    def mask_sensitive_data(data: dict) -> dict:
        """Mask sensitive fields in request body"""
        sensitive_fields = ['password', 'token', 'api_key', 'secret', 'credential']
        masked_data = data.copy()

        for key in masked_data:
            if any(field in key.lower() for field in sensitive_fields):
                masked_data[key] = '***MASKED***'

        return masked_data


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log slow requests
    Logs warnings for requests exceeding threshold
    """

    def __init__(self, app, slow_request_threshold_ms: float = 1000.0):
        super().__init__(app)
        self.slow_request_threshold_ms = slow_request_threshold_ms
        self.perf_logger = logging.getLogger('performance')

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        response = await call_next(request)

        execution_time = (time.time() - start_time) * 1000  # ms

        # Log slow requests
        if execution_time > self.slow_request_threshold_ms:
            self.perf_logger.warning(
                f"Slow Request: {request.method} {request.url.path} took {execution_time:.2f}ms",
                extra={
                    'event': 'slow_request',
                    'method': request.method,
                    'endpoint': request.url.path,
                    'execution_time': execution_time,
                    'threshold': self.slow_request_threshold_ms
                }
            )

        return response
