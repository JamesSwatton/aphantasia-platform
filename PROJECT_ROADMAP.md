# Research Platform - Project Roadmap

**Project:** Aphantasia Research Platform
**Tech Stack:** Django 5.2.8, django-allauth, SQLite (dev), HTMX/Alpine.js (planned)
**Date:** February 25, 2026

---

## ✅ Completed Features

### Core Infrastructure
- **Django Setup:** Complete authentication system with django-allauth (email/password)
- **User Model:** Custom user model with participant & researcher roles
- **Security:** Git repository with environment variables, proper .gitignore
- **Consent System:** Editable consent forms with versioning and history tracking
- **Researcher Management:** Secure invitation system with unique tokens and expiration tracking

### Survey System (Fully Functional)
- **Survey Creation:** Complete survey authoring through Django admin panel
- **Per-Question Likert Scales:** Reusable named scales (e.g., "Agreement 1-5", "Vividness 0-10")
- **Multiple Choice Questions:** Single-select and multi-select support with JSON storage
- **Free Text Questions:** Textarea input with configurable rows
- **Question Groups:** Named sections with meaningful identifiers (e.g., "A_01", "B_02")
- **Question Randomization:** Seeded per participant for consistent order across sessions
- **Reverse Coding:** Individual question inversion for detecting response patterns
- **Participant Dashboard:** Shows available and completed surveys with progress tracking
- **Researcher Test Mode:** Full validation with data preview, no database saves
- **Data Protection:** Automatic redirection prevents researchers contaminating participant data

### Lab.js Task Integration (Fully Functional)
- **Zip Upload:** Automatic unpacking and validation of lab.js exports
- **Task Management:** Researcher interface for viewing, previewing, and editing tasks
- **Task Execution:** Participants run tasks with direct navigation (no CORS issues)
- **Data Submission:** Complete pipeline capturing full lab.js datastore as JSON
- **Trial Data Filtering:** Configurable filtering to extract meaningful response rows
- **Test Mode:** Researchers run tasks through real pipeline, submissions flagged with `is_test=True`
- **CSV Export:** Download functionality for task results from admin panel
- **Accurate Timing:** Time tracking from lab.js duration data (not server timestamps)

---

## ⚠️ In Progress (Has Bug)

### Conditional Show/Hide Logic (Session 10)
**Status:** Implementation complete but blocked by validation bug

**What Works:**
- Backend implementation using N-questions trigger logic
- JavaScript dynamically enables/disables questions based on trigger answer
- Visual feedback with grayed-out disabled questions
- Clear instructions: "If answering no, skip to the next N question(s)"

**Blocking Bug:**
- Form validation fails even though `required` attributes are correctly removed from disabled questions
- Debug confirmed controlled questions show `required=false, disabled=true` (correct state)
- Form submission still blocked by validation error
- Need to identify: which field is blocking, browser vs Django validation, check for JS errors

**Next Step:** Debug validation issue to allow form submission

---

## 🔜 To Do (Priority Order)

### Immediate Priorities (Survey Redesign Completion)
1. **Fix Conditional Show/Hide Validation Bug** ← TOP PRIORITY
   - Debug why validation blocks submission despite correct attribute states
   - Test across different browsers
   - Ensure Django backend accepts empty values for disabled fields

2. **Subscales Implementation**
   - Groups with optional scale overrides
   - Different from visual grouping (affects data structure)

### Core Features
3. **Researcher Dashboard with Data Analytics**
   - Summary statistics across surveys and tasks
   - Participant completion rates
   - Response distribution visualizations
   - Data quality metrics

4. **Data Export for Surveys**
   - CSV export with configurable columns
   - JSON export for raw data
   - Excel export with formatted sheets
   - Include question identifiers, group codes, metadata

5. **Data Visualization**
   - Response distribution charts
   - Completion tracking over time
   - Participant demographics (if collected)
   - Export-ready graphs and tables

### Frontend Enhancement
6. **HTMX Integration**
   - Dynamic form updates without page reload
   - Real-time validation feedback
   - Smooth survey navigation

7. **Alpine.js Integration**
   - Client-side interactivity
   - Enhanced conditional logic
   - Improved user experience

### Production Readiness
8. **Production Configuration**
   - PostgreSQL database setup
   - Static file serving (whitenoise or CDN)
   - Security settings (HTTPS, CSRF, CORS)
   - Email backend configuration
   - Environment-specific settings files

---

## Feature Summary

| Category | Completed | In Progress | To Do | Total |
|----------|-----------|-------------|-------|-------|
| Survey System | 10 | 1 | 1 | 12 |
| Lab.js Integration | 8 | 0 | 0 | 8 |
| Data Management | 0 | 0 | 3 | 3 |
| Frontend | 0 | 0 | 2 | 2 |
| Infrastructure | 5 | 0 | 1 | 6 |
| **Total** | **23** | **1** | **7** | **31** |

---

## Recent Sessions Summary

### Session 10 (Latest - February 25, 2026)
- Unified survey management UX with task management (card layout, consistent styling)
- Simplified test workflow ("Preview & Test" instead of separate buttons)
- Implemented conditional show/hide logic with N-questions approach
- **Bug identified:** Validation fails on form submission despite correct JavaScript state

### Session 9
- Multiple choice questions (single & multi-select)
- Free text questions
- Question groups with meaningful identifiers
- Question numbering system (e.g., "A_01", "B_02", "Q5")

### Session 8
- Per-question Likert scales with reusable scale definitions
- Survey management improvements
- CSV export for task results

### Session 7
- Trial data filtering improvements
- Enhanced TaskSubmission admin with formatted tables
- Researcher test submissions with `is_test` flag
- Timing fix using lab.js duration data

### Session 6
- Full lab.js data submission pipeline
- Fixed race condition with fetch/then chaining
- Trial data filtering method

---

## Technical Architecture

### Apps Structure
- **accounts:** User authentication, consent forms, researcher invitations
- **core:** Domain, Researcher, Participant, Progress, DataDownloadLog
- **surveys:** Survey, Question, QuestionGroup, LikertScale, ParticipantResponse
- **tasks:** LabTask, TaskSubmission
- **dashboard:** Participant dashboard views

### Data Protection
- View-level checks redirect researchers from participant URLs
- Test mode saves responses with `is_test=True` flag
- Consistent approach across surveys and tasks
- Clear identification with badges in admin panel

### Key Features
- Question responses linked by question ID (not order) for data integrity
- Seeded randomization for consistent per-participant question order
- Reverse coding with transparent display in test mode
- Configurable trial data filtering for different lab.js designs
- Audit logging for data downloads and researcher actions

---

## Next Session Goals

1. **Fix conditional validation bug** (top priority)
2. **Complete subscales implementation** (if time permits)
3. **Begin researcher dashboard** (if conditional logic is stable)

---

*Generated: February 25, 2026*
