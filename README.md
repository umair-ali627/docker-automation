#######123#########
#############3
Install:

docker run -d -p 5432:5432 --name postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres postgres

docker run -d --name redis -p 6379:6379 redis:alpine

python -m venv venv

.\venv\Scripts\activate

pip install poetry

poetry install

pip install -r requirements.txt

uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000

<!-- livekit installations -->

pip install "livekit-agents[deepgram,silero,cartesia,noise_cancellation]"
