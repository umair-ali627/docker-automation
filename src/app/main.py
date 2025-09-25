from .api import router
from .core.config import settings
from .core.setup import create_application
from fastapi.middleware.cors import CORSMiddleware

app = create_application(router=router, settings=settings)
origins = settings.CORS_ORIGINS
print(f"Loaded CORS origins: {origins}")  # Debug print

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "Range"],
    max_age=3600,
)

# app = FastAPI()

# origins = [
#     "http://localhost:3000",
#     "http://localhost:8000",  # Add other origins as needed
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
#     allow_headers=["*"],  # Allows all headers
# )