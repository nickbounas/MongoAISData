from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from mongo import connect_to_mongo, close_mongo_connection
from fastapi.responses import JSONResponse
from exceptions import ApplicationException
from router import router

app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

@app.exception_handler(ApplicationException)
async def request_application_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message}
    )

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
