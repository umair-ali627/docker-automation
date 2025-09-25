from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl, ConfigDict, validator
from typing import Optional, Dict, Any, List, Literal
import uuid
from enum import Enum


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH" 

class AuthType(str, Enum):
    NONE = "none"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"

class FunctionToolBase(BaseModel):
    name: str = Field(..., description="The name of the function")
    description: Optional[str] = Field(None, description="A description of what the function does")
    
    # Function definition
    function_name: str = Field(..., description="The name of the function to call that will be used in the LLM")
    function_description: str = Field(..., description="A description of the function that will be used in the LLM")
    parameter_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON schema for the parameters of the function")

    # HTTP endpoint information
    http_method: HttpMethod = Field(default=HttpMethod.GET, description="The HTTP method to use for the function")
    base_url: str = Field(..., description="The base URL for the function")
    endpoint_path: str = Field(..., description="The path for the function")
    headers: Dict[str, str] = Field(default_factory=dict, description="The headers for the function")
    
    # Request configuration
    request_template: Dict[str, Any] = Field(default_factory=dict, description="The request template for the function")
    auth_required: bool = Field(default=False, description="Whether the function requires authentication")
    auth_type: Optional[AuthType] = Field(default=None, description="The type of authentication to use for the function")
    
    # Response handling
    response_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of response fields to function return values"
    )
    error_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of error codes/responses to error messages"
    )
    
    # Status flags
    active: bool = Field(default=True, description="Whether this function is active")
    is_public: bool = Field(default=False, description="Whether this function can be used by other users")
    
    # Validate that if auth_required is true, auth_type is not none
    @validator('auth_type')
    def validate_auth_type(cls, v, values):
        if values.get('auth_required', False) and not v:
            raise ValueError("auth_type must be specified if auth_required is true")
        return v

# Schema for creating a function tool
class FunctionToolCreate(FunctionToolBase):
    model_config = ConfigDict(extra="forbid")

# Schema for internal creation (with owner_id)
class FunctionToolCreateInternal(FunctionToolBase):
    owner_id: UUID

# Schema for updating an existing function tool (all fields optional)
class FunctionToolUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    name: Optional[str] = None
    description: Optional[str] = None
    function_name: Optional[str] = None
    function_description: Optional[str] = None
    parameter_schema: Optional[Dict[str, Any]] = None
    http_method: Optional[HttpMethod] = None
    base_url: Optional[str] = None
    endpoint_path: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    request_template: Optional[Dict[str, Any]] = None
    auth_required: Optional[bool] = None
    auth_type: Optional[AuthType] = None
    response_mapping: Optional[Dict[str, str]] = None
    error_mapping: Optional[Dict[str, str]] = None
    active: Optional[bool] = None
    is_public: Optional[bool] = None

# Schema for reading a function tool (with ID)
class FunctionToolRead(FunctionToolBase):
    id: UUID
    owner_id: UUID
    
    model_config = ConfigDict(from_attributes=True)

# Schema for deleting a function tool
class FunctionToolDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID

# Schema for a list of function tools
class FunctionToolList(BaseModel):
    items: List[FunctionToolRead]
    total: int

# Schema for assigning functions to an agent
class AgentFunctionAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    function_ids: List[UUID] = Field(..., description="List of function IDs to assign to the agent")

# Schema for testing a function
class FunctionTestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    function_id: UUID = Field(..., description="ID of the function to test")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters to pass to the function")

# Schema for function test response
class FunctionTestResponse(BaseModel):
    success: bool
    result: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    execution_time_ms: float