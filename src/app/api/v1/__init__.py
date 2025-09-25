from fastapi import APIRouter

from .login import router as login_router
from .logout import router as logout_router
from .posts import router as posts_router
from .rate_limits import router as rate_limits_router
from .signup import router as signup_router
from .tasks import router as tasks_router
from .tiers import router as tiers_router
from .users import router as users_router
from .voice_agents import router as va_router
from .livekit import router as livekit_router
from .register import router as register_router
from .agent_profiles import router as agent_profile_router
from .agent_knowledge import router as agent_knowledge_router
from .knowledge_base import router as knowledge_base_router
from .sip import router as sip_router
from .voice import router as voice_router
from .agent_functions import router as agent_functions_router
from .providers import router as providers_router
from .call_logs import router as call_logs_router
from .connections import router as connections_router
from .function_tool import router as function_tool_router

router = APIRouter(prefix="/v1")
router.include_router(login_router)
router.include_router(logout_router)
router.include_router(signup_router)
router.include_router(users_router)
router.include_router(posts_router)
router.include_router(tasks_router)
router.include_router(tiers_router)
router.include_router(rate_limits_router)
router.include_router(va_router)
router.include_router(livekit_router)
router.include_router(register_router)
router.include_router(agent_profile_router)
router.include_router(agent_knowledge_router)
router.include_router(knowledge_base_router)
router.include_router(sip_router)
router.include_router(voice_router)
router.include_router(agent_functions_router)
router.include_router(providers_router)
router.include_router(call_logs_router)
router.include_router(connections_router)
router.include_router(function_tool_router)