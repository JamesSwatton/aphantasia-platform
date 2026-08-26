# Lab.js Task Integration Guide

This guide explains how to prepare your lab.js experiments for upload to the research platform.

## Quick Start

After creating your experiment in the lab.js builder, you need to add a **completion screen** that submits participant data to the platform and redirects them back. This takes about 5 minutes.

## Step-by-Step Instructions

### 1. Open Your Experiment in Lab.js Builder

Open your completed experiment in the lab.js builder interface.

### 2. Add a Final "Screen" Component

1. At the very **end** of your experiment flow (after all trials/loops), add a new **"Screen"** component
2. You can drag it from the component panel or use the "+" button
3. Name it **"End"**

### 3. Configure the Completion Screen

In the Screen component editor:

**Content (HTML):** Leave blank or add a brief message. The screen will redirect automatically.
```html
<main></main>
```

**Important settings:**
- **Timeout:** Leave blank (no timeout) — the script controls when the redirect happens
- **Responses:** Leave blank — no participant input needed

### 4. Add the Data Submission Script

In the Screen component, go to the **"Scripts"** tab and add the following to the **"Run"** section:

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

**Important notes:**
- Use exactly `${TASK_ID}` — the platform replaces this with the real task ID on upload
- The script goes in **"Run"**, not "After end" — "After end" can race with other screen events
- Do **not** set a timeout on this screen — the redirect is handled by the script above
- The `.catch()` ensures participants are always redirected even if submission fails

### 5. Export Your Task

1. Click **"Export"** in the lab.js builder
2. Choose **"Generic (zip)"** format
3. Download the zip file
4. **Do not unzip it** — upload the zip file directly to the platform

### 6. Upload to Platform

1. Log into the admin panel
2. Go to **"Lab Tasks"** → **"Add Lab Task"**
3. Fill in the title, description, domain, and other details
4. Upload your zip file
5. Click **"Save"**

The platform will automatically:
- ✓ Unpack your zip file
- ✓ Replace `${TASK_ID}` with the actual task ID
- ✓ Make your task available to participants

---

## How Data Submission Works

When a participant completes the task:

1. The End screen's **Run** script fires immediately when the screen is reached
2. The full lab.js datastore is POSTed as JSON to `/tasks/${TASK_ID}/submit/`
3. The platform stores the raw data in the `TaskSubmission.results_data` field
4. The participant is redirected to `/tasks/${TASK_ID}/complete/` (the platform confirmation page)
5. The participant clicks "Confirm Completion" and is returned to the dashboard

The platform automatically filters the raw datastore to extract only meaningful trial response rows (screens with actual participant responses) when the data is used for analysis. The full raw data is always preserved.

---

## Testing Your Integration

After uploading:

1. Log in as a **participant account** (not a researcher) — researchers are automatically redirected to preview mode and their data is not saved
2. Go to the dashboard and run the task
3. Complete the task
4. Verify you are redirected to the platform completion page
5. Click "Confirm Completion"
6. Check **Admin → Task Submissions** to confirm `results_data` has been populated

**Note:** If you need to test as a researcher, use the **Preview** link in the task management page. Your data will not be saved, but you can verify the task runs correctly.

---

## Troubleshooting

### "The task doesn't redirect after completion"
- Make sure the script is in the **"Run"** section, not "After end"
- Check the browser console for JavaScript errors
- Ensure the End screen has **no timeout set**
- Verify the End screen is the **last** component in your flow

### "results_data is null in the admin"
- You may be logged in as a researcher — researcher data is never saved by design
- Test with a participant account in a separate browser or incognito window
- Check the browser console for a `'Data submission failed'` error

### "I see ${TASK_ID} in the URL instead of a number"
- The placeholder wasn't replaced during upload
- Try deleting the task and re-uploading the zip
- Check that `${TASK_ID}` appears in the script exactly as written (case-sensitive, with curly braces)

### "The browser console shows a CSRF error"
- This should not happen as the script reads the CSRF token from the Django session cookie
- Make sure the participant is logged in before running the task
- If the issue persists, contact the platform administrator

### "The data looks correct in the console but isn't saving"
- Check that the participant account does not have `is_staff=True` or `is_researcher=True`
- Only pure participant accounts (no researcher flags) have their data saved

---

## What Data Is Captured

The platform stores the complete lab.js datastore, which includes every screen event. A typical flanker-style task with 36 trials will produce ~146 raw entries including:

| Screen type | Count | Included in analysis |
|---|---|---|
| Trial screens (with response) | 36 | **Yes** |
| Fixation/empty screens | 36 | No |
| Feedback screens | 36 | No |
| Instructions, loop summaries | ~3 | No |

Each trial entry contains:
- Trial parameters (e.g. `orientation`, `congruency`, `position`)
- `response` — what the participant pressed
- `correctResponse` — the correct answer
- `correct` — boolean
- `duration` — reaction time in milliseconds
- Timestamps

The platform uses `TaskSubmission.get_trial_data()` to filter to meaningful trial rows when exporting or displaying data.

---

## Questions?

If you need help integrating your tasks, please contact the platform administrator.
