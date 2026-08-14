from typing import List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.schema import Bookmark, Progress
from app.utils.logger import logger

router = APIRouter(prefix="/sync", tags=["Cloud Sync"])

class SyncActionItem(BaseModel):
    id: str
    action_type: str
    payload: Dict[str, Any]
    created_at: str

class BatchSyncRequest(BaseModel):
    actions: List[SyncActionItem]

@router.post("/batch")
async def sync_batch_actions(payload: BatchSyncRequest, db: AsyncSession = Depends(get_db)):
    """
    Processes a batch of offline-queued actions from the mobile client.
    Supports: bookmark, reading_progress, test_submission.
    Deduplication: skips bookmarks that already exist for same source_book+source_page.
    """
    processed_count = 0
    errors = []

    for action in payload.actions:
        try:
            if action.action_type == "bookmark":
                data = action.payload
                source_book = data.get("source_book", data.get("book_name", ""))
                source_page = data.get("source_page", data.get("page_number", 0))
                title = data.get("title", data.get("note", ""))
                content = data.get("content", "")
                category = data.get("category", "bookmark")
                subject_name = data.get("subject_name", "")
                
                # Deduplicate: skip if same source_book + source_page exists
                result = await db.execute(
                    select(Bookmark).filter(
                        Bookmark.source_book == source_book,
                        Bookmark.source_page == source_page,
                        Bookmark.user_id == 1
                    )
                )
                existing = result.scalars().first()

                if not existing and source_book:
                    bm = Bookmark(
                        user_id=1,
                        title=title,
                        content=content,
                        category=category,
                        source_book=source_book,
                        source_page=source_page,
                        subject_name=subject_name
                    )
                    db.add(bm)
                processed_count += 1

            elif action.action_type == "reading_progress":
                data = action.payload
                subject_name = data.get("subject_name", "General")
                result = await db.execute(
                    select(Progress).filter(
                        Progress.user_id == 1,
                        Progress.subject_name == subject_name
                    )
                )
                prog = result.scalars().first()
                if not prog:
                    prog = Progress(user_id=1, subject_name=subject_name, total_questions_attempted=0, total_correct=0)
                    db.add(prog)
                prog.total_questions_attempted = (prog.total_questions_attempted or 0) + data.get("questions_attempted", 0)
                prog.total_correct = (prog.total_correct or 0) + data.get("correct", 0)
                processed_count += 1

            elif action.action_type == "test_submission":
                # Test submissions are handled separately via /tests/submit
                processed_count += 1

            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(f"Error processing sync action {action.id}: {e}")
            errors.append({"action_id": action.id, "error": str(e)})

    return {
        "success": True,
        "processed_count": processed_count,
        "errors": errors,
        "server_time": "UTC"
    }
