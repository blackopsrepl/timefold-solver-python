from meeting_scheduling.rest_api import app
from meeting_scheduling.domain import MeetingSchedule
from meeting_scheduling.converters import MeetingScheduleModel, model_to_schedule
from timefold.solver.score import HardMediumSoftScore

from fastapi.testclient import TestClient
from time import sleep
from pytest import fail
import json

client = TestClient(app)


def json_to_meeting_schedule(schedule_json):
    """Convert JSON response to MeetingSchedule domain object with proper score."""
    # Parse JSON to Pydantic model first
    schedule_model = MeetingScheduleModel.model_validate(schedule_json)
    
    # Convert to domain model
    schedule = model_to_schedule(schedule_model)
    
    return schedule


def test_feasible():
    demo_data_response = client.get("/demo-data")
    assert demo_data_response.status_code == 200

    job_id_response = client.post("/schedules", json=demo_data_response.json())
    assert job_id_response.status_code == 200
    job_id = job_id_response.text[1:-1]

    ATTEMPTS = 1_000
    for _ in range(ATTEMPTS):
        sleep(0.1)
        schedule_response = client.get(f"/schedules/{job_id}")
        schedule_json = schedule_response.json()
        schedule = json_to_meeting_schedule(schedule_json)
        
        if schedule.score is not None and schedule.score.is_feasible:
            # Additional validation like Java version
            assert all(assignment.starting_time_grain is not None and assignment.room is not None 
                      for assignment in schedule.meeting_assignments)
            
            stop_solving_response = client.delete(f"/schedules/{job_id}")
            assert stop_solving_response.status_code == 200
            return

    client.delete(f"/schedules/{job_id}")
    fail('solution is not feasible')


def test_analyze():
    demo_data_response = client.get("/demo-data")
    assert demo_data_response.status_code == 200

    job_id_response = client.post("/schedules", json=demo_data_response.json())
    assert job_id_response.status_code == 200
    job_id = job_id_response.text[1:-1]

    ATTEMPTS = 1_000
    for _ in range(ATTEMPTS):
        sleep(0.1)
        schedule_response = client.get(f"/schedules/{job_id}")
        schedule_json = schedule_response.json()
        schedule = json_to_meeting_schedule(schedule_json)
        
        if schedule.score is not None and schedule.score.is_feasible:
            # Test the analyze endpoint
            analysis_response = client.put("/schedules/analyze", json=schedule_json)
            assert analysis_response.status_code == 200
            analysis = analysis_response.text
            assert analysis is not None
            
            # Test with fetchPolicy parameter
            analysis_response_2 = client.put("/schedules/analyze?fetchPolicy=FETCH_SHALLOW", json=schedule_json)
            assert analysis_response_2.status_code == 200
            analysis_2 = analysis_response_2.text
            assert analysis_2 is not None
            
            client.delete(f"/schedules/{job_id}")
            return

    client.delete(f"/schedules/{job_id}")
    fail('solution is not feasible for analyze test')


def test_analyze_constraint_scores():
    """Test that the analyze endpoint returns proper constraint scores instead of all zeros."""
    demo_data_response = client.get("/demo-data")
    assert demo_data_response.status_code == 200

    job_id_response = client.post("/schedules", json=demo_data_response.json())
    assert job_id_response.status_code == 200
    job_id = job_id_response.text[1:-1]

    ATTEMPTS = 1_000
    for _ in range(ATTEMPTS):
        sleep(0.1)
        schedule_response = client.get(f"/schedules/{job_id}")
        schedule_json = schedule_response.json()
        schedule = json_to_meeting_schedule(schedule_json)
        
        if schedule.score is not None and schedule.score.is_feasible:
            # Test the analyze endpoint and verify constraint scores
            analysis_response = client.put("/schedules/analyze", json=schedule_json)
            assert analysis_response.status_code == 200
            
            # Parse the analysis response
            analysis_data = json.loads(analysis_response.text)
            constraints = analysis_data.get('constraints', [])
            
            # Verify we have constraints
            assert len(constraints) > 0, "Should have at least one constraint"
            
            # Check that at least some constraints have non-zero scores
            # (since we have a feasible solution, some soft constraints should be violated)
            non_zero_scores = 0
            for constraint in constraints:
                score_str = constraint.get('score', '')
                if score_str and score_str != '0hard/0medium/0soft':
                    non_zero_scores += 1
                    print(f"Found non-zero constraint score: {constraint.get('name')} = {score_str}")
            
            # We should have at least some non-zero scores for soft constraints
            assert non_zero_scores > 0, f"Expected some non-zero constraint scores, but all were zero. Total constraints: {len(constraints)}"
            
            print(f"✅ Analysis test passed: Found {non_zero_scores} constraints with non-zero scores out of {len(constraints)} total constraints")
            
            client.delete(f"/schedules/{job_id}")
            return

    client.delete(f"/schedules/{job_id}")
    fail('solution is not feasible for analyze constraint scores test') 