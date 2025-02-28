"""
Tests for the logging and debugging facilities.
"""
import os
import logging
import tempfile
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from django.conf import settings
from contests.middleware import LoggingContextMiddleware
from contests.debug import log_function_call, profile_function, DebugTimer


class LoggingTest(TestCase):
    """Test case for the logging facilities."""
    
    def setUp(self):
        """Set up the test case."""
        self.factory = RequestFactory()
        
        # Create a temporary log file for testing
        self.temp_log_fd, self.temp_log_path = tempfile.mkstemp()
        
        # Configure a test logger
        self.logger = logging.getLogger('test_logger')
        self.logger.setLevel(logging.DEBUG)
        
        # Add a handler to the test logger
        self.handler = logging.FileHandler(self.temp_log_path)
        self.handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(levelname)s %(message)s')
        self.handler.setFormatter(formatter)
        self.logger.addHandler(self.handler)
        
        # Save the original DEBUG_MODE setting
        self.original_debug_mode = settings.DEBUG_MODE
        settings.DEBUG_MODE = True
    
    def tearDown(self):
        """Clean up after the test case."""
        # Remove the handler from the logger first
        if hasattr(self, 'logger') and hasattr(self, 'handler'):
            self.logger.removeHandler(self.handler)
            self.handler.close()  # Close the file handler
        
        # Close and remove the temporary log file
        try:
            if hasattr(self, 'temp_log_fd'):
                os.close(self.temp_log_fd)
            if hasattr(self, 'temp_log_path') and os.path.exists(self.temp_log_path):
                os.unlink(self.temp_log_path)
        except (OSError, PermissionError):
            # If we can't delete the file, just ignore it
            pass
        
        # Restore the original DEBUG_MODE setting
        if hasattr(self, 'original_debug_mode'):
            settings.DEBUG_MODE = self.original_debug_mode
    
    def test_middleware_adds_request_context(self):
        """Test that the middleware adds request context."""
        # Create a request
        request = self.factory.get('/play/?contest=test&user=testuser')
        
        # Create a mock get_response function that returns an HttpResponse
        get_response = MagicMock(return_value=HttpResponse("Test response"))
        
        # Create the middleware
        middleware = LoggingContextMiddleware(get_response)
        
        # Process the request through the middleware
        response = middleware(request)
        
        # Check that the request has a request_id
        self.assertTrue(hasattr(request, 'request_id'))
        
        # Check that the request has a log_context
        self.assertTrue(hasattr(request, 'log_context'))
        
        # Check that the log_context has the expected fields
        self.assertIn('request_id', request.log_context)
        self.assertIn('client_ip', request.log_context)
        self.assertIn('user_id', request.log_context)
        
        # Check that user_id was extracted from the query parameters
        self.assertEqual(request.log_context['user_id'], 'testuser')
    
    def test_log_function_call_decorator(self):
        """Test the log_function_call decorator."""
        # Define a function with the decorator
        @log_function_call
        def test_function(arg1, arg2):
            return arg1 + arg2
        
        # Call the function with some arguments
        with patch('contests.debug.logger') as mock_logger:
            result = test_function(1, 2)
            
            # Check that the function returned the expected result
            self.assertEqual(result, 3)
            
            # Check that the logger.debug method was called
            self.assertTrue(mock_logger.debug.called)
            
            # Check for partial string match in any call
            found_call = False
            for call in mock_logger.debug.call_args_list:
                args, kwargs = call
                if args and "Calling" in args[0] and "test_function" in args[0]:
                    found_call = True
                    break
            self.assertTrue(found_call, "Expected function call logging message not found")
    
    def test_profile_function_decorator(self):
        """Test the profile_function decorator."""
        # Define a function with the decorator
        @profile_function
        def test_function():
            return "result"
        
        # Call the function
        with patch('contests.debug.logger') as mock_logger:
            result = test_function()
            
            # Check that the function returned the expected result
            self.assertEqual(result, "result")
            
            # Check that the logger.debug method was called
            self.assertTrue(mock_logger.debug.called)
            
            # Check for partial string match in any call
            found_call = False
            for call in mock_logger.debug.call_args_list:
                args, kwargs = call
                if args and "Profiling" in args[0] and "starting" in args[0]:
                    found_call = True
                    break
            self.assertTrue(found_call, "Expected profiling start message not found")
    
    def test_debug_timer(self):
        """Test the DebugTimer context manager."""
        # Use the timer with a mock logger
        with patch('contests.debug.logger') as mock_logger:
            with DebugTimer("Test operation"):
                pass
            
            # Check that the logger.debug method was called
            self.assertTrue(mock_logger.debug.called)
            
            # Check for partial string match in any call
            found_start = False
            found_complete = False
            for call in mock_logger.debug.call_args_list:
                args, kwargs = call
                if args:
                    if "Starting timer" in args[0]:
                        found_start = True
                    if "completed in" in args[0]:
                        found_complete = True
            
            self.assertTrue(found_start, "Expected timer start message not found")
            self.assertTrue(found_complete, "Expected timer completion message not found")
    
    def test_log_levels(self):
        """Test that different log levels are properly recorded."""
        # Log messages at different levels
        self.logger.debug("Debug message")
        self.logger.info("Info message")
        self.logger.warning("Warning message")
        self.logger.error("Error message")
        self.logger.critical("Critical message")
        
        # Force handlers to flush
        self.handler.flush()
        
        # Read the log file
        with open(self.temp_log_path, 'r') as f:
            log_content = f.read()
        
        # Check that all messages were logged
        self.assertIn("DEBUG Debug message", log_content)
        self.assertIn("INFO Info message", log_content)
        self.assertIn("WARNING Warning message", log_content)
        self.assertIn("ERROR Error message", log_content)
        self.assertIn("CRITICAL Critical message", log_content) 