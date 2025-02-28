"""
Debugging utilities for the Djungle Contest API.

This module provides utilities for debugging and logging in the Djungle Contest API.
"""
import logging
import time
import functools
import traceback
from django.conf import settings

# Configure logger
logger = logging.getLogger('contests.debug')

def log_function_call(func):
    """
    Decorator to log function calls including arguments and return values.
    
    This decorator logs the function name, arguments, and return value
    when a function is called. It also logs any exceptions raised by the function.
    It only logs detailed information if DEBUG_MODE is True in settings.
    
    Args:
        func: The function to decorate.
        
    Returns:
        The decorated function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        function_name = func.__name__
        module_name = func.__module__
        
        # Only log detailed information in debug mode
        if settings.DEBUG_MODE:
            # Stringify arguments for logging, but avoid excessive output
            args_str = str(args)[:500] + ("..." if len(str(args)) > 500 else "")
            kwargs_str = str(kwargs)[:500] + ("..." if len(str(kwargs)) > 500 else "")
            
            # Log the function call
            logger.debug(f"Calling {module_name}.{function_name} with args={args_str}, kwargs={kwargs_str}")
            
            # Measure execution time
            start_time = time.time()
            
            try:
                # Call the function
                result = func(*args, **kwargs)
                
                # Log the return value
                execution_time = time.time() - start_time
                result_str = str(result)[:500] + ("..." if len(str(result)) > 500 else "")
                logger.debug(f"{module_name}.{function_name} returned {result_str} (took {execution_time:.4f}s)")
                
                return result
            except Exception as e:
                # Log the exception
                execution_time = time.time() - start_time
                logger.error(f"{module_name}.{function_name} raised {type(e).__name__}: {str(e)} (took {execution_time:.4f}s)")
                logger.debug(f"Traceback: {traceback.format_exc()}")
                raise
        else:
            # In non-debug mode, just call the function
            return func(*args, **kwargs)
    
    return wrapper

def debug_print(*args, **kwargs):
    """
    Print debug information only if DEBUG_MODE is True.
    
    This function works like the built-in print function, but only
    prints if DEBUG_MODE is True in settings.
    
    Args:
        *args: Positional arguments to print.
        **kwargs: Keyword arguments for the print function.
    """
    if settings.DEBUG_MODE:
        print("[DEBUG]", *args, **kwargs)

def get_memory_usage():
    """
    Get the current memory usage of the Python process.
    
    Returns:
        dict: Memory usage information in MB.
    """
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        'rss': memory_info.rss / (1024 * 1024),  # RSS in MB
        'vms': memory_info.vms / (1024 * 1024),  # VMS in MB
    }

def profile_function(func):
    """
    Decorator to profile function execution time and memory usage.
    
    This decorator logs the function execution time and memory usage
    before and after the function call.
    
    Args:
        func: The function to decorate.
        
    Returns:
        The decorated function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.DEBUG_MODE:
            return func(*args, **kwargs)
        
        function_name = func.__name__
        module_name = func.__module__
        
        # Log start time and memory usage
        start_time = time.time()
        try:
            start_memory = get_memory_usage()
        except ImportError:
            start_memory = None
        
        logger.debug(f"Profiling {module_name}.{function_name}: starting")
        if start_memory:
            logger.debug(f"Memory before: RSS={start_memory['rss']:.2f}MB, VMS={start_memory['vms']:.2f}MB")
        
        try:
            # Call the function
            result = func(*args, **kwargs)
            
            # Log end time and memory usage
            end_time = time.time()
            execution_time = end_time - start_time
            
            logger.debug(f"Profiling {module_name}.{function_name}: completed in {execution_time:.4f}s")
            
            if start_memory:
                try:
                    end_memory = get_memory_usage()
                    memory_diff = {
                        'rss': end_memory['rss'] - start_memory['rss'],
                        'vms': end_memory['vms'] - start_memory['vms']
                    }
                    logger.debug(f"Memory after: RSS={end_memory['rss']:.2f}MB, VMS={end_memory['vms']:.2f}MB")
                    logger.debug(f"Memory diff: RSS={memory_diff['rss']:.2f}MB, VMS={memory_diff['vms']:.2f}MB")
                except Exception as e:
                    logger.warning(f"Error getting memory usage: {str(e)}")
            
            return result
        except Exception as e:
            # Log exception
            end_time = time.time()
            execution_time = end_time - start_time
            logger.error(f"Profiling {module_name}.{function_name}: failed after {execution_time:.4f}s with {type(e).__name__}: {str(e)}")
            raise
    
    return wrapper

class DebugTimer:
    """
    Context manager for timing code blocks.
    
    Example usage:
    ```
    with DebugTimer("My operation"):
        # Code to time goes here
    ```
    """
    
    def __init__(self, operation_name):
        """
        Initialize the timer.
        
        Args:
            operation_name (str): Name of the operation being timed.
        """
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        """
        Enter the context manager, starting the timer.
        
        Returns:
            DebugTimer: The timer instance.
        """
        self.start_time = time.time()
        if settings.DEBUG_MODE:
            logger.debug(f"Starting timer for '{self.operation_name}'")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context manager, stopping the timer and logging the elapsed time.
        
        Args:
            exc_type: Exception type if an exception was raised, None otherwise.
            exc_val: Exception value if an exception was raised, None otherwise.
            exc_tb: Exception traceback if an exception was raised, None otherwise.
        """
        end_time = time.time()
        elapsed_time = end_time - self.start_time
        
        if settings.DEBUG_MODE:
            if exc_type is None:
                logger.debug(f"'{self.operation_name}' completed in {elapsed_time:.4f}s")
            else:
                logger.error(f"'{self.operation_name}' failed after {elapsed_time:.4f}s with {exc_type.__name__}: {str(exc_val)}") 