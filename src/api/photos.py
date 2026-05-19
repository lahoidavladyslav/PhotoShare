import base64
import io
import uuid

import qrcode
from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.db.database import get_db
from src.db.models import Role, User
from src.repository import photos as repository_photos
from src.schemas.photo import PhotoResponse, PhotoTransformModel, TransformResponse
from src.services.cloudinary import cloudinary_service

router = APIRouter(prefix="/photos", tags=["Photos"])

@router.post("/", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    description: str = Form(...),
    tags: str = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    unique_id = uuid.uuid4().hex[:8] 
    file_name = file.filename.split('.')[0]
    public_id = f"photoshare/user_{current_user.id}/{file_name}_{unique_id}"
    
    try:
        image_url = cloudinary_service.upload_image(file.file, public_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary upload error: {str(e)}")

    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    new_photo = await repository_photos.create_photo(
        db=db,
        url=image_url,
        description=description,
        user=current_user,
        tag_names=tag_list
    )

    return new_photo

@router.get("/{photo_id}", response_model=PhotoResponse)
async def get_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    photo = await repository_photos.get_photo_by_id(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo

@router.put("/{photo_id}", response_model=PhotoResponse)
async def update_description(
    photo_id: int,
    new_description: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    photo = await repository_photos.get_photo_by_id(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    
    if photo.owner_id != current_user.id and current_user.role != Role.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    updated_photo = await repository_photos.update_photo_description(db, photo_id, new_description, current_user)
    return updated_photo

@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    photo = await repository_photos.get_photo_by_id(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    
    if photo.owner_id != current_user.id and current_user.role != Role.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    public_id = cloudinary_service.get_public_id_from_url(photo.url)
    if public_id:
        cloudinary_service.delete_image(public_id)

    await repository_photos.delete_photo(db, photo_id)
    return None

@router.post("/transform/{photo_id}", response_model=TransformResponse, status_code=status.HTTP_200_OK)
async def transform_photo(
    photo_id: int,
    transform_data: PhotoTransformModel = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Трансформує існуючу світлину та повертає новий URL + QR-код.
    """
    photo = await repository_photos.get_photo_by_id(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    public_id = cloudinary_service.get_public_id_from_url(photo.url)
    if not public_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not parse Cloudinary URL")

    transformed_url = cloudinary_service.transform_image(
        public_id=public_id,
        width=transform_data.width,
        height=transform_data.height,
        crop=transform_data.crop,
        effect=transform_data.effect
    )

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(transformed_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    qr_code_data_uri = f"data:image/png;base64,{qr_base64}"

    return {
        "original_url": photo.url,
        "transformed_url": transformed_url,
        "qr_code_url": qr_code_data_uri
    }