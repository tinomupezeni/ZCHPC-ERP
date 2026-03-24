"""
Django models for the Attendance module.
"""
from django.db import models


class AttendanceRecord(models.Model):
    """Employee attendance record."""
    employee = models.ForeignKey(
        'hr.Employees',
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField()
    time_in = models.TimeField(null=True, blank=True)
    time_out = models.TimeField(null=True, blank=True)

    class Meta:
        db_table = 'human_resources_attendancerecord'
        unique_together = ['employee', 'date']
        ordering = ['-date', 'employee__first_name']

    def __str__(self):
        return f"{self.employee} - {self.date}"
