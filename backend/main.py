from fastapi import FastAPI
from pydantic import BaseModel 
from crew import run_crew 
from prometheus_fastapi_instrumentator import Instrumentator


app=FastAPI()

class TravelRequest(BaseModel):
    city:str 
    interest:str
    budget:str 

Instrumentator().instrument(app).expose(app) 


@app.post('/plan_trip')
def plan_trip(request:TravelRequest):
    result=run_crew(request.city,request.interest,request.budget)
    return {'itenary':str(result)}

