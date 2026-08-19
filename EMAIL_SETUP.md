# Email Setup Guide

This platform sends two types of automated email:

1. **Signup confirmation** — sent by allauth when a participant creates an account (currently set to `"optional"` so not enforced, but the email is sent if a backend is configured)
2. **Withdrawal confirmation** — sent to the participant when they delete their account (not yet implemented in code — waiting on email infrastructure)

Currently `EMAIL_BACKEND = console` in settings, meaning all emails are printed to the terminal and nothing is sent to real addresses. The steps below cover what is needed to make real emails work in production.

---

## Step 1 — Choose a sending address

Decide on a `From:` address for outgoing emails. Options:

- **A University of Edinburgh address** (e.g. `noreply@ed.ac.uk` or a group mailbox like `phantasia-hub@ed.ac.uk`) — requires IT Services to authorise the address for SMTP relay
- **A dedicated domain address** (e.g. `noreply@phantasiaresearchhub.com`) — requires owning the domain and configuring DNS records (SPF, DKIM, DMARC) to avoid spam filtering

The sending address should be one participants recognise and trust. Using Dr Digard's address (`berengere.digard@ed.ac.uk`) as the reply-to but a no-reply address as the sender is a common pattern.

---

## Step 2 — Choose an email sending method

Two main options:

### Option A — University of Edinburgh SMTP relay
Contact IT Services and ask whether the university provides an authenticated SMTP relay for research web applications. If so, they will provide:
- `EMAIL_HOST` — the SMTP server address (e.g. `smtp.ed.ac.uk`)
- `EMAIL_PORT` — typically `587` (TLS) or `465` (SSL)
- `EMAIL_HOST_USER` — the authenticated username
- `EMAIL_HOST_PASSWORD` — the password or app token
- Whether `EMAIL_USE_TLS` or `EMAIL_USE_SSL` is required

This is the most straightforward option if the university supports it.

### Option B — Transactional email service
Services like **SendGrid**, **Mailgun**, or **Amazon SES** are designed for automated emails from web apps. They offer:
- Better deliverability (less likely to end up in spam)
- Delivery logs and bounce tracking
- Free tiers sufficient for a research platform at this scale

SendGrid's free tier allows 100 emails/day. Setup involves:
1. Create an account at sendgrid.com
2. Verify your sending domain (add DNS records they provide)
3. Create an API key
4. Install `django-sendgrid-v5` or use SMTP credentials they provide

---

## Step 3 — Configure Django settings

Once you have SMTP credentials, add these to your production `.env` file (never hardcode credentials):

```
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-username
EMAIL_HOST_PASSWORD=your-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Phantasia Research Hub <noreply@yourdomain.com>
```

Then update `settings.py` to read these from the environment:

```python
# Replace the current console backend line with:
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="webmaster@localhost")
```

This keeps the console backend for local development (no `.env` entry needed) and switches to real SMTP in production.

---

## Step 4 — Configure DNS records (if using a custom domain)

To prevent emails being marked as spam, three DNS records need to be added to your domain:

- **SPF** — declares which servers are allowed to send email from your domain
- **DKIM** — cryptographically signs outgoing emails so recipients can verify they're genuine
- **DMARC** — tells receiving servers what to do if SPF/DKIM checks fail

Your email provider (SendGrid, Mailgun etc.) will give you the exact DNS values to add. If using the University's SMTP relay, their IT team handles this for `ed.ac.uk` addresses.

---

## Step 5 — Customise email templates

### Allauth signup confirmation email
Override the default allauth templates by creating these two files:

- `templates/account/email/email_confirmation_subject.txt` — subject line
- `templates/account/email/email_confirmation_message.txt` — plain text body

Example subject:
```
Confirm your Phantasia Research Hub account
```

Example body:
```
Hello,

Thank you for signing up to the Phantasia Research Hub.

Please confirm your email address by clicking the link below:

{{ activate_url }}

If you did not create an account, you can safely ignore this email.

Best wishes,
The Eye's Mind Research Group
University of Edinburgh
```

### Withdrawal confirmation email
This needs to be implemented in code once the email infrastructure is in place. It would be sent in `accounts/views.py` inside `exit_survey_submit`, just before `user.delete()`, using the participant's email address which is still available at that point.

---

## Step 6 — Test before going live

Before deploying, test the full email flow:

1. Set `EMAIL_BACKEND = django.core.mail.backends.smtp.EmailBackend` in your local `.env` temporarily
2. Sign up with a real email address — confirm the verification email arrives and looks correct
3. Go through the withdrawal flow — confirm the confirmation email arrives
4. Check spam folders — if emails land there, DNS records need attention
5. Revert `EMAIL_BACKEND` to console for local dev

---

## Summary checklist

- [ ] Decide on sending address (University SMTP or transactional service)
- [ ] Obtain SMTP credentials or API key
- [ ] Add credentials to production `.env`
- [ ] Update `settings.py` to read email config from environment
- [ ] Add DNS records if using a custom domain (SPF, DKIM, DMARC)
- [ ] Write allauth email templates (`email_confirmation_subject.txt`, `email_confirmation_message.txt`)
- [ ] Implement withdrawal confirmation email in `accounts/views.py`
- [ ] Test end-to-end before going live
