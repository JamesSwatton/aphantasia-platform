# Phantasia Research Hub

A Django-based research platform for collecting participant data through surveys and lab.js tasks, built for the Eye's Mind Research Group's aphantasia study at the University of Edinburgh.

For project history, see [CHANGELOG.md](CHANGELOG.md). For the CSS refactor and deployment plans, see [docs/](docs/).

## Known Open Items

- **Window size warning banner styling** — the minimum-window-size gate on `templates/tasks/task_start.html` is functional but the warning banner is currently a bare `.alert--warning` strip; needs proper design treatment.
- **"World's largest study" hero copy** — needs replacing on the home page; discuss wording with Dr Digard.
- Responsive design has not yet been started — see `docs/css-refactor-plan.md` for the working pattern the responsive-design branch is expected to reuse.
- **University hosting requirements** — none started yet: WCAG accessibility audit, accessibility statement, privacy statement, DPIA, and EqIA are all required before the university-servers production deploy can go live. See [docs/deployment.md](docs/deployment.md#university-hosting-requirements).

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
- **ConsentForm**: Editable consent form text shown to participants during registration, rendered as individual required checkboxes. Supports versioning and history tracking.
- **WithdrawalText**: Editable copy shown on the withdrawal/exit-survey flow.
- **WithdrawalRecord**: Audit snapshot (anonymised participant ID + exit survey responses as JSON) created before an account is deleted.

### core
- **Domain**: Research domains/categories
- **DataDownloadLog**: Audit log for data downloads
- **Message**: Researcher-to-participant messaging system

### surveys
- **Survey**: Survey definitions with configurable Likert scale settings (`min_value`, `max_value`, `scale_labels`), optional question randomization, and result-display metadata (`result_min`/`result_max`/`result_aggregation`/`result_description`) for participant-facing scoring. `FeedbackSurvey`, `ExitSurvey`, and `DemographicSurvey` are proxy models built on `Survey` for the mid-study feedback form, the withdrawal exit survey, and the dashboard-gating demographic survey respectively.
- **QuestionGroup**: Groups questions into a visible section (shown to participants) or a hidden subscale (grouped only for scoring, no visual hint to participants).
- **LikertScale**: Named, reusable Likert scales definable per survey.
- **Question**: Individual survey questions belonging to a single survey, optionally in a `QuestionGroup`. Supports multiple question types (Likert, multiple choice single/multi, free text, dropdowns), ordering, required flag, reverse coding, scale factor, and conditional branching (`controls_next_n_questions` / `trigger_value`).
- **ParticipantResponse**: Participant responses to survey questions (linked by question ID, independent of order).

### tasks
- **LabTask**: Lab.js task uploads. Includes optional `trial_sender_filter` field (comma-separated sender names) to narrow trial data filtering beyond the default `ended_on='response'` filter, and an optional minimum-window-size gate (`requires_min_window_size`/`min_window_width`/`min_window_height`).
- **TaskSubmission**: Participant task submissions and results. Includes `is_test` flag for researcher/staff test runs, `get_trial_data()` method which filters raw lab.js data to response rows only, and logged browser window size.

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

Researchers are created directly through the Django admin panel by a superuser — there is no invitation system (an earlier invitation-based flow was removed; see [CHANGELOG.md](CHANGELOG.md), Session 32).

### Creating a Researcher Account

1. **Log in as a superuser** (only superusers can grant researcher/staff status).
2. Navigate to **Accounts → Users → Add user**.
3. Enter an email and password. `is_researcher` is available directly on the add form (in the "Role Information" fieldset) — tick it.
4. Save, then re-open the new user and tick **is_staff** under Permissions — this is what grants admin panel access. It's not on the initial add form, so it's a required second step.
5. The new researcher can now log in with their email/password at `/accounts/login/` and access the admin panel.

### Researcher Permissions

- `is_researcher` is editable only by superusers — for a non-superuser viewing another user's admin page, the field is read-only (`accounts/admin.py`, `get_readonly_fields`).
- Researchers with `is_staff=True` have full admin access to Surveys, Questions, Lab Tasks, Domains, Participant Responses, Task Submissions, and Data Download Logs (view/add only for response and submission data — deletion of participant data is restricted).
- Django system settings and superuser-only areas remain restricted to superusers.

### Data Protection for Researcher Accounts

Researchers keep `is_participant = True` by convention (so they can exercise the full participant experience), but **cannot submit real participant data** — view-level protections redirect researchers to test mode whenever they hit a participant survey/task URL. See "Data Protection & Research Integrity" below.

### Removing Researcher Status

Only a superuser can do this: **Users → select the researcher → uncheck `is_researcher`** (and `is_staff`, if admin access should also be revoked — it is not removed automatically) **→ Save**.

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

#### Question Types
Beyond Likert scales, a question can be: multiple choice (select one or select multiple, with optional disabled/context-only options), free text, or a dropdown (year + month combined, or country). `Question.question_type` selects the type; each renders and validates differently in `survey_take`/`survey_preview`.

#### Question Groups & Subscales
`QuestionGroup` groups questions either as a **visible section** (`show_title=True` — shown to participants as a titled matrix card, e.g. "Think of a relative or friend") or a **hidden subscale** (`show_title=False` — grouped only for scoring; questions render individually, interleaved with the rest of the survey by `order`, with no visual hint to participants that they belong together). Grouped questions get composite IDs like `1_a`, `1_b`.

#### Conditional Branching
A question can control the next N questions via `controls_next_n_questions` + `trigger_value`: when the trigger question's answer matches `trigger_value`, the controlled questions reveal (`.branch` UI, slides open); otherwise they stay collapsed and are auto-filled (minimum scale value for Likert, `NULL` otherwise) so every participant has a complete response row regardless of branch.

#### Results & Scoring
Surveys with `result_min`/`result_max` configured (survey-level, or per-`QuestionGroup` for subscale surveys) get participant-facing scoring: a spectrum chart for single-score surveys, or a radar/spider chart across subscales for surveys with multiple scored `QuestionGroup`s. See `surveys/utils.py` (`get_survey_result()`, `get_all_results()`) and the Results tab on `/accounts/account/`.

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
- `/tasks/<id>/submit/` - Receives the lab.js datastore JSON POST on task completion

### Documentation
Full integration guide, including the completion-screen code snippet researchers add to their lab.js exports, is at [docs/LABJS_INTEGRATION.md](docs/LABJS_INTEGRATION.md) — step-by-step instructions, troubleshooting, and advanced customization examples.

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
- `/accounts/account/` - Participant account page (profile, consent record, results, feedback)
- `/accounts/account/withdraw/` - Exit survey and account withdrawal flow
- `/accounts/signup/` - Participant registration with consent form
- `/accounts/login/` - User login
- `/accounts/logout/` - User logout
- `/accounts/password/change/` - Change password
- `/accounts/password/reset/` - Request password reset email
- `/accounts/` - Other authentication URLs (email verification)

### Participant Views
- `/dashboard/` - Participant dashboard showing available and completed surveys and tasks
- `/surveys/<id>/take/` - Take a survey (participants)
- `/tasks/<id>/run/` - Run a lab.js task (participants)
- `/tasks/<id>/complete/` - Task completion confirmation
- `/messages/` - Participant messages inbox

### Researcher Views
- `/surveys/` - Survey management list (researchers only)
- `/surveys/<id>/preview/` - Preview survey as participants see it (researchers only)
- `/surveys/<id>/preview/?test_mode=true` - Test survey with data validation display (researchers only)
- `/tasks/` - Task management list (researchers only)
- `/tasks/<id>/preview/` - Preview a lab.js task (researchers only)

### Home
- `/` - Home page with role-based navigation

## Deployment

See [docs/deployment.md](docs/deployment.md) for the git-tagging strategy and the planned Railway → university-server deployment path.
