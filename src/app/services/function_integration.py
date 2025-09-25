import logging
import asyncio
import json
import inspect
from typing import Dict, Any, List, Optional
import uuid

from livekit.agents import llm, JobContext
from livekit.agents.pipeline import VoicePipelineAgent

from ..utils.db_utils import with_worker_db
from ..crud.crud_function_tool import crud_function_tools
from ..schemas.function_tool import FunctionToolRead
from .function_executor import function_executor

logger = logging.getLogger("function-integration")

class FunctionIntegrationService:
    """Service to integrate external API function tools with LiveKit agents."""
    
    @staticmethod
    async def setup_agent_functions(agent: VoicePipelineAgent, agent_id: Optional[uuid.UUID] = None) -> None:
        """
        Set up function calling capabilities for an agent based on its assigned functions.
        
        Args:
            agent: The VoicePipelineAgent instance
            agent_id: Optional UUID of the agent profile
        """
        if not agent_id:
            logger.info("No agent ID provided, skipping function setup")
            return
            
        logger.info(f"Setting up functions for agent {agent_id}")
        
        # Get functions assigned to this agent
        try:
            functions = await with_worker_db(
                lambda db: crud_function_tools.get_agent_functions(db=db, agent_id=agent_id)
            )
            
            if not functions:
                logger.info(f"No functions assigned to agent {agent_id}")
                return
                
            logger.info(f"Found {len(functions)} functions assigned to agent {agent_id}")
            
            # Create function context if not exists
            if agent.fnc_ctx is None:
                agent.fnc_ctx = llm.FunctionContext()
            
            # First, check if we can get the valid parameters for ai_callable
            valid_params = FunctionIntegrationService._inspect_ai_callable_params()
            
            # Register each function
            for func in functions:
                FunctionIntegrationService._register_function(agent, func, valid_params)
                
        except Exception as e:
            logger.error(f"Error setting up agent functions: {e}")
    
    @staticmethod
    def _inspect_ai_callable_params():
        """Inspect the ai_callable decorator to determine its valid parameters."""
        try:
            signature = inspect.signature(llm.ai_callable)
            return set(signature.parameters.keys())
        except Exception as e:
            logger.warning(f"Couldn't inspect ai_callable parameters: {e}")
            return set()
    
    @staticmethod
    def _register_function(agent: VoicePipelineAgent, function_tool: FunctionToolRead, valid_params=None) -> None:
        """
        Register a function tool with the agent's function context.
        
        Args:
            agent: The VoicePipelineAgent instance
            function_tool: The function tool to register
            valid_params: Set of valid parameter names for ai_callable
        """
        if not agent.fnc_ctx:
            logger.error("Agent has no function context")
            return
            
        # Based on the error message, we know 'parameters' is not valid
        # Let's try different approaches based on what we've found
        try:
            # Approach 1: Use only name and description in decorator
            @llm.ai_callable(
                name=function_tool.function_name,
                description=function_tool.function_description
            )
            async def api_function(**kwargs):
                """Dynamic API function that will be called by the LLM."""
                logger.info(f"Executing function {function_tool.function_name} with parameters: {kwargs}")
                
                try:
                    # Execute the function via the HTTP client
                    result = await function_executor.execute_function(
                        function_id=function_tool.id,
                        parameters=kwargs
                    )
                    
                    if not result["success"]:
                        error_message = result.get("error", "Unknown error")
                        logger.error(f"Function execution failed: {error_message}")
                        return {"error": error_message}
                    
                    return result["result"]
                    
                except Exception as e:
                    logger.error(f"Error executing function {function_tool.function_name}: {e}")
                    return {"error": str(e)}
            
            # Try to add schema information to the function
            # This might be handled separately in LiveKit's implementation
            if hasattr(api_function, "_schema") or hasattr(api_function, "schema"):
                schema_attr = "_schema" if hasattr(api_function, "_schema") else "schema"
                setattr(api_function, schema_attr, function_tool.parameter_schema)
            
            # Register the function with the agent
            agent.fnc_ctx.register(api_function)
            logger.info(f"Successfully registered function {function_tool.function_name}")
            
        except Exception as e:
            logger.error(f"Error registering function {function_tool.function_name}: {e}")
            
            # Fallback approach: Try to use a JSON Schema compatible with OpenAI format
            try:
                # Convert our parameter schema to OpenAI format if needed
                openai_schema = {
                    "name": function_tool.function_name,
                    "description": function_tool.function_description,
                    "parameters": function_tool.parameter_schema
                }
                
                # Create a simple function without the decorator
                async def simple_function(**kwargs):
                    """Dynamic API function without decorator."""
                    logger.info(f"Executing function {function_tool.function_name} with parameters: {kwargs}")
                    
                    try:
                        result = await function_executor.execute_function(
                            function_id=function_tool.id,
                            parameters=kwargs
                        )
                        
                        if not result["success"]:
                            return {"error": result.get("error", "Unknown error")}
                        
                        return result["result"]
                        
                    except Exception as e:
                        return {"error": str(e)}
                
                # Set attributes that might be expected by the agent
                simple_function.__name__ = function_tool.function_name
                simple_function.__doc__ = function_tool.function_description
                
                # Try direct registration with schema
                if hasattr(agent.fnc_ctx, "register_with_schema"):
                    agent.fnc_ctx.register_with_schema(simple_function, openai_schema)
                    logger.info(f"Registered function with schema: {function_tool.function_name}")
                else:
                    # Last resort: try with custom logic
                    simple_function._schema = openai_schema
                    agent.fnc_ctx.register(simple_function)
                    logger.info(f"Registered function with schema attribute: {function_tool.function_name}")
                    
            except Exception as e2:
                logger.error(f"Fallback registration also failed: {e2}")

# Create singleton instance
function_integration = FunctionIntegrationService()