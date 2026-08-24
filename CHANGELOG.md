# Changelog

Session-by-session development history for the Phantasia Research Hub, oldest first. Sessions 1-12 predate the current dated-session convention and have no explicit branch names recorded in the original notes; from Session 13 onward, headings carry a month/year and most entries note the working branch.

Two systems mentioned in early sessions no longer exist in the current codebase: the original manual researcher-promotion system (Session 1, superseded within the same era) and the researcher invitation system (added Session 2, fully removed Session 32 — researchers are now created directly via the Users admin panel, see README.md's "Researcher Management" section).

---

## Session 1: Git Repository Setup & Security

### Environment Variables
- Implemented secure configuration with python-decouple
- `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` moved to `.env` file
- `.env.example` template for other developers
- All secrets excluded from version control

### Git Initialization
- Repository set up with proper `.gitignore`
- 77 files committed in initial commit
- Proper exclusions for sensitive data, media files, and virtual environment

### Survey Model Refactoring & Advanced Features
- **Question model restructure**: changed from many-to-many to one-to-many — questions now belong to a single survey via direct ForeignKey; removed the `SurveyQuestion` intermediary model; participant responses remain linked by question ID (unchanged)
- **Question ordering improvements**: auto-increment ordering (leave at 0), manual ordering support, `normalize_question_order()` method on Survey, admin action "Normalize question order"; removed unique constraint to allow flexible reordering without data loss
- **Question randomization**: seeded randomization (`randomize_questions` BooleanField on Survey) using participant ID as seed — consistent per-participant order, reduces order effects/acquiescence bias, admin still sees database order
- **Reverse coding**: `reverse_coded` BooleanField on Question; inverts scale values before storing (`stored = (max + min) - selected`), invisible to participants, test mode shows both values with **[RC]** indicator
- **Data integrity protection**: removed question deletion logic from `save()` — responses always linked by question ID so reordering never loses participant data

### Initial Researcher Management System (superseded)
- Automatic staff status granting for researchers, a `Researchers` Django group with granular permissions, signals to manage permissions automatically, `setup_researcher_permissions` management command
- Replaced by the invitation-based system below (Session 2-era), and the invitation system was itself fully removed in Session 32 — none of this exists in the current codebase; kept here as history only

### Participant Registration with Consent
- Custom signup form with required consent checkbox
- Consent form text storage on the User model
- Responsive signup and login templates
- django-allauth configured to use the custom form
- Home page with role-based navigation

### Survey Model Evolution
- Question model changed from multiple question types down to Likert-scale-only (richer types were reintroduced later, Sessions 9-12)
- Scale settings moved to Survey level (applies to all questions in a survey)
- JSON field added for custom scale labels
- Question model simplified to text + required flag only

---

## Session 2: Lab.js Task Integration

### Complete Task System Implementation
- Zip file upload with automatic unpacking and validation
- Task management interface for researchers (`/tasks/`)
- Task preview and execution views with CORS-free implementation
- Instructions screen with task metadata (domain, time limit, etc.)
- Integrated into participant dashboard alongside surveys

### Task Completion Flow (Template Approach)
- Researchers add a completion screen to lab.js exports
- Automatic `${TASK_ID}` placeholder replacement during upload
- Completion confirmation page at `/tasks/<id>/complete/`
- Status tracking: started → in_progress → completed
- Time calculation from task start to completion
- Preserves lab.js CSV download functionality

### Enhanced Admin Interface
- Upload status indicators (✓ Unpacked / ⧗ Pending)
- Preview links for quick testing
- Inline help text with upload instructions
- Link to full integration documentation

### Documentation
- Created `LABJS_INTEGRATION.md` (now `docs/LABJS_INTEGRATION.md`) with step-by-step guide, copy-paste code snippets, troubleshooting, and auto-redirect/manual-button examples

### Data Protection Extended to Tasks
- Researchers automatically redirected to preview mode
- `TaskSubmission` model tracks participant progress
- Role-based access control consistent with surveys

### Migration
- Added `task_slug`, `task_directory` fields; renamed `task_file` to `zip_file`

### Researcher Invitation System (removed in Session 32)
Added shortly after the initial researcher management system above:
- `ResearcherInvitation` model with unique UUID tokens, expiration tracking, and audit trail
- `InviteResearcherForm` (send invitations, configurable 1-30 day expiration) and `ResearcherSignupForm` (invitation-based registration)
- Custom admin interface with an "Invite New Researcher" button and invitation management
- Invitation acceptance view with automatic researcher account creation
- Email notifications sent automatically with invitation links (console backend in development)
- Resend-invitation action for pending invitations
- Replaced the initial manual-promotion system: removed `make_researcher`/`remove_researcher_status` bulk actions, made `is_researcher` read-only except for superusers

**Note**: this entire system — model, views, forms, admin — was removed in Session 32 in favour of creating researchers directly via the Users admin panel. Kept here as historical record only; nothing described in this subsection exists in the current codebase.

### Data Protection & Admin Improvements
- **Researcher data isolation**: researchers redirected to test mode when accessing participant survey URLs; dashboard access restricted to participants only
- **Editable consent forms**: `ConsentForm` model added, with versioning/history tracking and active/inactive status management
- **Admin panel cleanup**: removed django-allauth's `EmailAddress` model from admin to reduce confusion
- **Custom admin branding**: site header/title/index title configured in `research_platform/urls.py`

### Survey Views & Participant Dashboard
- `survey_take` (participant completion with full validation), `survey_preview` (researcher preview), `survey_list` (researcher-only management) views implemented
- **Test mode**: researchers can test surveys without saving to the database — validates responses, displays submitted data in a formatted table
- **Likert scale customization**: scale settings moved to Survey level, shared across all its questions, with custom labels displayed under radio buttons
- **Participant dashboard** created at `/dashboard/` — available/completed surveys, metadata, direct links to start/update responses
- **Role-based access control**: survey management restricted to researchers, participants redirected to dashboard
- Templates created: `survey_list.html`, `survey_detail.html`, `participant_dashboard.html`

---

## Session 3: Lab.js Task Testing & Refinement

- **Tested task completion flow** end-to-end: execution, `${TASK_ID}` placeholder replacement, redirect to completion confirmation, and status tracking all verified working (see also the "Testing Completed" note under Lab.js Task Integration)
- **Simplified integration approach**: removed complex HTML/button handlers that caused timing issues, switched to a simple redirect-only completion screen (empty screen + timeout + redirect script), updated `LABJS_INTEGRATION.md` accordingly
- **Identified the data submission issue** resolved in Session 6: lab.js's Download plugin wasn't triggering reliably, so task data wasn't reaching the database (only completion status was) — the `/tasks/<id>/submit/` endpoint existed but needed proper integration, and researcher test mode was needed for data preview

---

## Session 4: Lab.js Data Capture Implementation

- **Implemented data extraction**: identified `this.parent.options.datastore.data` as the correct method to capture clean structured trial data, avoiding metadata/internal state from `exportJson()`; logged to browser console for verification
- **Created a working completion-screen snippet**: captured clean trial-by-trial data into `window.labJsTaskData` ahead of the POST implementation landing in Session 6
- **Cleaned up the test environment**: cleared `media/lab_tasks/unpacked/` and `media/lab_tasks/zips/` of orphaned task files

---

## Session 5: Bug Fixes & Admin Improvements

- **Fixed a file cleanup bug**: bulk delete from the admin list view wasn't cleaning up task files — added `delete_queryset()` to `LabTaskAdmin` for bulk deletes and `delete_model()` for single deletes; zip files and unpacked directories are now properly removed in all deletion scenarios
- **Researcher dropdown filter**: added `SurveyAdminForm`/`LabTaskAdminForm` so the researcher dropdown in Survey/LabTask admin only shows `is_staff=True` users, hiding participants

---

## Session 6: Lab.js Data Submission & Filtering

Full data submission pipeline implemented and tested end-to-end:
- Diagnosed a race condition — `after:end` was firing after the screen-timeout redirect
- Fixed by moving the script to the **"Run"** event instead, which fires immediately when the End screen appears
- Replaced synchronous XHR (deprecated) with `fetch` + `.then()` chaining; redirect happens inside the `.then()` callback so the POST completes first
- Added `get_trial_data()` to `TaskSubmission` — filters the raw lab.js datastore (~146 entries) down to meaningful trial rows (~36) via `sender == 'Trial'` and `ended_on == 'response'`; raw data always preserved in `results_data`
- Rewrote `LABJS_INTEGRATION.md` (now `docs/LABJS_INTEGRATION.md`) with the correct, tested instructions — script placement, no End-screen timeout, `getCookie` helper, console logging, testing/troubleshooting guide. The working completion-screen snippet from this session lives there, not duplicated here.

---

## Session 7: Admin Trial Data Display, Test Submissions & Timing Fix

### Trial Data Filtering Improvements
- Generalised `get_trial_data()` from `sender=='Trial' AND ended_on=='response'` to `ended_on=='response'` only, so it works across lab.js task designs regardless of screen naming
- Added `trial_sender_filter` to `LabTask` — optional comma-separated sender names to narrow filtering per task; blank by default
- Investigated the Flanker task in detail: 146 raw rows filtered to 37 response rows (36 Trial + 1 accepted-as-noise Instructions row)

### Enhanced TaskSubmission Admin
- Detail view shows `get_trial_data()` as a readable HTML table with dynamic columns (common fields first, then task-specific ones; internal lab.js metadata hidden)
- Colour-coded `correct` field (green/red), trial-count column in list view, fieldsets split into Submission Info / Trial Data / Raw Data (collapsible JSON)

### Researcher Test Submissions
- Removed the researcher redirect — researchers/staff now go through the full submission pipeline instead of a data-less preview
- `is_test` flag added to `TaskSubmission`, auto-set for researcher/staff submissions; orange "TEST" badge in admin, filterable, with a test-mode notice on the completion page
- Removed stale CSV-download references left over from an earlier design

### Timing Fix
- `time_spent_seconds` now sourced from lab.js's own `duration` field on the `Task` sender row (ms) instead of server-side `started_at`/`completed_at` diffs — fixes a race condition that recorded 0 seconds for researcher test submissions, and is more accurate generally (server diffs included instructions/completion page overhead). Fallback to the server-side diff retained for tasks without a `Task` sender row; existing submissions backfilled.

---

## Session 8: Per-question Likert Scales

- New `LikertScale` model — named, reusable scales defined per survey (e.g. "Agreement 1–5", "Vividness 0–10"), authored once as an inline on the Survey admin page with JSON labels
- Each question can select which scale to use; falls back to the survey-level default if none selected
- Scale resolution chain: question's assigned scale → survey default `min_value`/`max_value`/`scale_labels`
- Helper methods on `Question`: `effective_min()`, `effective_max()`, `get_scale_options()`, `apply_reverse_coding()`
- Views/templates updated to use per-question scale options; fixed pre-existing bugs in `survey_take` (scale variable reference, response variable name)

This kicked off an incremental survey redesign — each new question type/feature (Sessions 9-12) was built, tested, and committed before the next was started.

---

## Session 9: Multiple Choice, Free Text & Question Groups

### Multiple choice & free text questions
- Added `question_type` to Question: `likert`, `multiple_choice_single`, `multiple_choice_multi`, `free_text`
- Multiple Choice (Select One) validated to exactly one answer; Multiple Choice (Select Multiple) allows one or more
- Options stored as JSON on `Question.options` (e.g. `{"1": "Option A", "2": "Option B"}`); disabled-option array syntax added later in Session 12
- Checkbox-based UI, clear "(Select one)"/"(Select one or more)" instructions, responses stored as JSON arrays
- Free text: textarea UI with configurable rows, plain-text storage, required-field validation
- Binary yes/no questions can be built as either a 2-value Likert scale or 2-option multiple choice

### Question groups & subscales
- New `QuestionGroup` model, dual-purpose for visual grouping and hidden subscales: `group_code` (auto-generated from order), `title`, `show_title` (visible section header vs. hidden subscale), `order`
- **Visible groups** (`show_title=True`): section headers with instructions, questions bundled into a single matrix card
- **Hidden subscales** (`show_title=False`): organisational grouping for scoring only — questions render as individual cards interleaved by `order`, with no visual hint of the grouping to participants
- Questions in groups get composite identifiers (`{group_code}_{question_number}`, e.g. "1_a", "1_b"); ungrouped questions use simple numbers
- Helper: `question.get_question_identifier()`; admin QuestionGroup inline with `show_title` checkbox; `organize_questions_by_group()` structures questions for rendering

---

## Session 10: Survey Management UX & Conditional Logic Design

### Survey Management Improvements
- Unified survey management styling with the task management page (same cards/buttons/badges)
- Simplified test workflow: removed the separate "Test Mode" button in favour of a single "Preview & Test" (matching tasks)
- Test response summary table showing question IDs, selected/stored values, labels, and reverse-coding indicators after a test submission
- Better metadata display (question count, scale range, randomization status, researcher, created date); improved "No Surveys Yet" empty state

### Design evolution for conditional logic
Worked through three designs before settling on the one shipped in Session 11-12:
1. Group-based trigger logic (a trigger question controls all questions in its group)
2. Making `QuestionGroup` itself a question — rejected, would fragment data across two response tables
3. **Settled on**: N-questions logic — any question can control the next N questions, no group dependency

---

## Session 11: Conditional Logic Fix, Scale Factor, Question IDs & CSV Export

### Conditional show/hide bug fixed
- Root cause: backend validation was checking all required questions, including ones disabled by conditional logic
- Fix: `survey_preview` and `survey_take` now build a `disabled_questions` set from trigger values and skip validation for those; removed leftover debug `console.log` statements

### Scale factor
- `scale_factor` IntegerField on Question (default 1, min 1) — multiplies Likert answers before storing (e.g. factor of 2 converts a 1-5 scale to 2-10), applied after reverse coding
- Shown as a "Factor" column (×2, ×3, ...) in the test response table

### Improved question ID system
- Group codes auto-generated from group `order` (1, 2, 3...); grouped questions get alphabetic identifiers (1_a, 1_b, 2_a, 2_b); ungrouped questions get simple numbers (5, 10, no "Q" prefix)
- `group_code` read-only/hidden in admin; `question_number` hidden but still used internally

### Admin UI improvements
- Preview links added to Survey and LabTask list/detail views
- `question_number` and QuestionGroup `description` hidden from admin for a cleaner interface

### CSV export for survey responses
- New admin action "Export responses as CSV (with full question metadata)" — one row per response with participant info, survey info, full question metadata (id, text, type, order, group), question settings (required, reverse_coded, scale_factor, range, scale name), and response data (answer, is_test, timestamps)
- Downloads as `survey_responses_{survey-name}_{date}.csv`

---

## Session 12: Survey Redesign Complete — Dropdowns, Auto-fill, Disabled Options

The incremental survey redesign (started Session 8) reached feature-complete here.

### Hidden subscales made fully invisible
- Groups with `show_title=False` are treated as ungrouped for rendering — each question gets its own card, interleaved by `order`, no visual hint of the grouping (scoring still reads `question.group_id` directly, unaffected)

### Auto-fill disabled conditional questions
- Questions disabled by conditional logic are now auto-filled instead of skipped: Likert questions get the scale minimum, non-Likert get "NULL"
- Test response table shows an orange `[Auto]` indicator with a light-yellow row background
- Applies to both `survey_preview` and `survey_take`

### NULL recording for optional questions
- Optional (non-required) questions left blank now record "NULL" instead of being skipped, across all question types — every participant has a response recorded for every question

### Disabled multiple choice options
- Options can be marked visible-but-unselectable via array syntax: `{"1": "Option A", "2": ["Option B (disabled)"], "3": "Option C"}`
- Rendered at 40% opacity with disabled checkboxes; validation filters out disabled options if somehow submitted; `get_enabled_option_keys()` helper added

### Dropdown question types
- Added `dropdown_year` (last 100 years), `dropdown_month` (stores 1-12, displays names), `dropdown_country` (195+ countries alphabetically) — later consolidated into a single `dropdown_year_month` type in Session 32
- Question text made optional (`blank=True`) to support self-explanatory dropdown questions

---
## Session 13: Admin Dashboard Improvements (March 2026)

### Domain-Based Filtering
Added domain filtering to survey and task management pages for better organization:
- Filter dropdown on survey list (`/surveys/`) and task list (`/tasks/`) pages
- Filter by specific domain or "Uncategorized" (items with no domain)
- "Clear Filter" link appears when filter is active
- Filter state persists via URL query parameters (`?domain=X`)
- **Implementation**: Updated `survey_list()` and `task_list()` views in `surveys/views.py` and `tasks/views.py`

### Download Logging & Audit Trail
Implemented comprehensive logging of all CSV data exports for compliance:
- **Survey exports**: Logs created when researchers export survey responses via admin action
- **Task exports**: Logs created for all 4 export methods (single trial/raw, bulk trial/raw)
- **Log data**: Researcher, download type, file format, survey/task ID, participant count, timestamp
- **Admin enhancements**:
  - Added `object_title` column showing survey/task name (or "deleted" if removed)
  - All fields readonly (audit log - no manual editing)
  - Prevented manual creation of log entries
  - Only superusers can delete logs (preserve audit trail)
  - Custom `ResearcherFilter` shows only staff/researchers (excludes participants)
- **Access**: Admin → Core → Data Download Logs

### Participant Progress Tracking
Added real-time progress tracking without redundant database tables:
- **Removed unused `Progress` model** - redundant with existing `ParticipantResponse` and `TaskSubmission` tracking
- **Added methods to `User` model**:
  - `get_survey_progress()` - Returns (completed, total, percentage)
  - `get_task_progress()` - Returns (completed, total, percentage)
  - `get_overall_progress()` - Returns combined percentage
- **Enhanced User admin** with new columns:
  - Survey Progress: "3/5 (60%)"
  - Task Progress: "1/2 (50%)"
  - Overall Progress: "✓ 100%" / "⧗ 55%" / "✗ 0%" (color-coded)
- Progress calculated from active surveys/tasks only, excludes test responses
- Real-time accuracy - always reflects current completion state

### Other Improvements
- Created test consent form for development/testing
- Cleaned up unused models to reduce confusion

**Branch**: `feature-admin-dashboard`

---

## Session 14: Priority Surveys and Tasks (April 2026)

### Priority Flagging System
Added ability to mark surveys and tasks as priority for better workflow management:
- **New `is_priority` field** added to both `Survey` and `LabTask` models
- **Updated model ordering**: Priority items appear first, then ordered by creation date
  - `Meta.ordering = ['-is_priority', '-created_at']`
- **Admin interface updates**:
  - Priority checkbox in survey and task edit forms
  - Priority column in list views
  - Priority filter in admin list filters
- **Visual indicators**: Red "Priority" badge in survey and task management pages
  - Appears next to Active/Inactive badge
  - Light red background (`#ffe5e5`) with dark red text (`#c0392b`) and border
- **Automatic ordering**: Priority items automatically appear at top of:
  - Survey management list (`/surveys/`)
  - Task management list (`/tasks/`)
  - Participant dashboard (`/dashboard/`)
- **Implementation**:
  - Models: `surveys/models.py`, `tasks/models.py`
  - Admin: `surveys/admin.py`, `tasks/admin.py`
  - Views: `dashboard/views.py`
  - Templates: `templates/surveys/survey_list.html`, `templates/tasks/task_list.html`
  - Migrations: `surveys/migrations/0021_*`, `tasks/migrations/0005_*`

**Branch**: `feature-admin-dashboard`

---

## Session 15: Messaging System Backend (April 2026)

### Message Model and Admin Interface
Implemented the backend infrastructure for researcher-to-participant messaging:
- **New `Message` model** in `core/models.py` with fields:
  - `subject` - Message subject line
  - `sender_name` - Display name (e.g., "Dr Bérengère Digard")
  - `body` - Message content (supports basic HTML: `<p>`, `<strong>`, `<em>`, `<a>`, `<h4>`, `<ul>`, `<li>`)
  - `created_by` - Automatically set to researcher creating the message
  - `is_published` - Toggle to show/hide from participants
  - `read_by` - ManyToManyField tracking which participants have read the message
  - `created_at` / `updated_at` - Automatic timestamps
- **Admin interface** for message management:
  - Clean form with organized fieldsets
  - List view: subject, sender, published status, creator, date
  - Filters: published status, creation date
  - Search: subject, sender name, body content
  - Auto-sets `created_by` to logged-in researcher
- **Read/unread tracking**:
  - Simple ManyToMany approach (no timestamp needed)
  - Supports "mark as read" and "mark all as read" functionality
  - Ready for unread badge counts when frontend is implemented
- **Migrations**: `core/migrations/0003_message.py`, `core/migrations/0004_message_read_by.py`
- **Mockup reference**: `mockups/messages.html` - design for future participant-facing page

**Note**: Participant-facing messages view will be implemented later with the design system.

**Branch**: `feature-messages`

---

## Session 16: Survey Bug Fixes (May 2026)

### Question Group Bug Fixes
Fixed two critical bugs affecting question groups in surveys:

#### 1. Question ID Generation Bug
**Problem**: Questions in groups were getting incorrect `question_id` values stored in the database (e.g., `1_a`, `3_b` instead of `3_a`, `3_b`).

**Root cause**: The `save()` method in `Question` model was calling `get_question_identifier()` to generate `question_id`, but the position calculation was based on existing database queries that didn't account for the current save operation properly.

**Fix** (`surveys/models.py`):
- Modified `Question.save()` to directly generate `question_id` inline instead of calling `get_question_identifier()`
- For grouped questions: `question_id = f"{self.group.group_code}_{self.question_number}"`
- For ungrouped questions: `question_id = str(self.order)`
- Position calculation now correctly counts questions in the group that come before the current question based on order

**Impact**: New questions now get correct IDs on creation. Preview mode (which uses `get_question_identifier()` on-the-fly) was already showing correct values, but stored database values were wrong.

#### 2. Question Rendering Order Bug
**Problem**: Question groups were rendering before ungrouped questions, regardless of their order values (e.g., questions at order 1-2 appeared after a group at order 3).

**Root cause**: The `organize_questions_by_group()` helper function in `surveys/views.py` was adding all ungrouped questions with a sort key of `float('inf')`, placing them at the end after all groups.

**Fix** (`surveys/views.py`):
- Rewrote `organize_questions_by_group()` to interleave groups and ungrouped questions based on their order values
- Groups use the minimum order of their questions as the sort key
- Ungrouped questions use `order - 0.5` as the sort key (ensures they appear before groups at the same order)
- All items are sorted together, maintaining proper order throughout the survey

**Impact**: Questions and groups now render in the correct order based on their order field, matching researcher expectations.

**Testing**: Both fixes verified with SWSQ survey containing 2 ungrouped questions (order 1-2) and 1 question group with 2 questions (order 3-4).

---

## Session 17: Design System Port (May 2026)

### CSS Design System Migration
Ported the mockup design system into Django templates, replacing all inline styles with a shared stylesheet and consistent component classes.

#### Design System (`static/css/styles.css`)
- Copied `mockups/styles.css` verbatim as the shared stylesheet
- Design tokens: `--bg-page`, `--bg-accent: #d8f24b` (lime-green), `--ink`, `--ink-muted`, `--ink-subtle`, `--rule`, `--font-display: "Quattrocento"`, `--font-body: "Helvetica"`, `--topbar-h: 72px`, `--page-padding-x: 44px`
- Light/dark theme via `data-theme="dark"` on `<html>`
- Components: topbar (sticky + static variants), footer, `.btn--primary`/`.btn--outline`, `.avatar`, `.section-label`, `.view-switch`, `.crest`

#### `templates/base.html` (complete rewrite)
- Quattrocento font loaded from Google Fonts
- Topbar with sticky scroll-shadow behaviour (JS IIFE)
- Authenticated state: Messages button (with live unread badge) + avatar initials; unauthenticated: Login + Sign up buttons
- Extensible blocks: `html_attrs`, `viewport`, `topbar_class`, `topbar_nav`, `extra_head`, `body`, `extra_js`

#### `templates/home.html` (complete rewrite)
- Dark theme (`data-theme="dark"`), static topbar
- Hero section with full-viewport background image
- "Join the study" two-column section with image and copy
- "About" section with research goals and researcher profiles
- Hero images copied from `mockups/images/` to `static/images/`

#### `templates/account/signup.html` (complete rewrite)
- Two-column grid layout: left info panel, right signup form
- Left column: switchable "Important Information" / "Consent Form" panels via `.view-switch`
  - Important Information: verbatim text from mockup
  - Consent Form: pulls live content from database via `{% get_active_consent_form %}`
  - Scrolls internally (`position: absolute; inset: 0`) to match the form height
- Right column: Name, Email, Password, Confirm password fields (no placeholders); single consent checkbox; submit disabled until consent ticked
- Layout: form drives row height (`align-self: start`), left panel stretches to match

#### `templates/account/login.html` (complete rewrite)
- Same two-column grid structure as signup
- Left column: brief brand/welcome copy, scrollable to match form height
- Right column: Email, Password fields + Remember me checkbox + Log in button + forgot password link
- Consistent field styles, custom checkbox, lime-green submit button

#### `accounts/forms.py`
- Added `name` field to `ParticipantSignupForm` (optional, splits into `first_name`/`last_name` on save)

**Branch**: `feature-design-port`

---

## Session 18: Participant Dashboard & Survey Management Port (May 2026)

### Participant Dashboard (`templates/dashboard/participant_dashboard.html`)
Complete rewrite matching the `mockups/index.html` design:
- Two-column CSS grid (360px sidebar + 1fr main) with column separator rule
- Topbar placed inside the grid (suppresses base.html header/footer blocks)
- **Sidebar INFO panel**: static blurb about the Hub and how to navigate it
- **Sidebar DOMAINS panel**: lists all `Domain` objects from the database with uppercase links
- **Main area**: "QUESTIONNAIRES & TASKS" section label + completed/total counter
- Unified task cards for surveys and lab tasks — available items first, completed items below a "COMPLETED" divider at reduced opacity
- Task card variants: blue indicator dot (default), red/warn dot (priority), hollow dot (completed)
- Empty state when no surveys or tasks are assigned
- JS sidebar panel switcher (INFO ↔ DOMAINS)

### Survey Management (`templates/surveys/survey_list.html`)
Complete rewrite matching the dashboard layout and design language:
- Same two-column grid as the participant dashboard for visual consistency
- **Sidebar INFO panel**: researcher-facing instructions
- **Sidebar DOMAINS panel**: domain links replace the old dropdown filter; active domain gets bold/italic/filled-dot treatment; auto-opens to Domains panel when a filter is active
- **Survey cards**: title + description + action buttons (Preview & Test, Edit) on the left; status pills + meta info (domain, question count, scale) in the narrow right column
- Priority pill uses `var(--warn)` red — consistent with the priority indicator dot on the participant dashboard
- "New Survey" button in the section header row
- Empty state with create prompt

### Navigation & UX fixes
- **Login redirect**: `LOGIN_REDIRECT_URL` changed from `/` to `/dashboard/` — participants land on the dashboard after signing in (researchers are redirected onward to `/surveys/` by the dashboard view)
- **Logout button**: added to all topbars (base, dashboard, survey list) using a POST form to `account_logout`
- **Home page topbar**: auth-aware — shows "Dashboard · Log out" when signed in, "Login · Sign up" when not
- **Flash messages**: success alerts (login/logout confirmations) suppressed — the button state already communicates this; errors and warnings still shown
- **Researcher topbar**: Messages button hidden for staff/researchers (participants keep it); avatar links to `/admin/` for staff/researchers, `#` placeholder for participants
- **base.html**: added `{% block header %}`, `{% block flash_messages %}`, `{% block footer %}` wrappers so grid-layout pages (dashboard, survey list) can suppress them and own their full layout
- **`static/css/styles.css`**: added `.alert` / `.alert--success/error/warning/info` styles for Django flash messages

**Branch**: `feature-design-port`

---

## Session 19: Survey Detail Design Port (June 2026)

### `templates/surveys/survey_detail.html` (complete rewrite)
Ported the survey detail/take page to the design system, matching the two-column grid layout used by the dashboard and survey list pages.

#### Layout
- Two-column CSS grid (360px sidebar + 1fr main), identical skeleton to dashboard/survey list
- Topbar placed inside the grid (suppresses base.html header/footer blocks)
- Sticky progress readout (answered / total) below topbar
- Topbar progress fill bar (2px blue line on bottom edge, grows as questions are answered)
- Sidebar INFO panel: survey description, domain, "How to answer" bullet list

#### Question rendering
- **Grouped Likert questions**: rendered as a single matrix card — group number as `q-num`, optional group title as `q-title`, radio buttons in a `<table class="matrix">` with `table-layout: fixed` and 44% first column for question stems
- **Standalone (ungrouped) Likert questions**: rendered as `<table class="matrix matrix--standalone">` with no question-text column; `table-layout: fixed` retained so columns stay evenly distributed across all scale sizes
- **Multiple choice** (single and multi): `.choice-list` fieldset with `.choice` rows
- **Free text**: `.q-textarea`
- **Dropdown** (year, month, country): `.q-select` with custom SVG arrow
- Preview/test mode banner, existing-responses notice, test response table (with RC/Auto badges) all retained and restyled

#### Banners and modals
- Preview mode banner (warn colour) and existing-responses notice (blue)
- Completion modal: shown server-side via `submitted=True` context var; `is-open` class triggers CSS transition; Escape + backdrop click dismiss it

#### JS
- Progress counter scans `[data-question-id]` elements (matrix rows for grouped, cards for ungrouped), excluding `.conditional-disabled` cards
- Conditional disable: greys out next N cards when trigger answer doesn't match `trigger_value` (behaviour unchanged from pre-port)
- Topbar scroll shadow
- Modal open/close

#### Bug fixes during port
- `{% url 'home' %}` → `{% url 'core:home' %}` in template; `redirect('core:home')` in `surveys/views.py`
- Multi-line `{# #}` Django comment rendered as literal text — collapsed to single-line comments
- Multi-line `{% if %}` blocks inside HTML opening tags — collapsed to single lines
- `survey_take` success path changed from redirect to re-render with `submitted=True` so the completion modal fires
- Standalone Likert offset: removed sr-only first column (was claiming 44% width under `table-layout: fixed`)
- `.matrix--standalone th:first-child` overrides inherited `width: 44%` / `text-align: left`

**Branch**: `feature-design-port`

---

## Session 20: Conditional Branch UI & Task List Port (June 2026)

### Conditional question rendering (survey detail)
Replaced the grey-out (`conditional-disabled`) pattern with the mockup's branch/gate pattern — no data model changes required.

#### `surveys/views.py` — `organize_questions_by_group`
- Before splitting into groups/ungrouped, scans all ungrouped trigger questions and attaches their N controlled questions as `q.branch_questions`
- Branch children are added to `branch_question_ids` and removed from the top-level rendering list so they don't appear as standalone cards
- Every question gets `q.branch_questions = []` so the template check is always safe (grouped questions get an empty list)

#### `templates/surveys/survey_detail.html`
- **CSS**: replaced `.conditional-disabled` with `.branch` — a collapsible div with a left vertical rule (`var(--ink)`), collapsed by default (`max-height: 0; opacity: 0`), slides open with `.is-open`
- **Gate questions**: trigger Likert questions (those with `branch_questions`) now render as `.pill-gate` — a row of pill-shaped radio buttons using the scale label text. Works for any trigger value, not just yes/no, since the JS checks against `data-trigger-value`
- **Branch markup**: `.branch` div lives inside the trigger's `.q-card`, loops over `question.branch_questions`, renders each with the full question-type switch (Likert, multiple choice, free text, dropdowns). Branch question text uses `q-title` at 17px
- **JS — gate script**: replaces the N-card grey-out; listens on `[data-gate]` elements, toggles `is-open` on the target `[data-branch]`, clears all inputs on retract
- **JS — progress counter**: upgraded to the mockup's three-state model — `data-conditional` questions only count toward progress while their `[data-branch]` ancestor has `is-open`, so a "No" gate answer can still reach 100%

### `templates/tasks/task_list.html` (complete rewrite)
Ported the researcher task management page to the design system, matching `survey_list.html` exactly.
- Two-column grid (360px sidebar + 1fr main), INFO/DOMAINS sidebar panels with domain filter
- Task cards: title, description, Preview + Edit buttons on the left; Active/Inactive/Priority pills + domain + time limit + date on the right
- Meta column stretches to fill card height, contents centred
- Sidebar auto-opens to Domains panel when a domain filter is active
- Empty state with upload prompt

### Card meta column polish (survey list + task list)
- `align-items: stretch` on both card grids so the meta column fills the full card height
- `align-items: center` on the meta column so its contents sit centred
- Pills: `line-height: 1`, `vertical-align: middle`, and asymmetric padding (`4px 10px 2px`) to correct the uppercase text optical baseline issue

**Branch**: `feature-design-port`

---

## Session 21: Task Templates & base.html Block Fix (June 2026)

### `{% block content %}` added to `base.html`
- Added `{% block content %}{% endblock %}` inside `{% block body %}` in `base.html`
- Simple pages (no custom grid) can now use `{% block content %}` and get the default topbar/footer for free
- Full-page grid templates that override `{% block body %}` are unaffected

### `templates/tasks/task_start.html` (complete rewrite)
- Ported to design system using `{% block content %}`
- Centered card layout (`max-width: 680px`, `background: var(--bg-card)`, bordered)
- Metadata strip (domain, time limit, type) with label/value pairs, separated from heading by a bottom rule
- Instructions in a plain bordered card
- Preview mode uses `.alert--info` strip; no redundant "ready to begin" note
- Back + Start task action buttons using `.btn--outline` / `.btn--primary`

### `templates/tasks/task_complete.html` (complete rewrite)
- Ported to design system using `{% block content %}`
- Centered single-column layout
- Lime-green circle checkmark mark using `var(--bg-accent)`
- Summary table (results recorded, participation time, started timestamp) in a bordered card
- Confirm & return button or dashboard link depending on completion status
- Test submission uses `.alert--warning` strip

**Branch**: `feature-design-port`

---

## Session 22: Participant Messages Page (June 2026)

### `templates/core/messages.html` (new)
Participant-facing messages page ported from `mockups/messages.html`:
- `<details>`/`<summary>` accordion — each message expands in place, lifting onto a card
- `.is-unread` status dot (filled blue for unread, hollow for read)
- Section header row: total/unread count + "Mark all as read" link
- Empty state when no published messages exist

### Messaging views (`core/views.py`)
- `messages_view`: fetches published messages, annotates each with read/unread state per user
- `mark_read`: POST `/messages/<id>/mark-read/` — adds user to `read_by`, returns `{unread_count}` JSON
- `mark_all_read`: POST `/messages/mark-all-read/` — marks all published messages read for user

### Context processor (`core/context_processors.py`)
- `unread_message_count` injected into every template — powers the topbar badge on all pages
- Registered in `settings.py` `TEMPLATES.OPTIONS.context_processors`

### Topbar badge
- `base.html`, `participant_dashboard.html`, and `survey_detail.html` all show a live unread badge on the Messages button, sourced from the context processor

**Branch**: `feature-design-port`

---

## Session 23: Account Page & Password Flow (June 2026)

### Participant account page (`/accounts/account/`)
New page for participants to view their profile and consent record:
- **Profile panel**: account details (name, email, participant ID, joined date, last active) + Change password action card
- **Consent panel**: renders the active `ConsentForm` content as prose, matching what participants saw at signup; consent metadata (date signed, version); withdrawal section with a disabled "Delete my account" placeholder
- **Participant ID**: derived as `PRH-{year}-{user.id:04d}` (e.g. `PRH-2026-0147`)
- Panel switching via `.view-switch` JS (Profile / Consent tabs)
- Avatar button in topbar and dashboard now links to `/accounts/account/` for participants

### Password change page (`/accounts/password/change/`)
Styled override of allauth's default password change page:
- Same two-column layout as login/signup
- Three fields: current password, new password, confirm new password
- "Forgot your password?" escape link to reset flow
- Redirects back to account page on success (via custom `AccountAdapter`)

### Password reset flow (4 pages)
Styled overrides for the full allauth password reset flow:
- `password_reset.html` — email input, "Send reset link"
- `password_reset_done.html` — confirmation, check your inbox
- `password_reset_from_key.html` — set new password form; handles expired/invalid token inline
- `password_reset_from_key_done.html` — success, "Log in" link

### `accounts/adapter.py`
Custom allauth adapter (`AccountAdapter`) overrides `get_password_change_redirect_url` to send users back to the account page instead of allauth's default (the change password page itself).

**Branch**: `feature-design-port`

---

## Session 24: Results Panel & Survey Scoring (June 2026)

### Survey result metadata (models + migrations)
Extended `Survey` and `QuestionGroup` models to support participant-facing result display:
- **`Survey.result_min` / `result_max`** (FloatField, nullable) — the display range for charting scores
- **`Survey.result_aggregation`** (`'mean'` or `'sum'`, default `'mean'`) — how question scores are combined
- **`QuestionGroup.result_label`** (CharField, blank) — short chart axis label (e.g. "Scene 1"); falls back to `title` if blank
- **`QuestionGroup.result_min` / `result_max`** — optional per-group range override; falls back to survey-level via `effective_result_min` / `effective_result_max` properties
- **`QuestionGroup.display_label`** property — returns `result_label` or `title`
- **`Survey.has_subscales`** property — `True` if any group has a `result_label` set; drives spider vs scalar chart selection. No extra field needed — derived from data.
- Migrations: `0022_add_result_range_fields`, `0023_add_result_aggregation`
- Admin: "Results Display Range" fieldset on Survey; `result_label`, `result_min`, `result_max` columns added to QuestionGroup inline

### Scoring utility (`surveys/utils.py`)
New `get_survey_result(survey, participant)` and `get_all_results(participant)` functions:
- Silently skips surveys with no `result_min`/`result_max` configured
- **Single-score surveys** (`has_subscales=False`): aggregates all likert responses → `{score, min, max, chart_json}`
- **Multi-subscale surveys** (`has_subscales=True`): aggregates per group → `{subscales: [{label, score, min, max}], chart_json}`
- `chart_json` is a pre-serialised JSON string injected directly into the template for Chart.js

### Results panel on account page
- Added **Results** tab to the `view-switch` nav on `/accounts/account/`
- **Radar chart** (Chart.js) for multi-subscale surveys — axes from `result_label`, scale from `effective_result_min/max`, legend lists each subscale score
- **Spectrum chart** (SVG curve + CSS `--score-position` marker) for single-score surveys — marker positioned proportionally between `result_min` and `result_max`
- Chart.js loaded from CDN (`chart.js@4.4.0`)
- Radar charts resize correctly when the Results tab is activated
- Empty state shown if no chartable results exist yet

### Seed data management command (`surveys/management/commands/seed_results_data.py`)
Run with `python manage.py seed_results_data`:
- Configures result ranges and aggregation on existing surveys (VVIQ, ASSIST-Lite, SBSDS)
- Sets `result_label` on VVIQ's 4 question groups ("Relative / Friend", "Rising Sun", "Shop Front", "Country Scene")
- Creates a fictional **Big Five Personality Inventory (Test)** survey with 5 subscale groups (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism), 3 likert questions each
- Seeds realistic fake responses for `participant@test.com` across all likert surveys
- Fully idempotent — safe to run multiple times

**Branch**: `feature-results-panel`

---

## Session 25: Researcher Access, Survey UX & Bug Fixes (June 2026)

### Researcher account fixes
- **`is_staff` now visible in admin**: Added `is_staff` to the Permissions fieldset in `UserAdmin` so it can be set when creating or editing a user
- **`is_researcher` now editable at creation**: Added `is_researcher` to `add_fieldsets` so it can be ticked when adding a new user via the admin "Add user" form
- **Fixed `is_researcher` always read-only bug**: `readonly_fields = ['consent_text', 'is_researcher']` at class level was overriding `get_readonly_fields`, making the field read-only even for superusers. Moved `is_researcher` out of `readonly_fields` — it is now only added to the readonly list dynamically for non-superusers
- **Removed Researchers group**: The `Researchers` Django group was never used at runtime — all access checks use `is_researcher or is_staff` directly. Removed group management from `accounts/signals.py` and deleted the unused `setup_researcher_permissions` management command
- **Researcher login via main login**: Researchers must log in with an email address (allauth is configured for email-based auth). Accounts created manually in the admin without an email set cannot log in via the main login page

### Survey scoring fixes
- **Subscale surveys no longer require survey-level range**: `get_survey_result()` in `surveys/utils.py` now only bails out early if the survey has no subscales *and* no `result_min`/`result_max`. Subscale surveys show results as long as the question groups have their ranges configured
- **`get_survey_result` accepts `is_test` parameter**: Allows computing results from test (researcher preview) responses as well as real participant responses

### Preview result chart
When a researcher submits test data via the survey preview page, the computed result chart is now shown immediately below the response table — the same spectrum or radar chart that participants see on their account page. This lets researchers verify scoring, ranges, and aggregation visually before activating a survey.
- `surveys/views.py`: initialises `test_result = None`; after saving test responses calls `get_survey_result(survey, request.user, is_test=True)` and passes `test_result` to the template
- `survey_detail.html`: loads Chart.js (CDN) only in preview mode; renders spectrum or radar chart from `test_result` if present; uses the same HTML/JS patterns as the account page results panel

### Survey instructions field
- New `instructions` TextField (blank, optional) on the `Survey` model (`surveys/models.py`)
- Migration: `0024_add_survey_instructions`
- Admin: field added to the "Survey Information" fieldset in `surveys/admin.py`, displayed below `description`
- Template: if set, rendered as a paragraph above the standard "How to answer" bullet list in the survey sidebar (`survey_detail.html`)

### Markdown rendering
- Added `markdown` package (`pip install markdown`, added to `requirements.txt`)
- New template filter `render_markdown` in `core/templatetags/markdown_extras.py` — converts markdown to safe HTML using the `nl2br` extension so single line breaks are preserved
- Applied to `survey.description` and `survey.instructions` in `survey_detail.html`; both fields now support markdown formatting

### Dashboard description truncation
- Task and survey descriptions on the participant dashboard (`participant_dashboard.html`) were rendering in full; now truncated to 30 words with `truncatewords:30` to match the survey and task list pages

### Brand link → dashboard
- Topbar brand ("Phantasia Research Hub") now links to `/dashboard/` when the user is logged in, and to `/` (home) when not. Updated in `base.html` (conditional), and hardcoded to `/dashboard/` in `participant_dashboard.html`, `survey_list.html`, `task_list.html`, and `survey_detail.html`

### Conditional branch required-field bug fix
Branch (conditional follow-up) questions with `required` inputs were blocking form submission when the branch was closed — the browser's native validation fires on all inputs in the DOM regardless of visibility. Fix:
- On page load, any required input inside a `.branch` div gets `data-was-required="1"` stamped on it
- The gate/branch JS in `survey_detail.html` now toggles `required` on those inputs when the branch opens or closes
- Closed branches have `required` removed so submission is never blocked; reopened branches restore it

**Branch**: `feature-results-panel`

## Session 26: Hidden Subscale Question Rendering (June 2026)

### Subscale groups now render questions individually
Previously, all questions belonging to a `QuestionGroup` were bundled into a single matrix card regardless of whether the group title was visible. This meant that even hidden subscale groups (used purely for scoring) caused their questions to cluster visually on the survey form.

**Change** (`surveys/views.py` — `organize_questions_by_group`):
- Groups with `show_title=True` continue to render as a single matrix card (the group heading is shown, questions are bundled — correct for visible instruction-style groups)
- Groups with `show_title=False` now have their questions treated as if they were ungrouped — each question gets its own card and is interleaved with all other questions by its `order` value

This means researchers can assign questions to a subscale group for scoring purposes without that grouping being visible to participants. Participants see the questions in their configured order with no visual hint that certain questions belong together, which prevents them from detecting or gaming the subscale structure.

Scoring is unaffected — `get_survey_result()` reads `question.group_id` directly from the database, not from the rendered structure.

**Branch**: `feature-results-panel`

---

## Session 27: Participant Feedback Form (August 2026)

### Feedback survey system
Added a mid-study feedback form that appears inline on the participant account page after a configurable number of surveys have been completed.

#### Model changes (`surveys/models.py`)
- **`Survey.is_feedback`** (BooleanField, default `False`) — marks a survey as a feedback form; hides it from the participant dashboard and researcher survey list
- **`Survey.show_after_n_surveys`** (PositiveIntegerField, default `2`) — threshold of completed regular surveys before the form appears on the account page
- **`FeedbackSurvey` proxy model** — sits in `surveys/models.py` but is registered under **Core** in the admin, keeping it visually separate from study surveys
- Migration: `0025_add_feedback_survey_fields`

#### Admin (`core/admin.py`)
- **Core → Feedback Surveys** section with a simplified admin: title, description, researcher, active toggle, threshold, default Likert scale, and a question inline limited to Likert and Free Text question types only

#### Account page (`/accounts/account/`)
- Feedback card rendered inside the **Profile panel**, below the Security card
- Hidden until `completed_regular_surveys >= show_after_n_surveys` and participant has no prior response
- Supports **Submit** (saves real answers) and **Skip** (records `NULL` for all questions) — both permanently hide the form
- Skipping uses `formnovalidate` to bypass browser required-field validation
- On submission, a **completion modal** fires (same pattern as survey completion) with Escape/backdrop dismiss and `history.replaceState` to strip `?feedback=submitted` from the URL so refresh doesn't reopen it
- Once submitted or skipped, shows a small "Thank you — your feedback has been received" card in place of the form

#### Data integrity
- Feedback surveys excluded from participant dashboard (`dashboard/views.py`) and from `/surveys/<id>/take/` (`surveys/views.py`)
- Responses stored as `ParticipantResponse` with `is_test=False`, visible under **Surveys → Participant Responses** filterable by survey name
- `NULL` answers on skip allow researchers to distinguish skipped from not-yet-shown

**Branch**: `feature-feedback-form`

---

## Session 29: Demographic Survey Gateway (August 2026)

### Demographic gateway survey
Added a gating mechanism so participants must complete a designated demographic survey before any other surveys or tasks become accessible.

#### Model changes (`surveys/models.py`)
- **`Survey.is_demographic`** (BooleanField, default `False`) — marks a survey as the demographic gateway; hidden from the main survey list and managed under **Core** in the admin
- **`DemographicSurvey` proxy model** — registered under **Core → Demographic Survey**; auto-sets `is_demographic=True` on save; supports all question types (Likert, multiple choice, free text, dropdowns)
- Migration: `0027_add_is_demographic`

#### Admin (`core/admin.py`)
- **Core → Demographic Survey** section with full question/group/scale inlines (same capability as a regular survey)
- `SurveyAdmin` queryset updated to exclude `is_demographic=True` surveys from the main Surveys list

#### Dashboard view (`dashboard/views.py`)
- Detects the active demographic survey and checks whether the participant has submitted any response
- Passes `demographic_survey`, `demographic_locked`, and `demographic_complete` to the template
- Active survey queryset now also excludes `is_exit_survey=True` (exit surveys were previously visible on the dashboard)

#### Dashboard template (`participant_dashboard.html`)
- Demographic card renders first, visually distinct: blue border + glowing indicator dot + "Start here" meta label when incomplete; fades to done state once complete
- Lock notice bar appears below the demographic card when locked, explaining what's required
- All other survey and task cards rendered at 45% opacity with `pointer-events: none` while locked
- Sidebar INFO panel switches to "Before you begin" copy naming the demographic survey when locked; reverts to normal copy once complete

#### URL-level guards
- **`survey_take`** (`surveys/views.py`): non-demographic surveys redirect participants to the dashboard with a warning message if the gate isn't complete; researchers/staff bypass the check
- **`task_run`** (`tasks/views.py`): same redirect for participants; researchers/staff unaffected

**Branch**: `feature-demographic-survey`

---

## Session 30: Bug Fixes & CSS Groundwork (August 2026)

### Bug fixes
- **Domain filter on participant dashboard**: Domain links were `href="#"` placeholders and the view ignored the query param. Now reads `?domain=<id>` and filters surveys and tasks accordingly. `?domain=all` keeps the domains panel open while showing everything. Domains panel auto-opens when a filter is active.
- **Demographic survey card hidden once complete**: Previously shown greyed-out at the top of the dashboard after completion. Now hidden entirely.
- **Participant avatar in survey detail was a `<div>`**: Replaced with `<a href="accounts:account">` matching every other page.
- **Topbar shadow on non-sticky pages**: Scroll listener now checks for `topbar--static` and skips adding `.is-scrolled`, so the shadow only appears when the topbar is actually stuck.
- **Avatar initials**: Replaced `|slice:":2"|upper` across all six avatar instances with a new `|initials` template filter (`core/templatetags/account_extras.py`) that extracts the first letter of the first and last word — giving proper initials (e.g. "JS") instead of the first two characters of the name string.

### Avatar hover state
Added a blue hover state to `.avatar` in `styles.css`: fades from lime-green to `var(--blue)` with white text on hover, making it feel interactive like the other topbar buttons.

### Static files now tracked in git
`/static/*` was blanket-ignored. Added exceptions for `static/css/`, `static/js/`, `static/images/`, and `static/LABJS_INTEGRATION.md` so source assets are version-controlled. Collected staticfiles (`/staticfiles/`) remain ignored.

**Branch**: `css-refactor`

---

## Session 32: Bug Fixes & New Features (August 2026)

**Branch**: `bug-fixes-and-misc`

### Bug fixes & misc
- **Researcher invitation system removed** — redundant since admins create researchers directly via the Users admin panel; removed `ResearcherInvitation` model, `accept_invitation` view/URL, `InviteResearcherForm`, `ResearcherSignupForm`, and `ResearcherInvitationAdmin`
- **Consent form as individual checkboxes** — signup page now parses the active `ConsentForm` markdown into individual required `BooleanField`s; multi-line list items joined correctly; server-side validation enforces all boxes ticked
- **Consent card height constrained** — consent record card on the account page is `max-height: 260px` with scroll, reducing visual weight
- **`btn--primary` hover outline** — added `border-color: var(--ink)` to `.btn--primary:hover` site-wide
- **Spectrum chart typography** — "Your score" label and score value switched from serif (`--font-display`) to body font to match the radar chart style

### New features
- **Random answers button** — "Fill with random answers" button on the survey preview page; fills all visible questions with valid random values including gate/branch support
- **Welcome email** — overrides allauth's `email_confirmation_signup_message.txt` with a branded welcome; uses `{{ user.first_name }}` and `{{ current_site.domain }}`
- **Withdrawal confirmation email** — sent via `send_mail` + `render_to_string` before `user.delete()`; template at `templates/account/email/withdrawal_confirmation_message.txt`
- **Withdrawal audit log** — `WithdrawalRecord` model snapshots anonymised participant ID, exit survey title, and responses as JSON before account deletion; admin with long-format CSV export
- **`dropdown_year_month` question type** — combined Month + Year dropdowns side-by-side in one question card; stores as `YYYY-MM`; standalone `dropdown_year` and `dropdown_month` types removed
- **`result_description` field on Survey** — short explanation shown below participant chart in both spectrum and radar variants; admin fieldset renamed to "Results Display Information"
- **Production email documentation** — `EMAIL_SETUP.md` covering SMTP options, DNS records, `settings.py` config, and testing checklist

---

## Session 33: Chart Axis Label Arrays & Radar Chart Fix (August 2026)

### Chart axis label arrays
`QuestionGroup.result_label` now accepts either a plain string or a JSON array of two strings, e.g. `["V", "Visual"]`:
- **`_parsed_result_label()`** (`surveys/models.py`) parses the field, returning `(short, long)` — falls back to plain-string / title behaviour when the field isn't a JSON array
- **`display_label`** (existing property) now returns just the short form — used for chart axis labels, unchanged in shape
- **`display_label_long`** (new property) returns the long form, or `None` if not set
- **`surveys/utils.py`**: `_subscale_result()` includes `label_long` alongside `label` in each subscale dict (and in `chart_json`)
- **Templates**: radar legend on both `accounts/account.html` (participant results panel) and `surveys/survey_detail.html` (researcher preview) renders "V = Visual" when `label_long` is present, otherwise just the short label — chart axis labels (Chart.js `labels:` array) are unaffected, they only ever use the short form
- Admin help text on `result_label` documents the array syntax

### Bug fix: researcher preview radar chart not rendering
Found while testing the above (pre-existing, unrelated to this session's changes — confirmed via `git blame` and by reproducing on a clean `HEAD`). The progress-counter script in `survey_detail.html` queries `[data-progress-done]` / `[data-progress-total]` / `[data-progress-fill]` unconditionally, but that markup is intentionally omitted once a researcher's test submission renders (`{% if not test_responses %}`, added in Session 25). The resulting `null.textContent` threw on page load, and this was blocking the later radar-chart-init script from running. Fixed by null-guarding both the `refresh()` function and the `survey:refresh` event listener's inline duplicate of the same lookup in `templates/surveys/survey_detail.html` — confirmed the radar chart now renders correctly on the researcher preview page.

### Compact admin inline widgets
`surveys/admin.py`:
- `QuestionInline` and `LikertScaleInline`: `formfield_overrides` narrows `TextField`/`JSONField` widgets (question `text`/`options`, Likert `scale_labels`) from Django's tall default to 5 rows
- New `QuestionInlineForm` narrows `trigger_value` to a 4-character `TextInput` — it only ever holds a single digit
- Survey-level `description`/`instructions` fields deliberately left at default size (only the inline table rows were the actual pain point)

### Minimum window size gate for lab tasks
Visual tasks need enough screen space to produce usable data, so researchers can now flag a `LabTask` as requiring a minimum browser window size:
- **`LabTask.requires_min_window_size`** (bool, default `False`), **`min_window_width`** / **`min_window_height`** (default `1024`×`768`) — new admin "Screen Requirements" fieldset
- **`templates/tasks/task_start.html`**: when enabled, checks `window.innerWidth`/`innerHeight` against the task's minimum on load and on every `resize`; shows a warning banner and disables the Start button while too small
- **Window size always logged** on `TaskSubmission.window_width`/`window_height` when a participant starts a task, regardless of whether a minimum is enforced — a data-quality fallback researchers can check later. Captured client-side and appended as `?w=&h=` query params on the Start link
- Because there was previously no reliable moment to capture window size for tasks with no instructions text (they skipped straight from the dashboard into the lab.js task), `task_preview`/`task_run` (`tasks/views.py`) now always route through `task_start.html` on first entry, not just when instructions exist
- **`TaskSubmissionAdmin`**: list view shows recorded window size, flagged red if below the task's minimum; detail view has a "Browser Window" fieldset

**TODO**: the warning banner styling on `task_start.html` is functional but needs proper design treatment — currently a bare `.alert--warning` strip.

**Branch**: `bug-fixes-and-misc`

