from dotenv import load_dotenv
import os
from livekit import api

load_dotenv()  # this loads values from .env into os.environ

# Create the token
token = (
    api.AccessToken()
    .with_identity("python-bot")
    .with_name("Python Bot")
    .with_grants(
        api.VideoGrants(
            room_join=True,  # allow joining rooms
            room="my-room",  # restrict to specific room (optional)
        )
    )
    .to_jwt()
)

print("Generated token:", token)
