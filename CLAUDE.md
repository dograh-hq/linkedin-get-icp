<system_context>
LinkedIn Lead Profiling Automation - Full-stack system that fetches LinkedIn post reactors, enriches their profiles with AI, and evaluates them against criteria (default ICP or custom use cases). Stores leads in Airtable. Built with Next.js frontend and FastAPI backend.
</system_context>

<file_map>
## FILE MAP
- `/frontend/` - Next.js application (TypeScript, runs on 0.0.0.0:3000)
  - `app/page.tsx` - Main dashboard (ICP evaluation for post reactors)
  - `app/manual-input/page.tsx` - Manual profile input (ICP evaluation)
  - `app/custom-evaluation/page.tsx` - Custom use case evaluation (NEW)
  - `app/login/page.tsx` - Password authentication login page
  - `app/api/auth/login/route.ts` - Authentication API endpoint
  - `middleware.ts` - Route protection middleware
- `/backend/` - FastAPI server (Python, runs on localhost:8000)
  - `workflow.py` - Main automation workflow (supports ICP + custom modes)
  - `prompts.py` - Centralized LLM prompt templates (ICP + custom prompts)
  - `main.py` - FastAPI server entry point (ICP + custom endpoints)
- `/README.md` - Setup instructions and documentation
- `/.gitignore` - Excludes todo.md, reference.md, must_follow_rules.md
</file_map>

<paved_path>
## ARCHITECTURE (PAVED PATH)

**Authentication:**
- **Frontend Authentication**: Password-protected portal access via `PORTAL_PASSWORD`
  - Middleware protects all routes except `/login`
  - HTTP-only secure cookie (7-day expiration)
  - Unauthenticated users redirected to login page
- **Backend API Authentication**: X-API-Key header validation
  - Password stored in sessionStorage after login
  - All API requests include `X-API-Key` header with password
  - Backend validates header against `PORTAL_PASSWORD` env variable
  - Protects `/api/process-post`, `/api/process-manual-profiles`, `/api/job-status/*`
  - Public endpoints: `/` (health check), `/api/auth/login`

**Data Flow:**

**Default ICP Mode** (pages: `/` and `/manual-input`):
1. User authenticates via `/login` (first time or after 7 days)
2. Password stored in sessionStorage for API authentication
3. User submits LinkedIn post URL or manual profile URLs
4. Frontend calls `/api/process-post` or `/api/process-manual-profiles` with `X-API-Key` header
5. Next.js proxies to `localhost:8000/api/*`
6. FastAPI validates API key and runs workflow:
   - Fetch reactions/profiles (Apify)
   - Fetch company details (Apify, with fallback)
   - Summarize with Groq Llama
   - **Evaluate ICP fit** with OpenAI GPT-5 mini (Dograh-specific criteria)
   - **Validate ICP evaluation** with Groq openai/gpt-oss-20b
   - Store in Airtable
7. Results return to frontend dashboard

**Custom Evaluation Mode (NEW)** (page: `/custom-evaluation`):
1. User authenticates (same as above)
2. User defines custom criteria:
   - Use case description (required)
   - Target roles, industries, company size, additional requirements (optional)
3. User submits post URL or manual profile URLs
4. Frontend calls `/api/process-post-custom` or `/api/process-manual-profiles-custom` with criteria
5. Next.js proxies to backend
6. FastAPI validates API key and runs workflow:
   - Fetch reactions/profiles (Apify)
   - Fetch company details (Apify, with fallback)
   - Summarize with Groq Llama (same as ICP mode)
   - **Evaluate custom use case** with OpenAI GPT-5 mini (user's criteria)
   - **Validate custom evaluation** with Groq openai/gpt-oss-20b
   - Store in Airtable (same fields as ICP mode)
7. Results return to frontend (same table structure)

**Tech Stack:**
- Frontend: Next.js 14, TypeScript, React
- Backend: FastAPI, Python 3
- APIs: Apify, Airtable, Groq, OpenAI
- Deployment: Frontend on 0.0.0.0:3000, Backend on localhost:8000

**Proxy Configuration:**
Next.js `rewrites()` in `next.config.js` routes all `/api/*` requests to FastAPI backend.
</paved_path>

<critical_notes>
## CRITICAL NOTES

- **All automation steps visible in one file**: `backend/workflow.py` contains the entire workflow linearly for easy modification
- **Centralized prompts**: All LLM prompts in `backend/prompts.py` for easy customization
- **Raw JSON to LLM**: Profile and company summaries receive complete raw Apify JSON responses via `json.dumps(data, indent=2)` - no pre-formatting
- **No helper functions**: Removed all data formatting functions - raw JSON passes directly to AI models for better context
- **Environment variables**: Backend requires `.env` file with API tokens (never commit)
- **Tokens provided**: Apify and Groq tokens included in `.env.example`
- **Airtable schema**: Requires specific fields (case-sensitive): URN, Name, Email Address, Title, Profile URL, Reason (capitalized), icp_fit_strength, validation_judgement, validation_reason, profile_summary, company_summary (lowercase)
- **ICP evaluation customizable**: Edit `ICP_EVALUATION_PROMPT` in `prompts.py` (not workflow.py) to change matching criteria
- **Company data fallback**: Primary scraper needs company name/URL, backup scraper works with company ID
- **Deduplication**: Checks Airtable URN before processing to avoid duplicate API calls
- **Reactor limit**: Processing limited to first 100 reactors per post to prevent API overload and avoid LinkedIn rate limits (configurable via `MAX_REACTORS_PER_POST`)
- **Per-profile timeout**: 180-second timeout prevents indefinite hangs, skipped profiles tracked separately
- **Company website extraction**: Displays company website URLs alongside company names in frontend table (extracted from company.website, company.websiteUrl, or company.basic_info.website)
- **Code optimization**: Reduced verbose debugging comments while maintaining essential step tracking (65-69% reduction in key functions)
- **Password authentication**: Portal protected with password from `backend/.env: PORTAL_PASSWORD`, backend validates server-side, cookie-based session management (7-day expiration)
- **Backend API security**: All processing endpoints require `X-API-Key` header matching `PORTAL_PASSWORD` - prevents unauthorized direct API access
- **Minimalist design**: Only essential features implemented, easy to extend
- **Custom evaluation mode (NEW)**: Separate `/custom-evaluation` page supports any use case - users define criteria via structured form (5 fields), system evaluates profiles against user's criteria instead of Dograh ICP, reuses same Airtable fields and table structure, zero impact on existing ICP workflows

**Gotchas:**
- Frontend must run on 0.0.0.0:3000 (not localhost) for proper access
- Backend must run on localhost:8000 for proxy to work
- Both servers must be running simultaneously
- Missing API keys will cause workflow to fail silently at that step
- **Security**: Direct backend API calls without valid `X-API-Key` header will be rejected with 401/403 errors
</critical_notes>

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

<workflow>
## DEVELOPMENT WORKFLOW

**Modifying LLM prompts:**
1. Edit prompts in `backend/prompts.py`
2. No code changes needed in `workflow.py`
3. Available prompts: PROFILE_SUMMARY_SYSTEM_PROMPT, COMPANY_SUMMARY_SYSTEM_PROMPT, ICP_EVALUATION_PROMPT

**Adding new automation steps:**
1. Edit `backend/workflow.py`
2. Add step function following existing pattern
3. Insert into `process_linkedin_post()` orchestrator
4. Update this CLAUDE.md with changes

**Adding new data sources:**
1. Create new function in `workflow.py`
2. Call from main workflow loop
3. Update Airtable schema if needed
4. Pass raw data to LLMs using `json.dumps(data, indent=2)`
</workflow>
