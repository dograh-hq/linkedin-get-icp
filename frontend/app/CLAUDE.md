<system_context>
Next.js App Router pages. Contains root layout and main dashboard page for LinkedIn lead profiling interface.
</system_context>

<file_map>
## FILE MAP
- `layout.tsx` - Root layout wrapper with HTML structure and metadata
- `page.tsx` - Main dashboard page with form, progress, and results table (protected)
- `manual-input/page.tsx` - Manual profile input workflow page (protected)
- `login/page.tsx` - Password authentication login page (public)
- `api/auth/login/route.ts` - Authentication API endpoint
</file_map>

<paved_path>
## COMPONENT STRUCTURE

**layout.tsx:**
- Minimal root layout
- Sets page title and description metadata
- Wraps all pages with HTML/body tags

**page.tsx (Main Dashboard):**
```
┌─ Input Form ──────────────┐
│ [LinkedIn URL input]      │
│ [Process Post button]     │
└───────────────────────────┘

┌─ Progress Section ────────┐
│ Current Step              │
│ Progress Bar              │
│ X / Y profiles processed  │
└───────────────────────────┘

┌─ Results Table ──────────────────────────────────────────────────┐
│ Name | Company | Email | Title | ICP Fit | ICP Reason | ... | URL │
│ ...  | ...     | ...   | ...   | ...     | ...        | ... | ... │
└──────────────────────────────────────────────────────────────────┘
(Columns: Name=150px, Company=150px, Email=180px, Title=120px, ICP Fit=100px,
 ICP Reason=500px, Validation=120px, Validation Reason=300px, Profile URL=120px)
```

**State Flow:**
1. User enters post URL
2. Submit → API call to `/api/process-post` returns job_id immediately
3. Poll `/api/job-status/{job_id}` every 20 seconds
4. Update `leads` state with partial results as they arrive
5. Table re-renders incrementally with new leads
6. Stop polling when status="completed"
</paved_path>

<critical_notes>
## CRITICAL NOTES

- **Authentication protected**: All pages except `/login` require authentication (middleware checks `auth_token` cookie)
- **Client component**: 'use client' directive required for useState
- **Inline styles only**: No external CSS files
- **Synchronous processing**: No WebSocket/SSE for real-time updates
- **Error handling**: Try-catch with error state display
- **Type safety**: All props and state explicitly typed

**UI States:**
- Loading: `isProcessing=true`, button disabled, progress bar showing
- Processing: Progress bar updates every 20 seconds, leads appear incrementally
- Error: Red error box displays
- Success: Results table fully populated with all leads
- Empty: No results message

**Incremental Results Display:**
- Results table updates every 20 seconds as new leads are processed
- Users can review leads while processing continues
- No need to wait for all 100 profiles to finish
- First result appears within ~1 minute

**Table Structure (Updated 2025-01-14):**
- **Company column** - Shows company_name + company_website as stacked display (150px)
  - First line: Company name
  - Second line: Clickable website URL (blue, 12px font, word-break)
  - Website extracted from: company.website or company.websiteUrl or company.basic_info.website
- **Email column** - Displays profile email address (180px)
  - Shows email from profile data (profile_data.get('email', ''))
  - Fallback: "Not Available" when email field is empty
  - Positioned after Company, before Title for logical grouping
- **Profile URL moved to last** - Displays full clickable URL for bulk copying (120px)
- **Column widths optimized** - ICP Reason 2.5x wider (500px), Title 0.4x narrower (120px), Validation Reason 1.5x wider (300px)
- Company name sourced from profile.companyName or company.name (fallback: 'Unknown')

**Color Coding:**
- ICP High: Green (#d4edda/#155724)
- ICP Medium: Yellow (#fff3cd/#856404)
- ICP Low: Red (#f8d7da/#721c24)
- Validation Correct: Green (#d4edda/#155724)
- Validation Incorrect: Red (#f8d7da/#721c24)
- Validation Unsure: Yellow (#fff3cd/#856404)
</critical_notes>

<example>
## CODE PATTERNS

**Current Lead Type:**
```typescript
type Lead = {
  urn: string;
  name: string;
  company_name: string;      // Company name (2nd column)
  company_website: string;    // NEW: Company website URL (displayed under company name)
  email: string;
  title: string;
  profile_url: string;
  icp_fit_strength: string;
  reason: string;
  validation_judgement: string;
  validation_reason: string;
  profile_summary: string;
  company_summary: string;
};
```

**Adding new table column:**
```typescript
// 1. Add to Lead type
type Lead = {
  // ... existing fields
  new_field: string;
};

// 2. Add table header with width
<th style={{ width: '150px' }}>New Field</th>

// 3. Add table cell with matching width
<td style={{ width: '150px' }}>{lead.new_field}</td>
```

**Adding new form field:**
```typescript
// 1. Add state
const [newField, setNewField] = useState('');

// 2. Add input
<input
  value={newField}
  onChange={(e) => setNewField(e.target.value)}
/>

// 3. Include in API call
body: JSON.stringify({ post_url: postUrl, new_field: newField })
```
</example>
