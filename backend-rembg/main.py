from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import Response
from rembg import remove, new_session

ALLOWED_MODELS = {"birefnet-general", "u2net_cloth_seg", "u2net"}
_sessions: dict = {}


def get_session(model_name: str):
    if model_name not in _sessions:
        print(f"Cargando modelo {model_name}...")
        _sessions[model_name] = new_session(model_name)
        print(f"Modelo {model_name} listo")
    return _sessions[model_name]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-cargar modelos al iniciar
    get_session("birefnet-general")
    get_session("u2net_cloth_seg")
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "models": list(_sessions.keys())}


@app.post("/remove-bg")
async def remove_bg(
    file: UploadFile = File(...),
    model: str = Form(default="birefnet-general"),
):
    if model not in ALLOWED_MODELS:
        model = "birefnet-general"

    input_data = await file.read()
    session = get_session(model)
    output = remove(input_data, session=session)
    return Response(content=output, media_type="image/png")
