from fastapi import FastAPI, Query
from dotenv import load_dotenv
from Client.rq_client import queue
from Queue.worker import process_query

load_dotenv()

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Server is up and running"}

@app.post("/chat")
def chat(
    query: str = Query(..., description="The chat queued for user")
):
    # Enqueue job to RQ worker
    job = queue.enqueue(process_query, query)
    return {"status": "queued", "job_id": job.id}

@app.get("/result")
def result(
    job_id: str = Query(..., description="The job ID to fetch result for")
):
    job = queue.fetch_job(job_id=job_id)
    if not job:
        return {"status": "not_found", "message": f"Job '{job_id}' not found or expired"}

    if job.is_finished:
        return {"status": "finished", "result": job.result}
    elif job.is_failed:
        return {"status": "failed", "error": str(job.exc_info)}
    else:
        return {"status": job.get_status()}