"""Shared Firestore client and helpers for all tools."""

import os
from google.cloud import firestore

_db = None


def get_db() -> firestore.Client:
    """Get or create Firestore client (singleton)."""
    global _db
    if _db is None:
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "jazari-coach")
        _db = firestore.Client(project=project)
    return _db


def get_user_ref(user_id: str) -> firestore.DocumentReference:
    """Get reference to a user document."""
    return get_db().collection("users").document(user_id)


def ensure_user(user_id: str) -> dict:
    """Create user profile if it doesn't exist. Return profile data."""
    ref = get_user_ref(user_id)
    doc = ref.get()
    if doc.exists:
        return doc.to_dict()
    profile = {
        "name": None,
        "language": "en",
        "preferences": {},
        "created_at": firestore.SERVER_TIMESTAMP,
    }
    ref.set(profile)
    return profile
