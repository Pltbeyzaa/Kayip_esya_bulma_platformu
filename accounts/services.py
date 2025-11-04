from typing import Dict, Any
from django.utils.timezone import localtime
from kayip_esya.mongodb import get_collection


def serialize_item_post(post) -> Dict[str, Any]:
    return {
        '_id': post.id,
        'title': post.title,
        'description': post.description,
        'post_type': post.post_type,
        'status': post.status,
        'location': post.location,
        'city': post.city,
        'district': post.district,
        'contact_phone': post.contact_phone,
        'contact_email': post.contact_email,
        'image': post.image.url if getattr(post, 'image', None) else None,
        'user_id': post.user_id,
        'username': post.user.username if post.user_id else None,
        'created_at': localtime(post.created_at),
        'updated_at': localtime(post.updated_at),
        'is_urgent': post.is_urgent,
    }


def upsert_item_post_to_mongo(post) -> None:
    col = get_collection('item_posts')
    doc = serialize_item_post(post)
    col.update_one({'_id': doc['_id']}, {'$set': doc}, upsert=True)


