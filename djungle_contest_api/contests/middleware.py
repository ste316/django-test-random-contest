"""
Middleware classes for the Djungle Contest API.
"""
import uuid
import logging
import threading

# Thread local storage for logging context
local = threading.local()

class LoggingContextMiddleware:
    """
    Middleware that adds request context to logs.
    
    This middleware adds request-specific information to the logging context,
    such as request IDs, user IDs, and client IPs. This information can then
    be included in log messages for better traceability.
    """
    
    def __init__(self, get_response):
        """
        Initialize the middleware.
        
        Args:
            get_response (callable): The next middleware or view in the chain.
        """
        self.get_response = get_response
        self.logger = logging.getLogger('contests.middleware')
    
    def __call__(self, request):
        """
        Process a request through the middleware.
        
        Args:
            request (HttpRequest): The request to process.
            
        Returns:
            HttpResponse: The response from the view.
        """
        # Generate a unique request ID
        request_id = str(uuid.uuid4())
        request.request_id = request_id
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            client_ip = x_forwarded_for.split(',')[0].strip()
        else:
            client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        # Get user ID if available
        # Check if user is authenticated, safely handle if user attribute doesn't exist
        if hasattr(request, 'user') and hasattr(request.user, 'id'):
            user_id = request.user.id
        else:
            user_id = 'anonymous'
            
        # Override with query parameter if present
        if 'user' in request.GET:
            user_id = request.GET.get('user')
        
        # Store context in thread local storage
        local.request_id = request_id
        local.client_ip = client_ip
        local.user_id = user_id
        
        # Add context to request object for use in views
        request.log_context = {
            'request_id': request_id,
            'client_ip': client_ip,
            'user_id': user_id
        }
        
        # Log the request
        self.logger.info(
            f"Request received: {request.method} {request.path}",
            extra=request.log_context
        )
        
        # Process the request
        response = self.get_response(request)
        
        # Log the response
        self.logger.info(
            f"Response sent: {response.status_code}",
            extra=request.log_context
        )
        
        # Clean up
        self._cleanup_thread_local()
        
        return response
    
    def _cleanup_thread_local(self):
        """
        Clean up thread local storage.
        
        This method should be called at the end of each request to prevent memory leaks.
        """
        if hasattr(local, 'request_id'):
            del local.request_id
        if hasattr(local, 'client_ip'):
            del local.client_ip
        if hasattr(local, 'user_id'):
            del local.user_id


class LoggingContextFilter(logging.Filter):
    """
    Logging filter that adds request context to log records.
    
    This filter adds request-specific information to log records,
    such as request IDs, user IDs, and client IPs. If these values
    are not available in the thread local storage (e.g., outside of
    a request context), default values are provided.
    """
    
    def filter(self, record):
        """
        Add request context to a log record.
        
        Args:
            record (LogRecord): The log record to modify.
            
        Returns:
            bool: Always True, indicating the record should be processed.
        """
        # Add request context to the log record with safe defaults
        if not hasattr(record, 'request_id'):
            record.request_id = getattr(local, 'request_id', 'no-request-id')
        
        if not hasattr(record, 'client_ip'):
            record.client_ip = getattr(local, 'client_ip', 'unknown')
        
        if not hasattr(record, 'user_id'):
            record.user_id = getattr(local, 'user_id', 'anonymous')
        
        return True 