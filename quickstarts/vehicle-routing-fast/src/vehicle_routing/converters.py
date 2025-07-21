from typing import List
from datetime import datetime, timedelta
from . import domain

# Conversion functions from domain to API models
def location_to_model(location: domain.Location) -> List[float]:
    return [location.latitude, location.longitude]


def visit_to_model(visit: domain.Visit) -> domain.VisitModel:
    return domain.VisitModel(
        id=visit.id,
        name=visit.name,
        location=location_to_model(visit.location),
        demand=visit.demand,
        min_start_time=visit.min_start_time.isoformat(),
        max_end_time=visit.max_end_time.isoformat(),
        service_duration=int(visit.service_duration.total_seconds()),
        vehicle=visit.vehicle.id if visit.vehicle else None,
        previous_visit=visit.previous_visit.id if visit.previous_visit else None,
        next_visit=visit.next_visit.id if visit.next_visit else None,
        arrival_time=visit.arrival_time.isoformat() if visit.arrival_time else None,
        departure_time=visit.departure_time.isoformat() if visit.departure_time else None,
        driving_time_seconds_from_previous_standstill=visit.driving_time_seconds_from_previous_standstill
    )


def vehicle_to_model(vehicle: domain.Vehicle) -> domain.VehicleModel:
    return domain.VehicleModel(
        id=vehicle.id,
        capacity=vehicle.capacity,
        home_location=location_to_model(vehicle.home_location),
        departure_time=vehicle.departure_time.isoformat(),
        visits=[visit.id for visit in vehicle.visits],
        total_demand=vehicle.total_demand,
        total_driving_time_seconds=vehicle.total_driving_time_seconds,
        arrival_time=vehicle.arrival_time.isoformat()
    )


def plan_to_model(plan: domain.VehicleRoutePlan) -> domain.VehicleRoutePlanModel:
    return domain.VehicleRoutePlanModel(
        name=plan.name,
        south_west_corner=location_to_model(plan.south_west_corner),
        north_east_corner=location_to_model(plan.north_east_corner),
        vehicles=[vehicle_to_model(v) for v in plan.vehicles],
        visits=[visit_to_model(v) for v in plan.visits],
        score=str(plan.score) if plan.score else None,
        solver_status=plan.solver_status.name if plan.solver_status else None,
        total_driving_time_seconds=plan.total_driving_time_seconds
    )


# Conversion functions from API models to domain
def model_to_location(model: List[float]) -> domain.Location:
    return domain.Location(latitude=model[0], longitude=model[1])


def model_to_visit(model: domain.VisitModel, vehicle_lookup: dict, visit_lookup: dict) -> domain.Visit:
    # Handle vehicle reference
    vehicle = None
    if model.vehicle:
        if isinstance(model.vehicle, str):
            vehicle = vehicle_lookup[model.vehicle]
        else:
            # This shouldn't happen in practice, but handle it for completeness
            vehicle = vehicle_lookup[model.vehicle.id]
    
    # Handle previous visit reference
    previous_visit = None
    if model.previous_visit:
        if isinstance(model.previous_visit, str):
            previous_visit = visit_lookup[model.previous_visit]
        else:
            previous_visit = visit_lookup[model.previous_visit.id]
    
    # Handle next visit reference
    next_visit = None
    if model.next_visit:
        if isinstance(model.next_visit, str):
            next_visit = visit_lookup[model.next_visit]
        else:
            next_visit = visit_lookup[model.next_visit.id]
    
    return domain.Visit(
        id=model.id,
        name=model.name,
        location=model_to_location(model.location),
        demand=model.demand,
        min_start_time=datetime.fromisoformat(model.min_start_time),
        max_end_time=datetime.fromisoformat(model.max_end_time),
        service_duration=timedelta(seconds=model.service_duration),
        vehicle=vehicle,
        previous_visit=previous_visit,
        next_visit=next_visit,
        arrival_time=datetime.fromisoformat(model.arrival_time) if model.arrival_time else None
    )


def model_to_vehicle(model: domain.VehicleModel, visit_lookup: dict) -> domain.Vehicle:
    # Handle visits references
    visits = []
    for visit_ref in model.visits:
        if isinstance(visit_ref, str):
            visits.append(visit_lookup[visit_ref])
        else:
            visits.append(visit_lookup[visit_ref.id])
    
    return domain.Vehicle(
        id=model.id,
        capacity=model.capacity,
        home_location=model_to_location(model.home_location),
        departure_time=datetime.fromisoformat(model.departure_time),
        visits=visits
    )


def model_to_plan(model: domain.VehicleRoutePlanModel) -> domain.VehicleRoutePlan:
    # Convert basic collections first
    vehicles = []
    visits = []
    
    # Convert visits first (they don't depend on vehicles)
    for visit_model in model.visits:
        visit = domain.Visit(
            id=visit_model.id,
            name=visit_model.name,
            location=model_to_location(visit_model.location),
            demand=visit_model.demand,
            min_start_time=datetime.fromisoformat(visit_model.min_start_time),
            max_end_time=datetime.fromisoformat(visit_model.max_end_time),
            service_duration=timedelta(seconds=visit_model.service_duration),
            vehicle=None,  # Will be set later
            previous_visit=None,  # Will be set later
            next_visit=None,  # Will be set later
            arrival_time=datetime.fromisoformat(visit_model.arrival_time) if visit_model.arrival_time else None
        )
        visits.append(visit)
    
    # Create lookup dictionaries
    visit_lookup = {v.id: v for v in visits}
    
    # Convert vehicles
    for vehicle_model in model.vehicles:
        vehicle = domain.Vehicle(
            id=vehicle_model.id,
            capacity=vehicle_model.capacity,
            home_location=model_to_location(vehicle_model.home_location),
            departure_time=datetime.fromisoformat(vehicle_model.departure_time),
            visits=[]
        )
        vehicles.append(vehicle)
    
    # Create vehicle lookup
    vehicle_lookup = {v.id: v for v in vehicles}
    
    # Now set up the relationships
    for i, visit_model in enumerate(model.visits):
        visit = visits[i]
        
        # Set vehicle reference
        if visit_model.vehicle:
            if isinstance(visit_model.vehicle, str):
                visit.vehicle = vehicle_lookup[visit_model.vehicle]
            else:
                visit.vehicle = vehicle_lookup[visit_model.vehicle.id]
        
        # Set previous/next visit references
        if visit_model.previous_visit:
            if isinstance(visit_model.previous_visit, str):
                visit.previous_visit = visit_lookup[visit_model.previous_visit]
            else:
                visit.previous_visit = visit_lookup[visit_model.previous_visit.id]
        
        if visit_model.next_visit:
            if isinstance(visit_model.next_visit, str):
                visit.next_visit = visit_lookup[visit_model.next_visit]
            else:
                visit.next_visit = visit_lookup[visit_model.next_visit.id]
    
    # Set up vehicle visits lists
    for vehicle_model in model.vehicles:
        vehicle = vehicle_lookup[vehicle_model.id]
        for visit_ref in vehicle_model.visits:
            if isinstance(visit_ref, str):
                vehicle.visits.append(visit_lookup[visit_ref])
            else:
                vehicle.visits.append(visit_lookup[visit_ref.id])
    
    # Handle score
    score = None
    if model.score:
        from timefold.solver.score import HardSoftScore
        score = HardSoftScore.parse(model.score)
    
    # Handle solver status
    solver_status = domain.SolverStatus.NOT_SOLVING
    if model.solver_status:
        solver_status = domain.SolverStatus[model.solver_status]
    
    return domain.VehicleRoutePlan(
        name=model.name,
        south_west_corner=model_to_location(model.south_west_corner),
        north_east_corner=model_to_location(model.north_east_corner),
        vehicles=vehicles,
        visits=visits,
        score=score,
        solver_status=solver_status
    ) 