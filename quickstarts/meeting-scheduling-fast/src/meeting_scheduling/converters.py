from typing import List, Optional, Union
from . import domain
from .json_serialization import JsonDomainBase
from pydantic import Field


# Pydantic models for API boundary
class PersonModel(JsonDomainBase):
    id: str
    full_name: str


class TimeGrainModel(JsonDomainBase):
    id: str
    grain_index: int
    day_of_year: int
    starting_minute_of_day: int


class RoomModel(JsonDomainBase):
    id: str
    name: str
    capacity: int


class RequiredAttendanceModel(JsonDomainBase):
    id: str
    person: PersonModel
    meeting_id: str = Field(..., alias="meeting")


class PreferredAttendanceModel(JsonDomainBase):
    id: str
    person: PersonModel
    meeting_id: str = Field(..., alias="meeting")


class MeetingModel(JsonDomainBase):
    id: str
    topic: str
    duration_in_grains: int
    speakers: Optional[List[PersonModel]] = None
    content: Optional[str] = None
    entire_group_meeting: bool = False
    required_attendances: List[RequiredAttendanceModel] = Field(default_factory=list, alias="requiredAttendances")
    preferred_attendances: List[PreferredAttendanceModel] = Field(default_factory=list, alias="preferredAttendances")


class MeetingAssignmentModel(JsonDomainBase):
    id: str
    meeting: Union[str, MeetingModel]
    pinned: bool = False
    starting_time_grain: Union[str, TimeGrainModel, None] = None
    room: Union[str, RoomModel, None] = None


class MeetingScheduleModel(JsonDomainBase):
    people: List[PersonModel]
    time_grains: List[TimeGrainModel] = Field(..., alias="timeGrains")
    rooms: List[RoomModel]
    meetings: List[MeetingModel]
    required_attendances: List[RequiredAttendanceModel] = Field(default_factory=list, alias="requiredAttendances")
    preferred_attendances: List[PreferredAttendanceModel] = Field(default_factory=list, alias="preferredAttendances")
    meeting_assignments: List[MeetingAssignmentModel] = Field(default_factory=list, alias="meetingAssignments")
    score: Optional[str] = None
    solver_status: Optional[str] = None


# Conversion functions from domain to API models
def person_to_model(person: domain.Person) -> PersonModel:
    return PersonModel(
        id=person.id,
        full_name=person.full_name
    )


def time_grain_to_model(time_grain: domain.TimeGrain) -> TimeGrainModel:
    return TimeGrainModel(
        id=time_grain.id,
        grain_index=time_grain.grain_index,
        day_of_year=time_grain.day_of_year,
        starting_minute_of_day=time_grain.starting_minute_of_day
    )


def room_to_model(room: domain.Room) -> RoomModel:
    return RoomModel(
        id=room.id,
        name=room.name,
        capacity=room.capacity
    )


def required_attendance_to_model(attendance: domain.RequiredAttendance) -> RequiredAttendanceModel:
    return RequiredAttendanceModel(
        id=attendance.id,
        person=person_to_model(attendance.person),
        meeting_id=attendance.meeting_id
    )


def preferred_attendance_to_model(attendance: domain.PreferredAttendance) -> PreferredAttendanceModel:
    return PreferredAttendanceModel(
        id=attendance.id,
        person=person_to_model(attendance.person),
        meeting_id=attendance.meeting_id
    )


def meeting_to_model(meeting: domain.Meeting) -> MeetingModel:
    return MeetingModel(
        id=meeting.id,
        topic=meeting.topic,
        duration_in_grains=meeting.duration_in_grains,
        speakers=[person_to_model(p) for p in meeting.speakers] if meeting.speakers else None,
        content=meeting.content,
        entire_group_meeting=meeting.entire_group_meeting,
        required_attendances=[required_attendance_to_model(ra) for ra in meeting.required_attendances],
        preferred_attendances=[preferred_attendance_to_model(pa) for pa in meeting.preferred_attendances]
    )


def meeting_assignment_to_model(assignment: domain.MeetingAssignment) -> MeetingAssignmentModel:
    return MeetingAssignmentModel(
        id=assignment.id,
        meeting=meeting_to_model(assignment.meeting),
        pinned=assignment.pinned,
        starting_time_grain=time_grain_to_model(assignment.starting_time_grain) if assignment.starting_time_grain else None,
        room=room_to_model(assignment.room) if assignment.room else None
    )


def schedule_to_model(schedule: domain.MeetingSchedule) -> MeetingScheduleModel:
    return MeetingScheduleModel(
        people=[person_to_model(p) for p in schedule.people],
        time_grains=[time_grain_to_model(tg) for tg in schedule.time_grains],
        rooms=[room_to_model(r) for r in schedule.rooms],
        meetings=[meeting_to_model(m) for m in schedule.meetings],
        required_attendances=[required_attendance_to_model(ra) for ra in schedule.required_attendances],
        preferred_attendances=[preferred_attendance_to_model(pa) for pa in schedule.preferred_attendances],
        meeting_assignments=[meeting_assignment_to_model(ma) for ma in schedule.meeting_assignments],
        score=str(schedule.score) if schedule.score else None,
        solver_status=schedule.solver_status.name if schedule.solver_status else None
    )


# Conversion functions from API models to domain
def model_to_person(model: PersonModel) -> domain.Person:
    return domain.Person(
        id=model.id,
        full_name=model.full_name
    )


def model_to_time_grain(model: TimeGrainModel) -> domain.TimeGrain:
    return domain.TimeGrain(
        id=model.id,
        grain_index=model.grain_index,
        day_of_year=model.day_of_year,
        starting_minute_of_day=model.starting_minute_of_day
    )


def model_to_room(model: RoomModel) -> domain.Room:
    return domain.Room(
        id=model.id,
        name=model.name,
        capacity=model.capacity
    )


def model_to_required_attendance(model: RequiredAttendanceModel) -> domain.RequiredAttendance:
    return domain.RequiredAttendance(
        id=model.id,
        person=model_to_person(model.person),
        meeting_id=model.meeting_id
    )


def model_to_preferred_attendance(model: PreferredAttendanceModel) -> domain.PreferredAttendance:
    return domain.PreferredAttendance(
        id=model.id,
        person=model_to_person(model.person),
        meeting_id=model.meeting_id
    )


def model_to_meeting(model: MeetingModel) -> domain.Meeting:
    return domain.Meeting(
        id=model.id,
        topic=model.topic,
        duration_in_grains=model.duration_in_grains,
        speakers=[model_to_person(p) for p in model.speakers] if model.speakers else None,
        content=model.content,
        entire_group_meeting=model.entire_group_meeting,
        required_attendances=[model_to_required_attendance(ra) for ra in model.required_attendances],
        preferred_attendances=[model_to_preferred_attendance(pa) for pa in model.preferred_attendances]
    )


def model_to_meeting_assignment(model: MeetingAssignmentModel, meeting_lookup: dict, room_lookup: dict, time_grain_lookup: dict) -> domain.MeetingAssignment:
    # Handle meeting reference
    if isinstance(model.meeting, str):
        meeting = meeting_lookup[model.meeting]
    else:
        meeting = model_to_meeting(model.meeting)
    
    # Handle room reference
    room = None
    if model.room:
        if isinstance(model.room, str):
            room = room_lookup[model.room]
        else:
            room = model_to_room(model.room)
    
    # Handle time grain reference
    starting_time_grain = None
    if model.starting_time_grain:
        if isinstance(model.starting_time_grain, str):
            starting_time_grain = time_grain_lookup[model.starting_time_grain]
        else:
            starting_time_grain = model_to_time_grain(model.starting_time_grain)
    
    return domain.MeetingAssignment(
        id=model.id,
        meeting=meeting,
        pinned=model.pinned,
        starting_time_grain=starting_time_grain,
        room=room
    )


def model_to_schedule(model: MeetingScheduleModel) -> domain.MeetingSchedule:
    # Convert basic collections first
    people = [model_to_person(p) for p in model.people]
    time_grains = [model_to_time_grain(tg) for tg in model.time_grains]
    rooms = [model_to_room(r) for r in model.rooms]
    meetings = [model_to_meeting(m) for m in model.meetings]
    
    # Create lookup dictionaries for references
    meeting_lookup = {m.id: m for m in meetings}
    room_lookup = {r.id: r for r in rooms}
    time_grain_lookup = {tg.id: tg for tg in time_grains}
    
    # Convert meeting assignments with lookups
    meeting_assignments = [
        model_to_meeting_assignment(ma, meeting_lookup, room_lookup, time_grain_lookup)
        for ma in model.meeting_assignments
    ]
    
    # Convert attendances
    required_attendances = [model_to_required_attendance(ra) for ra in model.required_attendances]
    preferred_attendances = [model_to_preferred_attendance(pa) for pa in model.preferred_attendances]
    
    # Handle score
    score = None
    if model.score:
        from timefold.solver.score import HardMediumSoftScore
        score = HardMediumSoftScore.parse(model.score)
    
    # Handle solver status  
    solver_status = domain.SolverStatus.NOT_SOLVING
    if model.solver_status:
        solver_status = domain.SolverStatus[model.solver_status]
    
    return domain.MeetingSchedule(
        people=people,
        time_grains=time_grains,
        rooms=rooms,
        meetings=meetings,
        required_attendances=required_attendances,
        preferred_attendances=preferred_attendances,
        meeting_assignments=meeting_assignments,
        score=score,
        solver_status=solver_status
    ) 