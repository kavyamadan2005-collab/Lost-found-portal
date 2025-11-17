from typing import List

import requests

ML_BASE_URL = "http://localhost:8001"


def extract_features(image_bytes: bytes) -> List[float]:
    files = {"image": ("image.jpg", image_bytes, "image/jpeg")}
    resp = requests.post(f"{ML_BASE_URL}/features/extract", files=files)
    resp.raise_for_status()
    return resp.json()["vector"]


def compare_features(query_vector: List[float], candidate_vectors: List[List[float]], candidate_ids: List[int]):
    payload = {
        "query_vector": query_vector,
        "candidate_vectors": candidate_vectors,
        "candidate_ids": candidate_ids,
    }
    resp = requests.post(f"{ML_BASE_URL}/features/compare", json=payload)
    resp.raise_for_status()
    return resp.json()["results"]
