from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="OBP REST Demo",
    description="""
Demonstration REST application for the course

**Database Design**

Demonstrates:

- relational model
- stored procedures
- JSON
- REST API
- SQL Server
""",
    version="1.0"
)

app.include_router(router)
