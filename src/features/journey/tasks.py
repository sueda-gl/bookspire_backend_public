# TODO: Implement a background scheduler to run the tasks in this file.
#
# This file contains periodic maintenance tasks that are NOT CURRENTLY EXECUTED.
# To enable them, a scheduling library like 'apscheduler' should be integrated.
#
# Implementation Steps:
# 1. Add 'apscheduler' to requirements.txt.
# 2. Create a scheduler instance in `src/core/events.py`.
# 3. In the `create_start_app_handler` function within `events.py`:
#    - Add this job to the scheduler to run on a schedule (e.g., daily).
#      `scheduler.add_job(cleanup_abandoned_sessions, "interval", hours=24)`
#    - Start the scheduler: `scheduler.start()`
# 4. In the `create_stop_app_handler` function, ensure the scheduler is shut down:
#    `scheduler.shutdown()`

import logging
from sqlalchemy import select
from datetime import datetime, timedelta

from src.core.db import SessionLocal
from src.features.journey.models import JourneySession

logger = logging.getLogger(__name__)

async def cleanup_abandoned_sessions():
    """Periodic task to clean up abandoned sessions"""
    async with SessionLocal() as db:
        try:
            # Find sessions that are not completed but haven't been updated in 24 hours
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            stmt = select(JourneySession).where(
                JourneySession.is_completed == False,
                JourneySession.started_at < cutoff_time
            )
            
            result = await db.execute(stmt)
            abandoned_sessions = result.scalars().all()
            
            for session in abandoned_sessions:
                logger.info(f"Marking abandoned session {session.id} as completed")
                session.is_completed = True
                session.completed_at = datetime.now()
                # Don't set is_passed to false - frontend will handle completion status
                
            await db.commit()
            
            logger.info(f"Cleaned up {len(abandoned_sessions)} abandoned sessions")
            
        except Exception as e:
            logger.error(f"Error in cleanup_abandoned_sessions: {str(e)}")
            await db.rollback()