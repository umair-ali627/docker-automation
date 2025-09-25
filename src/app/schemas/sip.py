# from pydantic import BaseModel, Field, UUID4, ConfigDict
# from typing import Optional, List, Dict, Any
# import uuid
# from enum import Enum
# from datetime import datetime


# class SIPTrunkType(str, Enum):
#     INBOUND = "inbound"
#     OUTBOUND = "outbound"

# class SIPCallDirection(str, Enum):
#     INBOUND = "inbound"
#     OUTBOUND = "outbound"

# class SIPCallStatus(str, Enum):
#     INITIATED = "initiated"
#     RINGING = "ringing"
#     ACTIVE = "active"
#     COMPLETED = "completed"
#     FAILED = "failed"

# class SIPTrunkBase(BaseModel):
#     name: str
#     description: Optional[str] = None
    
#     # SIP configuration
#     trunk_type: SIPTrunkType
#     sip_termination_uri: str
#     phone_number: str
    
#     # Optional authentication - may not be needed for inbound
#     username: Optional[str] = None
#     password: Optional[str] = None
    
#     # Optional configuration
#     config: Dict[str, Any] = Field(default_factory=dict)

# class SIPTrunkCreate(SIPTrunkBase):
#     model_config = ConfigDict(extra="forbid")

# class SIPTrunkCreateInternal(SIPTrunkCreate):
#     owner_id: uuid.UUID
#     trunk_id: str = ""

# class SIPTrunkRead(SIPTrunkBase):
#     id: uuid.UUID
#     owner_id: uuid.UUID
#     trunk_id: str
    
#     model_config = ConfigDict(from_attributes=True)

# class SIPTrunkUpdate(BaseModel):
#     model_config = ConfigDict(extra="forbid")
    
#     name: Optional[str] = None
#     description: Optional[str] = None
#     sip_termination_uri: Optional[str] = None
#     username: Optional[str] = None
#     password: Optional[str] = None
#     phone_number: Optional[str] = None
#     config: Optional[Dict[str, Any]] = None

# class SIPTrunkUpdateInternal(SIPTrunkUpdate):
#     pass

# class SIPTrunkDelete(BaseModel):
#     model_config = ConfigDict(extra="forbid")
#     id: UUID4

# # Mapping schemas
# class SIPAgentMappingBase(BaseModel):
#     sip_trunk_id: uuid.UUID
#     inbound_agent_id: Optional[uuid.UUID] = None
#     outbound_agent_id: Optional[uuid.UUID] = None

# class SIPAgentMappingCreate(BaseModel):
#     model_config = ConfigDict(extra="forbid")
    
#     inbound_agent_id: Optional[uuid.UUID] = None
#     outbound_agent_id: Optional[uuid.UUID] = None

# class SIPAgentMappingCreateInternal(SIPAgentMappingBase):
#     dispatch_rule_id: str = ""

# class SIPAgentMappingRead(SIPAgentMappingBase):
#     id: uuid.UUID
#     dispatch_rule_id: str
    
#     model_config = ConfigDict(from_attributes=True)

# class SIPAgentMappingUpdate(BaseModel):
#     model_config = ConfigDict(extra="forbid")
    
#     inbound_agent_id: Optional[uuid.UUID] = None
#     outbound_agent_id: Optional[uuid.UUID] = None

# class SIPAgentMappingUpdateInternal(SIPAgentMappingUpdate):
#     dispatch_rule_id: Optional[str] = None

# class SIPAgentMappingDelete(BaseModel):
#     model_config = ConfigDict(extra="forbid")
#     id: UUID4

# class SIPTrunkList(BaseModel):
#     items: List[SIPTrunkRead]
#     total: int

# # Focused schema for the complete SIP setup
# class CompleteSIPSetupCreate(BaseModel):
#     model_config = ConfigDict(extra="forbid")
    
#     # Basic info
#     name: str
#     description: Optional[str] = None
    
#     # SIP details for integration with external provider
#     sip_termination_uri: str
#     phone_number: str
#     username: str
#     password: str
    
#     # Agent association
#     inbound_agent_id: Optional[uuid.UUID] = None
#     outbound_agent_id: Optional[uuid.UUID] = None
    
#     # Additional configuration
#     config: Dict[str, Any] = Field(default_factory=dict)

# # Response schema for complete SIP setup
# class CompleteSIPSetupResponse(BaseModel):
#     inbound_trunk: SIPTrunkRead
#     outbound_trunk: SIPTrunkRead
#     agent_mapping: Optional[SIPAgentMappingRead] = None
#     dispatch_rule_id: str

# class SIPCallBase(BaseModel):
#     call_id: str
#     room_id: str
#     # room_id: uuid.UUID
#     direction: SIPCallDirection
#     phone_number: str
#     status: SIPCallStatus = SIPCallStatus.INITIATED
    
#     # Optional fields
#     trunk_id: Optional[uuid.UUID] = None
#     agent_id: Optional[uuid.UUID] = None
#     metadata: Dict[str, Any] = Field(default_factory=dict)

# class SIPCallCreate(SIPCallBase):
#     model_config = ConfigDict(extra="forbid")
#     metadata: Dict[str, Any] = Field(default_factory=dict)


# class SIPCallCreateInternal(SIPCallCreate):
#     pass

# class SIPCallRead(SIPCallBase):
#     id: uuid.UUID
#     created_at: datetime
#     answered_at: Optional[datetime] = None
#     completed_at: Optional[datetime] = None
#     duration_seconds: Optional[int] = None
#     success: Optional[bool] = None
    
#     model_config = ConfigDict(from_attributes=True)

# class SIPCallUpdate(BaseModel):
#     model_config = ConfigDict(extra="forbid")
    
#     status: Optional[SIPCallStatus] = None
#     agent_id: Optional[uuid.UUID] = None
#     answered_at: Optional[datetime] = None
#     completed_at: Optional[datetime] = None
#     duration_seconds: Optional[int] = None
#     success: Optional[bool] = None
#     metadata: Optional[Dict[str, Any]] = None

# class SIPCallUpdateInternal(SIPCallUpdate):
#     pass

# class SIPCallDelete(BaseModel):
#     model_config = ConfigDict(extra="forbid")
#     id: UUID4

# class SIPCallList(BaseModel):
#     items: List[SIPCallRead]
#     total: int

# # Webhook event schemas
# class SIPCallEventType(str, Enum):
#     INITIATED = "call.initiated"
#     RINGING = "call.ringing"
#     ANSWERED = "call.answered"
#     COMPLETED = "call.completed"
#     FAILED = "call.failed"

# class SIPCallEventData(BaseModel):
#     call_id: str
#     room_id: uuid.UUID
#     direction: SIPCallDirection
#     phone_number: str
#     status: SIPCallStatus
#     trunk_id: Optional[uuid.UUID] = None
#     agent_id: Optional[uuid.UUID] = None
#     timestamp: datetime
#     metadata: Dict[str, Any] = Field(default_factory=dict)

# class SIPCallEvent(BaseModel):
#     event_type: SIPCallEventType
#     data: SIPCallEventData


from pydantic import BaseModel, Field, UUID4, ConfigDict
from typing import Optional, List, Dict, Any
import uuid
from enum import Enum
from datetime import datetime


class SIPTrunkType(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class SIPCallDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class SIPCallStatus(str, Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


# ────────────── TRUNK SCHEMAS ──────────────
class SIPTrunkBase(BaseModel):
    name: str
    description: Optional[str] = None

    # SIP configuration
    trunk_type: SIPTrunkType
    sip_termination_uri: str
    phone_number: str

    # Optional authentication - may not be needed for inbound
    username: Optional[str] = None
    password: Optional[str] = None

    # Optional configuration
    config: Dict[str, Any] = Field(default_factory=dict)


class SIPTrunkCreate(SIPTrunkBase):
    model_config = ConfigDict(extra="forbid")


class SIPTrunkCreateInternal(SIPTrunkCreate):
    owner_id: uuid.UUID
    trunk_id: str = ""


class SIPTrunkRead(SIPTrunkBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    trunk_id: str
    is_deleted: bool = False

    model_config = ConfigDict(from_attributes=True)

class SIPTrunkReadAdmin(SIPTrunkRead):
    is_deleted: bool = False

class SIPTrunkUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    description: Optional[str] = None
    sip_termination_uri: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    phone_number: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class SIPTrunkUpdateInternal(SIPTrunkUpdate):
    pass


class SIPTrunkDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID4


# ────────────── AGENT MAPPING SCHEMAS ──────────────
class SIPAgentMappingBase(BaseModel):
    sip_trunk_id: uuid.UUID
    inbound_agent_id: Optional[uuid.UUID] = None
    outbound_agent_id: Optional[uuid.UUID] = None


class SIPAgentMappingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inbound_agent_id: Optional[uuid.UUID] = None
    outbound_agent_id: Optional[uuid.UUID] = None


class SIPAgentMappingCreateInternal(SIPAgentMappingBase):
    dispatch_rule_id: str = ""


class SIPAgentMappingRead(SIPAgentMappingBase):
    id: uuid.UUID
    dispatch_rule_id: str

    model_config = ConfigDict(from_attributes=True)


class SIPAgentMappingUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    inbound_agent_id: Optional[uuid.UUID] = None
    outbound_agent_id: Optional[uuid.UUID] = None


class SIPAgentMappingUpdateInternal(SIPAgentMappingUpdate):
    dispatch_rule_id: Optional[str] = None


class SIPAgentMappingDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID4


class SIPTrunkList(BaseModel):
    items: List[SIPTrunkRead]
    total: int


# ────────────── COMPLETE SETUP ──────────────
class CompleteSIPSetupCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Basic info
    name: str
    description: Optional[str] = None

    # SIP details for integration with external provider
    sip_termination_uri: str
    phone_number: str
    username: str
    password: str

    # Agent association
    inbound_agent_id: Optional[uuid.UUID] = None
    outbound_agent_id: Optional[uuid.UUID] = None

    # Additional configuration
    config: Dict[str, Any] = Field(default_factory=dict)


class CompleteSIPSetupResponse(BaseModel):
    inbound_trunk: SIPTrunkRead
    outbound_trunk: SIPTrunkRead
    agent_mapping: Optional[SIPAgentMappingRead] = None
    dispatch_rule_id: str


# ────────────── CALL SCHEMAS ──────────────
class SIPCallBase(BaseModel):
    call_id: str
    room_id: str
    direction: SIPCallDirection
    phone_number: str
    status: SIPCallStatus = SIPCallStatus.INITIATED

    # Optional fields
    trunk_id: Optional[uuid.UUID] = None
    agent_id: Optional[uuid.UUID] = None
    call_metadata: Dict[str, Any] = Field(default_factory=dict)  # ✅ fixed


class SIPCallCreate(SIPCallBase):
    model_config = ConfigDict(extra="allow")


class SIPCallCreateInternal(SIPCallCreate):
    answered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    success: Optional[bool] = None
    created_at: Optional[datetime] = None  # Add this line to prevent the lambda function from being passed.


class SIPCallRead(SIPCallBase):
    id: uuid.UUID
    created_at: datetime
    answered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    success: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True, extra="allow")

class SIPCallReadAdmin(SIPCallRead):
    is_deleted: bool = False
class SIPCallUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Optional[SIPCallStatus] = None
    agent_id: Optional[uuid.UUID] = None
    answered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    success: Optional[bool] = None
    call_metadata: Optional[Dict[str, Any]] = None  # ✅ fixed


class SIPCallUpdateInternal(SIPCallUpdate):
    pass


class SIPCallDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID4


class SIPCallList(BaseModel):
    items: List[SIPCallRead]
    total: int


# ────────────── EVENT SCHEMAS ──────────────
class SIPCallEventType(str, Enum):
    INITIATED = "call.initiated"
    RINGING = "call.ringing"
    ANSWERED = "call.answered"
    COMPLETED = "call.completed"
    FAILED = "call.failed"


class SIPCallEventData(BaseModel):
    call_id: str
    room_id: str
    direction: SIPCallDirection
    phone_number: str
    status: SIPCallStatus
    trunk_id: Optional[uuid.UUID] = None
    agent_id: Optional[uuid.UUID] = None
    timestamp: datetime
    call_metadata: Dict[str, Any] = Field(default_factory=dict)  # ✅ fixed


class SIPCallEvent(BaseModel):
    event_type: SIPCallEventType
    data: SIPCallEventData


class OutboundCallRequest(BaseModel):
    """Schema for initiating an outbound SIP call"""
    model_config = ConfigDict(extra="forbid")

    phone_numbers: List[str]
    agent_id: uuid.UUID
    trunk_id: Optional[uuid.UUID] = None
    attributes: Optional[Dict[str, str]] = Field(default_factory=dict)
    call_metadata: Optional[str] = None

class OutboundCallInfo(BaseModel):
    """Information about a single outbound call"""
    phone_number: str
    call_id: str
    room_id: str
    status: SIPCallStatus = SIPCallStatus.INITIATED

class OutboundCallResponse(BaseModel):
    """Response for outbound call requests"""
    success: bool
    calls: List[OutboundCallInfo] = Field(default_factory=list)
    errors: Dict[str, str] = Field(default_factory=dict)