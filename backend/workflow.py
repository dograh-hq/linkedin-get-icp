"""
LinkedIn Lead Profiling Automation Workflow
All automation steps are visible linearly in this file for easy modification.
"""
import os
import json
import requests
from dotenv import load_dotenv
from openai import OpenAI
from groq import Groq

# Load environment variables BEFORE initializing API clients
load_dotenv()

# Import prompt templates from centralized prompts.py
from prompts import (
    PROFILE_SUMMARY_SYSTEM_PROMPT,
    COMPANY_SUMMARY_SYSTEM_PROMPT,
    ICP_EVALUATION_PROMPT,
    ICP_VALIDATION_PROMPT
)

# ===================================
# CONFIGURATION
# ===================================

# API credentials from environment variables
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Leads")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Processing limit to avoid API overload and LinkedIn rate limits
MAX_REACTORS_PER_POST = 100

# Timeout configuration - Per-profile timeout in seconds
# Each profile has 180 seconds (3 minutes) to complete all processing steps
# If exceeded, profile is skipped and batch continues to next profile
PROFILE_TIMEOUT_SECONDS = 180

# Initialize API clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# TEMP DISABLED - AIRTABLE - Uncomment when subscription is sorted
# Airtable API configuration
# AIRTABLE_API_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
# AIRTABLE_HEADERS = {
#     "Authorization": f"Bearer {AIRTABLE_TOKEN}",
#     "Content-Type": "application/json"
# }

def normalize_linkedin_url(url: str) -> str:
    """Normalize LinkedIn profile URL to Apify format"""
    url = url.strip()
    if '?' in url:
        url = url.split('?')[0]
    url = url.rstrip('/')
    if not url.startswith('http'):
        url = 'https://' + url
    if url.startswith('http://'):
        url = url.replace('http://', 'https://')
    return url


# ===================================
# STEP 1: FETCH POST REACTIONS
# ===================================

def fetch_post_reactions(post_id: str) -> list:
    """Fetch all reactions from LinkedIn post via Apify"""
    url = f"https://api.apify.com/v2/acts/apimaestro~linkedin-post-reactions/run-sync-get-dataset-items?token={APIFY_TOKEN}"
    payload = {"post_url": post_id, "page_number": 1}
    response = requests.post(url, json=payload)
    response.raise_for_status()
    reactions = response.json()
    print(f"✓ Fetched {len(reactions)} reactions from post {post_id}")
    return reactions


# ===================================
# STEP 2: CHECK IF PROFILE EXISTS IN AIRTABLE
# ===================================

def check_profile_exists_DISABLED(urn: str) -> bool:
    """Check if profile exists in Airtable (DISABLED)"""
    try:
        escaped_urn = urn.replace("'", "\\'")
        params = {"filterByFormula": f"{{URN}}='{escaped_urn}'", "maxRecords": 1}
        response = requests.get(AIRTABLE_API_URL, headers=AIRTABLE_HEADERS, params=params, timeout=15)
        response.raise_for_status()
        records = response.json().get("records", [])
        return len(records) > 0
    except Exception as e:
        print(f"✗ Error checking Airtable: {e}")
        return False


# ===================================
# STEP 3: FETCH LINKEDIN PROFILE DETAILS
# ===================================

def fetch_profile_details(profile_url: str) -> dict:
    """Fetch LinkedIn profile data via Apify"""
    url = f"https://api.apify.com/v2/acts/dev_fusion~linkedin-profile-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"
    payload = {"profileUrls": [profile_url]}
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        profiles = response.json()
        if profiles and len(profiles) > 0:
            print(f"✓ Fetched profile: {profiles[0].get('fullName', 'Unknown')}")
            return profiles[0]
        else:
            print(f"✗ No profile data returned")
            return {}
    except Exception as e:
        print(f"✗ Error fetching profile: {e}")
        return {}


# ===================================
# STEP 4: FETCH COMPANY DETAILS (PRIMARY)
# ===================================

def fetch_company_details_primary(company_url: str) -> dict:
    """Fetch company details via primary Apify actor"""
    url = f"https://api.apify.com/v2/acts/logical_scrapers~linkedin-company-scraper/run-sync-get-dataset-items?token={APIFY_TOKEN}"
    payload = {"url": [company_url]}
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        companies = response.json()
        if companies and len(companies) > 0:
            print(f"✓ Fetched company: {companies[0].get('name', 'Unknown')}")
            return companies[0]
        else:
            print(f"✗ No company data (primary)")
            return {}
    except Exception as e:
        print(f"✗ Error fetching company (primary): {e}")
        return {}


# ===================================
# STEP 5: FETCH COMPANY DETAILS (BACKUP)
# ===================================

def fetch_company_details_backup(company_identifier: str) -> dict:
    """Fetch company details via backup Apify actor"""
    url = f"https://api.apify.com/v2/acts/apimaestro~linkedin-company-detail/run-sync-get-dataset-items?token={APIFY_TOKEN}"
    payload = {"identifier": [company_identifier]}
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        companies = response.json()
        if companies and len(companies) > 0:
            print(f"✓ Fetched company (backup): {companies[0].get('basic_info', {}).get('name', 'Unknown')}")
            return companies[0]
        else:
            print(f"✗ No company data (backup)")
            return {}
    except Exception as e:
        print(f"✗ Error fetching company (backup): {e}")
        return {}


# ===================================
# STEP 6: SUMMARIZE WITH GROQ LLAMA
# ===================================

def summarize_with_groq(profile_data: dict, company_data: dict) -> dict:
    """Generate AI summaries using Groq Llama"""
    try:
        profile_summary_response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": PROFILE_SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(profile_data, indent=2)}
            ],
            temperature=0.3,
            max_tokens=10000
        )
        company_summary_response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": COMPANY_SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(company_data, indent=2)}
            ],
            temperature=0.3,
            max_tokens=10000
        )
        print(f"✓ Generated summaries")
        return {
            "profile_summary": profile_summary_response.choices[0].message.content,
            "company_summary": company_summary_response.choices[0].message.content
        }
    except Exception as e:
        print(f"✗ Error generating summaries: {e}")
        return {
            "profile_summary": "Summary generation failed",
            "company_summary": "Summary generation failed"
        }


# ===================================
# STEP 7: EVALUATE ICP FIT WITH OPENAI
# ===================================

def evaluate_icp_fit(profile_summary: str, company_summary: str) -> dict:
    """Evaluates ICP fit using OpenAI GPT-5 mini with high reasoning effort"""
    try:
        prompt = ICP_EVALUATION_PROMPT.format(
            profile_summary=profile_summary,
            company_summary=company_summary
        )

        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-5-mini",
                "input": prompt,
                "reasoning": {"effort": "high"}
            }
        )
        response.raise_for_status()

        # Extract JSON from nested OpenAI response structure
        # Response format: output[{type:"reasoning"}, {type:"message", content:[{type:"output_text", text:"..."}]}]
        output_items = response.json().get("output", [])
        text_content = ""

        for item in output_items:
            if item.get("type") == "message":
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        text_content = content.get("text", "")
                        break
                if text_content:
                    break

        if text_content:
            icp_evaluation = json.loads(text_content)
            print(f"✓ ICP Evaluation: {icp_evaluation.get('icp_fit_strength', 'N/A')}")
            return icp_evaluation
        else:
            print(f"✗ No response text found from OpenAI")
            return {"icp_fit_strength": "Unknown", "reason": "No response from OpenAI"}

    except Exception as e:
        print(f"✗ Error evaluating ICP fit: {e}")
        return {"icp_fit_strength": "Unknown", "reason": "Evaluation failed"}


# ===================================
# STEP 7b: VALIDATE ICP EVALUATION
# ===================================

def extract_json_from_text(text: str) -> dict:
    """Extract JSON from LLM responses with multiple fallback strategies"""
    import re
    
    # Strategy 1: Direct JSON parse
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from markdown code blocks
    markdown_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    match = re.search(markdown_pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: Find JSON object with regex
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    matches = re.finditer(json_pattern, text, re.DOTALL)
    for match in matches:
        try:
            parsed = json.loads(match.group(0))
            if 'validation_judgement' in parsed or 'validation_reason' in parsed:
                return parsed
        except json.JSONDecodeError:
            continue

    # Strategy 4: Line-by-line parsing
    lines = text.split('\n')
    json_lines = []
    in_json = False
    for line in lines:
        if '{' in line:
            in_json = True
        if in_json:
            json_lines.append(line)
        if '}' in line and in_json:
            try:
                return json.loads('\n'.join(json_lines))
            except json.JSONDecodeError:
                json_lines = []
                in_json = False

    # Strategy 5: Regex field extraction
    judgement_pattern = r'(?:validation_judgement|judgement)[\"\']?\s*:\s*["\']?(Correct|Incorrect|Unsure)["\']?'
    reason_pattern = r'(?:validation_reason|reason)[\"\']?\s*:\s*["\']([^"\']+)["\']'
    judgement_match = re.search(judgement_pattern, text, re.IGNORECASE)
    reason_match = re.search(reason_pattern, text, re.DOTALL)
    if judgement_match or reason_match:
        return {
            "validation_judgement": judgement_match.group(1) if judgement_match else "Unsure",
            "validation_reason": reason_match.group(1).strip() if reason_match else "Could not extract reason"
        }

    print(f"✗ JSON extraction failed from validation response")
    return None


def validate_icp_evaluation(profile_summary: str, company_summary: str, icp_evaluation: dict) -> dict:
    """Validate ICP evaluation using openai/gpt-oss-20b via Groq"""
    try:
        icp_fit_strength = icp_evaluation.get('icp_fit_strength', 'Unknown')
        icp_reason = icp_evaluation.get('reason', 'No reason provided')
        
        prompt = ICP_VALIDATION_PROMPT.format(
            profile_summary=profile_summary,
            company_summary=company_summary,
            icp_fit_strength=icp_fit_strength,
            icp_reason=icp_reason
        )
        
        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You are a senior quality control analyst reviewing an ICP (Ideal Customer Persona) assessment. Respond ONLY with valid JSON, no other text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=15000
        )
        
        result_text = response.choices[0].message.content
        validation_result = extract_json_from_text(result_text)
        
        if validation_result is None:
            print(f"✗ Failed to parse validation response")
            return {
                "validation_judgement": "Unsure",
                "validation_reason": "Failed to parse validation response"
            }
        
        judgement = validation_result.get('validation_judgement', 'Unsure')
        reason = validation_result.get('validation_reason', 'Unable to validate')
        print(f"✓ Validation: {judgement}")
        
        return {
            "validation_judgement": judgement,
            "validation_reason": reason
        }
    
    except Exception as e:
        print(f"✗ Error in validation: {e}")
        return {
            "validation_judgement": "Unsure",
            "validation_reason": f"Validation error: {str(e)}"
        }


# ===================================
# TIMEOUT WRAPPER FOR PROFILE PROCESSING
# ===================================

def process_single_profile_with_timeout(reactor, idx, total_count, job_id=None):
    """
    Process profile with 180s timeout. Returns (success, lead_data, skip_info).
    """
    import concurrent.futures
    import time

    reactor_data = reactor.get('reactor', {})
    urn = reactor_data.get('urn')
    name = reactor_data.get('name', 'Unknown')
    profile_url = reactor_data.get('profile_url')

    print(f"\n--- Processing Reactor {idx}/{total_count}: {name} ---")
    start_time = time.time()

    def process_profile_internal():
        """Internal function that does the actual processing"""
        try:
            # STEP 2b: Fetch LinkedIn profile details
            print("STEP 2b: Fetching profile details...")
            profile_data = fetch_profile_details(profile_url)

            if not profile_data:
                return None, f"Could not fetch profile data"

            # STEP 2c: Fetch company details
            print("STEP 2c: Fetching company details...")
            company_data = {}

            # Try primary company scraper first
            company_linkedin = profile_data.get('companyLinkedin')
            if company_linkedin:
                company_data = fetch_company_details_primary(company_linkedin)

            # If primary failed, try backup with company URN
            if not company_data or len(company_data) == 0:
                print("→ Primary company scraper failed, trying backup...")
                if company_linkedin:
                    company_data = fetch_company_details_backup(company_linkedin)

            if not company_data:
                print(f"⚠ Warning: No company data available")
                company_data = {"name": profile_data.get('companyName', 'Unknown')}

            # STEP 2d: Summarize with Groq
            print("STEP 2d: Generating summaries with Groq...")
            summaries = summarize_with_groq(profile_data, company_data)

            # STEP 2e: Evaluate ICP fit with OpenAI
            print("STEP 2e: Evaluating ICP fit with OpenAI...")
            icp_evaluation = evaluate_icp_fit(
                summaries.get('profile_summary', ''),
                summaries.get('company_summary', '')
            )

            # STEP 2e-validation: Validate ICP evaluation
            print("STEP 2e-validation: Validating ICP evaluation...")
            validation_result = validate_icp_evaluation(
                summaries.get('profile_summary', ''),
                summaries.get('company_summary', ''),
                icp_evaluation
            )

            # Build lead data
            # Extract company website from various possible fields
            company_website = (
                company_data.get('website') or 
                company_data.get('websiteUrl') or 
                company_data.get('basic_info', {}).get('website') or 
                ''
            )
            
            lead_data = {
                "urn": urn,
                "name": profile_data.get('fullName', name),
                "company_name": profile_data.get('companyName') or company_data.get('name', 'Unknown'),
                "company_website": company_website,
                "email": profile_data.get('email', ''),
                "title": profile_data.get('headline', ''),
                "profile_url": profile_url,
                "icp_fit_strength": icp_evaluation.get('icp_fit_strength', 'Unknown'),
                "reason": icp_evaluation.get('reason', 'N/A'),
                "validation_judgement": validation_result.get('validation_judgement', 'Unsure'),
                "validation_reason": validation_result.get('validation_reason', 'N/A'),
                "profile_summary": summaries.get('profile_summary', ''),
                "company_summary": summaries.get('company_summary', '')
            }

            return lead_data, None

        except Exception as e:
            error_msg = f"Error during processing: {str(e)}"
            print(f"✗ {error_msg}")
            return None, error_msg

    # Execute with timeout using ThreadPoolExecutor
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(process_profile_internal)
            try:
                # Wait for result with timeout
                lead_data, error_msg = future.result(timeout=PROFILE_TIMEOUT_SECONDS)

                elapsed_time = time.time() - start_time

                if lead_data:
                    print(f"✓ Successfully processed {name} in {elapsed_time:.1f}s (not saved to Airtable)\n")
                    return True, lead_data, None
                else:
                    # Processing failed for some reason (API error, etc.)
                    print(f"⊘ Skipped {name}: {error_msg}\n")
                    skip_info = {
                        "urn": urn,
                        "name": name,
                        "reason": error_msg,
                        "profile_url": profile_url
                    }
                    return False, None, skip_info

            except concurrent.futures.TimeoutError:
                future.cancel()
                elapsed_time = time.time() - start_time
                timeout_msg = f"Processing exceeded {PROFILE_TIMEOUT_SECONDS}s timeout (actual: {elapsed_time:.1f}s)"
                print(f"⏱ TIMEOUT: {name} - {timeout_msg}\n")
                skip_info = {"urn": urn, "name": name, "reason": timeout_msg, "profile_url": profile_url}
                return False, None, skip_info

    except Exception as e:
        error_msg = f"Unexpected error in timeout wrapper: {str(e)}"
        print(f"✗ {error_msg}\n")
        skip_info = {"urn": urn, "name": name, "reason": error_msg, "profile_url": profile_url}
        return False, None, skip_info


# ===================================
# STEP 8: CREATE/UPDATE AIRTABLE RECORD
# ===================================

# TEMP DISABLED - AIRTABLE - Uncomment when subscription is sorted
def create_or_update_airtable_record_DISABLED(lead_data: dict) -> str:
    """Create or update Airtable record (DISABLED)"""
    try:
        urn = lead_data.get('urn')
        name = lead_data.get('name')
        escaped_urn = urn.replace("'", "\\'")
        
        record_fields = {
            "URN": lead_data.get("urn"),
            "Name": lead_data.get("name"),
            "company_name": lead_data.get("company_name"),
            "Email Address": lead_data.get("email", ""),
            "Title": lead_data.get("title"),
            "Profile URL": lead_data.get("profile_url"),
            "icp_fit_strength": lead_data.get("icp_fit_strength"),
            "Reason": lead_data.get("reason"),
            "validation_judgement": lead_data.get("validation_judgement"),
            "validation_reason": lead_data.get("validation_reason"),
            "profile_summary": lead_data.get("profile_summary"),
            "company_summary": lead_data.get("company_summary")
        }

        # STEP 1: Check if record exists
        print(f"  → STEP 6a: Checking if record exists in Airtable...")
        params = {
            "filterByFormula": f"{{URN}}='{escaped_urn}'",
            "maxRecords": 1
        }
        print(f"  → Request URL: {AIRTABLE_API_URL}")
        print(f"  → Request params: {params}")

        import time
        start_time = time.time()
        print(f"  → Making GET request... (started at {time.strftime('%H:%M:%S')})")

        response = requests.get(
            AIRTABLE_API_URL,
            headers=AIRTABLE_HEADERS,
            params=params,
            timeout=15
        )

        elapsed = time.time() - start_time
        print(f"  → GET request completed in {elapsed:.2f}s")
        print(f"  → Response status: {response.status_code}")
        response.raise_for_status()

        data = response.json()
        existing_records = data.get("records", [])
        print(f"  → Found {len(existing_records)} existing record(s)")

        if existing_records:
            # STEP 2: Update existing record
            record_id = existing_records[0]['id']
            print(f"  → STEP 6b: Updating existing record (ID: {record_id})...")
            update_url = f"{AIRTABLE_API_URL}/{record_id}"

            update_payload = {
                "fields": record_fields
            }

            start_time = time.time()
            print(f"  → Making PATCH request... (started at {time.strftime('%H:%M:%S')})")

            response = requests.patch(
                update_url,
                headers=AIRTABLE_HEADERS,
                json=update_payload,
                timeout=30
            )

            elapsed = time.time() - start_time
            print(f"  → PATCH request completed in {elapsed:.2f}s")
            print(f"  → Response status: {response.status_code}")
            response.raise_for_status()

            print(f"✓ Updated Airtable record for {name}")
            return record_id

        else:
            # STEP 3: Create new record
            print(f"  → STEP 6c: Creating new record...")
            create_payload = {
                "fields": record_fields
            }

            start_time = time.time()
            print(f"  → Making POST request... (started at {time.strftime('%H:%M:%S')})")

            response = requests.post(
                AIRTABLE_API_URL,
                headers=AIRTABLE_HEADERS,
                json=create_payload,
                timeout=30
            )

            elapsed = time.time() - start_time
            print(f"  → POST request completed in {elapsed:.2f}s")
            print(f"  → Response status: {response.status_code}")
            response.raise_for_status()

            new_record = response.json()
            record_id = new_record.get('id')
            print(f"  → New record ID: {record_id}")
            print(f"✓ Created Airtable record for {name}")
            return record_id

    except requests.exceptions.Timeout:
        print(f"✗ Timeout creating/updating Airtable record (30s exceeded)")
        print(f"  → Operation was taking too long and was cancelled")
        return None
    except requests.exceptions.RequestException as e:
        print(f"✗ Error creating/updating Airtable record: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  → Response status: {e.response.status_code}")
            try:
                error_detail = e.response.json()
                print(f"  → Airtable API error: {error_detail}")
            except:
                print(f"  → Response text: {e.response.text[:500]}")
        return None
    except Exception as e:
        print(f"✗ Unexpected error creating/updating Airtable record: {e}")
        import traceback
        print(f"  → Traceback: {traceback.format_exc()}")
        return None


# ===================================
# MAIN WORKFLOW ORCHESTRATOR
# ===================================

def process_linkedin_post(post_id: str) -> dict:
    """Process LinkedIn post reactors through enrichment pipeline (max 100 profiles)"""
    print(f"\n{'='*60}")
    print(f"STARTING LINKEDIN POST PROCESSING - Post ID: {post_id}")
    print(f"{'='*60}\n")
    
    print("STEP 1: Fetching post reactions...")
    reactions = fetch_post_reactions(post_id)
    total_reactors = len(reactions)

    if total_reactors > MAX_REACTORS_PER_POST:
        print(f"⚠️  Found {total_reactors} reactors. Limiting to first {MAX_REACTORS_PER_POST}")
        reactions = reactions[:MAX_REACTORS_PER_POST]
        reactors_to_process = MAX_REACTORS_PER_POST
    else:
        reactors_to_process = total_reactors

    print(f"Processing {reactors_to_process} reactors\n")
    processed_leads = []

    for idx, reaction in enumerate(reactions, 1):
        reactor = reaction.get('reactor', {})
        urn = reactor.get('urn')
        name = reactor.get('name')
        profile_url = reactor.get('profile_url')

        print(f"\n--- Processing Reactor {idx}/{reactors_to_process}: {name} ---")
        print("⊘ STEP 2a: Airtable check DISABLED")
        
        print("STEP 2b: Fetching profile details...")
        profile_data = fetch_profile_details(profile_url)
        if not profile_data:
            print(f"⊘ Could not fetch profile data. Skipping.\n")
            continue
        
        print("STEP 2c: Fetching company details...")
        company_data = {}
        company_linkedin = profile_data.get('companyLinkedin')
        if company_linkedin:
            company_data = fetch_company_details_primary(company_linkedin)

        if not company_data or len(company_data) == 0:
            print("→ Trying backup company scraper...")
            if company_linkedin:
                company_data = fetch_company_details_backup(company_linkedin)

        if not company_data:
            print(f"⚠ No company data available")
            company_data = {"name": profile_data.get('companyName', 'Unknown')}
        
        print("STEP 2d: Generating summaries...")
        summaries = summarize_with_groq(profile_data, company_data)
        
        print("STEP 2e: Evaluating ICP fit...")
        icp_evaluation = evaluate_icp_fit(
            summaries.get('profile_summary', ''),
            summaries.get('company_summary', '')
        )

        # STEP 2e-validation: Validate ICP evaluation
        print("STEP 2e-validation: Validating ICP evaluation...")
        validation_result = validate_icp_evaluation(
            summaries.get('profile_summary', ''),
            summaries.get('company_summary', ''),
            icp_evaluation
        )

        # TEMP DISABLED - AIRTABLE - Uncomment when subscription is sorted
        # STEP 2f: Create Airtable record
        # print("STEP 2f: Creating Airtable record...")
        print("⊘ STEP 2f: Airtable save DISABLED (temporary)")

        lead_data = {
            "urn": urn,
            "name": profile_data.get('fullName', name),
            "email": profile_data.get('email', ''),
            "title": profile_data.get('headline', ''),
            "profile_url": profile_url,
            "icp_fit_strength": icp_evaluation.get('icp_fit_strength', 'Unknown'),
            "reason": icp_evaluation.get('reason', 'N/A'),
            "validation_judgement": validation_result.get('validation_judgement', 'Unsure'),
            "validation_reason": validation_result.get('validation_reason', 'N/A'),
            "profile_summary": summaries.get('profile_summary', ''),
            "company_summary": summaries.get('company_summary', '')
        }

        # record_id = create_or_update_airtable_record(lead_data)
        #
        # if record_id:
        #     processed_leads.append(lead_data)
        #     print(f"✓ Successfully processed {name}\n")
        # else:
        #     print(f"✗ Failed to save to Airtable\n")

        # Always add to results (no Airtable save)
        processed_leads.append(lead_data)
        print(f"✓ Successfully processed {name} (not saved to Airtable)\n")
    
    # STEP 3: Return results
    print(f"\n{'='*60}")
    print(f"PROCESSING COMPLETE")
    print(f"Total Reactors: {total_reactors}")
    print(f"New Leads Processed: {len(processed_leads)}")
    print(f"{'='*60}\n")
    
    return {
        "leads": processed_leads,
        "total_reactors": total_reactors,
        "new_leads": len(processed_leads)
    }


# ===================================
# TRACKED WORKFLOW (WITH PROGRESS UPDATES)
# ===================================

def process_linkedin_post_tracked(post_id: str, job_id: str, jobs: dict) -> dict:
    """
    Same as process_linkedin_post() but updates job progress for async processing.
    Used by FastAPI background jobs to track real-time progress.
    """
    print(f"\n{'='*60}")
    print(f"STARTING LINKEDIN POST PROCESSING (Job ID: {job_id})")
    print(f"Post ID: {post_id}")
    print(f"{'='*60}\n")

    try:
        # STEP 1: Fetch all reactions
        print("STEP 1: Fetching post reactions...")
        jobs[job_id]["progress"]["message"] = "Fetching post reactions..."
        reactions = fetch_post_reactions(post_id)
        total_reactors = len(reactions)

        # Limit to first 100 reactors
        if total_reactors > MAX_REACTORS_PER_POST:
            print(f"⚠️  Found {total_reactors} reactors. Limiting to first {MAX_REACTORS_PER_POST} to avoid service overload.")
            reactions = reactions[:MAX_REACTORS_PER_POST]
            reactors_to_process = MAX_REACTORS_PER_POST
        else:
            reactors_to_process = total_reactors

        # Update total count
        jobs[job_id]["progress"]["total"] = reactors_to_process
        jobs[job_id]["progress"]["message"] = f"Found {total_reactors} reactors, processing {reactors_to_process}"
        print(f"Processing {reactors_to_process} reactors\n")

        processed_leads = []
        skipped_profiles = []

        # STEP 2: Loop through each reactor with timeout wrapper
        for idx, reaction in enumerate(reactions, 1):
            reactor_name = reaction.get('reactor', {}).get('name', 'Unknown')

            # Update progress
            successful_count = len(processed_leads)
            skipped_count = len(skipped_profiles)
            jobs[job_id]["progress"]["current"] = idx
            jobs[job_id]["progress"]["message"] = f"Processing {idx}/{reactors_to_process}: {reactor_name} ({successful_count} successful, {skipped_count} skipped)"

            # Process profile with 180-second timeout
            success, lead_data, skip_info = process_single_profile_with_timeout(
                reaction, idx, reactors_to_process, job_id
            )

            if success:
                # Successfully processed - add to results
                processed_leads.append(lead_data)
                # Add to partial results for real-time display
                jobs[job_id]["partial_results"].append(lead_data)
            else:
                # Skipped due to timeout or error - track skip info
                skipped_profiles.append(skip_info)
                # Also update job dict with skipped profiles for API response
                if "skipped_profiles" not in jobs[job_id]:
                    jobs[job_id]["skipped_profiles"] = []
                jobs[job_id]["skipped_profiles"].append(skip_info)

        # STEP 3: Return results
        print(f"\n{'='*60}")
        print(f"PROCESSING COMPLETE")
        print(f"Total Reactors: {total_reactors}")
        print(f"Successfully Processed: {len(processed_leads)}")
        print(f"Skipped (timeout/errors): {len(skipped_profiles)}")
        print(f"{'='*60}\n")

        return {
            "leads": processed_leads,
            "skipped_profiles": skipped_profiles,
            "total_reactors": total_reactors,
            "new_leads": len(processed_leads),
            "skipped_count": len(skipped_profiles)
        }

    except Exception as e:
        print(f"\n✗ Error in tracked workflow: {e}")
        raise


# ===================================
# MANUAL PROFILES WORKFLOW (WITH PROGRESS TRACKING)
# ===================================

def process_manual_profiles_tracked(profile_urls: list, job_id: str, jobs: dict) -> dict:
    """
    Process manually provided LinkedIn profile URLs with progress tracking.
    Similar to process_linkedin_post_tracked() but skips fetching reactions.
    """
    print(f"\n{'='*60}")
    print(f"STARTING MANUAL PROFILE PROCESSING (Job ID: {job_id})")
    print(f"Profile Count: {len(profile_urls)}")
    print(f"{'='*60}\n")

    try:
        # Normalize and validate profile URLs (remove query params, add https://, etc.)
        profile_urls = [normalize_linkedin_url(url) for url in profile_urls if url.strip()]
        total_profiles = len(profile_urls)

        if total_profiles > MAX_REACTORS_PER_POST:
            print(f"⚠️  Found {total_profiles} profiles. Limiting to first {MAX_REACTORS_PER_POST} to avoid service overload.")
            profile_urls = profile_urls[:MAX_REACTORS_PER_POST]
            profiles_to_process = MAX_REACTORS_PER_POST
        else:
            profiles_to_process = total_profiles

        # Update job progress
        jobs[job_id]["progress"]["total"] = profiles_to_process
        jobs[job_id]["progress"]["message"] = f"Processing {profiles_to_process} profiles"
        print(f"Processing {profiles_to_process} profiles\n")

        processed_leads = []
        skipped_profiles = []

        # Loop through each profile URL with timeout wrapper
        for idx, profile_url in enumerate(profile_urls, 1):
            # Extract profile ID from URL to use as URN (e.g., "priteshkr" from "linkedin.com/in/priteshkr/")
            url_parts = profile_url.rstrip('/').split('/')

            # Validate URL structure: must have at least .../in/username
            if len(url_parts) < 5 or url_parts[-2] != 'in' or not url_parts[-1]:
                print(f"\n⚠️ Skipping invalid URL (no profile ID): {profile_url}")
                skip_info = {
                    "urn": "unknown",
                    "name": "Unknown",
                    "reason": "Invalid URL format (no profile ID)",
                    "profile_url": profile_url
                }
                skipped_profiles.append(skip_info)
                if "skipped_profiles" not in jobs[job_id]:
                    jobs[job_id]["skipped_profiles"] = []
                jobs[job_id]["skipped_profiles"].append(skip_info)
                continue

            profile_id = url_parts[-1]

            # Additional validation: profile ID should not be reserved words
            if profile_id in ['in', 'company', 'school', 'www.linkedin.com', 'linkedin.com']:
                print(f"\n⚠️ Skipping invalid URL (reserved word as profile ID): {profile_url}")
                skip_info = {
                    "urn": profile_id,
                    "name": profile_id,
                    "reason": "Invalid URL (reserved word as profile ID)",
                    "profile_url": profile_url
                }
                skipped_profiles.append(skip_info)
                if "skipped_profiles" not in jobs[job_id]:
                    jobs[job_id]["skipped_profiles"] = []
                jobs[job_id]["skipped_profiles"].append(skip_info)
                continue

            # Validate profile ID is at least 3 characters
            if len(profile_id) < 3:
                print(f"\n⚠️ Skipping invalid URL (profile ID too short): {profile_url}")
                skip_info = {
                    "urn": profile_id,
                    "name": profile_id,
                    "reason": "Invalid URL (profile ID too short)",
                    "profile_url": profile_url
                }
                skipped_profiles.append(skip_info)
                if "skipped_profiles" not in jobs[job_id]:
                    jobs[job_id]["skipped_profiles"] = []
                jobs[job_id]["skipped_profiles"].append(skip_info)
                continue

            # Use profile ID as URN for manual input
            urn = profile_id

            # Update progress
            successful_count = len(processed_leads)
            skipped_count = len(skipped_profiles)
            jobs[job_id]["progress"]["current"] = idx
            jobs[job_id]["progress"]["message"] = f"Processing {idx}/{profiles_to_process}: {profile_id} ({successful_count} successful, {skipped_count} skipped)"

            # Construct fake reaction object to match expected structure for timeout wrapper
            fake_reaction = {
                "reactor": {
                    "urn": urn,
                    "name": profile_id,
                    "profile_url": profile_url
                }
            }

            # Process profile with 180-second timeout
            success, lead_data, skip_info = process_single_profile_with_timeout(
                fake_reaction, idx, profiles_to_process, job_id
            )

            if success:
                # Successfully processed - add to results
                processed_leads.append(lead_data)
                # Add to partial results for real-time display
                jobs[job_id]["partial_results"].append(lead_data)
            else:
                # Skipped due to timeout or error - track skip info
                skipped_profiles.append(skip_info)
                # Also update job dict with skipped profiles for API response
                if "skipped_profiles" not in jobs[job_id]:
                    jobs[job_id]["skipped_profiles"] = []
                jobs[job_id]["skipped_profiles"].append(skip_info)

        # Return results
        print(f"\n{'='*60}")
        print(f"PROCESSING COMPLETE")
        print(f"Total Profiles: {total_profiles}")
        print(f"Successfully Processed: {len(processed_leads)}")
        print(f"Skipped (timeout/errors): {len(skipped_profiles)}")
        print(f"{'='*60}\n")

        return {
            "leads": processed_leads,
            "skipped_profiles": skipped_profiles,
            "total_profiles": total_profiles,
            "new_leads": len(processed_leads),
            "skipped_count": len(skipped_profiles)
        }

    except Exception as e:
        print(f"\n✗ Error in manual profile workflow: {e}")
        raise
