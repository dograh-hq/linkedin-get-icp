<system_context>
Next.js 14 frontend with TypeScript. Provides UI for submitting LinkedIn posts and displays processed leads in dashboard format. Proxies API requests to FastAPI backend.
</system_context>

<file_map>
## FILE MAP
- `app/` - Next.js app directory with pages and components
  - `login/page.tsx` - Password authentication login page
  - `api/auth/login/route.ts` - Authentication API endpoint
  - `page.tsx` - Main dashboard (post reactors workflow)
  - `manual-input/page.tsx` - Manual profile input workflow
- `middleware.ts` - Route protection middleware (protects all routes except /login)
- `next.config.js` - Next.js configuration with proxy rewrites
- `package.json` - Dependencies and scripts
- `tsconfig.json` - TypeScript configuration
</file_map>

<paved_path>
## ARCHITECTURE (PAVED PATH)

**Next.js App Router Structure:**
```
app/
├── layout.tsx - Root layout with metadata
├── page.tsx - Main page with form + dashboard (protected)
├── manual-input/page.tsx - Manual profile input workflow (protected)
├── login/page.tsx - Authentication login page (public)
└── api/auth/login/route.ts - Authentication API endpoint
middleware.ts - Route protection (checks auth_token cookie)
```

**Authentication Flow:**
1. User visits any route → Middleware checks `auth_token` cookie
2. If NOT authenticated → Redirect to `/login`
3. User enters password: `______`
4. POST to `/api/auth/login` → Sets HTTP-only cookie (7-day expiration)
5. Redirect to dashboard → All subsequent requests include cookie

**Component Structure (in page.tsx):**
1. Input form - LinkedIn post URL submission
2. Progress tracker - Real-time processing status
3. Results table - Display processed leads with ICP fit

**API Communication:**
- Frontend calls `/api/process-post` (relative)
- Next.js proxy rewrites to `http://localhost:8000/api/process-post`
- Configured in `next.config.js` rewrites()

**State Management:**
- Local React state (useState)
- No global state needed (simple app)
- Types defined inline
</paved_path>

<critical_notes>
## CRITICAL NOTES

- **Must run on 0.0.0.0:3000**: Required for proper network access
- **Proxy configuration**: All `/api/*` requests auto-route to FastAPI backend
- **Authentication required**: All routes protected except `/login` (password: `__________`)
- **Cookie-based auth**: HTTP-only secure cookie with 7-day expiration
- **Middleware protection**: `middleware.ts` checks auth on every request
- **No TypeScript `any` types**: All types explicitly defined
- **Minimal styling**: Inline styles only, no CSS framework
- **Client-side only**: 'use client' directive on main page

**Type Definitions:**
```typescript
type Lead = {
  urn: string;
  name: string;
  email: string;
  title: string;
  profile_url: string;
  icp_fit_strength: string;
  reason: string;
  validation_judgement: string;
  validation_reason: string;
  profile_summary: string;
  company_summary: string;
  status: string;
};

type SkippedProfile = {
  urn: string;
  name: string;
  reason: string;
  profile_url: string;
};

type JobStatus = {
  job_id: string;
  status: 'processing' | 'completed' | 'failed';
  progress: {
    current: number;
    total: number;
    message: string;
  };
  results: Lead[];
  skipped_profiles: SkippedProfile[];
  error?: string;
};
```

**Skipped Profiles Display (NEW):**
- Separate table below successful leads showing profiles that timed out or failed
- Only displayed when `skippedProfiles.length > 0`
- Orange/yellow color scheme (#d97706, #fff3cd, #ffc107)
- Columns: Name, Skip Reason, Profile Link
- Reasons include: "Processing exceeded 180s timeout", API errors, network errors
- Helps users understand which profiles need manual review

**Gotchas:**
- Backend must be running on localhost:8000 before frontend starts
- Post URL can be full URL or just ID (backend extracts ID)
- Progress updates via polling every 20 seconds
- Results display incrementally as leads are processed
- ICP fit colors: High=green, Medium=yellow, Low=red
- Validation colors: Correct=green, Incorrect=red, Unsure=yellow
- Skipped profiles colors: Orange/yellow to differentiate from success/error states
</critical_notes>

<workflow>
## ADDING NEW UI FEATURES

1. Edit `app/page.tsx`
2. Add new state variables if needed
3. Create inline-styled components
4. Keep TypeScript types explicit
5. Update frontend/app/CLAUDE.md
6. Test in browser
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