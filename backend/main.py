"""
FastAPI server with async job queue for long-running LinkedIn lead profiling
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any
from workflow import process_linkedin_post

load_dotenv()

app = FastAPI(title="LinkedIn Lead Profiling API")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store (restart loses state - acceptable for internal tool)
jobs: Dict[str, Dict[str, Any]] = {}

class PostRequest(BaseModel):
    """Validates incoming LinkedIn post URL or ID"""
    post_url: str

class ManualProfilesRequest(BaseModel):
    """Validates incoming manual profile URLs"""
    profile_urls: list[str]

@app.get("/")
def root():
    """Health check endpoint"""
    return {"message": "LinkedIn Lead Profiling API is running"}

@app.post("/api/process-post")
async def process_post(request: PostRequest):
    """Start background job to process LinkedIn post reactors"""
    try:
        post_id = request.post_url.strip()

        # Extract numeric ID from URL if full URL provided
        if "linkedin.com" in post_id or "/" in post_id:
            parts = post_id.split("/")
            post_id = [p for p in parts if p and p.isdigit()][-1] if any(p.isdigit() for p in parts) else post_id

        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Initialize job state
        jobs[job_id] = {
            "status": "processing",
            "post_id": post_id,
            "progress": {
                "current": 0,
                "total": 0,
                "message": "Fetching post reactions..."
            },
            "results": [],
            "partial_results": [],  # Incremental results as they're processed
            "skipped_profiles": [],  # Profiles skipped due to timeout or errors
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "error": None
        }

        # Start background processing
        asyncio.create_task(process_job_async(job_id, post_id))

        return {
            "job_id": job_id,
            "status": "started",
            "message": f"Processing started for post {post_id}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-manual-profiles")
async def process_manual_profiles(request: ManualProfilesRequest):
    """Start background job to process manually provided LinkedIn profile URLs"""
    try:
        profile_urls = request.profile_urls

        # Validate and clean URLs
        profile_urls = [url.strip() for url in profile_urls if url.strip()]

        if not profile_urls:
            raise HTTPException(status_code=400, detail="No valid profile URLs provided")

        # Basic LinkedIn URL validation
        invalid_urls = []
        for url in profile_urls:
            if not ('linkedin.com/in/' in url.lower() or url.startswith('/')):
                invalid_urls.append(url)

        if invalid_urls:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid LinkedIn profile URLs: {', '.join(invalid_urls[:3])}"
            )

        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Initialize job state
        jobs[job_id] = {
            "status": "processing",
            "profile_count": len(profile_urls),
            "progress": {
                "current": 0,
                "total": 0,
                "message": "Starting manual profile processing..."
            },
            "results": [],
            "partial_results": [],  # Incremental results as they're processed
            "skipped_profiles": [],  # Profiles skipped due to timeout or errors
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "error": None
        }

        # Start background processing
        asyncio.create_task(process_manual_profiles_async(job_id, profile_urls))

        return {
            "job_id": job_id,
            "status": "started",
            "message": f"Processing started for {len(profile_urls)} profiles"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/job-status/{job_id}")
async def get_job_status(job_id: str):
    """Get current status and progress of a background job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "results": job["results"] if job["status"] == "completed" else job.get("partial_results", []),
        "skipped_profiles": job.get("skipped_profiles", []),  # Include skipped profiles
        "started_at": job["started_at"],
        "completed_at": job["completed_at"],
        "error": job["error"]
    }

async def process_job_async(job_id: str, post_id: str):
    """Run workflow in background and update job progress"""
    try:
        # Run workflow in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            process_linkedin_post_with_progress,
            post_id,
            job_id
        )

        # Mark job as completed
        successful_count = len(results.get("leads", []))
        skipped_count = len(results.get("skipped_profiles", []))

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["results"] = results.get("leads", [])
        # Skipped profiles already added during processing, but update from final results too
        jobs[job_id]["skipped_profiles"] = results.get("skipped_profiles", [])
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["progress"]["message"] = f"Completed! {successful_count} successful, {skipped_count} skipped"

    except Exception as e:
        # Mark job as failed
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["progress"]["message"] = f"Error: {str(e)}"

async def process_manual_profiles_async(job_id: str, profile_urls: list):
    """Run manual profile workflow in background"""
    try:
        # Run workflow in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            process_manual_profiles_with_progress,
            profile_urls,
            job_id
        )

        # Mark job as completed
        successful_count = len(results.get("leads", []))
        skipped_count = len(results.get("skipped_profiles", []))

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["results"] = results.get("leads", [])
        # Skipped profiles already added during processing, but update from final results too
        jobs[job_id]["skipped_profiles"] = results.get("skipped_profiles", [])
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["progress"]["message"] = f"Completed! {successful_count} successful, {skipped_count} skipped"

    except Exception as e:
        # Mark job as failed
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["progress"]["message"] = f"Error: {str(e)}"

def process_linkedin_post_with_progress(post_id: str, job_id: str) -> dict:
    """Wrapper to update job progress during processing"""
    from workflow import process_linkedin_post_tracked
    return process_linkedin_post_tracked(post_id, job_id, jobs)

def process_manual_profiles_with_progress(profile_urls: list, job_id: str) -> dict:
    """Wrapper to update job progress during manual profile processing"""
    from workflow import process_manual_profiles_tracked
    return process_manual_profiles_tracked(profile_urls, job_id, jobs)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
