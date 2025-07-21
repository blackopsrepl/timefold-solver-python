from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from uuid import uuid4
from typing import Annotated

from .domain import *
from .converters import *
from .score_analysis import *
from .demo_data import DemoData, generate_demo_data
from .solver import solver_manager, solution_manager


app = FastAPI(docs_url='/q/swagger-ui')
data_sets: dict[str, VehicleRoutePlan] = {}


@app.get("/demo-data")
async def demo_data_list():
    return [e.name for e in DemoData]


@app.get("/demo-data/{dataset_id}", response_model_exclude_none=True)
async def get_demo_data(dataset_id: str) -> VehicleRoutePlanModel:
    demo_data = generate_demo_data(getattr(DemoData, dataset_id))
    return plan_to_model(demo_data)


@app.get("/route-plans/{problem_id}", response_model_exclude_none=True)
async def get_route(problem_id: str) -> VehicleRoutePlanModel:
    route = data_sets[problem_id]
    route.solver_status = solver_manager.get_solver_status(problem_id)
    return plan_to_model(route)


def update_route(problem_id: str, route: VehicleRoutePlan):
    global data_sets
    data_sets[problem_id] = route


def json_to_vehicle_route_plan(json: dict) -> VehicleRoutePlan:
    try:
        return model_to_plan(VehicleRoutePlanModel.model_validate(json))
    except Exception as e:
        print(f"Error converting JSON to VehicleRoutePlan: {e}")
        print(f"JSON data: {json}")
        raise


async def setup_context(request: Request) -> VehicleRoutePlan:
    json = await request.json()
    return json_to_vehicle_route_plan(json)


@app.post("/route-plans")
async def solve_route(route: Annotated[VehicleRoutePlan, Depends(setup_context)]) -> str:
    print(f"Received solve request for route: {route.name}")
    job_id = str(uuid4())
    data_sets[job_id] = route
    solver_manager.solve_and_listen(job_id, route,
                                    lambda solution: update_route(job_id, solution))
    return job_id


@app.put("/route-plans/analyze")
async def analyze_route(route: Annotated[VehicleRoutePlan, Depends(setup_context)]) \
        -> dict['str', list[ConstraintAnalysisDTO]]:
    return {'constraints': [ConstraintAnalysisDTO(
        name=constraint.constraint_name,
        weight=constraint.weight,
        score=constraint.score,
        matches=[
            MatchAnalysisDTO(
                name=match.constraint_ref.constraint_name,
                score=match.score,
                justification=match.justification
            )
            for match in constraint.matches
        ]
    ) for constraint in solution_manager.analyze(route).constraint_analyses]}


@app.delete("/route-plans/{problem_id}")
async def stop_solving(problem_id: str) -> None:
    solver_manager.terminate_early(problem_id)


app.mount("/", StaticFiles(directory="static", html=True), name="static")
