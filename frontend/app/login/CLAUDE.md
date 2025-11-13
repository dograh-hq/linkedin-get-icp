<system_context>
Authentication login page - Password-protected portal access with simple single-password authentication.
</system_context>

<file_map>
## FILE MAP
- `page.tsx` - Login page component with password form
</file_map>

<paved_path>
## ARCHITECTURE (PAVED PATH)

**Authentication Flow:**
```
User visits protected route
         ↓
Middleware checks auth_token cookie
         ↓
No cookie found → Redirect to /login
         ↓
User enters password: "______"
         ↓
POST to /api/auth/login
         ↓
API validates password
         ↓
Set HTTP-only cookie (7 days)
         ↓
Redirect to dashboard (/)
         ↓
All routes now accessible
```

**Component Structure:**
```
┌─ Login Page ──────────────────┐
│ LinkedIn Profiling Portal     │
│ Enter password to access      │
│                               │
│ [Password field]              │
│ [Login button]                │
│                               │
│ [Error message if failed]     │
└───────────────────────────────┘
```

**State Management:**
- `password` - Input field value
- `error` - Error message display
- `loading` - Submit button state
</paved_path>

<critical_notes>
## CRITICAL NOTES

- **Single password**: `_______` (hardcoded in API route)
- **No username required**: Only password field shown
- **Client-side validation**: Button disabled when password is empty
- **Error display**: Red box shows validation errors
- **Auto-focus**: Password field focused on page load
- **Loading state**: "Authenticating..." shown during API call

**Password:**
- Value: `_______________`
- Validation happens server-side in `/api/auth/login`
- No client-side password checking (would expose password)

**Cookie Details:**
- Name: `auth_token`
- Value: `authenticated`
- HTTP-only: Yes (JavaScript cannot access)
- Secure: Yes in production (HTTPS only)
- SameSite: `lax` (CSRF protection)
- Max-age: 604800 seconds (7 days)
- Path: `/` (all routes)

**UI States:**
1. **Initial**: Empty password field, enabled button
2. **Typing**: Button enabled when password not empty
3. **Submitting**: Button disabled, shows "Authenticating..."
4. **Error**: Red error box appears above button
5. **Success**: Immediate redirect to `/` (dashboard)

**Security Features:**
- HTTP-only cookie prevents XSS attacks
- Secure flag ensures HTTPS-only transmission in production
- SameSite prevents CSRF attacks
- No password stored in localStorage or sessionStorage
- No password visible in network logs (sent in request body, not URL)

**Gotchas:**
- Cookie expires after 7 days (automatic logout)
- No "Remember Me" option (always 7 days)
- No logout button (must wait for cookie expiration or clear cookies manually)
- Already authenticated users redirected away from `/login` by middleware
- Password change requires editing `frontend/app/api/auth/login/route.ts`
</critical_notes>

<styling>
## UI DESIGN

**Layout:**
- Centered vertically and horizontally
- Card design with shadow
- Maximum width: 400px
- Gray background (#f5f5f5)
- White card with 40px padding

**Typography:**
- Title: 24px bold ("LinkedIn Profiling Portal")
- Subtitle: Gray text ("Enter password to access")
- Label: 14px medium weight
- Input: 14px

**Colors:**
- Background: #f5f5f5 (light gray)
- Card: white with subtle shadow
- Primary button: #007bff (blue)
- Disabled button: #ccc (gray)
- Error box: #fee background, #c00 text
- Input border: #ddd (light gray)

**Input Field:**
- Type: password (masked input)
- Placeholder: "Enter password"
- Border: 1px solid #ddd
- Border-radius: 4px
- Padding: 10px 12px
- Full width

**Button:**
- Full width
- Padding: 12px
- Border-radius: 4px
- Font size: 16px
- Disabled state: Gray background, not-allowed cursor
- Active state: Blue background, pointer cursor
- Loading state: Shows "Authenticating..." text
</styling>

<workflow>
## DEVELOPMENT WORKFLOW

**Changing the password:**
1. Edit `frontend/app/api/auth/login/route.ts`
2. Update `PORTAL_PASSWORD` constant
3. No other changes needed (login page is generic)

**Customizing login UI:**
1. Edit inline styles in `page.tsx`
2. Modify title/subtitle text
3. Update color scheme
4. Test with both success and error states

**Adding multi-user authentication:**
1. Replace single password with username/password
2. Update API to check database
3. Add user management system
4. Store user info in cookie or session
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
