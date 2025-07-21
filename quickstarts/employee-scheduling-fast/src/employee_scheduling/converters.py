from typing import List, Optional, Union
from datetime import datetime, date
from . import domain
from .json_serialization import JsonDomainBase
from pydantic import Field


# Conversion functions from domain to API models
def employee_to_model(employee: domain.Employee) -> domain.EmployeeModel:
    return domain.EmployeeModel(
        name=employee.name,
        skills=list(employee.skills),
        unavailable_dates=[d.isoformat() for d in employee.unavailable_dates],
        undesired_dates=[d.isoformat() for d in employee.undesired_dates],
        desired_dates=[d.isoformat() for d in employee.desired_dates]
    )


def shift_to_model(shift: domain.Shift) -> domain.ShiftModel:
    return domain.ShiftModel(
        id=shift.id,
        start=shift.start.isoformat(),
        end=shift.end.isoformat(),
        location=shift.location,
        required_skill=shift.required_skill,
        employee=employee_to_model(shift.employee) if shift.employee else None
    )


def schedule_to_model(schedule: domain.EmployeeSchedule) -> domain.EmployeeScheduleModel:
    return domain.EmployeeScheduleModel(
        employees=[employee_to_model(e) for e in schedule.employees],
        shifts=[shift_to_model(s) for s in schedule.shifts],
        score=str(schedule.score) if schedule.score else None,
        solver_status=schedule.solver_status.name if schedule.solver_status else None
    )


# Conversion functions from API models to domain
def model_to_employee(model: domain.EmployeeModel) -> domain.Employee:
    return domain.Employee(
        name=model.name,
        skills=set(model.skills),
        unavailable_dates={date.fromisoformat(d) for d in model.unavailable_dates},
        undesired_dates={date.fromisoformat(d) for d in model.undesired_dates},
        desired_dates={date.fromisoformat(d) for d in model.desired_dates}
    )


def model_to_shift(model: domain.ShiftModel, employee_lookup: dict) -> domain.Shift:
    # Handle employee reference
    employee = None
    if model.employee:
        if isinstance(model.employee, str):
            employee = employee_lookup[model.employee]
        else:
            employee = model_to_employee(model.employee)
    
    return domain.Shift(
        id=model.id,
        start=datetime.fromisoformat(model.start),
        end=datetime.fromisoformat(model.end),
        location=model.location,
        required_skill=model.required_skill,
        employee=employee
    )


def model_to_schedule(model: domain.EmployeeScheduleModel) -> domain.EmployeeSchedule:
    # Convert employees first
    employees = [model_to_employee(e) for e in model.employees]
    
    # Create lookup dictionary for employee references
    employee_lookup = {e.name: e for e in employees}
    
    # Convert shifts with employee lookups
    shifts = [
        model_to_shift(s, employee_lookup)
        for s in model.shifts
    ]
    
    # Handle score
    score = None
    if model.score:
        from timefold.solver.score import HardSoftDecimalScore
        score = HardSoftDecimalScore.parse(model.score)
    
    # Handle solver status
    solver_status = domain.SolverStatus.NOT_SOLVING
    if model.solver_status:
        solver_status = domain.SolverStatus[model.solver_status]
    
    return domain.EmployeeSchedule(
        employees=employees,
        shifts=shifts,
        score=score,
        solver_status=solver_status
    ) 