from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AgentReferenceLookupBase(BaseModel):
    roomid: UUID
    agentid: UUID  # Changed to UUID to match AgentProfile.id


class AgentReferenceLookupRead(AgentReferenceLookupBase):
    id: UUID
    
    model_config = ConfigDict(from_attributes=True)


class AgentReferenceLookupCreate(AgentReferenceLookupBase):
    model_config = ConfigDict(extra="forbid")


class AgentReferenceLookupCreateInternal(AgentReferenceLookupCreate):
    pass


class AgentReferenceLookupUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    
    roomid: UUID | None = None
    agentid: UUID | None = None  # Changed to UUID


class AgentReferenceLookupUpdateInternal(AgentReferenceLookupUpdate):
    pass


class AgentReferenceLookupDelete(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID