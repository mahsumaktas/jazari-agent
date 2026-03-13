"""LanceDB backup to Firestore — survive Cloud Run container restarts."""

import asyncio
from datetime import datetime, timezone
from tools.firestore_client import get_db

BACKUP_COLLECTION = "memory_backup"


async def backup_single_record(memory_id: str, record: dict):
    def _write():
        fs_db = get_db()
        doc_ref = fs_db.collection(BACKUP_COLLECTION).document(memory_id)
        backup_data = dict(record)
        if hasattr(backup_data.get("vector"), "tolist"):
            backup_data["vector"] = backup_data["vector"].tolist()
        backup_data["backed_up_at"] = datetime.now(timezone.utc).isoformat()
        doc_ref.set(backup_data)

    await asyncio.to_thread(_write)


def restore_from_firestore(db_path: str = "/tmp/lancedb"):
    import lancedb
    from memory.store import SCHEMA, TABLE_NAME

    fs_db = get_db()
    docs = fs_db.collection(BACKUP_COLLECTION).stream()

    records = []
    skipped = 0
    for doc in docs:
        data = doc.to_dict()
        # Skip incomplete records
        if not all(k in data for k in ("id", "content", "vector", "user_id")):
            skipped += 1
            continue
        try:
            records.append({
                "id": data["id"],
                "content": data["content"],
                "vector": data["vector"],
                "memory_type": data.get("memory_type", "fact"),
                "importance": float(data.get("importance", 0.5)),
                "modality": data.get("modality", "text"),
                "media_uri": data.get("media_uri", ""),
                "created_at": data.get("created_at", datetime.now(timezone.utc).isoformat()),
                "last_accessed": data.get("last_accessed", datetime.now(timezone.utc).isoformat()),
                "decay_factor": float(data.get("decay_factor", 15.0)),
                "user_id": data["user_id"],
            })
        except (ValueError, TypeError):
            skipped += 1

    if not records:
        return {"status": "empty", "count": 0, "skipped": skipped}

    db = lancedb.connect(db_path)
    try:
        db.drop_table(TABLE_NAME)
    except Exception:
        pass

    db.create_table(TABLE_NAME, records, schema=SCHEMA)
    return {"status": "restored", "count": len(records), "skipped": skipped}
