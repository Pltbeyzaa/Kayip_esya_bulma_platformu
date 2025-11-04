from typing import Optional
from pymongo import MongoClient
from django.conf import settings


_mongo_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(settings.MONGODB_URL)
    return _mongo_client


def get_db():
    client = get_client()
    return client[settings.MONGODB_DATABASE]


def get_collection(name: str):
    db = get_db()
    return db[name]


