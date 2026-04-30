from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, Form, Header, HTTPException
from fastapi.responses import Response
from rembg import remove, new_session
import os

ALLOWED_MODELS = {"birefnet-general", "u2net_cloth_seg", "u2net"}
_sessions: dict = {}
SECRET = os.environ.get("REMBG_SECRET", "")


def get_session(model_name: str):
    if model_name not in _sessions:
        print(f"Cargando modelo {model_name}...")
        _sessions[model_name] = new_session(model_name)
        print(f"Modelo {model_name} listo")
    return _sessions[model_name]


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_session("isnet-general-use")
    yield


app = FastAPI(lifespan=lifespan)


def verify_secret(x_rembg_secret: str = Header(default="")):
    if SECRET and x_rembg_secret != SECRET:
        raise HTTPException(status_code=401, detail="No autorizado")


@app.get("/health")
def health(x_rembg_secret: str = Header(default="")):
    verify_secret(x_rembg_secret)
    return {"status": "ok", "models": list(_sessions.keys())}


@app.post("/remove-bg")
async def remove_bg(
    file: UploadFile = File(...),
    model: str = Form(default="birefnet-general"),
    x_rembg_secret: str = Header(default=""),
):
    verify_secret(x_rembg_secret)

    if model not in ALLOWED_MODELS:
        model = "birefnet-general"

    input_data = await file.read()
    session = get_session(model)
    output = remove(input_data, session=session)
    return Response(content=output, media_type="image/png")
