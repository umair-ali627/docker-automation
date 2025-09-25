from pydantic import BaseModel, Field, UUID4, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Base Schemas ---

class CallLogBase(BaseModel):
    """Base schema with common fields for a call log."""
    room_name: str
    call_start_time: datetime
    call_end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    agent_id: UUID4
    
    model_config = ConfigDict(from_attributes=True)

# --- Create Schemas ---

class CallLogCreate(CallLogBase):
    """
    Schema for creating a new call log.
    The 'conversation' is received as a JSON object and will be uploaded to S3.
    The owner_id is derived from the agent_id, not provided in the request body.
    """
    conversation: List[Dict[str, Any]] = Field(..., description="The conversation transcript as a JSON array.")
    recording_url: Optional[str] = Field(None, description="URL to the call recording file.") # <-- New field added

class CallLogCreateInternal(CallLogBase):
    """Internal schema used for creating the log in the database."""
    owner_id: UUID4
    conversation_url: Optional[str] = None # <-- Updated to be optional
    recording_url: Optional[str] = None # <-- New field added


# --- Update Schemas ---

class CallLogUpdate(BaseModel):
    """
    Schema for updating an existing call log. All fields are optional.
    If 'conversation' is provided, it will be re-uploaded to S3 and the URL will be updated.
    """
    room_name: Optional[str] = None
    call_start_time: Optional[datetime] = None
    call_end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    conversation: Optional[List[Dict[str, Any]]] = None
    recording_url: Optional[str] = None # <-- New field added

    model_config = ConfigDict(from_attributes=True, extra='forbid')

class CallLogUpdateInternal(CallLogUpdate):
    """Internal schema for updating, storing the S3 URL."""
    conversation_url: Optional[str] = None

# --- Delete Schema ---
class CallLogDelete(BaseModel):
    """Schema for deleting a call log."""
    id: UUID4

# --- Read Schemas ---

class CallLogRead(CallLogBase):
    """Schema for returning a call log from the API."""
    id: UUID4
    owner_id: UUID4
    conversation_url: Optional[str] = Field(None, description="URL to the conversation log file in S3.") # <-- Updated to be optional
    recording_url: Optional[str] = Field(None, description="URL to the call recording file.") # <-- New field added
    is_deleted: bool # <-- Field added
    created_at: datetime
    updated_at: datetime

# --- List Schema ---

class CallLogList(BaseModel):
    """Schema for returning a paginated list of call logs."""
    items: List[CallLogRead]
    total: int

