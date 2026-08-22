from datetime import datetime, timezone, time
from typing import Tuple
from app.db.models.attendance import AttendanceStatus
from app.db.models.organization import WorkSchedule

class AttendanceRulesEngine:
    @staticmethod
    def calculate_worked_minutes(check_in: datetime, check_out: datetime) -> int:
        if not check_in or not check_out:
            return 0
        diff = check_out - check_in
        return max(0, int(diff.total_seconds() / 60))

    @staticmethod
    def calculate_late_minutes(check_in: datetime, schedule: WorkSchedule) -> int:
        if not check_in or not schedule:
            return 0
        # Parsing "HH:MM" start time
        try:
            h, m = map(int, schedule.start_time.split(":"))
            scheduled_time = check_in.replace(hour=h, minute=m, second=0, microsecond=0)
            if check_in > scheduled_time:
                diff = check_in - scheduled_time
                return max(0, int(diff.total_seconds() / 60))
        except:
            pass
        return 0

    @staticmethod
    def calculate_early_departure_minutes(check_out: datetime, schedule: WorkSchedule) -> int:
        if not check_out or not schedule:
            return 0
        try:
            h, m = map(int, schedule.end_time.split(":"))
            scheduled_time = check_out.replace(hour=h, minute=m, second=0, microsecond=0)
            if check_out < scheduled_time:
                diff = scheduled_time - check_out
                return max(0, int(diff.total_seconds() / 60))
        except:
            pass
        return 0

    @staticmethod
    def calculate_overtime_minutes(check_out: datetime, schedule: WorkSchedule) -> int:
        if not check_out or not schedule:
            return 0
        try:
            h, m = map(int, schedule.end_time.split(":"))
            scheduled_time = check_out.replace(hour=h, minute=m, second=0, microsecond=0)
            if check_out > scheduled_time:
                diff = check_out - scheduled_time
                return max(0, int(diff.total_seconds() / 60))
        except:
            pass
        return 0

    @staticmethod
    def determine_status(worked_minutes: int, schedule: WorkSchedule) -> AttendanceStatus:
        if worked_minutes == 0:
            return AttendanceStatus.ABSENT
        
        # Simple threshold for Half Day vs Present
        # Usually checking scheduled duration vs actual
        try:
            sh, sm = map(int, schedule.start_time.split(":"))
            eh, em = map(int, schedule.end_time.split(":"))
            total_scheduled = (eh * 60 + em) - (sh * 60 + sm)
            if worked_minutes < (total_scheduled / 2):
                return AttendanceStatus.HALF_DAY
            return AttendanceStatus.PRESENT
        except:
            return AttendanceStatus.PRESENT
