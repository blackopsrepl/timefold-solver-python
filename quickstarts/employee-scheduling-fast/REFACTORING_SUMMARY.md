# Employee Scheduling Fast - Model Separation Refactoring

This document summarizes the refactoring performed to separate data models in the employee-scheduling-fast project, following the pattern used in meeting-scheduling-fast.

## Overview

The refactoring separates the domain models (used by the Timefold solver) from the API models (used for REST API communication), providing better separation of concerns and cleaner architecture.

## Changes Made

### 1. Created `converters.py`

**New file**: `src/employee_scheduling/converters.py`

This file contains:
- **API Models**: Pydantic models for REST API communication
  - `EmployeeModel`: API representation of employees
  - `ShiftModel`: API representation of shifts  
  - `EmployeeScheduleModel`: API representation of schedules
- **Conversion Functions**: Functions to convert between domain and API models
  - `employee_to_model()`, `shift_to_model()`, `schedule_to_model()`: Domain → API
  - `model_to_employee()`, `model_to_shift()`, `model_to_schedule()`: API → Domain

### 2. Updated `domain.py`

**Changes**:
- Removed inheritance from `JsonDomainBase`
- Changed from Pydantic models to dataclasses with Timefold annotations
- Made imports more explicit (removed wildcard imports)
- Simplified field definitions using `field(default_factory=...)`

**Before**:
```python
class Employee(JsonDomainBase):
    name: Annotated[str, PlanningId]
    skills: Annotated[set[str], Field(default_factory=set)]
    # ...
```

**After**:
```python
@dataclass
class Employee:
    name: Annotated[str, PlanningId]
    skills: set[str] = field(default_factory=set)
    # ...
```

### 3. Updated `rest_api.py`

**Changes**:
- Updated imports to use converters
- Changed API endpoints to use API models instead of domain models
- Added conversion between API and domain models in request/response handling

**Before**:
```python
@app.get("/demo-data/{dataset_id}")
async def get_demo_data(dataset_id: str) -> EmployeeSchedule:
    return generate_demo_data(demo_data)
```

**After**:
```python
@app.get("/demo-data/{dataset_id}")
async def get_demo_data(dataset_id: str) -> EmployeeScheduleModel:
    domain_schedule = generate_demo_data(demo_data)
    return schedule_to_model(domain_schedule)
```

### 4. Updated `solver.py`

**Changes**:
- Made imports more explicit (removed wildcard imports)
- No functional changes needed

### 5. Updated Tests

**Changes**:
- Updated `test_feasible.py` to use API models and conversion functions
- `test_constraints.py` remains unchanged (uses domain models directly)

## Benefits of This Refactoring

1. **Separation of Concerns**: Domain models are purely for the solver, API models are for REST communication
2. **Type Safety**: Clear distinction between internal and external data structures
3. **Maintainability**: Changes to API format don't affect domain logic
4. **Consistency**: Follows the same pattern as meeting-scheduling-fast
5. **Flexibility**: API models can evolve independently of domain models

## Data Flow

```
REST API Request → API Models → Conversion → Domain Models → Solver
Solver → Domain Models → Conversion → API Models → REST API Response
```

## File Structure

```
src/employee_scheduling/
├── domain.py          # Domain models (dataclasses with Timefold annotations)
├── converters.py      # API models and conversion functions
├── rest_api.py        # REST API endpoints (uses API models)
├── constraints.py     # Constraint definitions (uses domain models)
├── solver.py          # Solver configuration (uses domain models)
├── demo_data.py       # Demo data generation (uses domain models)
└── json_serialization.py  # Base classes and serialization utilities
```

## Testing

A test script `test_refactoring.py` was created to verify:
- Domain models can be created correctly
- Conversion between domain and API models works
- Round-trip conversion preserves data integrity

## Compatibility

This refactoring maintains full backward compatibility for the solver and constraint logic. Only the REST API interface has changed to use the new API models. 