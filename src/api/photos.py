import base64
import io
import uuid
from typing import List

import qrcode
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_user
from src.db.database import get_db
from src.db.models import Role, User
from src.repository import photos as repository_photos
from src.schemas.photo import PhotoResponse, TransformResponse
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

@router.get("/search", response_model=List[PhotoResponse])
async def search_photos(
    query: str = Query(..., min_length=2, description="Слово для пошуку в описі або тегах"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Об'єднаний пошук світлин. 
    Шукає задане слово в описах фотографій та серед їхніх тегів.
    """
    photos = await repository_photos.search_photos(query, skip, limit, db)
    return photos

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

@router.post("/transform", response_model=TransformResponse, status_code=status.HTTP_200_OK)
async def transform_photo(
    photo_id: int,
    transformation: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Apply transformation to photo and generate QR code.
    
    Args: 
        photo_id (int): The ID of the photo to transform. 
        transformation (str): The transformation to apply. 
        db (Session): The database session. 
        current_user (User): The currently authenticated user.
        
    Returns: 
        TransformResponse: The transformed photo details.
        
    Raises: 
        HTTPException: If the photo is not found or transformation fails.
        
    **Доступні приклади команд:**
    * **Аватар (квадрат з фокусом на обличчі):** `c_fill,g_face,h_300,w_300`
    * **Чорно-білий фільтр:** `e_grayscale`
    * **Ефект мультфільму:** `e_cartoonify`
    * **Розмиття:** `e_blur:200`
    * **Зробити фото круглим:** `r_max`
    * **Сепія (старе фото):** `e_sepia`
    """
    photo = await repository_photos.get_photo_by_id(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    public_id = cloudinary_service.get_public_id_from_url(photo.url)
    if not public_id:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not parse Cloudinary URL")

    transformed_url = cloudinary_service.transform_image(
        public_id=public_id,
        transformation=transformation
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
    
    
@router.get("/{photo_id}/qrcode", summary="Згенерувати QR-код на сторінку світлини")
async def get_photo_qr_code(
        photo_id: int,
        request: Request, 
        db: AsyncSession = Depends(get_db)
):
    """
    Генерує QR-код, який містить посилання на деталі фотографії 
    (GET /api/photos/{photo_id}).
    """
    photo = await repository_photos.get_photo_by_id(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    app_photo_url = f"{request.base_url}api/photos/{photo_id}"

    qr = qrcode.make(app_photo_url)
    
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")