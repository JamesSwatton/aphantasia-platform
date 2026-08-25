# Deployment Roadmap

## Git Tagging — the Baseline Concept

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

## Planned Deployment Path

The intention is to deploy in two stages, both branching from the same stable tag:

1. **Tag a stable version** once development features are complete (`v1.0` or similar)
2. **Railway** (interim) — branch from the tag, add Railway-specific config, deploy for researcher content entry and light user testing before the study goes live. Data from this phase should be treated as test data and migrated carefully.
3. **University servers** (production) — branch from the same tag, configure for the university's infrastructure requirements. This is the live study environment.

The production config work (PostgreSQL, static files, `DEBUG=False`, environment variables) is largely the same for both — Railway is practice for the real thing.

## University Hosting Requirements

The domain `phantasia-research-hub.mvm.ed.ac.uk` has been approved (confirmed by IS US BioQuarter and Central MVM Support, 2026-08-22, in an email to Dr Digard). Before the university-servers production stage can go live, the site must satisfy five requirements. These are compliance/process items owned by Dr Digard and the university, not something this codebase can complete on its own — the table below tracks status and who's responsible for what.

| Requirement | Owner | Status | Notes |
|---|---|---|---|
| WCAG accessibility compliance ("as far as possible") | Dev (this repo) | Not started | No accessibility audit has been done yet. Natural to fold into the upcoming responsive-design work rather than as a separate pass — both touch every template. |
| Accessibility statement (published page) | Dev, content from Dr Digard | Not started | Static page once the accessibility audit's actual state of compliance is known — can't honestly write the statement before the audit. |
| Privacy statement (published page) | Dr Digard / university data protection process | Not started | University template/guidance: [data-protection.ed.ac.uk/guidance/privacy-notices](https://data-protection.ed.ac.uk/guidance/privacy-notices). Dev can build the page once text exists. |
| DPIA (Data Protection Impact Assessment) — required before going live | Dr Digard / university data protection process | Not started | University process: [data-protection.ed.ac.uk/data-protection-impact-assessments](https://data-protection.ed.ac.uk/data-protection-impact-assessments). See the technical data-collection summary below — written to save Dr Digard re-deriving this from the code. |
| EqIA (Equality Impact Assessment) — required before going live | Dr Digard / university | Not started | University process: [equality-diversity.ed.ac.uk/EqIA](https://equality-diversity.ed.ac.uk/EqIA). |
| Minimise PII storage — only what's clearly needed | Dev (this repo) | Audited 2026-08-24, one item flagged | See "PII minimisation" below. |

None of these gate the Railway interim deploy (that's explicitly for internal researcher/tester use, not the live study) — they gate the **university-servers production stage** specifically, i.e. before real participants use the live site.

### Technical data-collection summary (for the DPIA/EqIA)

What the platform actually stores, verified against the current models (`accounts/models.py`, `surveys/models.py`, `tasks/models.py`, `core/models.py`) as of 2026-08-24:

**Identifying/account data** — `User` model: email address, hashed password, `date_joined`, `last_login`, `consent_text` (the exact consent form text the participant agreed to, snapshotted at signup — this *is* the compliance record, not incidental collection). No name field is required at signup. No IP address, user-agent, or other request metadata is captured anywhere in the codebase (confirmed by search — there is no `request.META` client-info capture in any view).

**Research data** — `ParticipantResponse.answer` (survey answers, linked to the participant by foreign key) and `TaskSubmission.results_data` (raw lab.js trial data, no identifying fields embedded). Free-text survey/task questions could incidentally capture identifying information if a participant chooses to type it, but the platform doesn't request or require that.

**Deliberately collected, tied to a stated methodological need** — `TaskSubmission.window_width`/`window_height` (browser window size at task start): added because visual tasks need a minimum screen size to produce usable data; documented in the LabTask model's "Screen Requirements" fieldset.

**Withdrawal / right-to-erasure flow** (`accounts/views.py`, `exit_survey_submit`) — genuine hard delete: `user.delete()` cascades via foreign key to remove that participant's `ParticipantResponse` and `TaskSubmission` rows entirely. Before deletion, a `WithdrawalRecord` is created — deliberately with **no foreign key to `User`**, so it survives the delete — containing only a derived participant ID (`PRH-{year}-{id}`, not the user's name or email), the exit survey title, and the exit survey's `{question, answer}` pairs. The participant's email is used once, transiently, to send a withdrawal confirmation email, and is not persisted anywhere after that.

**Flag for Dr Digard — confirmed live, not hypothetical**: `WithdrawalRecord.responses` is retained indefinitely with no link back to the (deleted) user, by design, for audit purposes. The current active **Exit Survey** has a `free_text` question ("Do you have any suggestion on how we could improve the experience...") — any answer a withdrawing participant writes there is captured into that permanent record with no automated check for accidentally-included identifying content (e.g. naming a family member, a clinician, or themselves). This is a content/survey-design decision rather than a code bug — worth deciding whether that question should be removed/reworded to avoid open free text, or whether exit-survey free-text responses should get a manual review step before being treated as permanent. (The Participant Feedback Form has a similar free-text question, but its responses stay linked to the user and are deleted along with the rest of their data on withdrawal — not the same risk.)

**Not collected**: IP addresses, user-agent strings, device fingerprints, or any other request-level metadata; no name is required at signup; no third-party analytics or tracking scripts are present in any template.

### PII minimisation

Per the university's "should not store any PII unless there is a clear requirement" instruction: every stored field above traces to a specific need (auth, consent audit, research data, or the documented window-size methodology requirement). The one open item is the `WithdrawalRecord` free-text risk noted above — everything else checked out clean on this audit.

## Pre-tagging checklist

- [x] CSS refactor — see [CSS Refactor Plan](css-refactor-plan.md)
- [x] Customise allauth confirmation email templates (signup + withdrawal, `templates/account/email/`)

Both complete as of 2026-08-24 — `main` is ready to tag `v1.0`.

## Railway deployment notes

Work happens on the `railway` branch, cut from the `v1.0` tag.

**Done (verified locally, not yet deployed):**
- **PostgreSQL**: `DATABASES` reads `DATABASE_URL` via `dj-database-url` when set, falling back to SQLite otherwise. `psycopg2-binary` added. Verified against a local Postgres 17 install: `manage.py migrate` builds the full schema from scratch, and existing SQLite data copies over cleanly via `dumpdata`/`loaddata`.
- **Static files**: WhiteNoise added to `MIDDLEWARE` (compressed, cache-busted output via `STORAGES`). Verified `collectstatic` produces hashed files and they serve correctly under `DEBUG=False`.
- **App server**: `gunicorn` added; `Procfile` defines a `release` step (`migrate --noinput && collectstatic --noinput`) and a `web` process (`gunicorn research_platform.wsgi:application`). **Note**: Railway's builder (Railpack) does not actually run the `release` line — see "Done (deployed and verified live)" below for what Railway actually executes. The `Procfile` is kept for documentation/portability to other platforms.
- **HTTPS/security settings**: `SECURE_SSL_REDIRECT`, secure cookies, HSTS — all gated on `not DEBUG` so local dev is unaffected. `SECURE_PROXY_SSL_HEADER` trusts `X-Forwarded-Proto`, since Railway terminates TLS at its own proxy. `CSRF_TRUSTED_ORIGINS` reads from a new env var (needs the real `https://` origin once a domain is assigned).
- **Media storage**: `MEDIA_ROOT` now reads from a `MEDIA_ROOT` env var, falling back to the local `media/` folder for development. On Railway, this should point at a mounted **Railway Volume** (a persistent disk attached to the service — survives redeploys, unlike the rest of the container's filesystem, which is rebuilt from scratch every deploy). Chose a volume over S3-compatible storage because `LabTask`'s zip-unpacking logic (`tasks/models.py`) uses raw filesystem calls (`os.path.join`, `shutil.rmtree`, `zipfile.extractall`) rather than Django's storage abstraction — a volume needs zero code changes, since it's still a real local filesystem from the app's point of view; S3 would need that unpacking logic rewritten first. Verified locally: an existing lab task's unpacked directory still resolves and its files are found on disk with the new `MEDIA_ROOT` config.

**Done (deployed and verified live, 2026-08-25):**
- Railway project created (`honest-presence` in the dashboard, app service named `phantasia-research-hub`), connected to the `railway` branch on GitHub.
- Postgres add-on provisioned; env vars set (`SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASE_URL` referencing the Postgres service, `CSRF_TRUSTED_ORIGINS`, `DEBUG=False`).
- Public domain generated: `phantasia-research-hub-production.up.railway.app`.
- Railway's builder (Railpack) does not run the `Procfile`'s `release:` line — `migrate` and `collectstatic` had to be moved into the service's Start Command directly: `python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn research_platform.wsgi:application`.
- Local survey/question/user data migrated to Railway's Postgres via `dumpdata`/`loaddata` over a private SSH tunnel (`railway connect Postgres --tunnel-only`) — surveys, questions, consent/withdrawal text, domains, and all local users (including the existing superuser). Confirmed: admin login at `/admin/` works with existing local credentials.
- Participant response/submission data was deliberately left behind (test data, not needed on a fresh interim deploy).
- **Railway Volume** created on the app service, mounted at `/data/media`; `MEDIA_ROOT` env var set to match. The Flanker Task zip was re-uploaded through the live admin and confirmed working end-to-end (upload → unpack → admin preview → participant task start).
- Uploading surfaced two real bugs, unrelated to Railway/Railpack, that would have broken any `DEBUG=False` deploy: (1) the `STORAGES` setting only defined `"staticfiles"` and had silently dropped Django's `"default"` file storage entry, so any `FileField` save (`LabTask.zip_file`) raised `InvalidStorageError` — fixed by adding an explicit `"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}` entry; (2) `urls.py` only wired up `/media/...` serving when `DEBUG=True` (Django's dev-only `static()` helper) — WhiteNoise serves static files, not user-uploaded media, so on Railway media 404'd everywhere. Fixed by adding an `else` branch routing `MEDIA_URL` to `django.views.static.serve` when `DEBUG=False`. Both fixed, verified locally then on Railway.

**Still open:**
- Smoke-test the broader participant + researcher flow (survey completion, exit survey/withdrawal, feedback form) against the deployed instance before pointing testers at it — only the lab task upload/serve path has been end-to-end verified so far.

## Responsive design vs. deployment

The `responsive-design` branch is developed independently of the Railway deploy, then merged into `main` at safe checkpoints (a breakpoint's template fully done and browser-verified, not mid-template) — each merge redeploys Railway with the improvement, so testers see incremental progress rather than an in-progress broken state. See [CSS Refactor Plan](css-refactor-plan.md) for the phased working pattern this reuses.
