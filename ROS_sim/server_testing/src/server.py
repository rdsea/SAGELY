from fastapi import FastAPI

app = FastAPI()


@app.get("/tri")
async def root():
    return {"message": "Hello World"}

