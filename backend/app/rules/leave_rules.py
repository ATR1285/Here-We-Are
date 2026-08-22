from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db.models.organization import WorkSchedule
from app.db.models.leave import LeaveRequest, LeaveStatus, LeaveBalance

class LeaveRulesEngine:
    @staticmethod
    def calculate_leave_days(start_date: str, end_date: str, schedule: WorkSchedule) -> int:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
            
        if start > end:
            raise HTTPException(status_code=400, detail="Start date must be before or equal to end date")
            
        # Simplistic calculation matching the prompt's example
        # In a real system, we would parse schedule.working_days 
        # (e.g. "Monday-Friday") and exclude weekends.
        
        working_days = 0
        current = start
        
        # Determine valid weekdays
        # Default is standard workweek (0=Monday, 4=Friday)
        valid_weekdays = set([0, 1, 2, 3, 4])
        
        day_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, 
            "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
        }
        
        if schedule and schedule.working_days:
            s_str = schedule.working_days.lower().strip()
            parsed_days = set()
            for part in s_str.split(","):
                part = part.strip()
                if "-" in part:
                    s_day, e_day = part.split("-")
                    s_day, e_day = s_day.strip(), e_day.strip()
                    if s_day in day_map and e_day in day_map:
                        start_idx = day_map[s_day]
                        end_idx = day_map[e_day]
                        if start_idx <= end_idx:
                            parsed_days.update(range(start_idx, end_idx + 1))
                        else:
                            # e.g., Sunday-Monday
                            parsed_days.update(range(start_idx, 7))
                            parsed_days.update(range(0, end_idx + 1))
                else:
                    if part in day_map:
                        parsed_days.add(day_map[part])
            if parsed_days:
                valid_weekdays = parsed_days
            
        while current <= end:
            if current.weekday() in valid_weekdays:
                working_days += 1
            current += timedelta(days=1)
            
        if working_days == 0:
            raise HTTPException(status_code=400, detail="Leave request contains no working days")
            
        return working_days

    @staticmethod
    def validate_overlap(db: Session, employee_id: str, start_date: str, end_date: str) -> None:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        overlapping = db.query(LeaveRequest).filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED])
        ).all()
        
        for req in overlapping:
            req_start = datetime.strptime(req.start_date, "%Y-%m-%d").date()
            req_end = datetime.strptime(req.end_date, "%Y-%m-%d").date()
            
            # Check overlap logic: (StartA <= EndB) and (EndA >= StartB)
            if start <= req_end and end >= req_start:
                raise HTTPException(
                    status_code=409, 
                    detail=f"Leave request overlaps with existing {req.status.value} request ({req.start_date} to {req.end_date})"
                )

    @staticmethod
    def validate_leave_balance(balance: LeaveBalance, requested_days: int) -> None:
        if balance.available_days < requested_days:
            raise HTTPException(
                status_code=409, 
                detail=f"Insufficient leave balance. Available: {balance.available_days}, Requested: {requested_days}"
            )
            
    @staticmethod
    def calculate_available_balance(balance: LeaveBalance) -> int:
        return balance.allocated_days + balance.carried_forward_days - balance.used_days - balance.pending_days
