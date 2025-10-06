import torch
import torch.nn as nn
import pandas as pd
import joblib
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict
import io

# ------------------------------
# Configuración básica
# ------------------------------
app = FastAPI(title="Lightcurve AI API", version="1.0")

# CORS para conectar con tu frontend Svelte (ajusta el puerto si es distinto)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # puedes restringirlo a "http://localhost:5173"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------------------
# Carga de modelo PyTorch
# ------------------------------
INPUT_DIM = 34

model = nn.Sequential(
    nn.Linear(INPUT_DIM, 64),
    nn.ReLU(),
    nn.Linear(64, 64),
    nn.ReLU(),
    nn.Linear(64, 64),
    nn.ReLU(),
    nn.Linear(64, 32),
    nn.ReLU(),
    nn.Linear(32, 1),
)

print("Loading model...")
model.load_state_dict(torch.load("model.pth", map_location="cpu"))
model.eval()

# ------------------------------
# Carga del scaler
# ------------------------------
try:
    scaler = joblib.load("scaler.pkl")
    print("Scaler loaded successfully.")
except Exception as e:
    print(f"[WARN] Could not load scaler.pkl: {e}")
    scaler = None

# ------------------------------
# Esquema JSON
# ------------------------------
class JsonPayload(BaseModel):
    records: List[Dict[str, float]] = Field(..., description="List of feature dictionaries")


# ------------------------------
# Funciones auxiliares
# ------------------------------
def preprocess_dataframe(df: pd.DataFrame) -> torch.Tensor:
    """Escala, limpia y convierte a tensor."""
    drop_cols = ['koi_score', 'koi_fpflag_nt', 'koi_fpflag_ss', 'koi_fpflag_co', 'koi_fpflag_ec']
    df = df.dropna()
    df = df.apply(pd.to_numeric, errors="coerce").astype("float64")

    if scaler is not None:
        df_scaled = pd.DataFrame(scaler.transform(df), columns=df.columns)
    else:
        df_scaled = df.copy()

    for col in drop_cols:
        if col in df_scaled.columns:
            df_scaled = df_scaled.drop(columns=[col])

    if df_scaled.shape[1] != INPUT_DIM:
        raise ValueError(f"Expected {INPUT_DIM} features, got {df_scaled.shape[1]}.")

    return torch.tensor(df_scaled.values, dtype=torch.float32)


def predict_tensor(X: torch.Tensor):
    """Aplica inferencia en el modelo PyTorch."""
    with torch.no_grad():
        logits = model(X)
        probs = torch.sigmoid(logits)
        labels = (probs > 0.5).int()

    return {
        "probabilities": probs.numpy().flatten().tolist(),
        "labels": labels.numpy().flatten().tolist()
    }


# ------------------------------
# Endpoints
# ------------------------------

@app.get("/")
def root():
    return {"message": "Lightcurve AI backend online 🚀"}


@app.post("/predict/json")
def predict_from_json(payload: JsonPayload):
    """Recibe JSON con datos numéricos y devuelve la inferencia."""
    try:
        df = pd.DataFrame(payload.records)
        X = preprocess_dataframe(df)
        out = predict_tensor(X)
        return {"ok": True, **out}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("api/predict/csv")
async def predict_from_csv(file: UploadFile):
    """Recibe CSV y devuelve predicciones."""
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        X = preprocess_dataframe(df)
        out = predict_tensor(X)
        return {"ok": True, "filename": file.filename, **out}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
import torch
import torch.nn as nn
import pandas as pd
import joblib
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict
import io

# ------------------------------
# Configuración básica
# ------------------------------
app = FastAPI(title="Lightcurve AI API", version="1.0")

# CORS para conectar con tu frontend Svelte (ajusta el puerto si es distinto)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # puedes restringirlo a "http://localhost:5173"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------
# Carga de modelo PyTorch
# ------------------------------
INPUT_DIM = 34

model = nn.Sequential(
    nn.Linear(INPUT_DIM, 64),
    nn.ReLU(),
    nn.Linear(64, 64),
    nn.ReLU(),
    nn.Linear(64, 64),
    nn.ReLU(),
    nn.Linear(64, 32),
    nn.ReLU(),
    nn.Linear(32, 1),
)

print("Loading model...")
model.load_state_dict(torch.load("model.pth", map_location="cpu"))
model.eval()

# ------------------------------
# Carga del scaler
# ------------------------------
try:
    scaler = joblib.load("scaler.pkl")
    print("Scaler loaded successfully.")
except Exception as e:
    print(f"[WARN] Could not load scaler.pkl: {e}")
    scaler = None

# ------------------------------
# Esquema JSON
# ------------------------------
class JsonPayload(BaseModel):
    records: List[Dict[str, float]] = Field(..., description="List of feature dictionaries")


# ------------------------------
# Funciones auxiliares
# ------------------------------
def preprocess_dataframe(df: pd.DataFrame) -> torch.Tensor:
    """Escala, limpia y convierte a tensor."""
    drop_cols = ['koi_score', 'koi_fpflag_nt', 'koi_fpflag_ss', 'koi_fpflag_co', 'koi_fpflag_ec']
    df = df.dropna()
    df = df.apply(pd.to_numeric, errors="coerce").astype("float64")

    if scaler is not None:
        df_scaled = pd.DataFrame(scaler.transform(df), columns=df.columns)
    else:
        df_scaled = df.copy()

    for col in drop_cols:
        if col in df_scaled.columns:
            df_scaled = df_scaled.drop(columns=[col])

    if df_scaled.shape[1] != INPUT_DIM:
        raise ValueError(f"Expected {INPUT_DIM} features, got {df_scaled.shape[1]}.")

    return torch.tensor(df_scaled.values, dtype=torch.float32)


def predict_tensor(X: torch.Tensor):
    """Aplica inferencia en el modelo PyTorch."""
    with torch.no_grad():
        logits = model(X)
        probs = torch.sigmoid(logits)
        labels = (probs > 0.5).int()

    return {
        "probabilities": probs.numpy().flatten().tolist(),
        "labels": labels.numpy().flatten().tolist()
    }


# ------------------------------
# Endpoints
# ------------------------------

@app.get("/")
def root():
    return {"message": "Lightcurve AI backend online 🚀"}


@app.post("/predict/json")
def predict_from_json(payload: JsonPayload):
    """Recibe JSON con datos numéricos y devuelve la inferencia."""
    try:
        df = pd.DataFrame(payload.records)
        X = preprocess_dataframe(df)
        out = predict_tensor(X)
        return {"ok": True, **out}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/predict/csv")
async def predict_from_csv(file: UploadFile):
    """Recibe CSV y devuelve predicciones."""
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        X = preprocess_dataframe(df)
        out = predict_tensor(X)
        return {"ok": True, "filename": file.filename, **out}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
