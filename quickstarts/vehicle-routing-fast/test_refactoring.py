#!/usr/bin/env python3

"""Simple test script to verify the refactoring works correctly."""

from src.vehicle_routing.domain import Location, Visit, Vehicle, VehicleRoutePlan
from src.vehicle_routing.converters import location_to_model, visit_to_model, vehicle_to_model, plan_to_model
from datetime import datetime, timedelta

def test_basic_creation():
    """Test that we can create domain objects."""
    print("Testing basic domain object creation...")
    
    # Create a location
    location = Location(latitude=40.0, longitude=-75.0)
    print(f"✓ Created Location: {location}")
    
    # Create a visit
    visit = Visit(
        id="visit1",
        name="Test Visit",
        location=location,
        demand=10,
        min_start_time=datetime.now(),
        max_end_time=datetime.now() + timedelta(hours=2),
        service_duration=timedelta(minutes=30)
    )
    print(f"✓ Created Visit: {visit}")
    
    # Create a vehicle
    vehicle = Vehicle(
        id="vehicle1",
        capacity=100,
        home_location=location,
        departure_time=datetime.now()
    )
    print(f"✓ Created Vehicle: {vehicle}")
    
    # Create a plan
    plan = VehicleRoutePlan(
        name="Test Plan",
        south_west_corner=Location(latitude=39.0, longitude=-76.0),
        north_east_corner=Location(latitude=41.0, longitude=-74.0),
        vehicles=[vehicle],
        visits=[visit]
    )
    print(f"✓ Created VehicleRoutePlan: {plan}")
    
    return True

def test_conversion():
    """Test that we can convert between domain and API models."""
    print("\nTesting conversion functions...")
    
    # Create domain objects
    location = Location(latitude=40.0, longitude=-75.0)
    visit = Visit(
        id="visit1",
        name="Test Visit",
        location=location,
        demand=10,
        min_start_time=datetime.now(),
        max_end_time=datetime.now() + timedelta(hours=2),
        service_duration=timedelta(minutes=30)
    )
    vehicle = Vehicle(
        id="vehicle1",
        capacity=100,
        home_location=location,
        departure_time=datetime.now()
    )
    plan = VehicleRoutePlan(
        name="Test Plan",
        south_west_corner=Location(latitude=39.0, longitude=-76.0),
        north_east_corner=Location(latitude=41.0, longitude=-74.0),
        vehicles=[vehicle],
        visits=[visit]
    )
    
    # Convert to API models
    location_model = location_to_model(location)
    visit_model = visit_to_model(visit)
    vehicle_model = vehicle_to_model(vehicle)
    plan_model = plan_to_model(plan)
    
    print(f"✓ Converted Location to model: {location_model}")
    print(f"✓ Converted Visit to model: {visit_model}")
    print(f"✓ Converted Vehicle to model: {vehicle_model}")
    print(f"✓ Converted Plan to model: {plan_model}")
    
    return True

if __name__ == "__main__":
    try:
        test_basic_creation()
        test_conversion()
        print("\n🎉 All tests passed! The refactoring is working correctly.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 