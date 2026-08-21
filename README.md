# Research Platform

A Django-based research platform for collecting participant data through surveys and lab.js tasks.

## Tech Stack

- Django 5.2.8
- django-allauth (email/password authentication)
- SQLite (development database)
- Chart.js 4.4.0 (participant results charts)

## Project Structure

```
research_platform/
├── accounts/          # User authentication and custom user model
├── core/             # Core models (Domain, DataDownloadLog, Message)
├── surveys/          # Survey models and views
├── tasks/            # Lab.js task models and submissions
├── dashboard/        # Participant dashboard
├── media/            # User-uploaded files (lab.js tasks, etc.)
├── static/           # Static files (CSS, JS)
├── templates/        # HTML templates
│   ├── base.html     # Base template with navigation
│   ├── account/      # Authentication templates (signup, login)
│   ├── surveys/      # Survey list and detail templates
│   └── dashboard/    # Participant dashboard template
└── research_platform/ # Project settings and main URLs
```

## Apps and Models

### accounts
- **User**: Custom user model with `is_researcher` and `is_participant` fields, and `consent_text` field to track the consent form version agreed to during registration. Includes progress tracking methods.
- **ConsentForm**: Editable consent form text shown to participants during registration. Supports versioning and history tracking.
- **ResearcherInvitation**: Invitation system for appointing new researchers. Tracks invitation tokens, expiration dates, and who invited whom.

### core
- **Domain**: Research domains/categories
- **DataDownloadLog**: Audit log for data downloads
- **Message**: Researcher-to-participant messaging system

### surveys
- **Survey**: Survey definitions with configurable Likert scale settings (`min_value`, `max_value`, `scale_labels`) and optional question randomization
- **Question**: Individual survey questions belonging to a single survey. Each question has ordering, required flag, and optional reverse coding
- **ParticipantResponse**: Participant responses to survey questions (linked by question ID, independent of order)

### tasks
- **LabTask**: Lab.js task uploads. Includes optional `trial_sender_filter` field (comma-separated sender names) to narrow trial data filtering beyond the default `ended_on='response'` filter
- **TaskSubmission**: Participant task submissions and results. Includes `is_test` flag for researcher/staff test runs, and `get_trial_data()` method which filters raw lab.js data to response rows only

## Setup Instructions

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Install dependencies (if needed):**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations (already completed):**
   ```bash
   python manage.py migrate
   ```

4. **Create a superuser:**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

6. **Access the admin panel:**
   - URL: http://localhost:8000/admin/
   - Login with your superuser credentials

## Configuration Notes

### Django Allauth
The project is configured with django-allauth for authentication:
- Email-based authentication (username not required)
- Optional email verification
- Custom signup form with research consent

**Admin Panel Note**: The `EmailAddress` model from django-allauth has been hidden from the admin panel to reduce confusion (see `accounts/admin.py`). This model tracks email verification status internally and doesn't need manual management. If you need to re-enable it in the future (e.g., for manual email verification management or debugging), comment out the `admin.site.unregister(EmailAddress)` line in `accounts/admin.py`.

### Media Files
- Lab.js tasks are uploaded to `media/lab_tasks/YYYY/MM/`
- Media files are served in development mode only

### Renaming the Project Folder
The project root folder can be renamed without affecting the code, as Django uses relative paths (`BASE_DIR`). However, the virtual environment should be recreated after renaming:
```bash
# After renaming the folder
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Alternatively, you can keep the old venv and it will continue to work (though internal paths will reference the old folder name).

## Participant Registration & Consent

The platform includes a built-in consent system for research participants:

### Features
- **Required Consent**: Participants must agree to a research consent form before creating an account
- **Consent Tracking**: The full text of the consent form is stored with each user's account for audit purposes
- **Custom Signup Form**: Uses `accounts.forms.ParticipantSignupForm` which extends django-allauth's SignupForm
- **Automatic Role Assignment**: New registrations are automatically marked as participants (`is_participant = True`)

### Consent Form Contents
The consent form displayed during registration includes:
- Purpose of the study
- What participants will do
- Confidentiality information
- Voluntary participation notice

### Implementation Details
- Consent form text is stored in the database using the `ConsentForm` model (`accounts/models.py`)
- The consent checkbox is required; registration will fail without it
- The consent text is saved to the `User.consent_text` field when the account is created
- The `User.date_joined` field indicates when consent was given
- Since account creation requires consent, the existence of an account proves consent was provided
- A fallback consent text exists in `accounts/forms.py` as `DEFAULT_CONSENT_TEXT` in case no active consent form is in the database

### Managing the Consent Form
1. **Access the Admin Panel**: Navigate to **Accounts → Consent Forms**
2. **Edit Existing Form**: Click on the active consent form to edit its content
3. **Create New Version**: Click "Add Consent Form" to create a new version
   - Set a version identifier (e.g., "v2.0", "2024-11")
   - Check **is_active** to make it the current form
   - Only one consent form should be active at a time (system auto-deactivates others)
4. **View History**: All historical consent forms are preserved for audit purposes

**Note**: Each user's account stores the exact consent text they agreed to during registration, ensuring compliance and audit trail.

## Researcher Management

The platform uses a secure invitation system for appointing researchers. Only existing researchers or superusers can invite new researchers to join the platform.

### Setting Up Researchers

Researchers are users who can access the Django admin panel to create surveys, manage tasks, and view participant data. The platform automatically handles permissions and access control through an invitation-based workflow.

#### Initial Setup

1. **Create your first superuser** (if you haven't already):
   ```bash
   python manage.py createsuperuser
   ```
   The superuser can send the first researcher invitations.

#### Inviting Researcher Accounts

Researchers are appointed through a secure invitation system:

1. **Log into the admin panel** as a superuser or existing researcher
2. Navigate to **Accounts → Researcher Invitations**
3. Click the **"Invite New Researcher"** button (top-right corner)
4. Enter the invitee's **email address**
5. Set the **expiration period** (default: 7 days, max: 30 days)
6. Click **"Send Invitation"**

The system will:
- Create a unique, secure invitation token
- Send an email to the recipient with the invitation link
- Display a success message with the expiration date

**Note**: In development mode, invitation emails are printed to the console. Copy the invitation URL from the terminal output to test the registration flow.

#### Accepting an Invitation

When someone receives a researcher invitation:

1. They click the unique invitation link in the email
2. The link takes them to a researcher registration page
3. They fill out their details:
   - Email (pre-filled and read-only)
   - First and last name (optional)
   - Password (minimum 8 characters)
4. Upon registration, they're automatically:
   - Created as a researcher with `is_researcher=True`
   - Granted staff status for admin panel access
   - Added to the Researchers group with appropriate permissions
   - Marked as a participant (`is_participant=True`) for testing purposes
   - Logged in and redirected to the admin panel

The invitation is marked as "used" and cannot be reused.

### What Happens Automatically

When a researcher account is created via invitation, the system automatically:
- Grants Django **staff status** (`is_staff = True`) for admin panel access
- Adds them to the **Researchers group** with appropriate permissions
- Maintains their **participant status** (`is_participant = True`) to enable survey testing

**Important**: Although researchers have `is_participant = True`, they **cannot submit real participant data**. View-level protections automatically redirect researchers to test mode when they attempt to access participant survey URLs. This allows them to test the full participant experience without contaminating research data. See the "Data Protection & Research Integrity" section for details.

### Managing Invitations

In the **Researcher Invitations** admin page, you can:

- **View all invitations** with their status:
  - ⧗ **Pending**: Not yet used and not expired
  - ✓ **Used**: Successfully accepted and account created
  - ✗ **Expired**: Past expiration date and cannot be used

- **Resend invitations**: Select pending invitations and use the "Resend invitation email" action

- **Track who invited whom**: Each invitation records the inviting researcher and timestamp

### Researcher Permissions

Researchers have full access to:
- **Create, edit, delete**: Surveys, Questions, Lab Tasks, Domains, Researcher Invitations
- **View and add**: Participant Responses, Task Submissions, Progress data
- **Manage**: Data Download Logs

Researchers **cannot**:
- Access Django system settings (only superusers can)
- Delete participant data (view and add only)
- Manually promote users to researcher status (invitation-only system)
- Modify the `is_researcher` field directly (managed through invitations)

### Removing Researcher Status

Researcher status can only be removed by superusers:

1. Log in as a **superuser** (not just a researcher)
2. Navigate to **Users** under **ACCOUNTS**
3. Click on the researcher whose status you want to remove
4. Uncheck the **"is_researcher"** checkbox
5. Click **"Save"**

The system automatically:
- Removes the user from the Researchers group
- Staff status is **not** automatically removed for safety (adjust manually if needed)

**Note**: Regular researchers cannot modify the `is_researcher` field - it's read-only except for superusers.

### Best Practices

- **Superuser vs Researcher**: Create a superuser for platform administration, and researcher accounts for study management
- **Invitation Expiry**: Use shorter expiration periods (3-7 days) for better security
- **Regular Audits**: Periodically review the list of researchers to ensure only authorized users have access
- **Track Invitations**: Monitor who invites whom through the Researcher Invitations admin page
- **Email Verification**: In production, ensure invitation emails are sent from a trusted domain
- **Revoke Access Promptly**: If a researcher leaves the project, immediately remove their researcher status

## Survey System Features

### Creating and Managing Surveys

Surveys are created and managed through the Django admin panel by researchers:

1. **Create Survey**: Navigate to Surveys → Add Survey
   - Set title and description
   - Choose researcher and domain
   - Configure Likert scale range (e.g., 1-5, 1-7, 0-10)
   - Optionally add custom labels for scale values
   - Set as active/inactive
   - Enable question randomization (optional)

2. **Add Questions**: Use the inline question editor
   - Questions are simple text statements
   - Mark questions as required or optional
   - Enable reverse coding for specific questions (optional)
   - Questions inherit the survey's Likert scale settings
   - Order is automatically managed (leave at 0 for auto-increment)

3. **Configure Scale Labels** (Optional): Add JSON labels in the survey settings
   ```json
   {
     "1": "Strongly Disagree",
     "2": "Disagree",
     "3": "Neutral",
     "4": "Agree",
     "5": "Strongly Agree"
   }
   ```

### Researcher Workflow

**Survey Management Page** (`/surveys/`):
- View all surveys (active and inactive)
- Three action buttons per survey:
  - **Preview**: See exactly how participants will view the survey
  - **Test Mode**: Fill out the survey with full validation and see collected data without saving
  - **Edit**: Jump directly to admin panel to modify survey

**Test Mode Features**:
- Validates required fields
- Validates numeric ranges
- Displays submitted data in a table showing:
  - Question number and text (with **[RC]** indicator for reverse-coded questions)
  - Selected value (what participant clicked)
  - Stored value (after reverse coding, if applied)
  - Label for selected value
- No data is saved to database
- Perfect for verifying survey configuration and reverse coding

### Participant Workflow

**Dashboard** (`/dashboard/`):
- **Available Surveys Section**: Shows active surveys not yet completed
- **Completed Surveys Section**: Shows surveys with at least one response
- Each survey displays:
  - Title and description
  - Domain and question count
  - Scale range information
  - Button to start or update responses

**Taking Surveys**:
- Clean, responsive interface
- Radio buttons for each scale value
- Labels displayed under each option (if configured)
- Required fields enforced
- Can update responses by retaking the survey

### Advanced Survey Features

#### Question Ordering
Questions can be ordered manually or automatically:

1. **Auto-increment**: Leave the order field at `0` and it will automatically be set to the next available number
2. **Manual ordering**: Set a specific order number to position questions
3. **Normalize order**: Use the admin action "Normalize question order" to renumber all questions sequentially (1, 2, 3...), removing gaps and duplicates
4. **Display vs. Storage**: Questions display their position in the rendered list (which may be randomized), not their database order number

#### Question Randomization
Surveys can randomize question order for each participant:

- **Enable**: Check "Randomize questions" on the survey
- **Seeded randomization**: Each participant sees a consistent random order (using their ID as seed)
- **Persistence**: Same participant always sees the same order across sessions
- **Different per participant**: Each participant gets a unique randomized order
- **Admin unaffected**: Admin panel always shows questions in order field sequence

**Use case**: Reduce order effects and detect acquiescence bias

#### Reverse Coding
Individual questions can be reverse-coded to detect response patterns:

- **Enable**: Check "Reverse coded" on specific questions
- **Inversion formula**: `stored_value = (max_value + min_value) - selected_value`
- **Example (1-5 scale)**: Participant selects 5 → Database stores 1
- **Invisible to participants**: They see the normal scale
- **Test mode display**: Shows both selected and stored values with **[RC]** indicator
- **Data integrity**: Responses are always linked by question ID, never by order

**Use case**: Detect acquiescence bias (participants always clicking same value)

## Lab.js Task Integration

The platform now supports lab.js experimental tasks with full integration:

### Features Implemented
- **Zip Upload & Automatic Unpacking**: Upload lab.js exports as .zip files, automatically unpacked to task directories
- **File Validation**: Ensures zip contains index.html and is properly formatted
- **Task Management Interface**: Researchers can view, preview, and edit all tasks at `/tasks/`
- **Task Execution**: Participants run tasks via direct navigation (no iframe/CORS issues)
- **Instructions Screen**: Optional pre-task instructions page with task info and time limits
- **Task Completion Flow**: Template-based approach with automatic ${TASK_ID} placeholder replacement
- **Dashboard Integration**: Tasks appear alongside surveys on participant dashboard
- **Data Submission**: Lab.js POSTs full datastore JSON to `/tasks/<id>/submit/` on completion
- **Test Submissions**: Researchers run tasks through the real submission pipeline; data saved and flagged with `is_test=True` for review and deletion
- **Trial Data Filtering**: `get_trial_data()` filters raw lab.js datastore to response rows only (`ended_on='response'`), generic across task designs
- **Configurable Sender Filter**: Optional `trial_sender_filter` on `LabTask` to narrow filtering by sender name (e.g. `"Trial"`)
- **Accurate Timing**: `time_spent_seconds` derived from lab.js `Task` row `duration` field (actual in-task time), not server-side timestamp diffs

### Task Completion System
Researchers add a completion screen to their lab.js exports that redirects to `/tasks/${TASK_ID}/complete/`:
1. Platform automatically replaces `${TASK_ID}` with actual task ID during upload
2. Participant completes task → lab.js POSTs datastore JSON to `/tasks/${TASK_ID}/submit/`
3. Task redirects to completion confirmation page
4. Participant clicks "Confirm Completion" button
5. Status updated to 'completed', timing recorded from lab.js data, back to dashboard

### File Structure
```
media/lab_tasks/
├── zips/                          # Original uploaded zip files
└── unpacked/
    └── {task-slug}-{id}/          # Unpacked task directories
        ├── index.html
        ├── script.js              # ${TASK_ID} replaced automatically
        ├── style.css
        └── lib/                   # Lab.js library files
```

### URLs Structure
- `/tasks/` - Task management (researchers only)
- `/tasks/<id>/preview/` - Preview task (researchers only)
- `/tasks/<id>/run/` - Run task (participants, creates TaskSubmission)
- `/tasks/<id>/complete/` - Completion confirmation page
- `/tasks/<id>/submit/` - API endpoint for future JSON result submission

### Documentation
Full integration guide available at `LABJS_INTEGRATION.md` with:
- Step-by-step instructions for researchers
- Code snippets for completion screen
- Troubleshooting section
- Advanced customization examples

### ✅ Testing Completed (Session 3)
**Task completion flow has been tested and verified:**
1. ✅ Task execution and preview work correctly
2. ✅ `${TASK_ID}` placeholder replacement works
3. ✅ Redirect to completion confirmation page works
4. ✅ Task completion status tracking works
5. ✅ Simplified approach: minimal completion screen with redirect only

### ✅ Data Submission & Filtering (Session 6 - Latest)
**Full lab.js data submission pipeline implemented and tested:**
- ✅ Diagnosed race condition between `after:end` handler and screen timeout
- ✅ Fixed by moving script to **"Run"** event (fires immediately when End screen appears)
- ✅ Switched from synchronous XHR to `fetch` with `.then()` chaining (no deprecation warning)
- ✅ Data POSTed to `/tasks/<id>/submit/` endpoint and saved to `TaskSubmission.results_data`
- ✅ Full end-to-end flow tested: builder → export → upload → participant run → data saved
- ✅ Added `get_trial_data()` method to `TaskSubmission` model to filter raw datastore to meaningful trial rows only (`sender == 'Trial'` and `ended_on == 'response'`)
- ✅ Rewrote `LABJS_INTEGRATION.md` with correct, tested instructions for researchers

**Working completion screen snippet (add to End screen "Run" script in lab.js builder):**
```javascript
const datastore = this.parent.options.datastore;
const data = datastore.data;

console.log('=== Lab.js Task Data ===');
console.log('Task ID: ${TASK_ID}');
console.log('Data:', data);
console.log('Total Trials:', data.length);
console.log('========================');

function getCookie(name) {
  const value = '; ' + document.cookie;
  const parts = value.split('; ' + name + '=');
  if (parts.length === 2) return parts.pop().split(';').shift();
}

fetch('/tasks/${TASK_ID}/submit/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCookie('csrftoken'),
  },
  body: JSON.stringify(data),
})
.then(function(response) { return response.json(); })
.then(function(result) {
  console.log('Submission result:', result);
  window.location.href = "/tasks/${TASK_ID}/complete/";
})
.catch(function(e) {
  console.error('Data submission failed:', e);
  window.location.href = "/tasks/${TASK_ID}/complete/";
});
```

**Key notes:**
- Script goes in **"Run"** section, not "After end"
- End screen must have **no timeout** set
- `${TASK_ID}` is replaced automatically on upload
- See `LABJS_INTEGRATION.md` for full instructions

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

## TODO

- **`result_description` field on Survey**: A short text field explaining what the score means to the participant (e.g. "Higher scores indicate greater vividness of mental imagery"). Deferred — add once the results page UI is taking shape so we know how/where to display it.

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

---

## CSS Refactor Plan

A prior attempt at this refactor was done in one large sweep, became unwieldy, and had to be reset. This plan replaces that approach. **Work through it in small chunks on the `css-refactor` branch — one phase, one template group, one commit at a time. Never batch unrelated templates together.**

### Current state (audited 2026-08-20)

17 templates still have inline `<style>` blocks, totalling ~3,650 lines. `static/css/styles.css` is 1,021 lines and already holds the shared design system (tokens, topbar, footer, buttons, alerts, avatar).

| Template | Inline CSS lines |
|---|---|
| `surveys/survey_detail.html` | 756 |
| `accounts/account.html` | 490 |
| `dashboard/participant_dashboard.html` | 279 |
| `account/signup.html` | 242 |
| `tasks/task_list.html` | 210 |
| `surveys/survey_list.html` | 210 |
| `account/login.html` | 202 |
| `core/messages.html` | 192 |
| `home.html` | 187 |
| `accounts/exit_survey.html` | 157 |
| `account/password_reset.html` | 135 |
| `account/password_change.html` | 135 |
| `account/password_reset_from_key.html` | 134 |
| `tasks/task_start.html` | 102 |
| `tasks/task_complete.html` | 79 |
| `account/password_reset_done.html` | 73 |
| `account/password_reset_from_key_done.html` | 68 |

Selector-frequency audit found the duplication isn't random — it clusters into families of templates that share a layout skeleton and copy-pasted its CSS wholesale:

- **Auth-page family** (`.page`, `.page__heading*`, `.field`, `.field-errors`, `.non-field-errors`, `.form-submit`, `.back-link`, `.info-region`, `.heading`) — shared by `login.html`, `signup.html`, `password_reset.html`, `password_reset_from_key.html`, `password_change.html`. This is exactly the family that caused the button/link spacing bug fixed in Session 33 — the same rule had drifted three separate ways because it was defined three separate times.
- **Dashboard-grid family** (`.page__sidebar`, `.page__main`, `.sidebar-panel`, `.domain-list__*`, `.task-card*`, `.empty-state`) — shared by `participant_dashboard.html`, `survey_list.html`, `task_list.html`, and partially `survey_detail.html`.
- **Results/chart cluster** (`.radar`, `.radar-wrap`, `.radar-legend`, `.spectrum-*`) — shared by `account.html` and `survey_detail.html`.
- Everything else (`home.html`, `messages.html`, `exit_survey.html`, `task_start.html`, `task_complete.html`, the two `*_done.html` confirmation pages) is largely page-specific with lighter duplication.

### Phase 1 — Audit (no code changes)

For each of the 17 templates, classify every inline rule as one of:
- **Duplicate-identical** — byte-for-byte (or near enough) the same rule already exists in another template or in `styles.css`.
- **Duplicate-drifted** — same intent, slightly different values (the dangerous category — these are bugs waiting to be found, like the Session 33 spacing issue).
- **Page-specific** — genuinely unique to this template, no equivalent elsewhere.

Output: a short checklist per template group (reuse the clusters above as a starting grouping). This becomes the literal task list for Phase 2. Do this as its own pass before touching any template — it's cheap, low-risk, and prevents Phase 2 from rediscovering the same duplication piecemeal.

#### Phase 1 results (completed 2026-08-20)

**Important correction to Phase 2 below**: `static/css/styles.css` already contains shared versions of the entire auth-page-grid and dashboard-grid families (`.page--auth`, `.field`, `.form-submit`, `.domain-list__*`, `.empty-state`, `.page`, `.page__sidebar`, `.sidebar-panel`, `.info-content`/`.info-region`, `.form-region` — roughly 440 lines). Because `styles.css` loads before each template's inline block and both use equal-specificity bare class selectors, **every template's inline copy currently shadows the shared version** — the shared rules are written but effectively dead code right now. For the auth-page and dashboard-grid templates, Phase 2 is "delete the inline copy and confirm the existing shared rule still renders correctly," not "write a new shared rule from scratch."

**Cluster 1 — Auth-page family** (`login.html`, `signup.html`, `password_reset.html`, `password_reset_from_key.html`, `password_change.html`, `password_reset_done.html`, `password_reset_from_key_done.html`)
- `.page` grid, `--bg-page: #ffffff`, `.field`/`.field-errors`/`.non-field-errors`, `.info-region`, `.message-region` — duplicate-identical across all 7 + `styles.css` (styles.css scopes the grid as `.page--auth`, a rename not a value change).
- Padding variable, always `60px` — duplicate-identical value, naming drift only (`--login-padding-x`, `--signup-padding-x`, `--pad-x` ×5, `--auth-padding-x` in styles.css). Trivial Phase 3 unify.
- `.page__heading`/`.page__label` BEM suffixes — naming split, not drift: 5 pages use `--left`/`--right` (matches styles.css verbatim); login.html uses `--brand`/`--login`, signup.html uses `--info`/`--signup` (page-specific semantic names, same values).
- Submit button — duplicate-identical values, 3-way naming split (`.login-submit`, `.signup-submit`, `.form-submit` + styles.css).
  - **By-design, do not unify to one value**: `margin-top` is `8px` on `.login-submit` (sits after `.remember-row`'s own 20px padding) vs `28px` on `.form-submit` on the 3 reset/change pages (no preceding spacer, so the value compensates — this is the Session 33 fix, correct as shipped). Preserve the *visual* gap, not a single numeric value.
  - **Dead code**: `signup.html`'s `.signup-submit` has a commented-out `margin-top: 32px;` with no active margin-top — clean up in Phase 2/3.
- `.back-link`/`.forgot-link` — duplicate-identical at `24px`, naming-only variance. signup.html has no equivalent (genuine absence, not drift).
- Per-template split: login.html/signup.html ~35% shared-family, ~65% page-specific (hero copy, view-switch). Reset/change pages ~70%+ shared-family. The two `*_done.html` pages are almost entirely shared-family.

**Cluster 2 — Dashboard-grid family** (`participant_dashboard.html`, `survey_list.html`, `task_list.html`, `survey_detail.html` partial)
- `.page` grid (360px/1fr), `.page::before`, `.page__sidebar`, `.page__main`, `.sidebar-panel`, `.info-content`, `.domain-list__*` — duplicate-identical across all 4 + styles.css (unscoped here, matches directly).
- `.task-card` family (`__body`/`__title`/`__desc`/`__actions`/`__meta`) — duplicate-identical between `survey_list.html` (`.survey-card*`) and `task_list.html` (`.task-card*`), naming-only, safe merge.
- `.pill--priority`/`.pill--inactive`/`.pill--active` — likely duplicate-identical with styles.css's `.pill` component; not independently re-verified line-by-line, confirm in Phase 2.
- **Flag for a decision before Phase 3 touches these — do not auto-merge**:
  - `.empty-state` — real 3-way visual inconsistency, not by-design: `survey_list.html`/`task_list.html` use `padding:80px 0; color:var(--ink-muted)` (matches styles.css); `participant_dashboard.html` uses `padding:60px 0; font-size:14px; color:var(--ink-subtle)` (smaller, subtler); `core/messages.html` uses `padding:80px 24px; text-align:center` (different shape, centered). Needs a decision — pick one, or keep as deliberate per-context variants.
  - `participant_dashboard.html`'s own `.task-card` — genuinely more complex than the list-page cards: adds `text-decoration:none; color:inherit`, hover/focus-visible states, `--done`/`--priority` modifiers, an `__indicator` dot; also omits `align-items: stretch` that the list-page cards have. This is the dashboard's unified survey+task card (Session 18) — likely stays a distinct component that shares a base rather than a full merge.
- Per-template split: `participant_dashboard.html` (277 lines) ~half shared-family, ~half page-specific-but-drifted card variant, small genuine page-specific remainder (progress header). `survey_list.html`/`task_list.html` (~209 lines each) high overlap with each other, moderate overlap with dashboard (grid skeleton only). `survey_detail.html` (754 lines) only shares the outer `.page` grid with this family (~5% of its CSS) — the rest is page-specific (question rendering, matrix tables, branch/gate UI, progress bar, modal).

**Cluster 3 — Results/chart cluster** (`accounts/account.html`, `surveys/survey_detail.html`)
- `.spectrum-chart`/`.spectrum-track`/`.spectrum-marker`/`.spectrum-marker-dot`/`.spectrum-labels`, `.radar-wrap`, `.radar-legend` (`h5`/`li`/`.modality`/`.value`) — duplicate-identical (survey_detail's copy is condensed-formatted, not a value change).
- **Flag for a decision**: `.radar` `max-width` is `380px` on `account.html` (participant results) vs `340px` on `survey_detail.html` (researcher preview) — a real 40px difference in rendered chart size. Could be intentional (preview is secondary/compact) or accidental. Don't auto-merge to one value without checking.
- Small fraction of either template's total CSS — most of both files is unrelated to charts.

**Cluster 4 — Page-specific only, no reconciliation needed** — `home.html` (187 lines), `core/messages.html` (192 lines, except its `.empty-state` drift above), `accounts/exit_survey.html` (157 lines), `tasks/task_start.html` (100 lines), `tasks/task_complete.html` (77 lines). Zero cross-template selector hits found against the clusters above. Good Phase 2 quick wins — plain relocation, no reconciliation against the shared stylesheet needed.

**Ranked risk list for Phase 3** (highest judgement-call risk first): (1) `.empty-state` 3-way drift, (2) `.radar` max-width 340 vs 380, (3) dashboard `.task-card` vs list-page `.task-card`/`.survey-card` — structurally more complex, needs design judgement not just a value merge, (4) exit survey question blocks vs survey_detail.html's — see below, (5) `messages.html`'s page-header layout pattern vs `account.html`'s — see below.

**Added during Phase 2 extraction of `exit_survey.html` (2026-08-20)**: its `.q-num`/`.q-label`/`.likert-row`/`textarea` selectors were bare/unscoped in the original inline block, which forced scoping under `.exit-wrap` during extraction to avoid a global collision (see `styles.css` section 16). Two distinct findings on comparison, verified property-by-property:

- **`exit_survey.html` vs `account.html`'s feedback form — duplicate-identical, safe merge candidate.** Confirmed by direct diff: `.q-num`, `.q-label`, `.likert-row` (+ `label`, `input[type="radio"]`), and `textarea` (+ `:focus`) are byte-for-byte the same values in both (e.g. `.q-num` is `font-size: 11px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; display: block; margin-bottom: 6px` in both). This wasn't obvious from Phase 1's selector-frequency scan because `account.html` scopes its copy as `.feedback-form .q-num` while exit_survey's was a bare `.q-num` — genuinely the same rule, hidden by a scoping-prefix mismatch. Low-risk Phase 3 merge: pick one shared scope (e.g. `.survey-question-block` or similar) and point both `.exit-wrap` and `.feedback-form` at it.
- **`exit_survey.html`/`account.html` vs `survey_detail.html` — real drift, not the same component.** `survey_detail.html`'s own `.q-num` differs meaningfully: `font-size: 13px; font-family: var(--font-display); letter-spacing: 0.04em` with no bold/uppercase/`display:block`. It also renders different **template text**, not just different CSS — `survey_detail.html` shows `"Question {N}"` (`templates/surveys/survey_detail.html:972,1020`) while exit_survey/feedback-form show a bare `"{{ forloop.counter }}."`. Higher-judgement decision: if Phase 3 unifies visual style across all three, the label text needs reconciling too, or the result will look inconsistent (matching typography, mismatched wording).

**Added during Phase 2 extraction of `messages.html` (2026-08-20)**: `.page-head`, `.page-subtitle`, `.content`, and `.empty-state` collided with differently-valued rules of the same name in `account.html` (plus the already-flagged `.empty-state` 3-way drift). No existing wrapper element to scope under, so a new `.messages-page` div was added around the page's content in the template (a small, additive markup change — see `templates/core/messages.html`) and the colliding rules scoped under it (`styles.css` section 17). **Root cause for Phase 3**: `messages.html` uses a one-off `.page-head` + `.page-subtitle` + `.content` header pattern instead of reusing `account.html`'s established `.page-title`/`.page-subtitle`/`.content` pattern — the page header layout itself is inconsistent with the rest of the app, not just a CSS-values mismatch. Worth considering whether `messages.html` should be restructured to match the `account.html` header pattern rather than just merging CSS values.

### Phase 2 — Extract-only (relocate, don't unify)

Move each template's inline `<style>` block into `static/css/styles.css` **verbatim**, scoped under a clear comment header (e.g. `/* === survey_detail.html === */`), one template (or one tightly-coupled pair, like the two `*_done.html` confirmation pages) per session.

**For auth-page-family and dashboard-grid-family templates (clusters 1 and 2 above), `styles.css` already has a shared rule for most of the inline block** — for those, the step is "delete the inline copy and confirm the page still renders correctly against the existing shared rule," not "paste a new copy in." Only genuinely page-specific rules (the page-specific remainder noted per template in the Phase 1 results) get newly added to `styles.css`.

1. Pick the next template from the Phase 1 checklist.
2. For rules already covered by an existing shared rule in `styles.css`: delete the inline copy, don't re-paste it.
3. For genuinely page-specific rules: cut from the inline block, paste into `styles.css` under a labelled section for that template.
4. Delete the empty `{% block extra_head %}` style tag from the template (or the block entirely if nothing else lives there).
5. Run the dev server, load the page, visually compare against how it looked before (screenshot or side-by-side if possible) — check light and dark theme if the page supports both.
6. Commit — one template's extraction per commit, README updated with a one-line log entry.
7. Stop. Do not continue to the next template in the same sitting unless explicitly asked.

At the end of Phase 2, every template uses `{% load static %}` + the shared stylesheet only — zero inline `<style>` blocks — but `styles.css` will be large and still contain the duplication identified in Phase 1. That's expected and fine at this stage.

**Added during Phase 2 extraction of `password_reset_done.html` + `password_reset_from_key_done.html` (2026-08-21)**: both were 100% covered by the existing `.page--auth` shared rule (no page-specific remainder), but two things bit on extraction, relevant to the rest of Cluster 1 (`login.html`, `signup.html`, `password_reset.html`, `password_change.html`, `password_reset_from_key.html`) when they're extracted next:

- **Don't keep the bare `page` class alongside `page--auth`.** `styles.css` has a *separate*, later-in-file bare `.page` rule (dashboard-grid family, section 5, `360px 1fr` columns) that collides at equal specificity with `.page--auth`'s `1fr 1fr` columns — `class="page page--auth"` renders with the wrong (dashboard) grid because the dashboard rule appears later in the cascade. Use `class="page--auth"` alone.
- **`--bg-page: #ffffff` on `.page--auth` doesn't reach `body`/the topbar.** `body`'s background reads `--bg-page` from `:root`/`body` itself; `.page--auth` is a descendant div, and CSS custom properties don't cascade upward to ancestors. The shared `.page--auth` rule's own `--bg-page` override is therefore dead for that purpose (it only affects things nested inside `.page--auth`). Each auth template still needs its own small `:root { --bg-page: #ffffff; }` in `extra_head` — this is expected to stay page-level, not something to fold into `styles.css`.

**Added during Phase 2 extraction of `password_reset.html` (2026-08-21)**: confirmed the by-design `.form-submit` drift noted in Phase 1 (8px vs 28px `margin-top`) was never actually reconciled in `styles.css` — the shared rule had 8px (login.html's value), which is wrong for password_reset.html/password_change.html/password_reset_from_key.html (28px, no preceding spacer). Decision: updated the shared `.form-submit` to 28px now, since 3 of the remaining 5 Cluster 1 templates need that value and only `login.html` needs the 8px exception — `login.html` will need a scoped override when it's extracted next, not the other way around. Also added `.back-link` to `styles.css` (used identically by this template, `password_change.html`, and `password_reset_from_key.html`; `login.html` has an equivalent `.forgot-link` with the same values but a different name — Phase 3 naming unify, not now) and `.reset-form` (page-specific flex wrapper, shared verbatim with `password_reset_from_key.html`).

### Phase 3 — De-duplicate (unify, once everything is in one file)

Only start this once Phase 2 is fully complete for all 17 templates. With everything living in one file, duplicate-identical and duplicate-drifted rules are easy to `diff` side by side:

1. Work through the Phase 1 duplicate list, one cluster at a time (start with the auth-page family — it's the best-understood and lowest-risk).
2. For **duplicate-identical** rules: merge into a single shared rule, update the selector list, delete the redundant copies, verify all affected pages still render correctly.
3. For **duplicate-drifted** rules: this is a judgement call, not an automatic merge — decide whether the drift was intentional (a real design difference) or accidental (a bug like Session 33's). Confirm with the user before unifying if it's ambiguous.
4. Commit per cluster, not per rule — each commit should leave the site in a fully working state.

### Ground rules for every session on this branch

- One phase, one template/cluster, one commit. Never mix phases in a single change.
- Always verify in the browser before committing — type checking and `manage.py check` don't catch visual regressions.
- If a chunk starts to feel unwieldy mid-session, stop and split it further rather than pushing through — this is exactly the failure mode that caused the original reset.
- Update this section's checklist (or a linked progress note) as templates are completed, so any future session can see at a glance what's done.

---

## Next Steps

1. ~~**Implement survey views** for participants to complete surveys~~ ✅ **Completed**
2. ~~**Create participant dashboard**~~ ✅ **Completed**
3. ~~**Implement task views** for participants to complete lab.js tasks~~ ✅ **Completed**
4. ~~**Test lab.js task completion flow**~~ ✅ **Completed** (Session 3)
5. ~~**Implement automatic task data submission** to Django database~~ ✅ **Completed** (Session 6)
6. ~~**Display filtered trial data in admin panel** for task submissions~~ ✅ **Completed** (Session 7)
7. ~~**Create researcher test mode** for task data~~ ✅ **Completed** (Session 7 — test submissions flagged with `is_test`)
8. ~~**Add CSV export** for task results in admin panel~~ ✅ **Completed** (Session 8 — list action + per-submission download buttons)
9. ~~**Redesign survey system** to support richer question types~~ ✅ **Completed** (Sessions 8-12)
10. ~~**Admin dashboard improvements**~~ ✅ **Completed** (Session 13 — domain filtering, download logging, progress tracking)
11. ~~**Add feedback form to participant account page**~~ ✅ **Completed** (Session 27)
12. ~~**Add exit survey and withdrawal info to account page**~~ ✅ **Completed** (Session 28 — `WithdrawalText` model with markdown rendering; `ExitSurvey` proxy model; full withdrawal flow: account page → exit survey page → account deletion → goodbye page)
13. ~~**Customise allauth confirmation email**~~ ✅ **Completed** (Session 31 — overrides `templates/account/email/email_confirmation_signup_message.txt` with branded welcome; withdrawal confirmation email sent via `send_mail` before account deletion)
14. ~~**Implement demographic survey gateway**~~ ✅ **Completed** (Session 29 — `DemographicSurvey` proxy model; dashboard locked state with greyed-out cards; URL-level guards on `survey_take` and `task_run`)
15. **CSS refactor** — see [CSS Refactor Plan](#css-refactor-plan) below for the full three-phase approach.
16. **Configure production settings** (PostgreSQL, static files, security)

### Bug Fixes & Misc (current branch: `bug-fixes-and-misc`)

#### Bugs
- ~~**Survey success modal reappears on back/refresh**~~ ✅ Fixed — `history.replaceState` strips `?submitted=True` from the URL after the modal opens
- ~~**Consent panel not highlighted when toggled at signup**~~ ✅ Fixed — widened `navLinks` selector to include any `a[data-panel]`, so the "Consent Form" link in the checkbox label now triggers the panel switch
- ~~**Researcher test results not being logged for SUIS survey**~~ ✅ Investigated — data is being saved and scored correctly; issue could not be reproduced

#### Fixes — Participant-facing
- ~~**Completed survey/task behaviour**~~ ✅ Fixed — completed cards on dashboard changed from `<a>` to `<div>` (no hover, no pointer, no link); URL guards added to `survey_take` and `task_run` to redirect participants back to the dashboard if they navigate directly to a completed item
- ~~**Spectrum chart**~~ ✅ Fixed — replaced bell curve SVG with a simple horizontal track and blue dot marker; applied to both the participant account page and the researcher preview chart
- **Environment warning** — added inline to the dashboard info panel and "how to answer" sidebar in survey detail; considered sufficient
- **"World's largest study" hero text** — remove or replace; needs new copy (discuss with Dr Digard)
- **Window size warning styling** — the min-window-size gate on `task_start.html` (Session 33) is functional but the warning banner needs proper design treatment, currently a bare `.alert--warning` strip
- ~~**Username instead of Name at signup**~~ ✅ Fixed — field label updated in both `accounts/forms.py` and `templates/account/signup.html`

#### Fixes — Admin / Researcher-facing
- ~~**Participant display in admin Users list**~~ ✅ Fixed — participants now display as `PRH-{year}-{id:04d}` in the Users list; researchers and superusers show username/email as before
- ~~**CSV export and participant responses**~~ ✅ Fixed — `participant_email` field removed from survey response CSV export; `participant_id` remains
- ~~**Researcher preview**~~ ✅ Fixed — after test submission the form, banner, and progress readout are hidden; only the results table, chart, and a "← Back to survey management" link are shown
- ~~**Admin textarea fields**~~ ✅ Fixed (Session 33) — `QuestionInline` question `text`/`options` and `LikertScaleInline` `scale_labels` textareas were using Django's tall default; narrowed to 5 rows via `formfield_overrides`. `trigger_value` narrowed to a 4-char text input (only ever holds a single digit) via a small `QuestionInlineForm`. Survey-level `description`/`instructions` fields left at default size.
- ~~**Researcher invitation email**~~ ✅ Removed — invitation system was redundant since admins create researchers directly via the Users admin panel; all related models, views, URLs, and forms cleaned up
- ~~**Random answers button**~~ ✅ Added — "Fill with random answers" button on the survey preview page populates all fields with valid random values including gate/branch support; styled as an outline pill button outside the preview banner

#### New Features
- ~~**Real consent form**~~ ✅ Implemented (Session 31) — markdown consent content parsed into individual required checkboxes on the signup page; server-side validation; dynamic fields generated from active `ConsentForm` in the database
- ~~**Withdrawal audit log**~~ ✅ Implemented (Session 31) — `WithdrawalRecord` model snapshots participant ID, exit survey title, and responses as JSON before account deletion; admin with CSV export in long format
- ~~**Withdrawal email**~~ ✅ Implemented (Session 31) — confirmation email sent via `send_mail` + `render_to_string` before `user.delete()`; template at `templates/account/email/withdrawal_confirmation_message.txt`
- ~~**Exit survey data on withdrawal**~~ ✅ Resolved (Session 31) — exit survey responses snapshotted into `WithdrawalRecord.responses` (JSONField) before the user record is deleted; exportable as CSV from admin
- ~~**Year + Month demographic fields**~~ ✅ Implemented (Session 32) — new `dropdown_year_month` question type renders two side-by-side selects; stores as `YYYY-MM`; standalone `dropdown_year` and `dropdown_month` types removed
- ~~**Chart result label**~~ ✅ Implemented (Session 32) — `result_description` TextField added to Survey; shown below participant chart in both spectrum and radar card variants; admin section renamed to "Results Display Information"
- ~~**Chart axis label arrays**~~ ✅ Implemented (Session 33) — `QuestionGroup.result_label` accepts either a plain string or a JSON array `["V", "Visual"]`; `display_label` (short, used for the chart axis) and new `display_label_long` property parse it. Radar legend on both the participant results panel and researcher preview shows "V = Visual" when a long form is set, falling back to just the short label otherwise. Admin help text documents the array syntax.
- ~~**Browser window size check for visual tasks**~~ ✅ Implemented (Session 33) — see below. **Remaining**: warning banner on `task_start.html` needs proper styling (currently functional but placeholder-looking)
- ~~**Forgot password flow**~~ ✅ Verified (Session 33) — no backend changes needed, the allauth pipeline was already fully working. Tested end-to-end against the live dev server: request → branded email with correct reset link → key redemption → set-password form → confirmation page → old password rejected, new password logs in successfully. Fixed a styling inconsistency found along the way: `password_reset.html`, `password_reset_from_key.html`, and `password_change.html` had their submit button and back-link sitting closer together than on login/signup (which have a checkbox row providing spacing before the button) — aligned `.form-submit` margin-top (8px → 28px) and `.back-link` margin-top (12px → 24px) to match

### Survey Redesign Plan (Session 8+)

The survey system is being extended incrementally to support richer question types. Each type is built, tested, and committed before the next is started.

#### Completed: Per-question Likert scales (Session 8)
- New `LikertScale` model — named, reusable scales defined per survey (e.g. "Agreement 1–5", "Vividness 0–10")
- Researchers define scales once as an inline on the Survey admin page using JSON labels
- Each question has a dropdown to select which scale to use; falls back to the survey-level default if none selected
- Scale resolution chain: question's assigned scale → survey default `min_value`/`max_value`/`scale_labels`
- Helper methods on `Question`: `effective_min()`, `effective_max()`, `get_scale_options()`, `apply_reverse_coding()`
- Views and templates updated to use per-question scale options
- Pre-existing bugs in `survey_take` view fixed (scale variable reference, response variable name)

#### Completed: Multiple choice questions (Sessions 9 & 12)
- Added `question_type` field to Question model with choices: `likert`, `multiple_choice_single`, `multiple_choice_multi`, `free_text`
- Two multiple choice variants:
  - **Multiple Choice (Select One)**: participants select exactly one option (validated)
  - **Multiple Choice (Select Multiple)**: participants select one or more options
- Options stored as JSON in Question.options field (e.g. `{"1": "Option A", "2": "Option B"}`)
- **Disabled options** (Session 12): Options can be made visible but unselectable using array syntax:
  - Format: `{"1": "Option A", "2": ["Option B (disabled)"], "3": "Option C"}`
  - Disabled options appear grayed out with disabled checkboxes
  - Useful for "Not applicable" or contextual options
  - Validation automatically filters out disabled options if submitted
- Checkbox-based UI for all multiple choice questions
- Clear participant instructions: "(Select one)" or "(Select one or more)"
- Responses stored as JSON arrays in ParticipantResponse.answer field
- Validation ensures single-select questions only accept one answer
- Helper methods: `get_multiple_choice_options()`, `validate_multiple_choice_answer()`, `get_enabled_option_keys()`
- Binary yes/no questions can be created using a 2-value Likert scale OR multiple choice with two options

#### Completed: Free text questions (Session 9)
- Already fully implemented alongside multiple choice
- Backend validation ensures required fields are filled
- Textarea UI with configurable rows
- Responses stored as plain text in ParticipantResponse.answer field

#### Completed: Question groups & subscales (Sessions 9 & 11)
- New `QuestionGroup` model — serves dual purpose for visual grouping and hidden subscales
- Each group has:
  - `group_code`: Short identifier (auto-generated from order: "1", "2", "3", etc.)
  - `title`: The group heading/subscale name
  - `show_title`: Boolean to control visibility (True = show header to participants, False = hidden subscale)
  - `order`: Display order (auto-increments if set to 0)
- **Use cases:**
  - **Visible groups** (show_title=True): Section headers with instructions (e.g., "Think of a relative or friend"). Questions are bundled into a single matrix card.
  - **Hidden subscales** (show_title=False): Organizational grouping for scoring/analysis only (e.g., "extraversion", "agreeableness"). Questions render as individual cards interleaved with all other questions by their `order` value — participants see no visual grouping, which avoids telegraphing the subscale structure.
- Questions can optionally belong to a group via `group` ForeignKey
- Questions in groups get meaningful `question_id` identifiers: `{group_code}_{question_number}` (e.g., "1_a", "1_b", "2_a", "2_b")
- Ungrouped questions use simple identifiers like "5", "10"
- `question_id` field is:
  - Auto-generated on save from group_code and question_number
  - Stored in database with index for efficient querying
  - Displayed in admin as read-only field
  - Used for data analysis and exports
- Helper method: `question.get_question_identifier()` returns the composite ID
- Template conditionally displays group headers based on `show_title` field
- Admin interface includes QuestionGroup inline on Survey with `show_title` checkbox
- Helper function `organize_questions_by_group()` structures questions by their groups for rendering

#### Completed: Conditional show/hide (Sessions 10, 11 & 12) ✅
**Implementation complete with auto-fill for disabled questions**

- Added `controls_next_n_questions` field to Question model
- Questions can control the next N questions in order (e.g., set to 3 to control next 3 questions)
- Added `trigger_value` field - the answer value that enables controlled questions
- JavaScript dynamically disables/enables questions based on trigger answer
- Removes `required` attribute from disabled questions to prevent validation errors
- Clears values when disabling questions
- Shows instruction: "If answering no, skip to the next N question(s)"
- CSS grays out disabled questions with `conditional-disabled` class
- **Backend validation updated**: Views now check trigger conditions and skip validation for disabled questions
- **Auto-fill disabled questions** (Session 12): Likert questions auto-filled with minimum scale value, non-Likert with "NULL"
- Both `survey_preview` and `survey_take` views handle conditional logic correctly
- Removed all debug console.log statements

#### Completed: Scale factor (Session 11) ✅
**Multiply Likert answers before storing**

- Added `scale_factor` IntegerField to Question model (default=1, minimum value 1)
- Applies to Likert questions only
- Multiplies answer values before storing (e.g., factor of 2 converts 1-5 scale to 2-10)
- Applied after reverse coding: reverse first, then multiply
- Shown in test response table with "Factor" column (displays "×2", "×3", etc.)
- Useful for normalizing different scales or converting to different ranges

#### Completed: Improved question IDs (Session 11) ✅
**Auto-generated, meaningful identifiers**

- Group codes now auto-generated from group order (1, 2, 3...)
- Questions in groups use alphabetic identifiers: `1_a`, `1_b`, `2_a`, `2_b`, etc.
- Ungrouped questions use simple numbers: `5`, `10` (removed "Q" prefix)
- `group_code` is read-only and hidden from admin interface
- `question_number` hidden from admin (still used internally for ID generation)
- System automatically assigns letters based on question position within group

#### Survey Redesign Complete! ✅

All planned features for the incremental survey redesign have been implemented:
- ✅ Per-question Likert scales with flexible min/max values
- ✅ Multiple choice questions (single and multi-select) with disabled options
- ✅ Free text questions
- ✅ Dropdown questions (year, month, country)
- ✅ Question groups with visible/subscale modes
- ✅ Conditional show/hide logic with auto-fill
- ✅ Scale factor for Likert responses
- ✅ Reverse coding for Likert questions
- ✅ Auto-generated question IDs (group_code + letter)
- ✅ CSV export with full metadata
- ✅ NULL recording for optional questions
- ✅ Test mode for researcher preview

The survey system now supports rich, flexible question authoring while maintaining clean data structures for analysis.

#### Authoring approach
- Everything via Django admin
- `LikertScale` inline on Survey for named, reusable scales
- `QuestionGroup` inline on Survey for visible sections or hidden subscales
- Question inline on Survey with all configuration options
- Options stored as JSON (multiple choice, disabled options)
- Preview & Test functionality for researchers

## Data Protection & Research Integrity

The platform includes robust protections to prevent researcher data from contaminating participant responses:

### Researcher Test Mode
- **Automatic Redirection**: Researchers attempting to access participant survey URLs are automatically redirected to test mode
- **Test Data Flagging**: Test mode saves responses to the database flagged with `is_test=True` (consistent with task testing workflow)
- **Clear Identification**: Test responses show "🧪 TEST" badge in admin panel
- **Easy Cleanup**: Test data is filterable and deletable from admin panel
- **Dashboard Separation**: Researchers cannot access the participant dashboard and are redirected to Survey Management

### How It Works
1. **For Researchers — Surveys**:
   - Accessing `/surveys/<id>/take/` → Automatically redirected to `/surveys/<id>/preview/?test_mode=true`
   - Accessing `/dashboard/` → Automatically redirected to `/surveys/` (Survey Management)
   - From Survey Management page: Click "Preview" (read-only) or "Test Mode" (submit test data)
   - Test mode submissions saved to database with `is_test=True` flag
   - Test responses can be reviewed in admin and deleted after verification

2. **For Researchers — Lab.js Tasks**:
   - Researchers run tasks through the full submission pipeline (no redirect)
   - Submissions are saved but flagged with `is_test=True` automatically
   - Flagged submissions show an orange "TEST" badge in the admin and a notice on the completion page
   - Researchers can review the data looks correct in the admin, then delete the test submission

3. **For Participants**:
   - Normal survey and task access works as expected
   - Responses and submissions saved to database with `is_test=False`

4. **Technical Implementation**:
   - View-level checks redirect researchers away from participant survey URLs (`surveys/views.py`)
   - Test mode in `survey_preview` saves responses with `is_test=True` (surveys)
   - `task_submit` view sets `is_test` based on `request.user.is_researcher or request.user.is_staff` (tasks)
   - ParticipantResponse model has `is_test` BooleanField (default False)
   - Admin interfaces show "🧪 TEST" badge and provide filtering by test status

This design allows researchers to fully test the participant experience — including seeing real data in the admin — while keeping test data clearly identifiable and separate. The approach is consistent across both surveys and tasks.

## Recent Updates

### Complete Survey Redesign (Session 12 - Latest) 🎉

**The survey system is now feature-complete!** All planned features for the incremental survey redesign have been successfully implemented.

#### Hidden Subscales (Question Groups) ✅
**Groups can now be visible or hidden for subscale scoring**
- Added `show_title` BooleanField to QuestionGroup model (default=True)
- **Visible groups** (show_title=True): Display section headers to participants (e.g., "Think of a relative or friend")
- **Hidden subscales** (show_title=False): Organizational grouping for scoring/analysis only (e.g., "extraversion", "agreeableness")
- Questions in both types retain meaningful identifiers (1_a, 1_b, 2_a, 2_b) for data analysis
- Template conditionally displays group headers based on show_title field
- Admin interface includes show_title checkbox in QuestionGroup inline

#### Auto-fill Disabled Conditional Questions ✅
**Complete data collection with automatic default values**
- When trigger questions disable follow-up questions, those questions are now auto-filled instead of skipped
- **Likert questions**: Auto-filled with minimum scale value (e.g., 1 for 1-5 scale, 0 for 0-10 scale)
- **Non-Likert questions**: Auto-filled with "NULL"
- Test response table shows `[Auto]` indicator in orange for auto-filled responses
- Auto-filled rows have light yellow background for visual distinction
- **Benefits**: Complete datasets, easier statistical analysis, minimum value represents "not applicable"
- Applies to both `survey_preview` and `survey_take` views

#### NULL Recording for Optional Questions ✅
**Complete data matrix for all participants**
- Optional questions (required=False) that are left blank now record "NULL" instead of being skipped
- Applies to all question types: Likert, multiple choice, free text, and dropdowns
- **Benefits**: Every participant has a response for every question, no missing data in analysis
- Clear semantics: "NULL" = optional question not answered, minimum value = conditionally disabled question

#### Disabled Multiple Choice Options ✅
**Visible but unselectable options for context**
- Multiple choice options can now be disabled using array syntax in JSON
- **Format**: `{"1": "Option A", "2": ["Option B (disabled)"], "3": "Option C"}`
- Disabled options appear grayed out (40% opacity) with disabled checkboxes
- Validation automatically filters out disabled options if somehow submitted
- **Use cases**: "Not applicable" options, showing full scale context, conditional availability
- Helper methods: `get_enabled_option_keys()` returns only selectable options
- Updated help text in admin with syntax example

#### Dropdown Question Types ✅
**Year, Month, and Country dropdowns**
- Added three new question types: `dropdown_year`, `dropdown_month`, `dropdown_country`
- **Year dropdown**: Last 100 years (most recent first) for birth years or event dates
- **Month dropdown**: All 12 months, stores as numbers (1-12), displays as month names
- **Country dropdown**: Comprehensive list of 195+ countries in alphabetical order
- Clean dropdown UI with placeholder text ("-- Select Year --", etc.)
- Optional question text field (can be left blank for self-explanatory dropdowns)
- Consistent NULL handling when left blank
- Helper methods: `get_year_options()`, `get_month_options()`, `get_country_options()`

#### Question Text Now Optional ✅
**Flexibility for self-explanatory question types**
- `Question.text` field now allows `blank=True`
- Useful for dropdown questions where the type is self-explanatory
- Researchers can add custom labels if needed, or leave blank

### Bug Fixes, Scale Factor, Question IDs & CSV Export (Session 11)

#### Conditional Show/Hide Bug Fixed ✅
**Root cause identified and resolved**
- **Problem**: Backend validation was checking all required questions, including ones disabled by conditional logic
- **Solution**: Added trigger condition checking in both `survey_preview` and `survey_take` views
- Views now build a `disabled_questions` set based on trigger values and skip validation for those questions
- Removed all debug console.log statements for cleaner code

#### Scale Factor Implementation ✅
**New feature for scaling Likert responses**
- Added `scale_factor` field to Question model (IntegerField, default=1, min=1)
- Multiplies answer values before storing: e.g., factor of 2 converts 1-5 → 2-10
- Applied after reverse coding for correct order of operations
- Test response table shows "Factor" column with "×2", "×3", etc.
- Visible in admin inline for Likert questions
- Use case: Normalizing different scales or converting to specific ranges

#### Improved Question ID System ✅
**Auto-generated, meaningful identifiers**
- **Group codes**: Now auto-generated from group `order` (1, 2, 3...)
- **Question IDs in groups**: Use alphabetic characters (1_a, 1_b, 2_a, 2_b, etc.)
- **Ungrouped questions**: Simple numbers (5, 10) without "Q" prefix
- `group_code` is read-only and hidden from admin (auto-set on save)
- `question_number` hidden from admin (still used internally)
- Letters assigned automatically based on question position within group

#### Admin UI Improvements ✅
**Better navigation and less clutter**
- **Preview links**: Added to Survey list view and detail view (similar to tasks)
- **Preview links**: Added to LabTask list view (matching survey implementation)
- **Removed fields**: `question_number` and QuestionGroup `description` hidden from admin
- **Cleaner interface**: Less clutter, more focus on essential fields

#### CSV Export for Survey Responses ✅
**Complete data export with full question metadata**

New admin action: "Export responses as CSV (with full question metadata)"

**Export includes per response:**
- **Participant info**: email, ID
- **Survey info**: title, ID
- **Question metadata**: question_id, text, type, order, group_code, group_title
- **Question settings**: required, reverse_coded, scale_factor, min_value, max_value, likert_scale_name
- **Response data**: answer (stored value), is_test, created_at, updated_at

**Usage:**
1. Navigate to Admin → Participant Responses
2. Filter/select responses to export
3. Choose "Export responses as CSV" from Actions dropdown
4. File downloads as: `survey_responses_{survey-name}_{date}.csv`

**Use case**: One row per response, complete context for data analysis in R/Python/Excel

### Survey Management UX & Conditional Logic (Session 10)

#### Survey Management Improvements ✅
- **Unified styling with task management**: Survey management page now uses same card layout, buttons, badges as task page for visual cohesion
- **Simplified test workflow**: Removed separate "Test Mode" button — now just "Preview & Test" (matches task workflow)
- **Test response summary table**: After test submission, shows full overview of all captured data (question IDs, selected values, stored values, labels, reverse coding indicators)
- **Better metadata display**: Shows question count, scale range, randomization status, researcher, created date
- **Improved empty states**: "No Surveys Yet" message with create button

#### Design Evolution Session 10
1. Started with group-based trigger logic (trigger question controls all questions in same group)
2. Explored Option 1: Making QuestionGroup itself a question (rejected - causes data fragmentation with two response tables)
3. Settled on Option 2: N-questions logic (any question controls next N questions, no group dependency)

### Admin Trial Data Display, Test Submissions & Timing Fix (Session 7)

#### Trial Data Filtering Improvements
- **Generalised `get_trial_data()` filter**: Changed from `sender=='Trial' AND ended_on=='response'` to `ended_on=='response'` only, making it work across different lab.js task designs regardless of how researchers name their screens
- **Added `trial_sender_filter` field to `LabTask`**: Optional comma-separated sender names (e.g. `"Trial"`) to narrow filtering further per task. Blank by default — falls back to `ended_on='response'` for all tasks
- Investigated the Flanker task data in detail: 146 raw rows filtered to 37 response rows (36 Trial + 1 Instructions screen accepted as noise)

#### Enhanced TaskSubmission Admin
- **Formatted trial data table**: Detail view now shows `get_trial_data()` results as a readable HTML table with dynamic columns — common fields first (`sender`, `timestamp`, `duration`, `response`, `correct`, etc.), then task-specific fields. Internal lab.js metadata fields hidden
- **Colour-coded `correct` field**: Green for `True`, red for `False`
- **Trial count column**: List view shows number of response rows per submission at a glance
- **Organised fieldsets**: Detail view split into Submission Info, Trial Data (formatted table), and Raw Data (collapsible JSON)

#### Researcher Test Submissions
- **Removed researcher redirect**: Researchers/staff now go through the full submission pipeline instead of being redirected to a data-less preview
- **`is_test` flag on `TaskSubmission`**: Set to `True` automatically for researcher/staff submissions. Defaults `False` — existing participant submissions unaffected
- **Visual flagging in admin**: Orange "TEST" badge in list view; filterable via sidebar; `is_test` checkbox in detail view
- **Test mode notice on completion page**: Researchers see a yellow note explaining the submission is flagged and can be deleted after review
- **Removed stale CSV references**: Completion page no longer mentions CSV file download (leftover from an earlier design)

#### Timing Fix
- **`time_spent_seconds` now sourced from lab.js data**: Uses the `duration` field on the `Task` sender row (milliseconds, recorded by lab.js itself) rather than server-side `started_at`/`completed_at` diffs
- This fixes a race condition where researcher test submissions were recording 0 seconds (submission created and completed in the same request)
- Also more accurate for participants — server-side diffs included instructions page and completion page overhead; lab.js duration reflects only actual time inside the task
- Fallback to server-side diff retained for tasks that don't produce a `Task` sender row
- Existing submissions backfilled with corrected values

### Lab.js Data Submission & Filtering (Session 6)
- **Full data submission pipeline implemented and tested end-to-end**
  - Diagnosed race condition: `after:end` was firing after screen timeout redirect
  - Fixed by using `"run"` event instead — fires immediately when End screen appears
  - Replaced synchronous XHR (deprecated) with `fetch` and `.then()` chaining
  - Redirect now happens inside `.then()` callback, ensuring POST completes first
- **Added `get_trial_data()` method to `TaskSubmission` model**
  - Filters raw lab.js datastore (~146 entries) to meaningful trial rows only (~36)
  - Filters on `sender == 'Trial'` and `ended_on == 'response'`
  - Raw data always preserved in `results_data`; method used for analysis/export
- **Rewrote `LABJS_INTEGRATION.md`** with correct, tested instructions
  - Script placement: "Run" section (not "After end")
  - No timeout on End screen
  - Named variables, `getCookie` helper, console logging for debugging
  - Added data submission flow explanation, testing guide, and troubleshooting

### Bug Fixes & Admin Improvements (Session 5)
- **Fixed File Cleanup Bug**: Resolved issue where bulk delete from admin list view wasn't cleaning up task files
  - Added `delete_queryset()` method to `LabTaskAdmin` to ensure file cleanup on bulk deletes
  - Added `delete_model()` method for extra safety on single deletes
  - Both zip files and unpacked directories now properly deleted in all deletion scenarios
- **Researcher Dropdown Filter**: Added custom forms to filter researcher dropdowns in Survey and LabTask admin
  - Now only shows users with `is_staff=True` (researchers and superusers)
  - Prevents confusion by hiding regular participants from dropdown
  - Implemented via `SurveyAdminForm` and `LabTaskAdminForm`

### Lab.js Data Capture Implementation (Session 4)
- **Implemented Data Extraction**: Identified correct method to capture clean trial data
  - Using `this.parent.options.datastore.data` to get structured trial data
  - Avoids metadata and internal lab.js state from `exportJson()`
  - Logs data to browser console for verification
- **Created Working Snippet**: JavaScript code for completion screen
  - Captures clean trial-by-trial data
  - Stores in `window.labJsTaskData` for future POST request
  - Maintains redirect to completion confirmation page
- **Cleaned Up Test Environment**: Removed all orphaned task files
  - Cleared media/lab_tasks/unpacked/ directory
  - Cleared media/lab_tasks/zips/ directory
  - Ready for fresh testing workflow
- **Next Steps**:
  - Test data capture across multiple task types for consistency
  - Implement POST request to `/tasks/<id>/submit/` endpoint
  - Save data to TaskSubmission.results_data field

### Lab.js Task Testing & Refinement (Session 3)
- **Tested Task Completion Flow**: Verified end-to-end task execution and completion
  - Task preview and execution work correctly
  - `${TASK_ID}` placeholder replacement confirmed working
  - Redirect to completion confirmation page functional
  - Task completion status tracking verified
- **Simplified Integration Approach**: Updated documentation with minimal completion screen
  - Removed complex HTML and button handlers to avoid timing issues
  - Simple redirect-only approach (empty screen + timeout + redirect script)
  - Updated `LABJS_INTEGRATION.md` with streamlined instructions
- **Identified Data Submission Issue**: CSV download not working, needs database submission
  - lab.js Download plugin not triggering reliably
  - Task data not being saved to database (only completion status)
  - `/tasks/<id>/submit/` endpoint exists but needs proper integration
  - Researcher test mode needed for data preview

### Lab.js Task Integration (Session 2)
- **Complete Task System Implementation**: Full integration of lab.js experimental tasks
  - Zip file upload with automatic unpacking and validation
  - Task management interface for researchers (`/tasks/`)
  - Task preview and execution views with CORS-free implementation
  - Instructions screen with task metadata (domain, time limit, etc.)
  - Integrated into participant dashboard alongside surveys
- **Task Completion Flow (Template Approach)**:
  - Researchers add completion screen to lab.js exports
  - Automatic `${TASK_ID}` placeholder replacement during upload
  - Completion confirmation page at `/tasks/<id>/complete/`
  - Status tracking: started → in_progress → completed
  - Time calculation from task start to completion
  - Preserves lab.js CSV download functionality
- **Enhanced Admin Interface**:
  - Upload status indicators (✓ Unpacked / ⧗ Pending)
  - Preview links for quick testing
  - Inline help text with upload instructions
  - Link to full integration documentation
- **Comprehensive Documentation**:
  - Created `LABJS_INTEGRATION.md` with step-by-step guide
  - Code snippets for researchers to copy-paste
  - Troubleshooting section and advanced customization
  - Examples for auto-redirect and manual button approaches
- **Data Protection Extended to Tasks**:
  - Researchers automatically redirected to preview mode
  - TaskSubmission model tracks participant progress
  - Role-based access control consistent with surveys
- **Migration**: Added `task_slug`, `task_directory` fields; renamed `task_file` to `zip_file`

### Git Repository Setup & Security (Session 1)
- **Environment Variables**: Implemented secure configuration with python-decouple
  - SECRET_KEY, DEBUG, and ALLOWED_HOSTS moved to .env file
  - `.env.example` template for other developers
  - All secrets excluded from version control
- **Git Initialization**: Repository set up with proper .gitignore
  - 77 files committed in initial commit
  - Proper exclusions for sensitive data, media files, and virtual environment

### Survey Model Refactoring & Advanced Features
- **Question Model Restructure**: Changed from many-to-many to one-to-many relationship
  - Questions now belong to a single survey (direct ForeignKey)
  - Removed `SurveyQuestion` intermediary model
  - Simplified data model while maintaining all functionality
  - Participant responses remain linked by question ID (unchanged)
- **Question Ordering Improvements**:
  - Auto-increment ordering (leave at 0 for automatic numbering)
  - Manual ordering support (set specific order numbers)
  - `normalize_question_order()` method on Survey model
  - Admin action: "Normalize question order" to renumber questions sequentially
  - Removed unique constraint to allow flexible reordering without data loss
  - Display order reflects position in rendered list (not database order field)
- **Question Randomization**: Seeded randomization for reducing order effects
  - Added `randomize_questions` BooleanField to Survey model
  - Uses participant ID as seed for consistent ordering across sessions
  - Each participant gets unique random order, same participant always sees same order
  - Only affects participant views (admin shows database order)
  - Helps detect acquiescence bias and reduce order effects
- **Reverse Coding**: Individual question inversion for detecting response patterns
  - Added `reverse_coded` BooleanField to Question model
  - Inverts scale values before storing: `stored = (max + min) - selected`
  - Example (1-5 scale): Participant selects 5 → Database stores 1
  - Invisible to participants (they see normal scale)
  - Test mode shows both selected and stored values with **[RC]** indicator
  - Useful for detecting acquiescence bias (always clicking same value)
- **Data Integrity Protection**:
  - Removed question deletion logic from save() method
  - Responses always linked by question ID (order changes don't affect data)
  - Safe reordering without risk of losing participant responses

### Researcher Invitation System
- **Invitation-Based Researcher Appointment**: Implemented secure invitation system for appointing new researchers
  - Added `ResearcherInvitation` model with unique UUID tokens, expiration tracking, and audit trail
  - Created `InviteResearcherForm` for sending invitations with configurable expiration (1-30 days)
  - Created `ResearcherSignupForm` for invitation-based registration
  - Built custom admin interface with "Invite New Researcher" button and invitation management
  - Added invitation acceptance view with automatic researcher account creation
  - Email notifications sent automatically with invitation links (console backend for development)
  - Resend invitation functionality for pending invitations
- **Removed Manual Promotion System**: Deprecated old researcher appointment methods
  - Removed bulk admin actions (`make_researcher`, `remove_researcher_status`)
  - Made `is_researcher` field read-only (except for superusers)
  - Removed `is_researcher` from user creation form
  - Updated documentation to reflect invitation-only workflow
- **Enhanced Security**: Invitation tokens are unique, expire automatically, and can only be used once
- **Audit Trail**: Track who invited whom and when through the admin panel

### Data Protection & Admin Improvements
- **Researcher Data Isolation**: Implemented automatic redirection system to prevent researchers from submitting real participant data
  - Researchers are redirected to test mode when accessing participant survey URLs
  - Dashboard access restricted to participants only
  - View-level protection ensures data integrity
- **Editable Consent Forms**: Added `ConsentForm` model for managing consent text via admin panel
  - Support for versioning and history tracking
  - Active/inactive status management
  - Template integration with fallback support
- **Admin Panel Cleanup**: Removed django-allauth's `EmailAddress` model from admin to reduce confusion
  - Documentation added for re-enabling if needed
  - Single "Accounts" section with Users and Consent Forms
- **Custom Admin Branding**: Configured admin site headers and titles
  - Customizable site header, title, and index title
  - Easy to modify in `research_platform/urls.py`

### Survey Views & Participant Dashboard
- **Survey Views Implemented**: Created complete survey taking functionality for participants
  - `survey_take`: Participants can complete surveys with full validation
  - `survey_preview`: Researchers can preview how surveys appear to participants
  - `survey_list`: Researcher-only survey management interface
- **Test Mode Feature**: Researchers can test surveys without saving to database
  - Validates all responses (required fields, scale ranges)
  - Displays submitted data in a formatted table
  - Shows question number, text, numeric value, and label
  - Helps verify survey configuration before activating
- **Likert Scale Customization**: Survey-level scale configuration
  - Moved scale settings (`min_value`, `max_value`, `scale_labels`) from Question to Survey model
  - All questions in a survey share the same Likert scale
  - Custom labels support (e.g., "1: Strongly Disagree" through "5: Strongly Agree")
  - Labels displayed under radio buttons for clarity
- **Participant Dashboard**: Created dedicated dashboard at `/dashboard/`
  - Shows available surveys (active, not yet completed)
  - Shows completed surveys with progress tracking
  - Displays survey metadata (domain, question count, scale range)
  - Direct links to start or update survey responses
- **Role-Based Access Control**: Enforced permissions
  - Survey management (`/surveys/`) restricted to researchers only
  - Participants redirected to dashboard if attempting to access
  - Separate navigation paths for participants vs researchers
- **Templates Created**:
  - `survey_list.html`: Survey management interface with Preview/Test/Edit buttons
  - `survey_detail.html`: Survey form with dynamic Likert scale rendering
  - `participant_dashboard.html`: Participant homepage with survey listings

### Initial Researcher Management System (Deprecated - Now Uses Invitations)
- Implemented automatic staff status granting for researchers
- Created Researchers group with granular permissions
- Set up signals to automatically manage researcher permissions
- Created `setup_researcher_permissions` management command
- **Note**: Manual promotion system has been replaced with invitation-based system (see latest updates above)

### Participant Registration with Consent
- Implemented custom signup form with required consent checkbox
- Added consent form text storage to User model
- Created responsive signup and login templates
- Configured django-allauth to use custom form
- Added home page with role-based navigation

### Survey Model Evolution
- Changed Question model from multiple question types to Likert scale only
- Moved scale settings to Survey level (applies to all questions in survey)
- Added JSON field for custom scale labels
- Simplified Question model to text and required flag only

## Admin Panel Features

All models are registered in the Django admin panel with:
- List displays with relevant fields
- Search functionality
- Filtering options
- Inline editing for related models (e.g., Questions within Surveys)

### Custom Branding
The admin panel has been customized with research platform branding:
- **Site Header**: "Aphantasia Research Administration" (displayed at top of admin pages)
- **Site Title**: "Aphantasia Research Admin" (browser tab title)
- **Index Title**: "Site Administration" (heading on admin home page)
- Customizable in `research_platform/urls.py` (lines 11-13)

### Consent Form Management
Administrators can edit participant consent forms directly through the admin panel:
- Navigate to **Accounts → Consent Forms**
- Create new versions with version identifiers (e.g., "v2.0", "2024-11")
- Only one consent form can be active at a time
- All historical consent forms are preserved for audit purposes
- Each participant's account stores the exact consent text they agreed to

## URLs Structure

### Authentication & Admin
- `/admin/` - Django admin panel (researchers and superusers)
- `/admin/accounts/researcherinvitation/invite/` - Send researcher invitation (researchers and superusers)
- `/accounts/invite/accept/<token>/` - Accept researcher invitation and register
- `/accounts/account/` - Participant account page (profile + consent record)
- `/accounts/signup/` - Participant registration with consent form
- `/accounts/login/` - User login
- `/accounts/logout/` - User logout
- `/accounts/password/change/` - Change password
- `/accounts/password/reset/` - Request password reset email
- `/accounts/` - Other authentication URLs (email verification)

### Participant Views
- `/dashboard/` - Participant dashboard showing available and completed surveys
- `/surveys/<id>/take/` - Take a survey (participants)

### Researcher Views
- `/surveys/` - Survey management list (researchers only)
- `/surveys/<id>/preview/` - Preview survey as participants see it (researchers only)
- `/surveys/<id>/preview/?test_mode=true` - Test survey with data validation display (researchers only)

### Task Views (To Be Implemented)
- `/tasks/` - Lab task views

### Home
- `/` - Home page with role-based navigation

## Deployment Roadmap

### Git Tagging — the Baseline Concept

A **git tag** marks a specific point in the project's history as a named, referenceable snapshot. Unlike a branch (which moves forward as you commit), a tag stays fixed. Think of it as a bookmark you can always return to.

```bash
# Create a tag
git tag v1.0-stable

# List all tags
git tag

# Return to a tagged state (read-only look)
git checkout v1.0-stable

# Create a new branch from a tag (e.g. to start deployment config)
git checkout -b railway v1.0-stable
```

### Planned Deployment Path

The intention is to deploy in two stages, both branching from the same stable tag:

1. **Tag a stable version** once development features are complete (`v1.0` or similar)
2. **Railway** (interim) — branch from the tag, add Railway-specific config, deploy for researcher content entry and light user testing before the study goes live. Data from this phase should be treated as test data and migrated carefully.
3. **University servers** (production) — branch from the same tag, configure for the university's infrastructure requirements. This is the live study environment.

The production config work (PostgreSQL, static files, `DEBUG=False`, environment variables) is largely the same for both — Railway is practice for the real thing.

### What needs doing before tagging

- CSS refactor — see [CSS Refactor Plan](#css-refactor-plan)
- Customise allauth confirmation email templates
