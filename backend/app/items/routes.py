import logging
from typing import List, Optional

import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Item, ItemImage, ImageFeature, User
from ..schemas import ItemDetail, ItemOut, MatchResult
from ..ml.client import extract_features, compare_features

logger = logging.getLogger(__name__)

router = APIRouter()

STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)
logger.info(f"Static directory configured at: {STATIC_DIR.absolute()}")


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
    logger.info(f"POST /lost endpoint called - Title: {title}, Images: {len(images)}")
    try:
        owner: Optional[User] = db.query(User).order_by(User.id.asc()).first()
        if not owner:
            logger.error("No users available to own this item")
            raise HTTPException(status_code=400, detail="No users available to own this item")

        logger.debug(f"Creating lost item owned by user ID: {owner.id}")
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
        logger.info(f"✓ Lost item created with ID: {item.id}")

        # Save images to disk and call ML service
        for img in images:
            logger.debug(f"Processing image: {img.filename}")
            contents = await img.read()
            filename = f"item_{item.id}_{img.filename}"
            path = STATIC_DIR / filename
            path.write_bytes(contents)
            logger.debug(f"✓ Image saved to: {path}")

            image_row = ItemImage(item_id=item.id, image_url=f"/static/{filename}")
            db.add(image_row)
            db.flush()  # get image_row.id

            try:
                logger.debug(f"Extracting features from image: {filename}")
                vec = extract_features(contents)
                feature_row = ImageFeature(
                    image_id=image_row.id,
                    model_name="yolov11n",
                    feature_dim=len(vec),
                    feature_vec=json.dumps(vec),
                )
                db.add(feature_row)
                logger.debug(f"✓ Features extracted and stored for image: {filename}")
            except Exception as e:
                logger.warning(f"⚠ ML service failed for image {filename}: {e}")
                pass

        db.commit()
        db.refresh(item)
        logger.info(f"✓ Lost item fully created with images: {item.id}")
        return item
    except Exception as e:
        logger.error(f"✗ Failed to create lost item: {e}")
        db.rollback()
        raise


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
    logger.info(f"POST /found endpoint called - Title: {title}, Images: {len(images)}")
    try:
        owner: Optional[User] = db.query(User).order_by(User.id.asc()).first()
        if not owner:
            logger.error("No users available to own this item")
            raise HTTPException(status_code=400, detail="No users available to own this item")

        logger.debug(f"Creating found item owned by user ID: {owner.id}")
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
        logger.info(f"✓ Found item created with ID: {item.id}")

        for img in images:
            logger.debug(f"Processing image: {img.filename}")
            contents = await img.read()
            filename = f"item_{item.id}_{img.filename}"
            path = STATIC_DIR / filename
            path.write_bytes(contents)
            logger.debug(f"✓ Image saved to: {path}")

            image_row = ItemImage(item_id=item.id, image_url=f"/static/{filename}")
            db.add(image_row)
            db.flush()

            try:
                logger.debug(f"Extracting features from image: {filename}")
                vec = extract_features(contents)
                feature_row = ImageFeature(
                    image_id=image_row.id,
                    model_name="yolov11n",
                    feature_dim=len(vec),
                    feature_vec=json.dumps(vec),
                )
                db.add(feature_row)
                logger.debug(f"✓ Features extracted and stored for image: {filename}")
            except Exception as e:
                logger.warning(f"⚠ ML service failed for image {filename}: {e}")
                pass

        db.commit()
        db.refresh(item)
        logger.info(f"✓ Found item fully created with images: {item.id}")
        return item
    except Exception as e:
        logger.error(f"✗ Failed to create found item: {e}")
        db.rollback()
        raise


@router.get("/", response_model=List[ItemDetail])
def list_items(
    type: Optional[str] = None,
    name: Optional[str] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db),
):
    logger.info(f"GET /items endpoint called - Type: {type}, Name: {name}, Location: {location}")
    try:
        q = db.query(Item)
        if type:
            q = q.filter(Item.type == type)
        if name:
            # simple case-insensitive title contains search
            q = q.filter(Item.title.ilike(f"%{name}%"))
        if location:
            q = q.filter(Item.location == location)
        
        results = q.order_by(Item.created_at.desc()).all()
        logger.info(f"✓ Retrieved {len(results)} items")
        return results
    except Exception as e:
        logger.error(f"✗ Failed to list items: {e}")
        raise


@router.get("/{item_id}", response_model=ItemDetail)
def get_item(item_id: int, db: Session = Depends(get_db)):
    logger.info(f"GET /items/{item_id} endpoint called")
    try:
        item = db.query(Item).filter(Item.id == item_id).first()
        if not item:
            logger.warning(f"Item not found: {item_id}")
            raise HTTPException(status_code=404, detail="Item not found")
        logger.info(f"✓ Retrieved item: {item_id}")
        return item
    except Exception as e:
        logger.error(f"✗ Failed to get item {item_id}: {e}")
        raise


@router.get("/matches/{lost_item_id}", response_model=List[MatchResult])
def get_matches_for_lost_item(lost_item_id: int, db: Session = Depends(get_db)):
    """Find matching FOUND items for a given LOST item using stored features."""
    logger.info(f"GET /matches/{lost_item_id} endpoint called")
    try:
        lost_item = db.query(Item).filter(Item.id == lost_item_id, Item.type == "lost").first()
        if not lost_item:
            logger.warning(f"Lost item not found: {lost_item_id}")
            raise HTTPException(status_code=404, detail="Lost item not found")

        # Get one feature vector for the lost item
        logger.debug(f"Retrieving features for lost item: {lost_item_id}")
        lost_feature = (
            db.query(ImageFeature)
            .join(ItemImage, ImageFeature.image_id == ItemImage.id)
            .filter(ItemImage.item_id == lost_item_id)
            .first()
        )
        if not lost_feature:
            logger.warning(f"No features available for lost item: {lost_item_id}")
            raise HTTPException(status_code=400, detail="No features available for this lost item")

        query_vector = json.loads(lost_feature.feature_vec)
        logger.debug(f"Query vector loaded with {len(query_vector)} dimensions")

        # Gather candidate features for all FOUND items
        logger.debug("Retrieving candidate features from found items...")
        candidate_rows = (
            db.query(Item.id.label("item_id"), ImageFeature.feature_vec)
            .join(ItemImage, ImageFeature.image_id == ItemImage.id)
            .join(Item, ItemImage.item_id == Item.id)
            .filter(Item.type == "found")
            .all()
        )

        if not candidate_rows:
            logger.info("No found items available for matching")
            return []

        candidate_vectors: List[List[float]] = []
        candidate_ids: List[int] = []

        for row in candidate_rows:
            candidate_ids.append(row.item_id)
            candidate_vectors.append(json.loads(row.feature_vec))

        logger.info(f"Comparing with {len(candidate_vectors)} candidate items...")
        try:
            results = compare_features(query_vector, candidate_vectors, candidate_ids)
            logger.debug(f"ML service returned {len(results)} results")
            logger.debug(f"Raw ML results: {results}")
        except Exception as exc:
            logger.error(f"✗ ML service error: {exc}")
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

        # Keep matches with score > 0.1 (10% similarity)
        filtered = [r for r in sorted_results if r["score"] > 0.1][:5]
        logger.info(f"✓ Found {len(filtered)} matching items (scores: {[r['score'] for r in filtered]})")
        return [MatchResult(item_id=_get_result_id(r), score=r["score"]) for r in filtered]
    except Exception as e:
        logger.error(f"✗ Failed to get matches for item {lost_item_id}: {e}")
        raise


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    logger.info(f"DELETE /items/{item_id} endpoint called")
    try:
        item = db.query(Item).filter(Item.id == item_id).first()
        if not item:
            logger.warning(f"Item not found for deletion: {item_id}")
            raise HTTPException(status_code=404, detail="Item not found")

        logger.debug(f"Deleting item images for item: {item_id}")
        # Delete associated images explicitly to avoid integrity errors
        db.query(ItemImage).filter(ItemImage.item_id == item_id).delete(synchronize_session=False)

        db.delete(item)
        db.commit()
        logger.info(f"✓ Item deleted: {item_id}")
        return None
    except Exception as e:
        logger.error(f"✗ Failed to delete item {item_id}: {e}")
        db.rollback()
        raise


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
