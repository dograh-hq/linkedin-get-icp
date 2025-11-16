"""
FastAPI server with async job queue for long-running LinkedIn lead profiling
"""
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv
import os
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from workflow import process_linkedin_post
import json

load_dotenv()

app = FastAPI(title="LinkedIn Lead Profiling API")

# Add exception handler to log Pydantic validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log and return detailed validation errors"""
    print("\n" + "="*80)
    print("VALIDATION ERROR DETECTED!")
    print(f"Request URL: {request.url}")
    print(f"Request method: {request.method}")

    # Try to get raw request body
    try:
        body = await request.body()
        print(f"Raw request body: {body.decode('utf-8')}")
    except Exception as e:
        print(f"Could not read request body: {e}")

    print(f"Validation errors: {exc.errors()}")
    print("="*80 + "\n")

    return JSONResponse(
        status_code=400,
        content={
            "detail": exc.errors(),
            "body": str(exc.body) if hasattr(exc, 'body') else None
        }
    )

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

# ===================================
# AUTHENTICATION
# ===================================

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Verify X-API-Key header matches PORTAL_PASSWORD from environment.
    This protects backend endpoints from unauthorized access.
    """
    portal_password = os.getenv("PORTAL_PASSWORD")
    
    if not portal_password:
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: PORTAL_PASSWORD not set"
        )
    
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header. Please authenticate first."
        )
    
    if x_api_key != portal_password:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    
    return True

# ===================================
# REQUEST MODELS
# ===================================

class PostRequest(BaseModel):
    """Validates incoming LinkedIn post URL or ID"""
    post_url: str

class ManualProfilesRequest(BaseModel):
    """Validates incoming manual profile URLs"""
    profile_urls: list[str]

class LoginRequest(BaseModel):
    """Validates incoming login credentials"""
    password: str

class CustomCriteria(BaseModel):
    """Custom evaluation criteria for generic use case evaluation"""
    use_case_description: str  # Required field - what the user is looking for
    target_roles: Optional[str] = None  # Optional comma-separated roles
    target_industries: Optional[str] = None  # Optional industries/sectors
    company_size: Optional[str] = None  # Optional company size range
    additional_requirements: Optional[str] = None  # Optional exclusions, examples, edge cases

class PostRequestCustom(BaseModel):
    """Validates incoming LinkedIn post URL with custom evaluation criteria"""
    post_url: str
    custom_criteria: CustomCriteria

class ManualProfilesRequestCustom(BaseModel):
    """Validates incoming manual profile URLs with custom evaluation criteria"""
    profile_urls: list[str]
    custom_criteria: CustomCriteria

@app.get("/")
def root():
    """Health check endpoint"""
    return {"message": "LinkedIn Lead Profiling API is running"}

@app.post("/api/auth/login")
async def authenticate(request: LoginRequest):
    """Validate portal password from environment variable"""
    try:
        portal_password = os.getenv("PORTAL_PASSWORD")
        
        # Check if password is configured
        if not portal_password:
            raise HTTPException(
                status_code=500, 
                detail="Portal password not configured. Set PORTAL_PASSWORD in .env file"
            )
        
        # Validate password
        if request.password == portal_password:
            return {
                "success": True,
                "message": "Authentication successful"
            }
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid password"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-post")
async def process_post(request: PostRequest, authenticated: bool = Depends(verify_api_key)):
    """Start background job to process LinkedIn post reactors (requires authentication)"""
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
async def process_manual_profiles(request: ManualProfilesRequest, authenticated: bool = Depends(verify_api_key)):
    """Start background job to process manually provided LinkedIn profile URLs (requires authentication)"""
    try:
        profile_urls = request.profile_urls

        # Validate and clean URLs
        profile_urls = [url.strip() for url in profile_urls if url.strip()]

        if not profile_urls:
            raise HTTPException(status_code=400, detail="No valid profile URLs provided")

        # Basic LinkedIn URL validation - filter out invalid URLs instead of blocking
        invalid_urls = []
        valid_profile_urls = []

        for url in profile_urls:
            if 'linkedin.com/in/' in url.lower() or url.startswith('/'):
                valid_profile_urls.append(url)
            else:
                invalid_urls.append(url)
                print(f"Skipping invalid URL (not a profile): {url}")

        if invalid_urls:
            print(f"WARNING - Skipping {len(invalid_urls)} invalid URLs (company pages, etc.)")

        # Update profile_urls to only valid ones
        profile_urls = valid_profile_urls

        # Check if we have any valid URLs left
        if not profile_urls:
            raise HTTPException(
                status_code=400,
                detail="No valid LinkedIn profile URLs found. All URLs must contain 'linkedin.com/in/' (company pages are not supported)"
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

        # Build response message
        message = f"Processing started for {len(profile_urls)} valid profiles"
        if invalid_urls:
            message += f" ({len(invalid_urls)} invalid URLs skipped)"

        return {
            "job_id": job_id,
            "status": "started",
            "message": message,
            "valid_profiles": len(profile_urls),
            "skipped_urls": len(invalid_urls)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/job-status/{job_id}")
async def get_job_status(job_id: str, authenticated: bool = Depends(verify_api_key)):
    """Get current status and progress of a background job (requires authentication)"""
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

@app.post("/api/process-post-custom")
async def process_post_custom(request: PostRequestCustom, authenticated: bool = Depends(verify_api_key)):
    """Start background job to process LinkedIn post reactors with custom evaluation criteria (requires authentication)"""
    try:
        post_id = request.post_url.strip()

        # Extract numeric ID from URL if full URL provided
        if "linkedin.com" in post_id or "/" in post_id:
            parts = post_id.split("/")
            post_id = [p for p in parts if p and p.isdigit()][-1] if any(p.isdigit() for p in parts) else post_id

        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Initialize job state (same structure as regular endpoint)
        jobs[job_id] = {
            "status": "processing",
            "post_id": post_id,
            "custom_mode": True,  # Flag to track this is custom evaluation
            "progress": {
                "current": 0,
                "total": 0,
                "message": "Fetching post reactions..."
            },
            "results": [],
            "partial_results": [],
            "skipped_profiles": [],
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "error": None
        }

        # Start background processing with custom criteria
        asyncio.create_task(process_job_custom_async(job_id, post_id, request.custom_criteria))

        return {
            "job_id": job_id,
            "status": "started",
            "message": f"Custom evaluation started for post {post_id}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process-manual-profiles-custom")
async def process_manual_profiles_custom(request: ManualProfilesRequestCustom, authenticated: bool = Depends(verify_api_key)):
    """Start background job to process manually provided LinkedIn profiles with custom evaluation criteria (requires authentication)"""
    try:
        # DEBUG LOGGING - Log incoming request details
        print("\n" + "="*80)
        print("DEBUG: Received custom evaluation request")
        print(f"DEBUG: Request type: {type(request)}")
        print(f"DEBUG: Profile URLs: {request.profile_urls}")
        print(f"DEBUG: Custom criteria type: {type(request.custom_criteria)}")
        print(f"DEBUG: Custom criteria object: {request.custom_criteria}")
        print(f"DEBUG: use_case_description: {request.custom_criteria.use_case_description}")
        print(f"DEBUG: target_roles: {request.custom_criteria.target_roles}")
        print(f"DEBUG: target_industries: {request.custom_criteria.target_industries}")
        print(f"DEBUG: company_size: {request.custom_criteria.company_size}")
        print(f"DEBUG: additional_requirements: {request.custom_criteria.additional_requirements}")
        print("="*80 + "\n")

        profile_urls = request.profile_urls

        # Validate and clean URLs
        profile_urls = [url.strip() for url in profile_urls if url.strip()]
        print(f"DEBUG: Cleaned profile URLs count: {len(profile_urls)}")

        if not profile_urls:
            print("DEBUG: ERROR - No valid profile URLs after cleaning")
            raise HTTPException(status_code=400, detail="No valid profile URLs provided")

        # Basic LinkedIn URL validation - filter out invalid URLs instead of blocking
        invalid_urls = []
        valid_profile_urls = []

        for url in profile_urls:
            if 'linkedin.com/in/' in url.lower() or url.startswith('/'):
                valid_profile_urls.append(url)
            else:
                invalid_urls.append(url)
                print(f"DEBUG: Skipping invalid URL (not a profile): {url}")

        if invalid_urls:
            print(f"DEBUG: WARNING - Skipping {len(invalid_urls)} invalid URLs (company pages, etc.):")
            for url in invalid_urls[:5]:
                print(f"  - {url}")

        # Update profile_urls to only valid ones
        profile_urls = valid_profile_urls

        # Check if we have any valid URLs left
        if not profile_urls:
            print("DEBUG: ERROR - No valid profile URLs after filtering")
            raise HTTPException(
                status_code=400,
                detail="No valid LinkedIn profile URLs found. All URLs must contain 'linkedin.com/in/' (company pages are not supported)"
            )

        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Initialize job state
        jobs[job_id] = {
            "status": "processing",
            "profile_count": len(profile_urls),
            "custom_mode": True,  # Flag to track this is custom evaluation
            "progress": {
                "current": 0,
                "total": 0,
                "message": "Starting custom evaluation..."
            },
            "results": [],
            "partial_results": [],
            "skipped_profiles": [],
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "error": None
        }

        # Start background processing with custom criteria
        asyncio.create_task(process_manual_profiles_custom_async(job_id, profile_urls, request.custom_criteria))

        # Build response message
        message = f"Custom evaluation started for {len(profile_urls)} valid profiles"
        if invalid_urls:
            message += f" ({len(invalid_urls)} invalid URLs skipped)"

        return {
            "job_id": job_id,
            "status": "started",
            "message": message,
            "valid_profiles": len(profile_urls),
            "skipped_urls": len(invalid_urls)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

async def process_job_custom_async(job_id: str, post_id: str, custom_criteria: CustomCriteria):
    """Run workflow in background with custom evaluation criteria"""
    try:
        # Convert Pydantic model to dict for workflow function
        criteria_dict = custom_criteria.dict()

        # Run workflow in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            process_linkedin_post_custom_with_progress,
            post_id,
            job_id,
            criteria_dict
        )

        # Mark job as completed
        successful_count = len(results.get("leads", []))
        skipped_count = len(results.get("skipped_profiles", []))

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["results"] = results.get("leads", [])
        jobs[job_id]["skipped_profiles"] = results.get("skipped_profiles", [])
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["progress"]["message"] = f"Completed! {successful_count} successful, {skipped_count} skipped"

    except Exception as e:
        # Mark job as failed
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["progress"]["message"] = f"Error: {str(e)}"

async def process_manual_profiles_custom_async(job_id: str, profile_urls: list, custom_criteria: CustomCriteria):
    """Run manual profile workflow in background with custom evaluation criteria"""
    try:
        # Convert Pydantic model to dict for workflow function
        criteria_dict = custom_criteria.dict()

        # Run workflow in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            process_manual_profiles_custom_with_progress,
            profile_urls,
            job_id,
            criteria_dict
        )

        # Mark job as completed
        successful_count = len(results.get("leads", []))
        skipped_count = len(results.get("skipped_profiles", []))

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["results"] = results.get("leads", [])
        jobs[job_id]["skipped_profiles"] = results.get("skipped_profiles", [])
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["progress"]["message"] = f"Completed! {successful_count} successful, {skipped_count} skipped"

    except Exception as e:
        # Mark job as failed
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["progress"]["message"] = f"Error: {str(e)}"

def process_linkedin_post_custom_with_progress(post_id: str, job_id: str, custom_criteria_dict: dict) -> dict:
    """Wrapper to update job progress during custom post processing"""
    from workflow import process_linkedin_post_tracked
    return process_linkedin_post_tracked(post_id, job_id, jobs, custom_criteria_dict)

def process_manual_profiles_custom_with_progress(profile_urls: list, job_id: str, custom_criteria_dict: dict) -> dict:
    """Wrapper to update job progress during custom manual profile processing"""
    from workflow import process_manual_profiles_tracked
    return process_manual_profiles_tracked(profile_urls, job_id, jobs, custom_criteria_dict)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
