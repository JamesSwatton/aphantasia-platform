# Research Platform

A Django-based research platform for collecting participant data through surveys and lab.js tasks.

## Tech Stack

- Django 5.2.8
- django-allauth (email/password authentication)
- SQLite (development database)
- HTMX/Alpine.js (frontend, to be integrated)

## Project Structure

```
research_platform/
├── accounts/          # User authentication and custom user model
├── core/             # Core models (Domain, Researcher, Participant, Progress, DataDownloadLog)
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
- **User**: Custom user model with `is_researcher` and `is_participant` fields, and `consent_text` field to track the consent form version agreed to during registration
- **ConsentForm**: Editable consent form text shown to participants during registration. Supports versioning and history tracking.
- **ResearcherInvitation**: Invitation system for appointing new researchers. Tracks invitation tokens, expiration dates, and who invited whom.

### core
- **Domain**: Research domains/categories
- **Researcher**: Extended researcher profile
- **Participant**: Extended participant profile
- **Progress**: Tracks participant progress through surveys/tasks
- **DataDownloadLog**: Audit log for data downloads

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

1. **Run the setup command** (only needed once):
   ```bash
   python manage.py setup_researcher_permissions
   ```
   This creates a "Researchers" group with appropriate permissions.

2. **Create your first superuser** (if you haven't already):
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

## Next Steps

1. ~~**Implement survey views** for participants to complete surveys~~ ✅ **Completed**
2. ~~**Create participant dashboard**~~ ✅ **Completed**
3. ~~**Implement task views** for participants to complete lab.js tasks~~ ✅ **Completed**
4. ~~**Test lab.js task completion flow**~~ ✅ **Completed** (Session 3)
5. ~~**Implement automatic task data submission** to Django database~~ ✅ **Completed** (Session 6)
6. ~~**Display filtered trial data in admin panel** for task submissions~~ ✅ **Completed** (Session 7)
7. ~~**Create researcher test mode** for task data~~ ✅ **Completed** (Session 7 — test submissions flagged with `is_test`)
8. ~~**Add CSV export** for task results in admin panel~~ ✅ **Completed** (Session 8 — list action + per-submission download buttons)
9. **Redesign survey system** to support richer question types ⚠️ **In progress (feature-surveys branch)**
10. **Create researcher dashboard** with data analytics
11. **Integrate HTMX** for dynamic interactions
12. **Add Alpine.js** for frontend interactivity
13. **Implement data export** functionality (CSV, JSON, Excel) for surveys
14. **Add data visualization** for research insights
15. **Configure production settings** (PostgreSQL, static files, security)

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
  - **Visible groups** (show_title=True): Section headers with instructions (e.g., "Think of a relative or friend")
  - **Hidden subscales** (show_title=False): Organizational grouping for scoring/analysis (e.g., "extraversion", "agreeableness")
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
- `/accounts/signup/` - Participant registration with consent form
- `/accounts/login/` - User login
- `/accounts/logout/` - User logout
- `/accounts/` - Other authentication URLs (password reset, email verification)

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
