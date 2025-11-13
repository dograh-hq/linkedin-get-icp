<system_context>
FastAPI backend that orchestrates LinkedIn lead profiling workflow. Exposes single endpoint that processes post reactions through linear automation pipeline.
</system_context>

<file_map>
## FILE MAP
- `main.py` - FastAPI server with /api/process-post endpoint
- `workflow.py` - Complete automation workflow (all steps visible linearly)
- `prompts.py` - Centralized LLM prompt templates
- `test_components.py` - Individual component testing script
- `requirements.txt` - Python dependencies
- `.env.example` - Template for environment variables
</file_map>

<paved_path>
## ARCHITECTURE (PAVED PATH)

**Entry Point:**
`main.py` → FastAPI app → `/api/process-post` endpoint → `workflow.process_linkedin_post()`

**Workflow Execution (in workflow.py):**
```
1. fetch_post_reactions() - Get reactors from LinkedIn post (limited to first 100)
2. Loop through each reactor:
   a. check_profile_exists() - Skip if already in Airtable
   b. fetch_profile_details() - Get LinkedIn profile data
   c. fetch_company_details_primary() - Get company info
   d. fetch_company_details_backup() - Fallback if primary fails
   e. summarize_with_groq() - AI summarization
   f. evaluate_icp_fit() - OpenAI ICP matching
   g. validate_icp_evaluation() - Quality check on ICP evaluation (Groq openai/gpt-oss-20b)
   h. create_or_update_airtable_record() - Store results
3. Return aggregated results

Note: Limited to 100 reactors per post to avoid API overload and LinkedIn rate limits
```

**API Integrations:**
- Apify: 4 different actors for LinkedIn scraping
- Airtable: pyairtable SDK for lead storage
- Groq: llama-3.3-70b-versatile for summarization
- OpenAI: gpt-5-mini via /v1/responses endpoint with high reasoning effort for ICP evaluation
</paved_path>

<critical_notes>
## CRITICAL NOTES

- **Single workflow file**: All automation logic in `workflow.py` for easy modification
- **Centralized prompts**: All LLM prompts in `prompts.py` for easy customization
- **Raw JSON to LLM**: Profile and company summaries use raw Apify JSON as input (not formatted text)
- **Sequential summarization**: Profile → Company → ICP evaluation (uses summaries from previous steps)
- **Environment variables required**:
  - `APIFY_TOKEN` - Already provided in .env.example
  - `AIRTABLE_TOKEN` - User must add
  - `AIRTABLE_BASE_ID` - User must add
  - `AIRTABLE_TABLE_NAME` - Defaults to "Leads"
  - `OPENAI_API_KEY` - User must add
  - `GROQ_API_KEY` - Already provided in .env.example
  - `PORTAL_PASSWORD` - Portal authentication password (example provided in .env.example, MUST CHANGE for production)

- **Apify actors used**:
  1. `apimaestro~linkedin-post-reactions` - Get reactions
  2. `dev_fusion~linkedin-profile-scraper` - Profile details (more reliable than previous actor)
  3. `logical_scrapers~linkedin-company-scraper` - Company (primary)
  4. `apimaestro~linkedin-company-detail` - Company (backup)

- **Profile data field mapping**:
  - New actor uses camelCase: `fullName`, `companyLinkedin`, `companyName`, `email` (string, not array)
  - `companyLinkedin` is the critical field linking profiles to company lookup
  - Raw JSON still passed to LLMs for better context - no pre-processing needed

- **Airtable field mapping** (CRITICAL - case-sensitive):
  - Code uses lowercase keys: urn, name, company_name, company_website, email, title, profile_url, reason, icp_fit_strength, validation_judgement, validation_reason, profile_summary, company_summary
  - Maps to Airtable columns: URN, Name, company_name, company_website, Email Address, Title, Profile URL, Reason, icp_fit_strength, validation_judgement, validation_reason, profile_summary, company_summary
  - Mapping done in `create_or_update_airtable_record()` function
  - **Field names must match EXACTLY in Airtable (capitalization matters)**
  - **company_website** extracted from: company_data.get('website') or company_data.get('websiteUrl') or company_data.get('basic_info', {}).get('website')

- **OpenAI response parsing**:
  - Uses `/v1/responses` endpoint (not `/v1/chat/completions`)
  - Response has `output` array with nested structure: `[{type: "reasoning"}, {type: "message", content: [{type: "output_text", text: "..."}]}]`
  - Code extracts item with `type: "message"`, then finds `type: "output_text"` in nested `content` array
  - JSON is in the `text` field of the output_text item
  - High reasoning effort enabled for better ICP evaluation

- **ICP customization**: Edit `ICP_EVALUATION_PROMPT` in `prompts.py` (not workflow.py)
- **ICP validation**: Second LLM validates first evaluation using `ICP_VALIDATION_PROMPT` in `prompts.py` - uses Groq openai/gpt-oss-20b model for quality control
- **No helper functions**: Removed all formatting functions - raw JSON passes directly to AI models via `json.dumps(data, indent=2)`
- **Error handling**: Each step logs success/failure, continues on errors
- **Deduplication**: URN-based checking prevents re-processing same profiles (uses `{URN}` in Airtable formula)
- **Environment loading**: `load_dotenv()` called at top of workflow.py before initializing API clients
- **Reactor limit**: Processing limited to first 100 reactors per post (`MAX_REACTORS_PER_POST = 100`) to prevent API overload and avoid LinkedIn rate limits

- **Per-Profile Timeout**:
  - Each profile has 180-second (3-minute) timeout for ALL processing steps combined
  - Configured via `PROFILE_TIMEOUT_SECONDS = 180` constant in workflow.py
  - If timeout exceeded, profile is skipped and added to `skipped_profiles` list
  - Batch processing continues immediately to next profile (no blocking)
  - Timeout enforced via `concurrent.futures.ThreadPoolExecutor` with timeout parameter
  - Skipped profiles tracked with: urn, name, reason (timeout/error message), profile_url
  - Both successful leads and skipped profiles returned to frontend for display
  - No individual API timeouts - simpler implementation with per-profile wrapper only

- **Code Optimization (2025-01-13)**:
  - Reduced verbose debug comments throughout workflow.py while maintaining essential debugging
  - `extract_json_from_text()` reduced from 102 to 36 lines (65% reduction)
  - `validate_icp_evaluation()` reduced from 121 to 38 lines (69% reduction)
  - Removed excessive logging, validation_debug.log file writing, and strategy-by-strategy prints
  - Kept: Step tracking (STEP 1:, STEP 2b:), success/failure indicators (✓/✗/⊘/⚠), progress counters
  - Result: Cleaner code, faster execution, easier maintenance

**Gotchas:**
- Must run on localhost:8000 for Next.js proxy to work
- Missing API keys cause silent failures at that step
- **Airtable schema must match expected fields EXACTLY (case-sensitive)**
- **AIRTABLE_TABLE_NAME** can be table name (e.g. "Leads") or table ID (e.g. "tbl...")
- Company fallback triggers only if primary returns empty
- OpenAI response structure differs from standard chat completion format
</critical_notes>

<example>
## EXAMPLE REQUEST/RESPONSE

**Request to /api/process-post:**
```json
{
  "post_url": "7392508631268835328"
}
```

**Response:**
```json
{
  "status": "completed",
  "leads": [
    {
      "urn": "ACoAAC...",
      "name": "John Doe",
      "email": "john@example.com",
      "title": "Software Engineer",
      "profile_url": "https://linkedin.com/in/...",
      "icp_fit_strength": "High",
      "reason": "Senior technical role...",
      "profile_summary": "## Summary\n...",
      "company_summary": "## Company\n..."
    }
  ],
  "total_processed": 1,
  "message": "Processing completed successfully"
}
```
</example>

<workflow>
## ADDING NEW AUTOMATION STEPS

1. Create new function in `workflow.py` following naming pattern
2. Add comprehensive comments
3. Insert function call in `process_linkedin_post()` loop
4. Update return data structure if needed
5. Test with single profile first
6. Update this CLAUDE.md

## TESTING INDIVIDUAL COMPONENTS

Use `test_components.py` to test each workflow function independently:

**Quick Start:**
```bash
cd backend
python test_components.py
```

**Available Tests:**
- `test_fetch_reactions()` - Test Apify post reactions scraper
- `test_check_airtable()` - Test URN existence check
- `test_fetch_profile()` - Test LinkedIn profile scraper (dev_fusion actor)
- `test_fetch_company_primary()` - Test primary company scraper
- `test_fetch_company_backup()` - Test backup company scraper
- `test_summarize_groq()` - Test Groq AI summarization
- `test_evaluate_icp()` - Test OpenAI ICP evaluation
- `test_create_airtable()` - Test Airtable record creation
- `test_full_pipeline()` - Test complete end-to-end workflow

**Usage:**
1. Edit `test_components.py`
2. Replace example URLs/IDs with real LinkedIn data
3. Uncomment the tests you want to run
4. Run: `python test_components.py`

Tests can run independently or sequentially with data flow between them.
</workflow>

<must_follow_rules>
## MISSION CRITICAL RULES

1. **Keep workflow linear and visible** - All automation steps in `workflow.py`, never split across files
2. **Flexible for future automations** - Structure supports adding new workflows without refactoring
3. **Minimalist approach** - Only implement requested features, don't over-engineer
4. **Update CLAUDE.md on changes** - Keep living documentation current in all folders
5. **Never commit .env files** - Sensitive credentials must stay local
6. **create nested CLAUDE.md** -cladue.md files shall be created in every folder and subfolder and should contain an updated context and overview of the code in that subfolder/module
7. **keep updating all CLAUDE.md files** - it is a living documentation
8. **Add good comments everywhere** -  add comments in your code to make it better documented
9. **Update on change** - If code changes affect docs, update immediately- update and create claude.md for folders and subfolders. Also update readme.md for context and any updates. When making updates , remove any old context that got changed.

</must_follow_rules>