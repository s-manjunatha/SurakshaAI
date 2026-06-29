from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "SurakshaAI Backend Running"}

@app.get("/health")
def health():
    return {"status": "ok"}
