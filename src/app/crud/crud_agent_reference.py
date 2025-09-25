from fastcrud import FastCRUD

from ..models.agent_profile import AgentReferenceLookup
from ..schemas.agent_reference import (
    AgentReferenceLookupCreateInternal,
    AgentReferenceLookupDelete,
    AgentReferenceLookupUpdate,
    AgentReferenceLookupUpdateInternal,
    AgentReferenceLookupRead
)

CRUDAgentReferenceLookup = FastCRUD[
    AgentReferenceLookup,
    AgentReferenceLookupCreateInternal,
    AgentReferenceLookupUpdate,
    AgentReferenceLookupUpdateInternal,
    AgentReferenceLookupDelete,
    AgentReferenceLookupRead
]


crud_agent_references = CRUDAgentReferenceLookup(AgentReferenceLookup)