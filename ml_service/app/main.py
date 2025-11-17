from typing import List

import numpy as np
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from PIL import Image

from .model import extract_features

app = FastAPI(title="ML Feature Service")


class CompareRequest(BaseModel):
    query_vector: List[float]
    candidate_vectors: List[List[float]]
    candidate_ids: List[int]


@app.get("/")
async def root():
    return {"message": "ML service running"}


@app.post("/features/extract")
async def features_extract(image: UploadFile = File(...)):
    img = Image.open(image.file).convert("RGB")
    vec = extract_features(img)
    return {"vector": vec.tolist()}


@app.post("/features/compare")
async def features_compare(req: CompareRequest):
    q = np.array(req.query_vector, dtype=np.float32)
    candidates = np.array(req.candidate_vectors, dtype=np.float32)
    # cosine similarity
    scores = np.dot(candidates, q)  # assuming vectors are normalized
    order = np.argsort(scores)[::-1]
    results = [
        {"item_id": int(req.candidate_ids[i]), "score": float(scores[i])}
        for i in order
    ]
    return {"results": results}
