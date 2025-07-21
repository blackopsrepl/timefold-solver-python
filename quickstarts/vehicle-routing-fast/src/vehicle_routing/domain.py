from timefold.solver import SolverStatus
from timefold.solver.score import HardSoftScore
from timefold.solver.domain import *

from datetime import datetime, timedelta
from typing import Annotated, Optional, List, Union
from dataclasses import dataclass, field
from .json_serialization import JsonDomainBase
from pydantic import Field


@dataclass
class Location:
    latitude: float
    longitude: float

    def driving_time_to(self, other: 'Location') -> int:
        return round((
             (self.latitude - other.latitude) ** 2 +
             (self.longitude - other.longitude) ** 2
         ) ** 0.5 * 4_000)

    def __str__(self):
        return f'[{self.latitude}, {self.longitude}]'

    def __repr__(self):
        return f'Location({self.latitude}, {self.longitude})'


@planning_entity
@dataclass
class Visit:
    id: Annotated[str, PlanningId]
    name: str
    location: Location
    demand: int
    min_start_time: datetime
    max_end_time: datetime
    service_duration: timedelta
    vehicle: Annotated[Optional['Vehicle'],
                       InverseRelationShadowVariable(source_variable_name='visits')] = None
    previous_visit: Annotated[Optional['Visit'],
                              PreviousElementShadowVariable(source_variable_name='visits')] = None
    next_visit: Annotated[Optional['Visit'],
                          NextElementShadowVariable(source_variable_name='visits')] = None
    arrival_time: Annotated[
        Optional[datetime],
        CascadingUpdateShadowVariable(target_method_name='update_arrival_time')] = None

    def update_arrival_time(self):
        if self.vehicle is None or (self.previous_visit is not None and self.previous_visit.arrival_time is None):
            self.arrival_time = None
        elif self.previous_visit is None:
            self.arrival_time = (self.vehicle.departure_time +
                                 timedelta(seconds=self.vehicle.home_location.driving_time_to(self.location)))
        else:
            self.arrival_time = (self.previous_visit.calculate_departure_time() +
                                 timedelta(seconds=self.previous_visit.location.driving_time_to(self.location)))

    def calculate_departure_time(self):
        if self.arrival_time is None:
            return None

        return max(self.arrival_time, self.min_start_time) + self.service_duration

    @property
    def departure_time(self) -> Optional[datetime]:
        return self.calculate_departure_time()

    @property
    def start_service_time(self) -> Optional[datetime]:
        if self.arrival_time is None:
            return None
        return max(self.arrival_time, self.min_start_time)

    def is_service_finished_after_max_end_time(self) -> bool:
        return self.arrival_time is not None and self.calculate_departure_time() > self.max_end_time

    def service_finished_delay_in_minutes(self) -> int:
        if self.arrival_time is None:
            return 0
        # Floor division always rounds down, so divide by a negative duration and negate the result
        # to round up
        # ex: 30 seconds / -1 minute = -0.5,
        # so 30 seconds // -1 minute = -1,
        # and negating that gives 1
        return -((self.calculate_departure_time() - self.max_end_time) // timedelta(minutes=-1))

    @property
    def driving_time_seconds_from_previous_standstill(self) -> Optional[int]:
        if self.vehicle is None:
            return None

        if self.previous_visit is None:
            return self.vehicle.home_location.driving_time_to(self.location)
        else:
            return self.previous_visit.location.driving_time_to(self.location)

    def __str__(self):
        return self.id

    def __repr__(self):
        return f'Visit({self.id})'


@planning_entity
@dataclass
class Vehicle:
    id: Annotated[str, PlanningId]
    capacity: int
    home_location: Location
    departure_time: datetime
    visits: Annotated[list[Visit],
                      PlanningListVariable] = field(default_factory=list)

    @property
    def arrival_time(self) -> datetime:
        if len(self.visits) == 0:
            return self.departure_time
        return (self.visits[-1].departure_time +
                timedelta(seconds=self.visits[-1].location.driving_time_to(self.home_location)))

    @property
    def total_demand(self) -> int:
        return self.calculate_total_demand()

    @property
    def total_driving_time_seconds(self) -> int:
        return self.calculate_total_driving_time_seconds()

    def calculate_total_demand(self) -> int:
        total_demand = 0
        for visit in self.visits:
            total_demand += visit.demand
        return total_demand

    def calculate_total_driving_time_seconds(self) -> int:
        if len(self.visits) == 0:
            return 0
        total_driving_time_seconds = 0
        previous_location = self.home_location

        for visit in self.visits:
            total_driving_time_seconds += previous_location.driving_time_to(visit.location)
            previous_location = visit.location

        total_driving_time_seconds += previous_location.driving_time_to(self.home_location)
        return total_driving_time_seconds

    def __str__(self):
        return self.id

    def __repr__(self):
        return f'Vehicle({self.id})'


@planning_solution
@dataclass
class VehicleRoutePlan:
    name: str
    south_west_corner: Location
    north_east_corner: Location
    vehicles: Annotated[list[Vehicle], PlanningEntityCollectionProperty]
    visits: Annotated[list[Visit], PlanningEntityCollectionProperty, ValueRangeProvider]
    score: Annotated[Optional[HardSoftScore], PlanningScore] = None
    solver_status: SolverStatus = SolverStatus.NOT_SOLVING

    @property
    def total_driving_time_seconds(self) -> int:
        out = 0
        for vehicle in self.vehicles:
            out += vehicle.total_driving_time_seconds
        return out

    def __str__(self):
        return f'VehicleRoutePlan(name={self.name}, vehicles={self.vehicles}, visits={self.visits})'


# Pydantic REST models for API (used for deserialization and context)
class LocationModel(JsonDomainBase):
    latitude: float
    longitude: float


class VisitModel(JsonDomainBase):
    id: str
    name: str
    location: List[float]  # [lat, lng] array
    demand: int
    min_start_time: str = Field(..., alias="minStartTime")  # ISO datetime string
    max_end_time: str = Field(..., alias="maxEndTime")    # ISO datetime string
    service_duration: int = Field(..., alias="serviceDuration")  # Duration in seconds
    vehicle: Union[str, 'VehicleModel', None] = None
    previous_visit: Union[str, 'VisitModel', None] = Field(None, alias="previousVisit")
    next_visit: Union[str, 'VisitModel', None] = Field(None, alias="nextVisit")
    arrival_time: Optional[str] = Field(None, alias="arrivalTime")  # ISO datetime string
    departure_time: Optional[str] = Field(None, alias="departureTime")  # ISO datetime string
    driving_time_seconds_from_previous_standstill: Optional[int] = Field(None, alias="drivingTimeSecondsFromPreviousStandstill")


class VehicleModel(JsonDomainBase):
    id: str
    capacity: int
    home_location: List[float] = Field(..., alias="homeLocation")  # [lat, lng] array
    departure_time: str = Field(..., alias="departureTime")  # ISO datetime string
    visits: List[Union[str, VisitModel]] = Field(default_factory=list)
    total_demand: int = Field(0, alias="totalDemand")
    total_driving_time_seconds: int = Field(0, alias="totalDrivingTimeSeconds")
    arrival_time: Optional[str] = Field(None, alias="arrivalTime")  # ISO datetime string


class VehicleRoutePlanModel(JsonDomainBase):
    name: str
    south_west_corner: List[float] = Field(..., alias="southWestCorner")  # [lat, lng] array
    north_east_corner: List[float] = Field(..., alias="northEastCorner")  # [lat, lng] array
    vehicles: List[VehicleModel]
    visits: List[VisitModel]
    score: Optional[str] = None
    solver_status: Optional[str] = None
    total_driving_time_seconds: int = Field(0, alias="totalDrivingTimeSeconds")
