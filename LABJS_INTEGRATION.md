# Lab.js Task Integration Guide

This guide explains how to prepare your lab.js experiments for upload to the research platform.

## Quick Start

After creating your experiment in lab.js builder, you need to add a **completion screen** that redirects participants back to the platform. This takes about 2 minutes.

## Step-by-Step Instructions

### 1. Open Your Experiment in Lab.js Builder

Open your completed experiment in the lab.js builder interface.

### 2. Add a Final "Screen" Component

1. At the very **end** of your experiment flow (after all trials/loops), add a new **"Screen"** component
2. You can drag it from the component panel or use the "+" button
3. Name it something like "Task Complete" or "Thank You"

### 3. Configure the Completion Screen

In the Screen component editor:

**Title:** `Complete`

**Content (HTML):**
```html
<div class="text-center">
  <h1>Task Complete!</h1>
  <p class="lead">Thank you for completing this task.</p>
  <p>Your results have been downloaded.</p>
  <p><strong>Redirecting back to dashboard in 3 seconds...</strong></p>
  <p style="margin-top: 2rem;">
    <button id="return-now" style="font-size: 1.2rem; padding: 0.75rem 2rem;">
      Return Now
    </button>
  </p>
</div>
```

### 4. Add the Redirect Script

In the same Screen component, go to the **"Scripts"** tab and add this to the **"After end"** section:

```javascript
// Redirect back to platform
window.location.href = "/tasks/${TASK_ID}/complete/";
```

**Important:** Use exactly `${TASK_ID}` - the platform will automatically replace this with the correct task ID when you upload.

### 5. Set Screen Timeout (Optional)

In the Screen component settings:
- Set **"Timeout"** to `3000` (milliseconds) to auto-redirect after 3 seconds
- OR leave it blank if you want participants to click the button manually

### 6. Add Button Click Handler (If Using Button)

If you want the "Return Now" button to work immediately, add this to the **"After prepare"** script:

```javascript
// Make the return button work
document.getElementById('return-now').addEventListener('click', function() {
  window.location.href = "/tasks/${TASK_ID}/complete/";
});
```

### 7. Export Your Task

1. Click **"Export"** in lab.js builder
2. Choose **"Generic (zip)"** format
3. Download the zip file
4. **Do not unzip it** - upload the zip file directly to the platform

### 8. Upload to Platform

1. Log into the admin panel
2. Go to **"Lab Tasks"** → **"Add Lab Task"**
3. Fill in the title and description
4. Upload your zip file
5. Click **"Save"**

The platform will automatically:
- ✓ Unpack your zip file
- ✓ Replace `${TASK_ID}` with the actual task ID
- ✓ Make your task available to participants

## Complete Example

Here's a complete example of what the final screen should look like in lab.js builder:

### Screen Component: "Complete"

**Content:**
```html
<div class="text-center">
  <h1 style="color: #27ae60;">✓ Task Complete!</h1>
  <p class="lead">Thank you for completing this task.</p>
  <p>Your results have been downloaded to your computer.</p>
  <hr style="margin: 2rem 0;">
  <p><strong>Redirecting back to dashboard in 3 seconds...</strong></p>
  <p style="margin-top: 2rem;">
    <button id="return-now" class="btn btn-primary btn-lg">
      Return to Dashboard Now
    </button>
  </p>
</div>
```

**Scripts → After prepare:**
```javascript
// Make button work
document.getElementById('return-now').addEventListener('click', function() {
  window.location.href = "/tasks/${TASK_ID}/complete/";
});
```

**Scripts → After end:**
```javascript
// Auto-redirect after timeout
window.location.href = "/tasks/${TASK_ID}/complete/";
```

**Settings:**
- Timeout: `3000` (3 seconds)
- Skip: Leave unchecked

## Testing Your Integration

After uploading:

1. Go to **"Lab Tasks"** in admin
2. Click **"Preview"** on your task
3. Complete the task
4. Verify you're redirected back to the platform
5. Check that the completion is recorded

## Troubleshooting

### "The task doesn't redirect"
- Make sure you added the redirect script to **"After end"**
- Check that you used `${TASK_ID}` exactly (case-sensitive)
- Verify the completion screen is the **last** component in your flow

### "I see ${TASK_ID} in the URL instead of a number"
- The placeholder wasn't replaced during upload
- Try re-uploading the task
- Contact support if the issue persists

### "The download plugin isn't working"
- Make sure `lab.plugins.Download` is still in your study plugins
- Don't remove any existing plugins when adding the completion screen

## Advanced: Customization

You can customize the completion screen to match your branding:

```html
<div style="max-width: 600px; margin: 0 auto; padding: 2rem;">
  <div style="text-align: center;">
    <img src="your-logo.png" alt="Logo" style="max-width: 200px; margin-bottom: 2rem;">
    <h1>Experiment Complete</h1>
    <p>Thank you for your participation in this study.</p>
  </div>

  <div style="background: #f0f0f0; padding: 1.5rem; border-radius: 8px; margin: 2rem 0;">
    <h3>What happens next:</h3>
    <ul style="text-align: left;">
      <li>Your data has been securely saved</li>
      <li>Results were downloaded to your computer</li>
      <li>You can view other available studies on your dashboard</li>
    </ul>
  </div>

  <button id="return-now" style="background: #3498db; color: white; border: none; padding: 1rem 2rem; font-size: 1.1rem; border-radius: 5px; cursor: pointer;">
    Return to Dashboard
  </button>
</div>

<script>
document.getElementById('return-now').addEventListener('click', function() {
  window.location.href = "/tasks/${TASK_ID}/complete/";
});
</script>
```

## Questions?

If you need help integrating your tasks, please contact the platform administrator.
