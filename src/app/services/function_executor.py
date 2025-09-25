import asyncio
import json
import logging
import time
import re
import httpx
from typing import Dict, Any, Optional, List, Tuple, Union
import uuid
from pydantic import ValidationError

from ..schemas.function_tool import FunctionToolRead, AuthType
from ..utils.db_utils import with_worker_db
from ..crud.crud_function_tool import crud_function_tools

logger = logging.getLogger("function-executor")

class FunctionExecutor:
    """Service for executing function tools via HTTP requests."""
    
    def __init__(self, timeout_seconds: float = 30.0):
        """Initialize the function executor.
        
        Args:
            timeout_seconds: Maximum timeout for HTTP requests
        """
        self.timeout_seconds = timeout_seconds
        
    async def execute_function(
        self, 
        function_id: uuid.UUID, 
        parameters: Dict[str, Any],
        auth_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Execute a function tool by ID.
        
        Args:
            function_id: UUID of the function to execute
            parameters: Parameters to pass to the function
            auth_headers: Optional auth headers to include (for runtime auth)
            
        Returns:
            Dict containing the execution results
        """
        start_time = time.time()
        
        try:
            # Get the function tool definition
            function_tool = await with_worker_db(
                lambda db: crud_function_tools.get(db=db, id=function_id)
            )
            
            if not function_tool:
                raise ValueError(f"Function tool with ID {function_id} not found")
                
            if not function_tool.active:
                raise ValueError(f"Function tool '{function_tool.name}' is not active")
                
            # Execute the HTTP request
            response_data = await self._make_http_request(
                function_tool=function_tool,
                parameters=parameters,
                auth_headers=auth_headers
            )
            
            # Process the response
            result = self._process_response(function_tool, response_data)
            
            # Calculate execution time
            execution_time_ms = (time.time() - start_time) * 1000
            
            logger.warning(f"Function {function_tool.name} executed in {execution_time_ms}ms. The result is {result}.")  

            return {
                "success": True,
                "result": result,
                "execution_time_ms": execution_time_ms
            }
            
        except Exception as e:
            logger.error(f"Error executing function {function_id}: {str(e)}")
            
            # Calculate execution time even for errors
            execution_time_ms = (time.time() - start_time) * 1000
            
            return {
                "success": False,
                "result": {},
                "error": str(e),
                "execution_time_ms": execution_time_ms
            }
    
    async def _make_http_request(
        self,
        function_tool: FunctionToolRead,
        parameters: Dict[str, Any],
        auth_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make the actual HTTP request.
        
        Args:
            function_tool: The function tool definition
            parameters: Parameters to pass to the function
            auth_headers: Optional auth headers
            
        Returns:
            Dict containing the HTTP response data
        """
        # Construct the URL with path parameters
        url = self._build_url(function_tool, parameters)
        
        # Prepare headers
        headers = function_tool.headers.copy()
        if auth_headers:
            headers.update(auth_headers)
            
        # Handle authentication if required
        if function_tool.auth_required and not auth_headers:
            # In a real implementation, we would retrieve auth credentials from a secure store
            # This is a placeholder for demonstration
            if function_tool.auth_type == AuthType.BEARER:
                headers["Authorization"] = f"Bearer {parameters.get('auth_token', '')}"
            elif function_tool.auth_type == AuthType.API_KEY:
                headers["X-API-Key"] = parameters.get('api_key', '')
            elif function_tool.auth_type == AuthType.BASIC:
                # Basic auth would be handled by the httpx client directly
                pass
        
        # Prepare request body if needed
        request_body = None
        if function_tool.http_method in ("POST", "PUT", "PATCH"):
            request_body = self._build_request_body(function_tool, parameters)
        
        # Create query parameters for GET requests
        query_params = None
        if function_tool.http_method == "GET":
            query_params = self._build_query_params(function_tool, parameters)
        
        # Make the HTTP request
        logger.info(f"Making {function_tool.http_method} request to {url}")
        
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            if function_tool.http_method == "GET":
                response = await client.get(url, headers=headers, params=query_params)
            elif function_tool.http_method == "POST":
                response = await client.post(url, headers=headers, json=request_body)
            elif function_tool.http_method == "PUT":
                response = await client.put(url, headers=headers, json=request_body)
            elif function_tool.http_method == "DELETE":
                response = await client.delete(url, headers=headers)
            elif function_tool.http_method == "PATCH":
                response = await client.patch(url, headers=headers, json=request_body)
            else:
                raise ValueError(f"Unsupported HTTP method: {function_tool.http_method}")
        
        # Check for successful response
        if response.status_code >= 400:
            error_message = self._get_error_message(function_tool, response)
            raise ValueError(f"HTTP error {response.status_code}: {error_message}")
        
        # Parse and return the response
        try:
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            else:
                # For non-JSON responses, wrap the text in a dict
                return {"text": response.text}
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return {"text": response.text}
    
    def _build_url(self, function_tool: FunctionToolRead, parameters: Dict[str, Any]) -> str:
        """Build the full URL, replacing path parameters.
        
        Args:
            function_tool: The function tool definition
            parameters: Parameters to pass to the function
            
        Returns:
            Complete URL with path parameters replaced
        """
        base_url = function_tool.base_url.rstrip('/')
        endpoint_path = function_tool.endpoint_path.lstrip('/')
        
        # Replace path parameters (format: {param_name})
        path = endpoint_path
        for param_name, param_value in parameters.items():
            placeholder = "{" + param_name + "}"
            if placeholder in path:
                path = path.replace(placeholder, str(param_value))
        
        return f"{base_url}/{path}"
    
    def _build_request_body(self, function_tool: FunctionToolRead, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Build the request body from the template and parameters.
        
        Args:
            function_tool: The function tool definition
            parameters: Parameters to pass to the function
            
        Returns:
            Dict containing the request body
        """
        if not function_tool.request_template:
            # If no template is provided, use parameters as the body
            return parameters
        
        # Make a deep copy of the template
        body = json.loads(json.dumps(function_tool.request_template))
        
        # Replace parameter placeholders in the template (format: ${param_name})
        body_json = json.dumps(body)
        for param_name, param_value in parameters.items():
            placeholder = "${" + param_name + "}"
            body_json = body_json.replace(placeholder, json.dumps(param_value))
        
        # Parse the JSON back into a dict
        return json.loads(body_json)
    
    def _build_query_params(self, function_tool: FunctionToolRead, parameters: Dict[str, Any]) -> Dict[str, str]:
        """Build query parameters for GET requests.
        
        Args:
            function_tool: The function tool definition
            parameters: Parameters to pass to the function
            
        Returns:
            Dict containing query parameters
        """
        # Filter out parameters used in the path
        query_params = {}
        
        for param_name, param_value in parameters.items():
            # Skip parameters that are used in the path
            placeholder = "{" + param_name + "}"
            if placeholder not in function_tool.endpoint_path:
                # Convert all values to strings for query parameters
                query_params[param_name] = str(param_value)
                
        return query_params
    
    def _get_error_message(self, function_tool: FunctionToolRead, response) -> str:
        """Get an appropriate error message from the response.
        
        Args:
            function_tool: The function tool definition
            response: The HTTP response
            
        Returns:
            Error message string
        """
        # Check if there's a mapping for this status code
        if str(response.status_code) in function_tool.error_mapping:
            return function_tool.error_mapping[str(response.status_code)]
        
        # Try to parse the response body for error information
        try:
            if response.headers.get("content-type", "").startswith("application/json"):
                error_data = response.json()
                # Check common error fields
                for field in ["error", "message", "error_message", "errorMessage"]:
                    if field in error_data:
                        return str(error_data[field])
                return str(error_data)
            else:
                return response.text
        except Exception:
            # If we can't parse the response, return a generic message
            return f"HTTP {response.status_code} error"
    
    def _process_response(self, function_tool: FunctionToolRead, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the response according to the response mapping.
        
        Args:
            function_tool: The function tool definition
            response_data: The response data
            
        Returns:
            Processed response according to the mapping
        """
        if not function_tool.response_mapping:
            # If no mapping is provided, return the full response
            return response_data
        
        # Apply the response mapping
        result = {}
        for output_field, path in function_tool.response_mapping.items():
            try:
                value = self._extract_value_from_path(response_data, path)
                result[output_field] = value
            except (KeyError, IndexError) as e:
                logger.warning(f"Could not extract {path} from response: {e}")
                result[output_field] = None
                
        return result
    
    def _extract_value_from_path(self, data: Dict[str, Any], path: str) -> Any:
        """Extract a value from a nested dictionary using a dot-notation path.
        
        Args:
            data: The data to extract from
            path: The dot-notation path (e.g., "data.items.0.name")
            
        Returns:
            The extracted value
        """
        current = data
        for part in path.split('.'):
            # Handle array index notation (e.g., "items.0")
            if part.isdigit():
                current = current[int(part)]
            else:
                current = current[part]
        return current

# Create a singleton instance
function_executor = FunctionExecutor()