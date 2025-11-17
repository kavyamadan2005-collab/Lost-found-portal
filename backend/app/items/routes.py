from typing import List, Optional

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Item, ItemImage, ImageFeature, User
from ..schemas import ItemDetail, ItemOut, MatchResult
from ..ml.client import extract_features, compare_features

router = APIRouter()

STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)


@router.post("/lost", response_model=ItemOut)
async def create_lost_item(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    date_reported: Optional[str] = Form(None),  # ISO date string
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
):
    owner: Optional[User] = db.query(User).order_by(User.id.asc()).first()
    if not owner:
        raise HTTPException(status_code=400, detail="No users available to own this item")

    item = Item(
        user_id=owner.id,
        type="lost",
        title=title,
        description=description,
        category=category,
        location=location,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    # Save images to disk and call ML service
    for img in images:
        contents = await img.read()
        filename = f"item_{item.id}_{img.filename}"
        path = STATIC_DIR / filename
        path.write_bytes(contents)

        image_row = ItemImage(item_id=item.id, image_url=f"/static/{filename}")
        db.add(image_row)
        db.flush()  # get image_row.id

        try:
            vec = extract_features(contents)
            feature_row = ImageFeature(
                image_id=image_row.id,
                model_name="yolov11n",
                feature_dim=len(vec),
                feature_vec=json.dumps(vec),
            )
            db.add(feature_row)
        except Exception:
            # If ML service fails, we still keep the item and image
            pass

    db.commit()
    db.refresh(item)
    return item


@router.post("/found", response_model=ItemOut)
async def create_found_item(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    date_reported: Optional[str] = Form(None),
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
):
    owner: Optional[User] = db.query(User).order_by(User.id.asc()).first()
    if not owner:
        raise HTTPException(status_code=400, detail="No users available to own this item")

    item = Item(
        user_id=owner.id,
        type="found",
        title=title,
        description=description,
        category=category,
        location=location,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    for img in images:
        contents = await img.read()
        filename = f"item_{item.id}_{img.filename}"
        path = STATIC_DIR / filename
        path.write_bytes(contents)

        image_row = ItemImage(item_id=item.id, image_url=f"/static/{filename}")
        db.add(image_row)
        db.flush()

        try:
            vec = extract_features(contents)
            feature_row = ImageFeature(
                image_id=image_row.id,
                model_name="yolov11n",
                feature_dim=len(vec),
                feature_vec=json.dumps(vec),
            )
            db.add(feature_row)
        except Exception:
            pass

    db.commit()
    db.refresh(item)
    return item


@router.get("/", response_model=List[ItemDetail])
def list_items(
    type: Optional[str] = None,
    name: Optional[str] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Item)
    if type:
        q = q.filter(Item.type == type)
    if name:
        # simple case-insensitive title contains search
        q = q.filter(Item.title.ilike(f"%{name}%"))
    if location:
        q = q.filter(Item.location == location)
    return q.order_by(Item.created_at.desc()).all()


@router.get("/{item_id}", response_model=ItemDetail)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.get("/matches/{lost_item_id}", response_model=List[MatchResult])
def get_matches_for_lost_item(lost_item_id: int, db: Session = Depends(get_db)):
    """Find matching FOUND items for a given LOST item using stored features."""

    lost_item = db.query(Item).filter(Item.id == lost_item_id, Item.type == "lost").first()
    if not lost_item:
        raise HTTPException(status_code=404, detail="Lost item not found")

    # Get one feature vector for the lost item
    lost_feature = (
        db.query(ImageFeature)
        .join(ItemImage, ImageFeature.image_id == ItemImage.id)
        .filter(ItemImage.item_id == lost_item_id)
        .first()
    )
    if not lost_feature:
        raise HTTPException(status_code=400, detail="No features available for this lost item")

    query_vector = json.loads(lost_feature.feature_vec)

    # Gather candidate features for all FOUND items
    candidate_rows = (
        db.query(Item.id.label("item_id"), ImageFeature.feature_vec)
        .join(ItemImage, ImageFeature.image_id == ItemImage.id)
        .join(Item, ItemImage.item_id == Item.id)
        .filter(Item.type == "found")
        .all()
    )

    if not candidate_rows:
        return []

    candidate_vectors: List[List[float]] = []
    candidate_ids: List[int] = []

    for row in candidate_rows:
        candidate_ids.append(row.item_id)
        candidate_vectors.append(json.loads(row.feature_vec))

    try:
        results = compare_features(query_vector, candidate_vectors, candidate_ids)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"ML service error: {exc}")

    # results is a list of objects with a score and some id field. Try common keys.
    def _get_result_id(r: dict) -> int:
        if "id" in r:
            return r["id"]
        if "item_id" in r:
            return r["item_id"]
        if "index" in r:
            # fall back to treating index as candidate index
            idx = r["index"]
            if 0 <= idx < len(candidate_ids):
                return candidate_ids[idx]
        raise KeyError("No suitable id field in ML result")

    # Sort by score descending
    sorted_results = sorted(results, key=lambda r: r["score"], reverse=True)

    # Keep only reasonably good matches (e.g. score >= 0.3) and limit to top 5
    filtered = [r for r in sorted_results if r["score"] >= 0.3][:5]
    return [MatchResult(item_id=_get_result_id(r), score=r["score"]) for r in filtered]


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Delete associated images explicitly to avoid integrity errors
    db.query(ItemImage).filter(ItemImage.item_id == item_id).delete(synchronize_session=False)

    db.delete(item)
    db.commit()
    return None
