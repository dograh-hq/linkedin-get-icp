"""
LinkedIn Lead Profiling - Component Testing Suite

PURPOSE:
This test script allows you to test each automation component independently before
running the full workflow. This helps identify issues at specific steps and validates
that all API integrations are working correctly.

USAGE:
1. Ensure backend/.env is configured with all API keys
2. Replace example URLs/IDs with real LinkedIn data
3. Uncomment the tests you want to run in the main block
4. Run from backend directory: python test_components.py

TESTING STRATEGIES:
- Individual Tests: Test one component at a time (recommended for debugging)
- Sequential Tests: Run tests in order, passing data between them (realistic flow)
- Full Pipeline: Test complete end-to-end workflow with one profile

NOTE: The main workflow limits processing to 100 reactors per post for rate limiting.
This test script processes only 1 profile for faster testing.
"""
import os
from dotenv import load_dotenv
load_dotenv()

# Import workflow functions
from workflow import (
    fetch_post_reactions,
    check_profile_exists,
    fetch_profile_details,
    fetch_company_details_primary,
    fetch_company_details_backup,
    summarize_with_groq,
    evaluate_icp_fit,
    create_or_update_airtable_record
)
import json

# ===================================
# TEST 1: FETCH POST REACTIONS
# ===================================
def test_fetch_reactions():
    """
    Tests Apify post reactions scraper
    
    WHAT IT TESTS:
    - Apify API connectivity and authentication
    - LinkedIn post reactions scraping (apimaestro~linkedin-post-reactions actor)
    - Data structure returned from Apify
    
    EXPECTED OUTPUT:
    - List of reactions with reactor details (urn, name, headline, profile_url)
    - Each reaction contains nested 'reactor' object with profile information
    
    NOTE: Main workflow limits to first 100 reactors for rate limiting
    """
    print("\n" + "="*60)
    print("TEST 1: FETCH POST REACTIONS")
    print("="*60)

    # Replace with a real LinkedIn post ID or URL
    # Format: Just the ID number (e.g., "7393603376913149952")
    # Or full URL (backend extracts ID automatically)
    post_id = "7393603376913149952"  # Example post ID

    try:
        reactions = fetch_post_reactions(post_id)

        print(f"\n✓ Total reactions fetched: {len(reactions)}")

        if reactions:
            print(f"\n📋 Sample reaction structure:")
            print(json.dumps(reactions[0], indent=2)[:500] + "...")

            # Show first 3 reactors
            print(f"\n👥 First 3 reactors:")
            for i, reaction in enumerate(reactions[:3], 1):
                reactor = reaction.get('reactor', {})
                print(f"  {i}. {reactor.get('name', 'N/A')} - {reactor.get('headline', 'N/A')}")

        return reactions

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return None


# ===================================
# TEST 2: CHECK AIRTABLE
# ===================================
def test_check_airtable():
    """Tests Airtable URN existence check for deduplication"""
    print("\n" + "="*60)
    print("TEST 2: CHECK AIRTABLE")
    print("="*60)

    # Replace with a real URN from your Airtable or use a dummy one
    test_urn = "ACoAACTestURN123"

    try:
        exists = check_profile_exists(test_urn)

        print(f"\n✓ URN '{test_urn}' exists in Airtable: {exists}")

        if exists:
            print("  → This profile will be SKIPPED in the workflow")
        else:
            print("  → This profile will be PROCESSED in the workflow")

        return exists

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return None


# ===================================
# TEST 3: FETCH PROFILE DETAILS
# ===================================
def test_fetch_profile():
    """
    Tests Apify LinkedIn profile enrichment
    
    WHAT IT TESTS:
    - Profile scraping via dev_fusion~linkedin-profile-scraper actor
    - Profile data extraction (name, headline, company, experiences, education)
    - Email extraction (if publicly available)
    - Company LinkedIn URL extraction (critical for company lookup)
    
    EXPECTED OUTPUT:
    - Profile object with camelCase fields: fullName, headline, companyName, companyLinkedin
    - email field as string (not array like previous actor)
    - experiences, education, skills arrays
    
    KEY FIELDS USED IN WORKFLOW:
    - fullName: Person's full name
    - companyLinkedin: Company page URL (used for company scraping)
    - companyName: Fallback company name if company scraping fails
    - email: Contact email if available
    - headline: Job title and brief description
    """
    print("\n" + "="*60)
    print("TEST 3: FETCH PROFILE DETAILS")
    print("="*60)

    # Replace with a real LinkedIn profile URL
    # Format: https://www.linkedin.com/in/username
    profile_url = "https://www.linkedin.com/in/example"

    print(f"📍 Testing profile: {profile_url}")

    try:
        profile_data = fetch_profile_details(profile_url)

        if profile_data:
            print(f"\n✓ Profile fetched successfully!")
            print(f"  Name: {profile_data.get('fullName', 'N/A')}")
            print(f"  Headline: {profile_data.get('headline', 'N/A')}")
            print(f"  Company: {profile_data.get('companyName', 'N/A')}")
            print(f"  Company LinkedIn: {profile_data.get('companyLinkedin', 'N/A')}")
            print(f"  Location: {profile_data.get('location', 'N/A')}")
            print(f"  Email: {profile_data.get('email', 'N/A')}")

            print(f"\n📊 Available data keys: {len(profile_data.keys())} fields")
            print(f"  Keys: {', '.join(list(profile_data.keys())[:10])}...")

            print(f"\n📄 Full profile data (first 800 chars):")
            print(json.dumps(profile_data, indent=2)[:800] + "...")

        return profile_data

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return None


# ===================================
# TEST 4: FETCH COMPANY (PRIMARY)
# ===================================
def test_fetch_company_primary():
    """
    Tests primary Apify company scraper (logical_scrapers)
    
    WHAT IT TESTS:
    - Company scraping via logical_scrapers~linkedin-company-scraper actor
    - Company data extraction (name, industry, size, website, description)
    - Primary company data source (flat structure)
    
    EXPECTED OUTPUT:
    - Company object with flat structure: name, slogan, Industry, numberOfEmployees
    - website field: Company website URL (NEW: used in frontend display)
    - websiteUrl field: Alternative website field name
    - description, specialties, headquarters information
    
    KEY FIELDS USED IN WORKFLOW:
    - name: Company name (displayed in table)
    - website/websiteUrl: Company website (NEW: displayed in Company column)
    - Industry, numberOfEmployees: Used in company summary for LLM
    
    FALLBACK BEHAVIOR:
    - If this scraper fails, backup scraper (apimaestro) is attempted
    - If both fail, companyName from profile is used as fallback
    """
    print("\n" + "="*60)
    print("TEST 4: FETCH COMPANY (PRIMARY)")
    print("="*60)

    # Replace with a real company LinkedIn URL or name
    # Format: https://www.linkedin.com/company/company-name
    company_url = "https://www.linkedin.com/company/microsoft"

    print(f"📍 Testing company: {company_url}")

    try:
        company_data = fetch_company_details_primary(company_url)

        if company_data:
            print(f"\n✓ Company data fetched successfully!")
            print(f"  Name: {company_data.get('name', 'N/A')}")
            print(f"  Website: {company_data.get('website') or company_data.get('websiteUrl', 'N/A')}")
            print(f"  Slogan: {company_data.get('slogan', 'N/A')}")
            print(f"  Industry: {company_data.get('Industry', 'N/A')}")
            print(f"  Employees: {company_data.get('numberOfEmployees', 'N/A')}")

            print(f"\n📊 Available data keys: {len(company_data.keys())} fields")
            print(f"  Keys: {', '.join(list(company_data.keys())[:10])}...")

            print(f"\n📄 Full company data (first 800 chars):")
            print(json.dumps(company_data, indent=2)[:800] + "...")

        return company_data

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return None


# ===================================
# TEST 5: FETCH COMPANY (BACKUP)
# ===================================
def test_fetch_company_backup():
    """
    Tests backup Apify company scraper (apimaestro, nested structure)
    
    WHAT IT TESTS:
    - Backup company scraping via apimaestro~linkedin-company-detail actor
    - Nested company data structure (basic_info, stats, locations)
    - Alternative company data source when primary fails
    
    EXPECTED OUTPUT:
    - Company object with nested structure:
      * basic_info: {name, slogan, industries, website}
      * stats: {employee_count, follower_count}
      * locations: Array of office locations
    - website field: Located in basic_info.website (NEW: used in frontend display)
    
    KEY FIELDS USED IN WORKFLOW:
    - basic_info.name: Company name (fallback if primary scraper fails)
    - basic_info.website: Company website (NEW: extracted via company_data.get('basic_info', {}).get('website'))
    - stats.employee_count: Company size information
    
    WHEN USED:
    - Primary scraper (logical_scrapers) fails or returns empty
    - Workflow automatically tries this scraper as fallback
    - If both fail, profile.companyName is used as final fallback
    """
    print("\n" + "="*60)
    print("TEST 5: FETCH COMPANY (BACKUP)")
    print("="*60)

    # Replace with a company identifier (URL or company ID)
    # Format: https://www.linkedin.com/company/company-name or company ID
    company_id = "https://www.linkedin.com/company/microsoft"

    print(f"📍 Testing company: {company_id}")

    try:
        company_data = fetch_company_details_backup(company_id)

        if company_data:
            basic_info = company_data.get('basic_info', {})
            stats = company_data.get('stats', {})

            print(f"\n✓ Company data fetched successfully!")
            print(f"  Name: {basic_info.get('name', 'N/A')}")
            print(f"  Website: {basic_info.get('website', 'N/A')}")
            print(f"  Slogan: {basic_info.get('slogan', 'N/A')}")
            print(f"  Industries: {', '.join(basic_info.get('industries', []))}")
            print(f"  Employees: {stats.get('employee_count', 'N/A')}")

            print(f"\n📊 Data structure: basic_info, stats, locations, etc.")
            print(f"  Top-level keys: {', '.join(list(company_data.keys()))}")

            print(f"\n📄 Full company data (first 800 chars):")
            print(json.dumps(company_data, indent=2)[:800] + "...")

        return company_data

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return None


# ===================================
# TEST 6: SUMMARIZE WITH GROQ
# ===================================
def test_summarize_groq(profile_data=None, company_data=None):
    """
    Tests Groq Llama 3.3 70B summarization (raw JSON to AI)
    
    WHAT IT TESTS:
    - Groq API connectivity and authentication
    - llama-3.3-70b-versatile model for text generation
    - Profile summarization from raw JSON
    - Company summarization from raw JSON
    
    HOW IT WORKS:
    - Raw profile/company JSON is passed directly to LLM via json.dumps(data, indent=2)
    - No pre-processing or formatting - AI gets complete context
    - Two separate API calls: one for profile summary, one for company summary
    - System prompts defined in prompts.py (PROFILE_SUMMARY_SYSTEM_PROMPT, COMPANY_SUMMARY_SYSTEM_PROMPT)
    
    EXPECTED OUTPUT:
    - profile_summary: Markdown-formatted summary of person's background, experience, skills
    - company_summary: Markdown-formatted summary of company's business, industry, size
    
    MODEL PARAMETERS:
    - Temperature: 0.3 (low = more consistent, deterministic summaries)
    - Max tokens: 10000 (allows for detailed summaries)
    
    TIMING:
    - Typically takes 10-30 seconds total (5-15s per summary)
    - Depends on API load and input size
    """
    print("\n" + "="*60)
    print("TEST 6: SUMMARIZE WITH GROQ")
    print("="*60)

    # Use real data if provided, otherwise use sample data
    if not profile_data:
        profile_data = {
            "full_name": "John Doe",
            "headline": "Senior Software Engineer at Tech Co",
            "summary": "Experienced developer with 10+ years in full-stack development...",
            "location": "San Francisco, CA",
            "experiences": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Tech Co",
                    "starts_at": "2020-01",
                    "ends_at": None
                }
            ],
            "education": [
                {
                    "school": "University of California",
                    "degree_name": "BS Computer Science",
                    "field_of_study": "Computer Science"
                }
            ]
        }
        print("⚠️  Using SAMPLE profile data (pass real data for better results)")
    else:
        print("✓ Using REAL profile data from previous test")

    if not company_data:
        company_data = {
            "name": "Tech Co",
            "description": "Leading technology company specializing in cloud solutions...",
            "numberOfEmployees": 500,
            "Industry": "Technology, Information and Internet",
            "website": "https://techco.com"
        }
        print("⚠️  Using SAMPLE company data (pass real data for better results)")
    else:
        print("✓ Using REAL company data from previous test")

    try:
        print("\n🤖 Calling Groq Llama 3.3 70B for summarization...")
        print("   (This may take 10-30 seconds)")

        summaries = summarize_with_groq(profile_data, company_data)

        print(f"\n✓ Summaries generated successfully!")

        print(f"\n📝 PROFILE SUMMARY (first 500 chars):")
        print("-" * 60)
        print(summaries.get('profile_summary', 'N/A')[:500] + "...")

        print(f"\n🏢 COMPANY SUMMARY (first 500 chars):")
        print("-" * 60)
        print(summaries.get('company_summary', 'N/A')[:500] + "...")

        print(f"\n📊 Summary lengths:")
        print(f"  Profile: {len(summaries.get('profile_summary', ''))} characters")
        print(f"  Company: {len(summaries.get('company_summary', ''))} characters")

        return summaries

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return None


# ===================================
# TEST 7: EVALUATE ICP FIT
# ===================================
def test_evaluate_icp(profile_summary=None, company_summary=None):
    """
    Tests OpenAI GPT-5 mini ICP evaluation with high reasoning effort
    
    WHAT IT TESTS:
    - OpenAI API connectivity and authentication
    - gpt-5-mini model with extended reasoning capability
    - ICP (Ideal Customer Persona) matching logic
    - JSON response parsing from /v1/responses endpoint
    
    HOW IT WORKS:
    - Takes profile and company summaries (from previous step)
    - Evaluates against ICP criteria defined in prompts.py (ICP_EVALUATION_PROMPT)
    - Uses /v1/responses endpoint with reasoning: {effort: "high"}
    - Model does extended reasoning before responding (increases accuracy)
    - Returns JSON with icp_fit_strength (High/Medium/Low) and reason
    
    EXPECTED OUTPUT:
    - icp_fit_strength: "High", "Medium", or "Low"
    - reason: Detailed explanation of why profile matches/doesn't match ICP
    
    MODEL PARAMETERS:
    - Model: gpt-5-mini (faster, cheaper than GPT-4, better than GPT-3.5)
    - Reasoning effort: high (enables extended thinking for better evaluation)
    
    RESPONSE STRUCTURE:
    - OpenAI returns: output[{type:"reasoning"}, {type:"message", content:[{type:"output_text", text:"JSON"}]}]
    - Workflow extracts text from output_text type and parses as JSON
    
    TIMING:
    - Typically takes 15-45 seconds due to high reasoning effort
    - Longer than standard chat completion but more accurate
    
    CUSTOMIZATION:
    - Edit ICP_EVALUATION_PROMPT in prompts.py to change matching criteria
    - No code changes needed in workflow.py
    """
    print("\n" + "="*60)
    print("TEST 7: EVALUATE ICP FIT")
    print("="*60)

    # Use real summaries if provided, otherwise use sample summaries
    if not profile_summary:
        profile_summary = """
        Senior Software Engineer with 10 years of experience in building scalable
        cloud applications. Currently leading a team of 5 engineers at Tech Co,
        focusing on microservices architecture and DevOps practices. Strong background
        in Python, AWS, and Kubernetes. MBA from Stanford University.
        """
        print("⚠️  Using SAMPLE profile summary (pass real summary for better results)")
    else:
        print("✓ Using REAL profile summary from previous test")

    if not company_summary:
        company_summary = """
        Tech Co is a Series B startup with 500 employees, specializing in enterprise
        SaaS solutions for the healthcare industry. Founded in 2015, the company has
        raised $50M in funding and serves over 200 enterprise clients. Headquarters
        in San Francisco with offices in New York and Austin.
        """
        print("⚠️  Using SAMPLE company summary (pass real summary for better results)")
    else:
        print("✓ Using REAL company summary from previous test")

    try:
        print("\n🤖 Calling OpenAI GPT-5 mini with high reasoning effort...")
        print("   (This may take 15-45 seconds due to reasoning)")

        evaluation = evaluate_icp_fit(profile_summary, company_summary)

        print(f"\n✓ ICP Evaluation completed!")

        print(f"\n🎯 ICP FIT STRENGTH: {evaluation.get('icp_fit_strength', 'N/A')}")
        print(f"\n💡 REASON:")
        print("-" * 60)
        print(evaluation.get('reason', 'N/A'))

        # Color coding feedback
        fit = evaluation.get('icp_fit_strength', '')
        if fit == 'High':
            print("\n🟢 HIGH FIT - Strong candidate for outreach")
        elif fit == 'Medium':
            print("\n🟡 MEDIUM FIT - Consider for nurture campaign")
        elif fit == 'Low':
            print("\n🔴 LOW FIT - Deprioritize for now")

        return evaluation

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return None


# ===================================
# TEST 8: CREATE AIRTABLE RECORD
# ===================================
def test_create_airtable(use_real_data=False, lead_data=None):
    """
    Tests Airtable record creation with exact field mapping
    
    WHAT IT TESTS:
    - Airtable API connectivity and authentication
    - Record creation via direct HTTP POST request
    - Record update via direct HTTP PATCH request
    - Deduplication logic (checks URN before creating)
    - Field name mapping (code keys → Airtable column names)
    
    HOW IT WORKS:
    1. Check if record with URN exists (GET request with filterByFormula)
    2. If exists: UPDATE existing record (PATCH request)
    3. If not: CREATE new record (POST request)
    
    FIELD MAPPING (CRITICAL - CASE SENSITIVE):
    Code Key             → Airtable Column Name
    ------------------------------------------------
    urn                  → URN (capitalized)
    name                 → Name (capitalized)
    company_name         → company_name (lowercase) [NEW]
    company_website      → company_website (lowercase) [NEW]
    email                → Email Address (capitalized, space)
    title                → Title (capitalized)
    profile_url          → Profile URL (capitalized, space)
    icp_fit_strength     → icp_fit_strength (lowercase)
    reason               → Reason (capitalized)
    validation_judgement → validation_judgement (lowercase)
    validation_reason    → validation_reason (lowercase)
    profile_summary      → profile_summary (lowercase)
    company_summary      → company_summary (lowercase)
    
    AIRTABLE SCHEMA REQUIREMENTS:
    - URN: Single line text (primary key for deduplication)
    - Name: Single line text
    - company_name: Single line text [NEW: for table display]
    - company_website: URL or Single line text [NEW: for table display]
    - Email Address: Email field type
    - Title: Long text
    - Profile URL: URL field type
    - icp_fit_strength: Single select (High, Medium, Low)
    - Reason: Long text (capitalized in Airtable!)
    - validation_judgement: Single select (Correct, Incorrect, Unsure)
    - validation_reason: Long text
    - profile_summary: Long text
    - company_summary: Long text
    
    NOTE: This test is currently DISABLED in workflow.py (Airtable integration paused)
    """
    print("\n" + "="*60)
    print("TEST 8: CREATE AIRTABLE RECORD")
    print("="*60)

    # Use real lead data if provided, otherwise use test data
    if not lead_data:
        lead_data = {
            "urn": "ACoAACTestURN_" + str(os.urandom(4).hex()),  # Unique test URN
            "name": "Test User (DELETE ME)",
            "company_name": "Test Company Inc.",
            "company_website": "https://testcompany.example.com",
            "email": "test@example.com",
            "title": "Test Engineer - This is a test record",
            "profile_url": "https://linkedin.com/in/test",
            "icp_fit_strength": "High",
            "reason": "This is a TEST record created by test_components.py. Safe to delete.",
            "validation_judgement": "Correct",
            "validation_reason": "Test validation - automated test record",
            "profile_summary": "Test profile summary - created by automated test",
            "company_summary": "Test company summary - created by automated test"
        }
        print("⚠️  Using TEST data (will create test record in Airtable)")
        print("   Record will be clearly marked as test data")
    else:
        print("✓ Using REAL lead data from previous tests")

    if not use_real_data and not lead_data:
        print("\n⚠️  WARNING: This will create a TEST record in your Airtable")
        print("   The record will be marked with 'Test User (DELETE ME)'")
        response = input("\nProceed with test record creation? (y/n): ")
        if response.lower() != 'y':
            print("❌ Test cancelled by user")
            return None

    try:
        print(f"\n📤 Creating Airtable record...")
        print(f"   Name: {lead_data.get('name')}")
        print(f"   URN: {lead_data.get('urn')}")
        print(f"   ICP Fit: {lead_data.get('icp_fit_strength')}")

        record_id = create_or_update_airtable_record(lead_data)

        if record_id:
            print(f"\n✓ Record created/updated successfully!")
            print(f"   Record ID: {record_id}")
            print(f"\n🔗 Check your Airtable base to see the record")
        else:
            print(f"\n✗ Failed to create/update record")

        return record_id

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        return None


# ===================================
# TEST 9: FULL PIPELINE (END-TO-END)
# ===================================
def test_full_pipeline():
    """
    Tests complete workflow pipeline with one reactor
    
    WHAT IT TESTS:
    - Full end-to-end automation flow with all steps
    - Integration between all components
    - Data flow between steps (reactions → profile → company → summaries → ICP → Airtable)
    - Error handling at each step
    
    WORKFLOW STEPS:
    1. Fetch post reactions (gets list of reactors)
    2. Check if profile exists in Airtable (deduplication)
    3. Fetch profile details from LinkedIn
    4. Fetch company details (tries primary, then backup)
    5. Generate AI summaries with Groq
    6. Evaluate ICP fit with OpenAI
    7. Validate ICP evaluation with Groq [NEW: not included in this test yet]
    8. Create/update Airtable record
    
    TIMING:
    - Typically takes 60-120 seconds for one profile
    - Breakdown:
      * Reactions: 5-10s
      * Profile fetch: 15-30s
      * Company fetch: 15-30s
      * Summaries: 10-30s
      * ICP evaluation: 15-45s
      * Airtable: 2-5s
    
    NOTE: Main workflow limits to 100 reactors per post for rate limiting.
    This test processes only 1 profile for faster testing and debugging.
    
    BEST PRACTICE:
    - Test individual components first before running full pipeline
    - Use this test to verify end-to-end flow after making changes
    - Check Airtable to see final stored record
    """
    print("\n" + "="*60)
    print("TEST 9: FULL PIPELINE (END-TO-END)")
    print("="*60)

    post_id = "7392508631268835328"  # Replace with real post ID

    print(f"📍 Testing full pipeline with post: {post_id}")
    print("   (Will process only the FIRST reactor)")

    try:
        # Step 1: Fetch reactions
        print("\n🔄 STEP 1: Fetching reactions...")
        reactions = fetch_post_reactions(post_id)
        if not reactions:
            print("✗ No reactions found")
            return None

        # Process only the first reactor
        reaction = reactions[0]
        reactor = reaction.get('reactor', {})
        urn = reactor.get('urn')
        name = reactor.get('name')
        profile_url = reactor.get('profile_url')

        print(f"✓ Found {len(reactions)} reactors, processing: {name}")

        # Step 2: Check Airtable
        print(f"\n🔄 STEP 2: Checking if profile exists in Airtable...")
        exists = check_profile_exists(urn)
        if exists:
            print(f"⚠️  Profile already exists in Airtable - skipping")
            return None

        # Step 3: Fetch profile
        print(f"\n🔄 STEP 3: Fetching profile details...")
        profile_data = fetch_profile_details(profile_url)
        if not profile_data:
            print("✗ Failed to fetch profile")
            return None

        # Step 4: Fetch company
        print(f"\n🔄 STEP 4: Fetching company details...")
        company_linkedin = profile_data.get('company_linkedin')
        company_data = fetch_company_details_primary(company_linkedin) if company_linkedin else {}

        if not company_data:
            print("   → Trying backup company scraper...")
            company_data = fetch_company_details_backup(company_linkedin) if company_linkedin else {}

        if not company_data:
            print("   ⚠️  No company data, using placeholder")
            company_data = {"name": profile_data.get('company_name', 'Unknown')}

        # Step 5: Summarize
        print(f"\n🔄 STEP 5: Generating AI summaries...")
        summaries = summarize_with_groq(profile_data, company_data)

        # Step 6: Evaluate ICP
        print(f"\n🔄 STEP 6: Evaluating ICP fit...")
        evaluation = evaluate_icp_fit(
            summaries.get('profile_summary', ''),
            summaries.get('company_summary', '')
        )

        # Step 7: Create record
        print(f"\n🔄 STEP 7: Creating Airtable record...")
        
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
            "title": profile_data.get('headline', reactor.get('headline', '')),
            "profile_url": profile_url,
            "icp_fit_strength": evaluation.get('icp_fit_strength', 'Unknown'),
            "reason": evaluation.get('reason', 'N/A'),
            "validation_judgement": "Unsure",  # Not tested in this pipeline
            "validation_reason": "N/A",
            "profile_summary": summaries.get('profile_summary', ''),
            "company_summary": summaries.get('company_summary', '')
        }

        record_id = create_or_update_airtable_record(lead_data)

        # Summary
        print(f"\n" + "="*60)
        print("✓ FULL PIPELINE TEST COMPLETE")
        print("="*60)
        print(f"  Name: {lead_data['name']}")
        print(f"  ICP Fit: {lead_data['icp_fit_strength']}")
        print(f"  Airtable Record: {record_id}")
        print(f"\n🔗 Check your Airtable to see the full record")

        return lead_data

    except Exception as e:
        print(f"\n✗ Full pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


# ===================================
# MAIN TEST RUNNER
# ===================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("LINKEDIN WORKFLOW COMPONENT TESTS")
    print("="*60)
    print("\nSetup: Ensure .env configured, replace example URLs, uncomment tests below")

    # ==================================================
    # UNCOMMENT THE TESTS YOU WANT TO RUN
    # ==================================================

    # Test 1: Fetch post reactions
    reactions = test_fetch_reactions()

    # Test 2: Check Airtable
    # test_check_airtable()

    # Test 3: Fetch profile
    # profile = test_fetch_profile()

    # Test 4: Fetch company (primary)
    # company_primary = test_fetch_company_primary()

    # Test 5: Fetch company (backup)
    # company_backup = test_fetch_company_backup()

    # Test 6: Groq summarization
    # summaries = test_summarize_groq()
    # summaries = test_summarize_groq(profile, company_primary)

    # Test 7: OpenAI ICP evaluation
    # evaluation = test_evaluate_icp()
    # evaluation = test_evaluate_icp(summaries['profile_summary'], summaries['company_summary'])

    # Test 8: Airtable record creation
    # test_create_airtable()

    # Test 9: Full pipeline end-to-end
    # test_full_pipeline()

    # ==================================================
    # SEQUENTIAL TESTING EXAMPLE
    # ==================================================
    # Run tests with data flow between them:
    # reactions = test_fetch_reactions()
    # if reactions:
    #     profile = test_fetch_profile()
    #     company = test_fetch_company_primary()
    #     summaries = test_summarize_groq(profile, company)
    #     evaluation = test_evaluate_icp(summaries['profile_summary'], summaries['company_summary'])

    print("\n" + "="*60)
    print("ℹ️  Edit file and uncomment tests to run")
    print("="*60)
