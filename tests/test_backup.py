"""Tests for Firestore backup and restore."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import numpy as np

FAKE_VECTOR = np.random.rand(768).astype(np.float32).tolist()


async def test_backup_single_record():
    """backup_single_record writes to Firestore."""
    mock_db = MagicMock()
    mock_doc_ref = MagicMock()
    mock_db.collection.return_value.document.return_value = mock_doc_ref

    with patch("memory.backup.get_db", return_value=mock_db):
        from memory.backup import backup_single_record
        await backup_single_record("mem-1", {
            "id": "mem-1",
            "content": "test",
            "vector": FAKE_VECTOR,
            "user_id": "u1",
        })

    mock_doc_ref.set.assert_called_once()
    call_data = mock_doc_ref.set.call_args[0][0]
    assert call_data["id"] == "mem-1"
    assert "backed_up_at" in call_data


def test_restore_from_firestore_empty():
    """restore with no data returns empty status."""
    mock_db = MagicMock()
    mock_db.collection.return_value.stream.return_value = iter([])

    with patch("memory.backup.get_db", return_value=mock_db):
        from memory.backup import restore_from_firestore
        result = restore_from_firestore(db_path="/tmp/test_restore_empty")

    assert result["status"] == "empty"
    assert result["count"] == 0


def test_restore_from_firestore_with_data(tmp_path):
    """restore with data creates LanceDB table."""
    mock_docs = []
    for i in range(3):
        doc = MagicMock()
        doc.to_dict.return_value = {
            "id": f"mem_{i}",
            "content": f"Memory {i}",
            "vector": FAKE_VECTOR,
            "memory_type": "fact",
            "importance": 0.8,
            "modality": "text",
            "media_uri": "",
            "created_at": "2026-01-01T00:00:00+00:00",
            "last_accessed": "2026-01-01T00:00:00+00:00",
            "decay_factor": 24.0,
            "user_id": "u1",
        }
        mock_docs.append(doc)

    mock_db = MagicMock()
    mock_db.collection.return_value.stream.return_value = iter(mock_docs)

    with patch("memory.backup.get_db", return_value=mock_db):
        from memory.backup import restore_from_firestore
        result = restore_from_firestore(db_path=str(tmp_path / "restore_db"))

    assert result["status"] == "restored"
    assert result["count"] == 3


def test_restore_skips_incomplete_records(tmp_path):
    """restore skips records missing required fields."""
    good_doc = MagicMock()
    good_doc.to_dict.return_value = {
        "id": "good", "content": "test", "vector": FAKE_VECTOR,
        "user_id": "u1", "memory_type": "fact", "importance": 0.5,
        "modality": "text", "created_at": "2026-01-01T00:00:00+00:00",
        "last_accessed": "2026-01-01T00:00:00+00:00", "decay_factor": 15.0,
    }
    bad_doc = MagicMock()
    bad_doc.to_dict.return_value = {"id": "bad"}  # missing required fields

    mock_db = MagicMock()
    mock_db.collection.return_value.stream.return_value = iter([good_doc, bad_doc])

    with patch("memory.backup.get_db", return_value=mock_db):
        from memory.backup import restore_from_firestore
        result = restore_from_firestore(db_path=str(tmp_path / "restore_skip"))

    assert result["count"] == 1
    assert result["skipped"] == 1
