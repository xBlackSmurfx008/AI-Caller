"""Intelligent task scheduling service (Motion-like)"""

from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta, time as dt_time
import pytz
from dataclasses import dataclass

from src.database.models import ProjectTask, CalendarBlock, WorkPreferences
from src.calendar.google_calendar import get_freebusy, create_event, update_event, delete_event, is_connected
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TimeSlot:
    """Represents an available time slot"""
    start: datetime
    end: datetime
    duration_minutes: int


class TaskScheduler:
    """Intelligent task scheduler that allocates tasks to calendar"""
    
    def __init__(self):
        """Initialize scheduler"""
        pass
    
    def schedule_tasks(
        self,
        db: Session,
        task_ids: Optional[List[str]] = None,
        force_reschedule: bool = False
    ) -> Dict[str, Any]:
        """
        Schedule tasks into calendar based on constraints
        
        Args:
            db: Database session
            task_ids: Optional list of specific task IDs to schedule (None = all schedulable)
            force_reschedule: If True, reschedule even locked blocks
        
        Returns:
            Dictionary with scheduling results
        """
        if not is_connected():
            return {
                "success": False,
                "error": "Google Calendar not connected"
            }
        
        # Get work preferences
        prefs = self._get_work_preferences(db)
        
        # Get schedulable tasks
        if task_ids:
            tasks = db.query(ProjectTask).filter(
                ProjectTask.id.in_(task_ids),
                ProjectTask.status != "done"
            ).all()
        else:
            tasks = self._get_schedulable_tasks(db)
        
        if not tasks:
            return {
                "success": True,
                "scheduled": 0,
                "failed": 0,
                "warnings": []
            }
        
        # Get calendar availability
        time_min = datetime.now(pytz.UTC)
        time_max = time_min + timedelta(days=30)  # Look ahead 30 days
        
        freebusy = get_freebusy(
            time_min.isoformat(),
            time_max.isoformat()
        )
        busy_periods = freebusy.get("busy", [])
        
        # Sort tasks by priority
        sorted_tasks = self._sort_tasks_by_priority(tasks)
        
        # Schedule each task
        scheduled_count = 0
        failed_count = 0
        warnings = []
        
        for task in sorted_tasks:
            # Skip if locked and not forcing reschedule
            if task.locked_schedule and not force_reschedule:
                existing_blocks = db.query(CalendarBlock).filter(
                    CalendarBlock.task_id == task.id
                ).all()
                if existing_blocks:
                    continue
            
            # Check dependencies
            if not self._dependencies_satisfied(db, task):
                warnings.append(f"Task '{task.title}' has unmet dependencies")
                continue
            
            # Find available time slot
            slot = self._find_time_slot(
                task,
                busy_periods,
                prefs,
                time_min,
                time_max
            )
            
            if not slot:
                failed_count += 1
                warnings.append(f"Could not find time for task '{task.title}'")
                continue
            
            # Create calendar block
            result = self._create_calendar_block(db, task, slot, prefs)
            if result["success"]:
                scheduled_count += 1
            else:
                failed_count += 1
                warnings.append(f"Failed to create calendar block for '{task.title}': {result.get('error')}")
        
        return {
            "success": True,
            "scheduled": scheduled_count,
            "failed": failed_count,
            "warnings": warnings
        }
    
    def reschedule_task(
        self,
        db: Session,
        task_id: str,
        new_start: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Reschedule a specific task
        
        Args:
            db: Database session
            task_id: Task ID to reschedule
            new_start: Optional new start time (if None, finds next available slot)
        
        Returns:
            Dictionary with result
        """
        task = db.query(ProjectTask).filter(ProjectTask.id == task_id).first()
        if not task:
            return {"success": False, "error": "Task not found"}
        
        if task.locked_schedule:
            return {"success": False, "error": "Task schedule is locked"}
        
        # Delete existing blocks
        existing_blocks = db.query(CalendarBlock).filter(
            CalendarBlock.task_id == task_id
        ).all()
        
        for block in existing_blocks:
            if block.calendar_event_id:
                try:
                    delete_event(block.calendar_event_id)
                except Exception as e:
                    logger.warning("failed_to_delete_calendar_event", error=str(e), event_id=block.calendar_event_id)
            db.delete(block)
        
        db.commit()
        
        # Schedule to new time
        if new_start:
            # Validate new_start is available
            prefs = self._get_work_preferences(db)
            time_min = datetime.now(pytz.UTC)
            time_max = time_min + timedelta(days=30)
            
            freebusy = get_freebusy(
                time_min.isoformat(),
                time_max.isoformat()
            )
            busy_periods = freebusy.get("busy", [])
            
            # Check if new_start conflicts
            if self._is_time_busy(new_start, task.estimated_minutes or 60, busy_periods, prefs):
                return {"success": False, "error": "Requested time is not available"}
            
            slot = TimeSlot(
                start=new_start,
                end=new_start + timedelta(minutes=task.estimated_minutes or 60),
                duration_minutes=task.estimated_minutes or 60
            )
        else:
            # Find next available slot
            prefs = self._get_work_preferences(db)
            time_min = datetime.now(pytz.UTC)
            time_max = time_min + timedelta(days=30)
            
            freebusy = get_freebusy(
                time_min.isoformat(),
                time_max.isoformat()
            )
            busy_periods = freebusy.get("busy", [])
            
            slot = self._find_time_slot(task, busy_periods, prefs, time_min, time_max)
            if not slot:
                return {"success": False, "error": "Could not find available time slot"}
        
        # Create new block
        result = self._create_calendar_block(db, task, slot, prefs)
        return result
    
    def _get_schedulable_tasks(self, db: Session) -> List[ProjectTask]:
        """Get all tasks that can be scheduled"""
        return db.query(ProjectTask).filter(
            ProjectTask.status.in_(["todo", "scheduled"]),
            ProjectTask.estimated_minutes.isnot(None),
            ProjectTask.estimated_minutes > 0
        ).all()
    
    def _sort_tasks_by_priority(self, tasks: List[ProjectTask]) -> List[ProjectTask]:
        """Sort tasks by deadline, priority, and slack time"""
        def sort_key(task: ProjectTask) -> Tuple[int, int, int]:
            # Hard deadlines first
            deadline_priority = 0 if task.deadline_type == "HARD" else 1
            
            # Earlier deadlines first
            if task.due_at:
                days_until_due = (task.due_at - datetime.now(task.due_at.tzinfo)).days
            else:
                days_until_due = 999
            
            # Higher priority first
            priority = task.priority or 5
            
            return (deadline_priority, days_until_due, -priority)
        
        return sorted(tasks, key=sort_key)
    
    def _dependencies_satisfied(self, db: Session, task: ProjectTask) -> bool:
        """Check if all task dependencies are completed"""
        if not task.dependencies:
            return True
        
        dependency_ids = task.dependencies
        completed_deps = db.query(ProjectTask).filter(
            ProjectTask.id.in_(dependency_ids),
            ProjectTask.status == "done"
        ).count()
        
        return completed_deps == len(dependency_ids)
    
    def _find_time_slot(
        self,
        task: ProjectTask,
        busy_periods: List[Dict[str, Any]],
        prefs: WorkPreferences,
        time_min: datetime,
        time_max: datetime
    ) -> Optional[TimeSlot]:
        """Find available time slot for task"""
        estimated_minutes = task.estimated_minutes or 60
        
        # Respect earliest_start_at
        search_start = time_min
        if task.earliest_start_at:
            if task.earliest_start_at > search_start:
                search_start = task.earliest_start_at
        
        # Respect due_at (must finish before)
        search_end = time_max
        if task.due_at:
            if task.due_at < search_end:
                search_end = task.due_at
        
        # Must have enough time before deadline
        if (search_end - search_start).total_seconds() < estimated_minutes * 60:
            return None
        
        # Get working hours
        working_days = prefs.working_days or [0, 1, 2, 3, 4]  # Mon-Fri default
        work_start = self._parse_time(prefs.working_hours_start or "09:00")
        work_end = self._parse_time(prefs.working_hours_end or "17:00")
        
        # Try to find slot
        current = search_start.replace(hour=work_start.hour, minute=work_start.minute)
        
        while current < search_end:
            # Check if within working hours
            if current.weekday() not in working_days:
                current = self._next_working_day(current, working_days, work_start)
                continue
            
            # Check if within work hours
            current_time = current.time()
            if current_time < work_start or current_time >= work_end:
                current = current.replace(hour=work_start.hour, minute=work_start.minute)
                if current.date() > search_end.date():
                    break
                continue
            
            # Check if slot is available
            slot_end = current + timedelta(minutes=estimated_minutes)
            
            if not self._is_time_busy(current, estimated_minutes, busy_periods, prefs):
                # Check if slot fits before deadline
                if slot_end <= search_end:
                    return TimeSlot(
                        start=current,
                        end=slot_end,
                        duration_minutes=estimated_minutes
                    )
            
            # Move to next potential slot (increment by 30 minutes)
            current += timedelta(minutes=30)
        
        return None
    
    def _is_time_busy(
        self,
        start: datetime,
        duration_minutes: int,
        busy_periods: List[Dict[str, Any]],
        prefs: WorkPreferences
    ) -> bool:
        """Check if a time slot conflicts with busy periods"""
        end = start + timedelta(minutes=duration_minutes)
        
        for busy in busy_periods:
            busy_start = datetime.fromisoformat(busy["start"].replace("Z", "+00:00"))
            busy_end = datetime.fromisoformat(busy["end"].replace("Z", "+00:00"))
            
            # Check overlap
            if start < busy_end and end > busy_start:
                return True
        
        return False
    
    def _create_calendar_block(
        self,
        db: Session,
        task: ProjectTask,
        slot: TimeSlot,
        prefs: WorkPreferences
    ) -> Dict[str, Any]:
        """Create calendar block and database record"""
        try:
            # Create calendar event
            event = create_event(
                summary=f"{task.title}",
                start_iso=slot.start.isoformat(),
                end_iso=slot.end.isoformat(),
                description=task.description or "",
                timezone_str=prefs.timezone or "UTC",
                add_google_meet=False
            )
            
            # Create database record
            block = CalendarBlock(
                task_id=task.id,
                calendar_event_id=event.get("id"),
                start_at=slot.start,
                end_at=slot.end,
                locked=task.locked_schedule
            )
            
            db.add(block)
            
            # Update task status
            if task.status == "todo":
                task.status = "scheduled"
            
            db.commit()
            
            return {
                "success": True,
                "block_id": block.id,
                "event_id": event.get("id"),
                "start": slot.start.isoformat(),
                "end": slot.end.isoformat()
            }
        except Exception as e:
            logger.error("failed_to_create_calendar_block", error=str(e), task_id=task.id)
            db.rollback()
            return {"success": False, "error": str(e)}
    
    def _get_work_preferences(self, db: Session) -> WorkPreferences:
        """Get work preferences (create default if none exists)"""
        prefs = db.query(WorkPreferences).first()
        if not prefs:
            prefs = WorkPreferences()
            db.add(prefs)
            db.commit()
            db.refresh(prefs)
        return prefs
    
    def _parse_time(self, time_str: str) -> dt_time:
        """Parse HH:MM time string"""
        parts = time_str.split(":")
        return dt_time(int(parts[0]), int(parts[1]))
    
    def _next_working_day(
        self,
        current: datetime,
        working_days: List[int],
        work_start: dt_time
    ) -> datetime:
        """Get next working day at work start time"""
        next_day = current + timedelta(days=1)
        while next_day.weekday() not in working_days:
            next_day += timedelta(days=1)
        return next_day.replace(hour=work_start.hour, minute=work_start.minute, second=0, microsecond=0)

