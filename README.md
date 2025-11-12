# LinkedIn Lead Profiling Automation

> ⚠️ **TEMPORARY NOTICE (2025-01-11):** Airtable integration is currently disabled due to performance issues. All profiles are processed and displayed on the frontend, but **NOT saved to Airtable**. This is temporary until Airtable subscription is sorted. See `CHANGES.md` Section 13 for details and revert instructions.

An automated system that profiles LinkedIn users, enriches their data, and evaluates them against your Ideal Customer Persona (ICP). Supports two workflows: processing post reactors automatically or manually inputting specific profiles.

## Features

### Two Processing Workflows:
- 🔄 **From Post Reactors**: Automatically fetch and process reactions from a LinkedIn post
- ✍️ **Manual Input**: Process specific profiles by entering LinkedIn URLs (one per line)

### Core Capabilities:
- 👤 Enrich profile data from LinkedIn (via Apify)
- 🏢 Gather company information with fallback mechanism
- 🤖 AI-powered profile and company summarization (Groq Llama 3.3 70B)
- 🎯 ICP matching evaluation (OpenAI GPT-5 mini with high reasoning effort)
- 📊 Store and track leads in Airtable
- 💻 Full-stack dashboard with real-time progress tracking
- ⚡ Smart rate limiting (max 100 profiles per batch)
- 🔁 Automatic deduplication (skips existing profiles)
- 📈 Incremental results display (see leads as they're processed, every 20 seconds)

## Architecture

- **Frontend**: Next.js (TypeScript) - Runs on `0.0.0.0:3000`
- **Backend**: FastAPI (Python) - Runs on `localhost:8000`
- **Proxy**: Next.js proxies `/api/*` requests to FastAPI

## Project Structure

```
linkedin-profiling/
├── frontend/                    # Next.js frontend
│   ├── app/
│   │   ├── page.tsx            # Post reactors workflow
│   │   ├── manual-input/
│   │   │   └── page.tsx        # Manual profile input workflow
│   │   └── layout.tsx
│   ├── next.config.js          # Proxy configuration
│   ├── package.json
│   └── tsconfig.json
│
├── backend/                    # FastAPI backend
│   ├── main.py                # FastAPI server with job queue
│   ├── workflow.py            # Linear automation workflows
│   ├── prompts.py             # Centralized LLM prompts
│   ├── test_components.py     # Component testing script
│   ├── requirements.txt
│   └── .env.example
│
└── README.md
```

## 🚀 NEXT STEPS FOR USER

Before running the application, complete these setup tasks:

### 1. Get API Credentials

You need accounts and API keys for these services:

#### Apify (Already provided)
- ✅ Token included in `.env.example`: `apify_api_____________`

#### Airtable
- [ ] Sign up at https://airtable.com
- [ ] Create a new base (or use existing)
- [ ] Go to https://airtable.com/create/tokens
- [ ] Create a personal access token with `data.records:read` and `data.records:write` scopes
- [ ] Copy your Base ID from the base URL: `https://airtable.com/YOUR_BASE_ID/...`
- [ ] Create a table named "Leads" (or your preferred name)

#### OpenAI
- [ ] Sign up at https://platform.openai.com
- [ ] Go to https://platform.openai.com/api-keys
- [ ] Create a new API key
- [ ] Copy the key (starts with `sk-...`)

#### Groq (Already provided)
- ✅ Token included in `.env.example`: `gsk_______________`

### 2. Set Up Airtable Table

Create a table with these fields (**exact names required** - case-sensitive):

| Field Name | Field Type | Options |
|-----------|------------|---------|
| URN | Single line text | - |
| Name | Single line text | - |
| company_name | Single line text | - |
| company_website | URL or Single line text | - |
| Email Address | Email | - |
| Title | Long text | - |
| Profile URL | URL | - |
| icp_fit_strength | Single select | Options: High, Medium, Low |
| Reason | Long text | - |
| validation_judgement | Single select | Options: Correct, Incorrect, Unsure |
| validation_reason | Long text | - |
| profile_summary | Long text | - |
| company_summary | Long text | - |

**IMPORTANT:** Field names are case-sensitive. Capital letters must match exactly (URN, Name, Email Address, Title, Profile URL, Reason). The remaining fields are lowercase (company_name, company_website, icp_fit_strength, validation_judgement, validation_reason, profile_summary, company_summary).

### 3. Configure Environment Variables

Edit `backend/.env` with your credentials:
```bash
cd backend
cp .env.example .env
# Edit .env and add your tokens
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file from `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Fill in your API credentials in `.env`:
   - `APIFY_TOKEN`: Your Apify API token
   - `AIRTABLE_TOKEN`: Your Airtable personal access token
   - `AIRTABLE_BASE_ID`: Your Airtable base ID
   - `AIRTABLE_TABLE_NAME`: Table name (default: "Leads")
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `GROQ_API_KEY`: Your Groq API key

6. Run the FastAPI server:
   ```bash
   python main.py
   ```
   Server will start on `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```
   App will be available on `http://0.0.0.0:3000` or `http://localhost:3000`

## Airtable Schema

Create a table with these fields (**exact names - case-sensitive**):

| Field Name           | Field Type      | Description                          |
|----------------------|-----------------|--------------------------------------|
| URN                  | Single line text| LinkedIn URN (unique identifier)     |
| Name                 | Single line text| Full name                            |
| company_name         | Single line text| Company name                         |
| company_website      | URL or Single line text| Company website URL            |
| Email Address        | Email           | Email address (if available)         |
| Title                | Long text       | Job title/headline                   |
| Profile URL          | URL             | LinkedIn profile URL                 |
| icp_fit_strength     | Single select   | "High", "Medium", "Low"              |
| Reason               | Long text       | Reason for ICP evaluation            |
| validation_judgement | Single select   | "Correct", "Incorrect", "Unsure"     |
| validation_reason    | Long text       | Reason for validation judgement      |
| profile_summary      | Long text       | AI-generated profile summary         |
| company_summary      | Long text       | AI-generated company summary         |

**Note:** Field names must match exactly. Capitalized fields: URN, Name, Email Address, Title, Profile URL, Reason. Lowercase fields: company_name, company_website, icp_fit_strength, validation_judgement, validation_reason, profile_summary, company_summary.

## Usage

### Option 1: From Post Reactors (Automatic)
1. Start both backend and frontend servers
2. Open `http://localhost:3000` in your browser
3. Click "From Post Reactors" tab (default)
4. Enter a LinkedIn post URL or ID (e.g., `7392508631268835328`)
5. Click "Process Post"
6. View real-time progress and results in the dashboard
   - **Progress bar** updates every 20 seconds showing X/100 profiles processed
   - **Results appear incrementally** as leads are saved to Airtable (~1 lead per minute)
   - **No need to wait** - review leads while processing continues

### Option 2: Manual Profile Input
1. Start both backend and frontend servers
2. Open `http://localhost:3000` in your browser
3. Click "Manual Input" tab
4. Paste LinkedIn profile URLs (one per line, max 100)
   - Format: `https://linkedin.com/in/username`
5. Click "Process X Profiles"
6. View real-time progress and results in the dashboard
   - **Progress bar** updates every 20 seconds showing X/100 profiles processed
   - **Results appear incrementally** as leads are saved to Airtable (~1 lead per minute)
   - **No need to wait** - review leads while processing continues

## Results Table Layout

The frontend dashboard displays processed leads in a structured table with the following columns:

| Column | Width | Description |
|--------|-------|-------------|
| **Name** | 150px | Full name of the LinkedIn profile |
| **Company** | 150px | Company name + website URL (stacked display) |
| **Title** | 120px | Job title/headline |
| **ICP Fit** | 100px | High/Medium/Low badge (color-coded) |
| **ICP Reason** | 500px | Detailed explanation of ICP evaluation |
| **Validation** | 120px | Correct/Incorrect/Unsure badge (color-coded) |
| **Validation Reason** | 300px | Explanation of validation assessment |
| **Profile URL** | 120px | Full clickable LinkedIn profile URL |

**Key Features:**
- **Company column**: Shows company name on first line, website URL on second line (if available)
  - Website extracted from company API: `website`, `websiteUrl`, or `basic_info.website`
  - Clickable blue link (12px font size)
- **Profile URL column**: Displays full URL as clickable text (for easy bulk copying)
- **Optimized widths**: ICP Reason (2.5x wider), Title (0.4x narrower), Validation Reason (1.5x wider) for better readability
- **Color-coded badges**: Green (High/Correct), Yellow (Medium/Unsure), Red (Low/Incorrect)

## Workflow Steps

All automation steps are visible in `backend/workflow.py`:

### From Post Reactors Workflow:
1. **Fetch Post Reactions**: Get reactors from the LinkedIn post
2. For each reactor:
   - **Check Airtable**: Skip profiles already in the database
   - **Enrich Profile**: Fetch detailed LinkedIn profile data (Apify)
   - **Enrich Company**: Fetch company information with fallback (Apify)
   - **Summarize**: Generate digestible summaries (Groq Llama 3.3 70B)
   - **Evaluate ICP**: Assess if lead matches your ICP (OpenAI GPT-5 mini with high reasoning)
   - **Validate ICP**: Quality check on ICP evaluation (Groq openai/gpt-oss-20b)
   - **Store**: Save/update record in Airtable

### Manual Input Workflow:
1. **Parse Profile URLs**: Validate and clean provided LinkedIn profile URLs
2. For each profile URL:
   - **Extract Profile ID**: Use LinkedIn username from URL as URN (e.g., "priteshkr" from "linkedin.com/in/priteshkr/")
   - **Check Airtable**: Skip profiles already in the database (using profile ID as URN)
   - **Enrich Profile**: Fetch detailed LinkedIn profile data (Apify)
   - **Enrich Company**: Fetch company information with fallback (Apify)
   - **Summarize**: Generate digestible summaries (Groq Llama 3.3 70B)
   - **Evaluate ICP**: Assess if lead matches your ICP (OpenAI GPT-5 mini with high reasoning)
   - **Validate ICP**: Quality check on ICP evaluation (Groq openai/gpt-oss-20b)
   - **Store**: Save/update record in Airtable with profile ID as URN

**Note:** Processing is limited to 100 profiles per batch (both workflows) to prevent API overload and avoid LinkedIn rate limits. This limit can be adjusted in `backend/workflow.py` by changing the `MAX_REACTORS_PER_POST` constant.

**URN Format Difference:**
- **Post Reactors**: Uses Apify's URN field (e.g., `urn:li:person:123456789`)
- **Manual Input**: Uses LinkedIn profile ID from URL (e.g., `priteshkr` from `linkedin.com/in/priteshkr/`)
- This ensures consistent and predictable URNs for manually added profiles

## Timeout Handling

**Per-Profile Timeout (180 seconds):**
- Each profile has a **180-second (3-minute) timeout** for all processing steps combined
- If processing exceeds the timeout, the profile is **automatically skipped**
- Batch processing **continues immediately** to the next profile (no blocking)
- Skipped profiles are tracked separately with the reason for skipping

**Common Skip Reasons:**
- ⏱️ "Processing exceeded 180s timeout" - Profile took too long to process
- 🔌 "Network error during profile fetch" - API connectivity issues
- ⚠️ "API error: [specific message]" - Upstream service errors
- ❌ "Could not fetch profile data" - Profile not accessible or invalid

**Skipped Profiles Display:**
- Skipped profiles appear in a **separate table** below successful leads
- Table shows: Profile Name, Skip Reason, Profile URL link
- Orange/yellow color scheme distinguishes skipped from successful profiles
- Allows manual review of profiles that need attention

**Why 180 seconds?**
- Profile processing involves 7+ API calls (LinkedIn scraping, company data, multiple LLM calls)
- Some LinkedIn profiles/companies are slow to scrape (30-60s each)
- Conservative timeout ensures legitimate slow responses complete
- Prevents indefinite hangs while allowing most profiles to succeed

**Configuration:**
- Timeout can be adjusted in `backend/workflow.py`: `PROFILE_TIMEOUT_SECONDS = 180`
- No individual API timeouts - simpler implementation with per-profile wrapper only

## Customization

### Modify ICP Criteria

Edit the `ICP_EVALUATION_PROMPT` in `backend/prompts.py` to customize what defines your ideal customer.

### Modify LLM Prompts

All LLM prompts are centralized in `backend/prompts.py`:
- `PROFILE_SUMMARY_SYSTEM_PROMPT` - How to summarize LinkedIn profiles
- `COMPANY_SUMMARY_SYSTEM_PROMPT` - How to summarize company data
- `ICP_EVALUATION_PROMPT` - How to evaluate lead fit

The workflow passes complete raw JSON from Apify directly to AI models using `json.dumps(data, indent=2)` for better context and accuracy - no helper functions or pre-formatting.

### Add/Remove Steps

All workflow steps are in `backend/workflow.py`. You can easily:
- Add new data sources
- Skip certain steps
- Modify the evaluation logic
- Add custom enrichment

### Add More Automations

The structure is flexible to accommodate additional automations. Create new workflow files following the same pattern.

## API Endpoints

- `GET /` - Health check
- `POST /api/process-post` - Process a LinkedIn post
  ```json
  {
    "post_url": "7392508631268835328"
  }
  ```

## External Services Used

- **Apify**: LinkedIn data scraping
  - `apimaestro~linkedin-post-reactions`: Get post reactions
  - `anchor~linkedin-profile-enrichment`: Profile details
  - `logical_scrapers~linkedin-company-scraper`: Company data (primary)
  - `apimaestro~linkedin-company-detail`: Company data (backup)
- **Airtable**: Lead database and CRM
- **Groq**: AI summarization (Llama 3.3 70B model)
- **OpenAI**: ICP evaluation (GPT-5 mini via /v1/responses endpoint with high reasoning effort)

## Development

### Run in Development Mode

Backend:
```bash
cd backend
uvicorn main:app --reload --host localhost --port 8000
```

Frontend:
```bash
cd frontend
npm run dev
```

### Testing Individual Components

Test each workflow component independently before running the full pipeline:

```bash
cd backend
python test_components.py
```

**Available Tests:**
- Test Apify post reactions scraper
- Test LinkedIn profile enrichment
- Test company data scraping (primary and backup)
- Test Groq AI summarization
- Test OpenAI ICP evaluation
- Test Airtable record creation
- Test full end-to-end pipeline (single lead)

**How to use:**
1. Edit `backend/test_components.py`
2. Replace example URLs/IDs with real LinkedIn data
3. Uncomment the specific tests you want to run
4. Run the script

See detailed instructions in `backend/test_components.py`.

### Build for Production

Frontend:
```bash
cd frontend
npm run build
npm run start
```

## 🧪 TESTING INSTRUCTIONS

Follow these steps to test the application:

### Step 1: Test Backend Server

1. Start the backend server:
   ```bash
   cd backend
   python main.py
   ```

2. Verify server is running:
   - You should see: `INFO: Uvicorn running on http://localhost:8000`
   - Open http://localhost:8000 in browser
   - You should see: `{"message": "LinkedIn Lead Profiling API is running"}`

3. Check for errors:
   - ✅ No errors → Backend is ready
   - ❌ Import errors → Run `pip install -r requirements.txt`
   - ❌ Environment errors → Check `.env` file exists and has all keys

### Step 2: Test Frontend Server

1. **In a new terminal**, start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

2. Verify frontend is running:
   - You should see: `- Local: http://localhost:3000`
   - Open http://localhost:3000 in browser
   - You should see the LinkedIn Lead Profiling dashboard

3. Check the UI:
   - ✅ Input form visible → "Enter LinkedIn Post URL or ID"
   - ✅ "Process Post" button visible → UI is ready

### Step 3: Test with a LinkedIn Post

1. Find a LinkedIn post with reactions:
   - Go to LinkedIn and find any post with reactions
   - Copy the post URL or ID (e.g., `7392508631268835328`)

2. Process the post:
   - Paste the URL/ID in the input field
   - Click "Process Post"
   - Watch the backend terminal for logs

3. Expected behavior:
   ```
   Backend logs should show:
   ====================================
   STARTING LINKEDIN POST PROCESSING
   Post ID: 7392508631268835328
   ====================================

   STEP 1: Fetching post reactions...
   ✓ Fetched 6 reactions from post...

   --- Processing Reactor 1/6: John Doe ---
   STEP 2a: Checking Airtable...
   → New profile. Proceeding with enrichment...
   ...
   ```

4. Check results:
   - ✅ Progress bar updates
   - ✅ Results table appears with processed leads
   - ✅ ICP fit strength shown (High/Medium/Low)
   - ✅ "View Profile" links work

### Step 4: Verify Airtable Integration

1. Open your Airtable base
2. Check the "Leads" table
3. Verify:
   - ✅ New records created
   - ✅ All fields populated (name, title, ICP fit, etc.)
   - ✅ URN field contains LinkedIn URN
   - ✅ Profile URL is clickable

### Troubleshooting

**Frontend can't connect to backend:**
- Make sure backend is running on `localhost:8000`
- Check browser console for errors
- Verify `next.config.js` proxy configuration

**Backend API errors:**
- Check `.env` file has all required tokens
- Verify Apify token is valid
- Verify Airtable base ID and table name are correct
- Check backend terminal for specific error messages

**No results returned:**
- Check if post ID is valid (should be a numeric string)
- Verify Apify can access the LinkedIn post
- Check rate limits on Apify account

**Airtable errors:**
- Verify table schema matches exactly (field names are case-sensitive)
- Check Airtable token has read/write permissions
- Ensure base ID is correct

### Quick Test with Provided Data

Use this test post ID from the reference: `7392508631268835328`

Expected result: 6 reactors should be processed and appear in results table.

## License

Private - Not for distribution

## Notes

- Keep your `.env` files secure and never commit them
- The automation respects rate limits of external services
- Profile data is cached in Airtable to avoid redundant API calls
- All logs are printed to console for transparency
