from timefold.solver import SolverStatus
from timefold.solver.domain import (
    planning_entity, planning_solution, PlanningId, PlanningVariable,
    PlanningEntityCollectionProperty, ProblemFactCollectionProperty, ValueRangeProvider,
    PlanningScore
)
from timefold.solver.score import HardSoftDecimalScore
from datetime import datetime, date
from typing import Annotated, List, Optional, Union
from dataclasses import dataclass, field
from .json_serialization import JsonDomainBase
from pydantic import Field


@dataclass
class Employee:
    name: Annotated[str, PlanningId]
    skills: set[str] = field(default_factory=set)
    unavailable_dates: set[date] = field(default_factory=set)
    undesired_dates: set[date] = field(default_factory=set)
    desired_dates: set[date] = field(default_factory=set)


@planning_entity
@dataclass
class Shift:
    id: Annotated[str, PlanningId]
    start: datetime
    end: datetime
    location: str
    required_skill: str
    employee: Annotated[Employee | None, PlanningVariable] = None


@planning_solution
@dataclass
class EmployeeSchedule:
    employees: Annotated[list[Employee], ProblemFactCollectionProperty, ValueRangeProvider]
    shifts: Annotated[list[Shift], PlanningEntityCollectionProperty]
    score: Annotated[HardSoftDecimalScore | None, PlanningScore] = None
    solver_status: SolverStatus = SolverStatus.NOT_SOLVING


# Pydantic REST models for API (used for deserialization and context)
class EmployeeModel(JsonDomainBase):
    name: str
    skills: List[str] = Field(default_factory=list)
    unavailable_dates: List[str] = Field(default_factory=list, alias="unavailableDates")
    undesired_dates: List[str] = Field(default_factory=list, alias="undesiredDates")
    desired_dates: List[str] = Field(default_factory=list, alias="desiredDates")


class ShiftModel(JsonDomainBase):
    id: str
    start: str  # ISO datetime string
    end: str    # ISO datetime string
    location: str
    required_skill: str = Field(..., alias="requiredSkill")
    employee: Union[str, EmployeeModel, None] = None


class EmployeeScheduleModel(JsonDomainBase):
    employees: List[EmployeeModel]
    shifts: List[ShiftModel]
    score: Optional[str] = None
    solver_status: Optional[str] = None
