# Frontend spec: Job Tracker MVP

## Goal
A simple web app where a student can sign up, add the jobs they've applied to, and update each one's status in one click. It replaces a spreadsheet, so it has to be faster than one.

The frontend is built with AI assistance (Claude Code). The backend API is the focus of this project.

## Stack
- React + Vite, JavaScript
- React Router for pages (the only extra dependency)
- Plain CSS, `fetch` for API calls, no UI or state libraries
- `VITE_API_URL` points at the API (defaults to `http://localhost:8000`). It is public by design, so no secrets go in the frontend.

## Pages
| Route | Page | Access |
|---|---|---|
| `/login` | Email + password, log in | Public |
| `/register` | Email + password, create an account, then log in automatically | Public |
| `/` | Applications for logged-in users; a landing page (what the app does, Sign up / Log in) for visitors | Public |

## Auth behavior
- Login calls `POST /auth/login` (form data) and stores the token in `localStorage`.
- Register calls `POST /auth/register`, then logs in automatically. A duplicate email shows "An account with this email already exists."
- On page load, if there's a token, call `/auth/me` to confirm it still works and get the email for the header.
- Any `401` from the API clears the token and goes to `/login` with "Your session expired. Log in again."
- Log out clears the token. No server call is needed because tokens are stateless.

## Applications page
- Header: app name, the user's email, Log out
- Toolbar: status filter tabs (All, Applied, Interviewing, Offer, Rejected) with a count on each, a company search box (`?company=`), and an "Add application" button
- List: a table on desktop (Company, Role, Status, Date applied, Link, Notes, Edit/Delete) and stacked cards on phones
- Board view (default): a column per status; drag a card to another column to change its status (mouse only), or use the dropdown on each card. A Board / List toggle is remembered between visits.
- List view: Company and Applied columns sort when their header is clicked (`sort_by`, `order`)
- Status is a dropdown on each row; changing it sends `PATCH` immediately
- Status colors: applied blue, interviewing amber, offer green, rejected gray
- Sorted by date applied, newest first
- Add/edit form in a panel: Company*, Role*, Status (default Applied), Date applied (default today), Job URL, Notes. API validation errors (`422`) show next to their field.
- Delete asks for confirmation inside the page, not in a browser popup

## States
- Empty: "No applications yet. Add the first one you've applied to."
- Loading: gray placeholder cards and rows shaped like the real content
- Cold start: if a request takes more than 3 seconds, show "Waking up the server. This can take up to a minute." (Render's free tier sleeps when idle.)
- Network or server error: a short message and a Retry button

## Code structure
```
src/
  api.js            # fetch wrapper: base URL, token header, JSON, 401 handling, slow-request notice
  auth/             # login state shared across the app (React context)
  pages/            # LoginPage, RegisterPage, ApplicationsPage
  components/       # form, rows, status select, confirm delete, notices
```

## Later: add from a job link
Paste a job posting URL and get company, role, and URL filled in as an "Applied" draft. Backend endpoint (`POST /applications/parse`) that fetches the page server-side, reads schema.org `JobPosting` data first, falls back to an LLM, and otherwise returns just the URL. Needs SSRF protection: http/https only, block private and internal IPs (including after redirects), timeouts, size limits, and rate limiting.

## Not in this version
Stats dashboard, password reset, pagination UI (loads up to 200 applications), frontend tests, TypeScript, dark mode (the app uses a white, light-only design).

## Build order
1. `api.js`, auth context, login and register pages
2. Applications list, status filters with counts, company search
3. Add, edit, delete, and the status dropdown
4. Empty, loading, cold-start and error states, plus the phone layout

## Manual test checklist
Register, log out, log in, add three applications, change a status from the dropdown, filter by status, search by company, edit one, delete one, refresh (still logged in?), open on a phone, and log in as a second account (can't see the first account's data).
