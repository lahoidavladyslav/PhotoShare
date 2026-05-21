import re

import cloudinary
import cloudinary.uploader

from src.core.config import settings


class CloudinaryService:
    def __init__(self):
        cloudinary.config(
            cloud_name=settings.cloudinary_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True
        )

    @staticmethod
    def upload_image(file, public_id: str):
        """
        Завантажує фото на Cloudinary.
        public_id — це зазвичай шлях/ім'я файлу (наприклад, 'users/avatar/1')
        """
        r = cloudinary.uploader.upload(file, public_id=public_id, overwrite=True)
        return r.get('url')
    
    @staticmethod
    def delete_image(public_id: str):
        """Видаляє світлину з Cloudinary за її public_id."""
        cloudinary.uploader.destroy(public_id)

    @staticmethod
    def get_url_for_image(public_id, version):
        """Генерує посилання на зображення (корисно для трансформацій)."""
        return cloudinary.CloudinaryImage(public_id).build_url(
            version=version
        )
        
    @staticmethod
    def get_public_id_from_url(url: str) -> str:
        """Витягує public_id з повного URL Cloudinary."""
        match = re.search(r'/upload/(?:v\d+/)?(.+?)\.[a-zA-Z0-9]+$', url)
        if match:
            return match.group(1)
        return ""

    @staticmethod
    def transform_image(public_id: str, transformation: str) -> str:
        """Генерує URL з трансформаціями на основі рядка."""
        url, options = cloudinary.utils.cloudinary_url(
            public_id, 
            raw_transformation=transformation
        )
        return url

cloudinary_service = CloudinaryService()