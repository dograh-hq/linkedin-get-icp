<system_context>
Manual profile input page - Allows users to directly input LinkedIn profile URLs (one per line) for batch processing, bypassing the post reactor workflow.
</system_context>

<file_map>
## FILE MAP
- `page.tsx` - Manual input form with URL validation and results dashboard
</file_map>

<paved_path>
## ARCHITECTURE (PAVED PATH)

**Component Structure:**
```
┌─ Navigation ──────────────────┐
│ ← From Post Reactors | Manual │
└───────────────────────────────┘

┌─ Input Form ──────────────────┐
│ LinkedIn Profile URLs (X/100) │
│ [Textarea - one URL per line] │
│ [Process X Profiles button]   │
└───────────────────────────────┘

┌─ Progress Section ────────────┐
│ Current Step                  │
│ Progress Bar                  │
│ X / Y profiles processed      │
└───────────────────────────────┘

┌─ Results Table ───────────────┐
│ Name | Company | Title | ...  │
│ ...  | ...     | ...   | ...  │
└───────────────────────────────┘

┌─ Skipped Profiles ────────────┐
│ (if any timeouts/errors)      │
└───────────────────────────────┘
```

**Data Flow:**
1. User pastes LinkedIn profile URLs (one per line, max 100)
2. Form validates URLs contain "linkedin.com/in/"
3. Submit → POST `/api/process-manual-profiles` with `profile_urls` array
4. Backend returns `job_id` immediately
5. Poll `/api/job-status/{job_id}` every 20 seconds
6. Display results incrementally as they arrive
7. Show skipped profiles separately if timeouts occur
</paved_path>

<critical_notes>
## CRITICAL NOTES

- **Authentication protected** - Requires valid `auth_token` cookie (password: `_______`)
- **Max 100 profiles per batch** - Hard limit to prevent API overload
- **URL validation** - Must contain "linkedin.com/in/"
- **One URL per line** - Textarea split by newlines
- **Real-time counter** - Shows "X/100" profiles entered
- **Monospace textarea** - Better for viewing URLs
- **Same API structure** - Uses job queue system like post reactor workflow
- **Incremental results** - Leads appear as they're processed (~1 min per profile)

**Table Structure (Updated 2025-01-13):**
Columns: Name (150px) | **Company (150px)** | Title (120px) | ICP Fit (100px) | ICP Reason (500px) | Validation (120px) | Validation Reason (300px) | **Profile URL (120px)**

**Key Changes:**
- **Company column** - Shows company_name + company_website in stacked display
  - First line: Company name
  - Second line: Clickable website URL (blue, 12px, word-break)
  - Website extracted from: company.website, company.websiteUrl, or company.basic_info.website
- **Profile URL moved to last** - Displays full clickable URL for bulk copying
- **Column widths optimized** - ICP Reason 2.5x wider (500px), Title 0.4x narrower (120px), Validation Reason 1.5x wider (300px)

**Skipped Profiles:**
- Separate orange/yellow table below results
- Shows profiles that exceeded 180s timeout or hit errors
- Includes: Name, Skip Reason, Profile URL
- Only appears when `skippedProfiles.length > 0`

**Type Definitions:**
```typescript
type Lead = {
  urn: string;
  name: string;
  company_name: string;      // Company name
  company_website: string;    // NEW (2025-01-13): Company website URL
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

type SkippedProfile = {
  urn: string;
  name: string;
  reason: string;
  profile_url: string;
};
```

**Gotchas:**
- Disabled submit button if no URLs or >100 URLs entered
- Progress polling stops on completion/failure
- Error state displays above progress section
- Results persist after completion for review
- Profile URLs now show full URL text instead of "View Profile →" button
</critical_notes>

<workflow>
## DEVELOPMENT WORKFLOW

**Adding new validation rules:**
1. Update URL validation in `handleSubmit`
2. Add error message for invalid format
3. Test with edge cases

**Changing batch limits:**
1. Update `MAX_PROFILES` constant in validation
2. Update placeholder text count
3. Update backend limit if needed

**Adding table columns:**
1. Update `Lead` type definition
2. Add `<th>` in table header with width
3. Add `<td>` in table body with matching width
4. Ensure backend includes field in response
</workflow>

<must_follow_rules>
## MISSION CRITICAL RULES

1. **Keep workflow linear and visible** - All automation steps in `workflow.py`, never split across files
2. **Flexible for future automations** - Structure supports adding new workflows without refactoring
3. **Minimalist approach** - Only implement requested features, don't over-engineer
4. **Update CLAUDE.md on changes** - Keep living documentation current in all folders
5. **Never commit .env files** - Sensitive credentials must stay local
6. **create nested CLAUDE.md** - claude.md files shall be created in every folder and subfolder
7. **keep updating all CLAUDE.md files** - it is a living documentation
8. **Add good comments everywhere** - add comments in your code to make it better documented
9. **Update on change** - If code changes affect docs, update immediately
</must_follow_rules>
