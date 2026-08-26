# Survey Question Guide

A field-by-field walkthrough of the survey admin page, in the order the fields
appear on screen, plus the idiosyncrasies of each question type. For how survey
*responses* flow through to participants and results generally, see the "Survey
System Features" section of the main README.

## Survey Information

- **Title, Description, Instructions, Researcher, Domain, Is Active, Is Priority** —
  standard fields.
  - **Instructions** is optional survey-specific text shown in the sidebar before the
    standard how-to-answer points.
  - **Researcher** dropdown only lists staff users.
  - **Is Priority** pins the survey to the top of participant-facing lists.
- **Randomize Questions** — shuffles question order per participant. The shuffle is
  seeded by participant ID, so a given participant always sees the same order if they
  return to the survey.
- **Preview** — a link to preview the survey as it will appear to participants. Shows
  "Save survey first to generate preview link" until the survey has been saved once.

## Default Likert Scale

- **Min Value / Max Value** — the numeric range used by any Likert question in this
  survey that doesn't have its own Likert Scale assigned (see the Likert Scales
  inline below).
- **Scale Labels** — JSON mapping each value to a label, e.g.
  `{"1": "Strongly Disagree", "2": "Disagree", "3": "Neutral", "4": "Agree", "5": "Strongly Agree"}`.

This is a fallback only. If you assign a specific Likert Scale to a question, these
survey-level values are ignored for that question.

## Results Display Information

- **Result Aggregation** — Mean or Sum. How question scores are combined into a
  group/survey result.
- **Result Min / Result Max** — the display range participant scores are mapped to
  for charts (e.g. 0–100). Leave blank if you don't need a mapped/scored result at
  all.
- **Result Description** — short explanatory text shown to participants alongside
  their result (e.g. "Higher scores indicate greater vividness of mental imagery").

A survey only produces a scored result if either these two Result Min/Max fields are
both set, or at least one Question Group below has a Result Label set (see Question
Groups). **Only numeric answers count toward scoring** — free text, multiple choice,
and dropdown answers are stored as non-numeric strings and are silently excluded from
aggregation. In practice this means only Likert questions (after reverse
coding/scale factor are applied) feed into the result.

## Likert Scales (inline)

Lets you define named, reusable scales within this survey — useful when different
questions need different ranges or labels than the survey default (e.g. a 1–7 scale
for one set of items and 1–5 for another).

- **Name, Min Value, Max Value, Scale Labels** — same shape as the survey defaults
  above, just scoped to this named scale instead of the whole survey.
- A question picks up a specific scale via its own **Likert Scale** dropdown (see
  Questions inline below). If a question doesn't select one, it falls back to the
  survey's Default Likert Scale.
- This inline only shows rows for scales that already exist on this survey — it
  starts empty (aside from the one blank "add new" row) until you've added at least
  one. That's expected; most surveys that only need one scale never need to touch
  this section at all and can rely on the Default Likert Scale fields instead.

## Question Groups (inline)

A **Question Group** collects related questions together, either as a visible
section or a hidden subscale.

- **Title** — the participant-facing heading/prompt for the group (e.g. "Think of a
  relative or friend").
- **Show Title** — if checked, the Title is displayed to participants as a heading.
  If unchecked, the group has no visible presence at all — it exists purely to score
  its questions together as a named subscale. Use unchecked groups when you want a
  composite score for a set of questions without exposing the grouping in the survey
  itself.
- **Result Label** — the label used for this group in charts/results. Leave blank to
  fall back to the Title. A group only counts as a scored subscale if this is
  non-blank. For a short chart-axis label paired with a longer legend string, enter a
  JSON array of two strings: `["V", "Visual"]` — "V" appears on the axis, "Visual" in
  the legend.
- **Result Min / Result Max** — override the survey-level result range just for this
  subscale's display. Leave blank to inherit the survey's range.
- **Order** — display order of the group. Leave at 0 to auto-append to the end.

Notes:

- **Group Code isn't a field you can set here** — it's not shown in this inline
  because it's auto-derived from Order on every save (`group_code = str(order)`).
  Reordering a group changes its code, which in turn changes the identifiers of the
  questions inside it (see Question IDs below).
- Like the Likert Scales inline, this section only lists groups that already exist on
  this survey, so it starts empty until you add one. A survey with no groups at all
  is completely normal — questions just render top to bottom without any grouping or
  subscale scoring.

## Questions (inline)

Each row is one question. Fields, in the order they appear:

### Question Type

One of six types — see [Question Types](#question-types-in-detail) below for full
behavior of each.

### Text

The question text/label shown to participants. Can be left blank for
self-explanatory types like dropdowns.

### Order

- **0 means "add to the end"** — auto-assigned the next available position.
- Setting a specific number does **not** shift other questions out of the way, so
  duplicate or out-of-sequence order values are possible and won't error.
- Randomizing (via the survey's Randomize Questions checkbox) shuffles the
  participant-facing order but doesn't change the stored Order values.
- Use the **"Normalize question order"** action on the Surveys list (select the
  survey, choose the action from the dropdown) to renumber everything sequentially
  and clean up gaps/duplicates. Safe to run any time — responses are linked to
  questions by ID, not by order, so this doesn't affect already-recorded data. It
  will, however, change the `question_id` of any ungrouped questions (see below).

### Group

Assigns the question to one of this survey's Question Groups. Only lists groups that
already exist on this survey (so this dropdown is empty until you've added at least
one group above — nothing to do with whether the survey itself has been saved).
Leave blank for an ungrouped question.

### Question ID (read-only)

Auto-generated, shown for reference only — you can't edit it directly.

- **Grouped questions** get a composite ID like `1_a`, `1_b`, `2_a` — the group's
  code, an underscore, then a letter sequence (a, b, ... z, aa, ab, ...) based on the
  question's position within the group. This is recalculated on every save, so
  reordering questions within a group changes their letters.
- **Ungrouped questions** just use their Order number as the ID (e.g. `"5"`). This
  means an ungrouped question's ID **changes if you reorder the survey or run
  Normalize Question Order.** If you need stable identifiers for a question across
  data exports over time, put it in a group — group membership changes far less
  often than raw order does.

### Likert Scale

Only relevant for `likert` type questions. Picks one of the scales defined in the
Likert Scales inline above; leave blank to use the survey's Default Likert Scale.
Only lists scales that exist on this survey (empty until you've added one above).

### Required

If checked and the participant leaves the question blank, submission is blocked.
Applies to every question type.

### Reverse Coded

Likert-only. Inverts the stored value using `(max + min) - answer`. Use this for
negatively-worded items so all items in a scale score in the same direction. This
only changes what's *stored* — participants still see and pick from the normal
scale.

### Scale Factor

Likert-only. Multiplies the answer before storing. Applied **after** reverse coding,
so the order is: raw answer → reverse-coded (if enabled) → × scale factor → stored.
Must be 1 or greater — 0 and negative values aren't allowed. Example: a factor of 2
turns a 1–5 scale into stored values of 2–10.

Note: range validation for Likert answers only happens when a participant actually
submits a response. The admin won't warn you if a question's assigned Likert Scale
conflicts with the survey defaults — check ranges manually when reviewing a survey.

### Options

Multiple-choice-only. JSON mapping option keys to labels:

```json
{"1": "Option A", "2": "Option B", "3": "Option C"}
```

- **Keys must be numeric strings** ("1", "2", ...) — they're sorted and compared as
  integers internally. A non-numeric key will error.
- **To show an option but make it unselectable** (e.g. a "coming soon" or
  context-only choice), use an array instead of a plain string:

  ```json
  {"1": "Option A", "2": ["Option B (disabled)"], "3": "Option C"}
  ```

  Disabled options remain visible to participants, just greyed out/unselectable. If a
  disabled value is force-submitted anyway (e.g. via browser devtools), it's silently
  dropped rather than raising a validation error.
- The same format is used for both `multiple_choice_single` and
  `multiple_choice_multi` — the type alone determines whether more than one
  selection is allowed. Selecting more than one option on a "select one" question is
  rejected.

### Controls Next N Questions / Trigger Value

Together these set up conditional branching — see
[Conditional Questions](#conditional-questions-branching) below.

## Question Types in detail

| Type | What it renders |
|---|---|
| `likert` | Radio-button scale |
| `multiple_choice_single` | Radio buttons (select one) |
| `multiple_choice_multi` | Checkboxes (select multiple) |
| `free_text` | Open text box |
| `dropdown_year_month` | Two dropdowns: year + month |
| `dropdown_country` | One dropdown: country name |

**Likert Scale** — see Likert Scale/Reverse Coded/Scale Factor fields above; those
are the only settings that apply.

**Multiple Choice (Select One / Select Multiple)** — see the Options field above.
Answers are stored as a JSON-encoded list even for single-select.

**Free Text** — no type-specific settings beyond Required. The full text is stored
exactly as submitted; any truncation you might see in a preview/summary table is
purely a display convenience, not what's actually saved.

**Dropdown (Year + Month)** — renders two `<select>`s. Years list the last 100 years,
descending; months are a fixed January–December list. Both fields must be filled in
to count as answered — filling in only one is treated as blank, not flagged as a
partial-answer error. Stored as a single combined string, e.g. `2019-March`.

**Dropdown (Country)** — a single dropdown from a fixed, alphabetical list of ~190
countries. No configuration needed; the stored value is just the country name.

## Conditional Questions (branching)

Set on the *trigger* question, using the two fields at the end of its row:

- **Controls Next N Questions** — how many of the immediately-following questions
  this question gates. 0 means "not a trigger."
- **Trigger Value** — the exact answer string required to unlock those questions
  (e.g. `"2"` for a "Yes" option on a 1–2 Likert scale).

Important constraints:

- **Branching only works between ungrouped questions.** If the trigger or any of the
  questions it would control belong to a Question Group, the proximity logic won't
  pick them up — keep conditional blocks out of groups.
- Which questions get controlled is determined purely by **Order proximity** — the
  next N questions *by order number* after the trigger, not by any reference to
  specific question IDs. Reordering questions after setting up a branch can silently
  change which questions end up controlled.
- **If a participant's answer doesn't match the Trigger Value**, the controlled
  questions aren't simply left blank — they're automatically disabled and filled in
  on submission:
  - Likert questions are auto-filled with the scale's **minimum** value.
  - Every other type is auto-filled with the literal string `"NULL"`.

  This guarantees a response row exists for every question regardless of which branch
  a participant took, but it means **these auto-filled rows need to be filtered or
  accounted for in analysis** — a Likert "1" or a literal `"NULL"` string may mean
  "skipped by branch logic," not a genuine answer.

This is unrelated to the **demographic gateway** described below, which is a
survey-level setting, not a per-question one.

## Survey types: regular, feedback, exit, demographic

The main "Surveys" list in admin only shows ordinary surveys. Feedback, Exit, and
Demographic surveys are the same underlying model but managed under their own
sections in admin, hidden from the regular list:

- **Feedback Survey** — hidden from the participant dashboard; shown inline on the
  participant's account page after they've completed a set number of regular surveys
  (configurable, defaults to 2).
- **Exit Survey** — shown when a participant chooses to withdraw from the study.
- **Demographic Survey** — the gateway survey. Participants cannot access any other
  survey or task until they've submitted this one. **Only one survey should ever have
  this enabled** — the system doesn't enforce that for you.

All the field and question-type behavior described above applies identically inside
these — they're the same Survey/Question models underneath.

## Exporting data

The **Participant Responses** admin includes an "Export responses as CSV (with full
question metadata)" action. Each row already includes question type, group, required
flag, reverse-coding/scale-factor settings, and effective min/max/scale name, so you
generally don't need to cross-reference the survey structure separately when
analyzing exports. Every export is logged for research-integrity auditing.
