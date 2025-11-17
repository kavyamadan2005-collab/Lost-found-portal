from functools import lru_cache

import numpy as np
from PIL import Image
from ultralytics import YOLO


@lru_cache(maxsize=1)
def get_yolo_model():
    """Load a YOLO model once and reuse it.

    This uses a small YOLO model for speed. If you have a specific YOLOv11
    weights file, update the path below (e.g. "yolov11n.pt").
    """
    # Use a standard small YOLOv8 model; Ultralytics will download
    # "yolov8n.pt" automatically if it is not present locally.
    # If you download weights manually, place the .pt file in this folder
    # and point this path to that file.
    model = YOLO("yolov8n.pt")
    return model


def _build_confidence_vector(model: YOLO, yolo_result) -> np.ndarray:
    """Convert YOLO detections into a fixed-length confidence vector.

    For each class, store the maximum confidence of any detection of that class.
    This gives a vector of shape (num_classes,), which we then L2-normalize.
    """

    names = model.model.names  # dict: {class_id: class_name}
    num_classes = len(names)
    vec = np.zeros(num_classes, dtype=np.float32)

    boxes = getattr(yolo_result, "boxes", None)
    if boxes is None or boxes.cls is None or boxes.conf is None:
        return vec

    cls_ids = boxes.cls.cpu().numpy().astype(int)
    confs = boxes.conf.cpu().numpy().astype(np.float32)

    for cid, conf in zip(cls_ids, confs):
        if 0 <= cid < num_classes:
            vec[cid] = max(vec[cid], conf)

    # L2-normalize
    norm = float(np.linalg.norm(vec) + 1e-10)
    vec = vec / norm
    return vec.astype(np.float32)


def extract_features(image: Image.Image) -> np.ndarray:
    """Extract a YOLO-based feature vector from a PIL image.

    The image is passed through YOLO; we then build a per-class confidence
    vector from the detections and normalize it. This vector can be used for
    similarity comparison (cosine / dot product).
    """

    model = get_yolo_model()

    # Ensure RGB
    img_rgb = image.convert("RGB")

    # Run YOLO inference; Ultralytics handles resizing and preprocessing
    results = model(img_rgb, verbose=False)
    if not results:
        # No detections at all; return zero vector (will be all zeros)
        names = model.model.names
        return np.zeros(len(names), dtype=np.float32)

    result = results[0]
    vec = _build_confidence_vector(model, result)
    return vec
