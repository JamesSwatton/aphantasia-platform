# Phantasia Research Hub — Django Backend Reference

A reference document covering three backend patterns for the Phantasia Research Hub. Written to accompany the static HTML/CSS frontend (`index.html`, `home.html`, `signup.html`, `account.html`). When moving to a Django-backed implementation, these are the patterns to reach for.

**Contents:**

1. [Score pipeline](#1-score-pipeline) — computing derived imagery scores on save, rendering into the account page
2. [Consent record](#2-consent-record) — immutable audit trail of what each participant agreed to
3. [Withdrawal](#3-withdrawal) — deleting a participant's data while preserving an audit trail

---

## 1. Score pipeline

**Decision:** scores are computed on save (via `post_save` signal or explicit call from the submission view) and stored as snapshots. Rendered into the page server-side as JSON, picked up by Chart.js.

### Flow

```
Participant completes a questionnaire
         ↓
QuestionnaireResponse saved to DB
         ↓
post_save signal fires
         ↓
Score pipeline recalculates derived scores
         ↓
ImageryScore row created (new snapshot)
         ↓
Next /account/ visit: view reads latest snapshot
         ↓
Template renders scores as JSON + HTML, Chart.js picks them up
```

Three distinct concerns: **storing raw responses**, **deriving scores**, and **rendering**. Keep them separate so each can be tested and changed independently.

### Models

```python
# participants/models.py
from django.db import models
from django.contrib.auth.models import User

class Participant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    participant_id = models.CharField(max_length=20, unique=True)
    joined_at = models.DateTimeField(auto_now_add=True)
```

```python
# measures/models.py
class QuestionnaireResponse(models.Model):
    """A single completed questionnaire — e.g. VVIQ, Bucknell, etc."""
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    measure_type = models.CharField(max_length=50)   # 'vviq', 'bais', etc.
    raw_score = models.FloatField()
    answers = models.JSONField()                      # individual question responses
    completed_at = models.DateTimeField(auto_now_add=True)
```

```python
# scores/models.py
class ImageryScore(models.Model):
    """A snapshot of derived imagery scores. New row each recalculation."""
    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name='imagery_scores'
    )
    calculated_at = models.DateTimeField(auto_now_add=True)

    # VVIQ-style score, used for the spectrum
    vviq_score = models.FloatField(null=True)

    # Modality scores out of 10, used for the radar
    visual = models.FloatField(null=True)
    auditory = models.FloatField(null=True)
    spatial = models.FloatField(null=True)
    tactile = models.FloatField(null=True)
    memory = models.FloatField(null=True)

    # Which measures contributed — useful for showing confidence / completeness
    source_measures = models.JSONField(default=list)

    class Meta:
        ordering = ['-calculated_at']
        indexes = [models.Index(fields=['participant', '-calculated_at'])]
```

**Design notes:**

- Keeping scores as snapshots rather than mutating a single row gives a free audit trail — you can see how someone's scores changed over time, useful for a longitudinal study.
- The index on `(participant, -calculated_at)` matters — without it, fetching the latest score would scan the whole table as the database grows.
- `null=True` on modality fields: a participant might not have completed all measures yet. Better to store `None` than fabricate a zero.

### Score computation (pure function, separate module)

```python
# scores/pipeline.py
from dataclasses import dataclass, field
from typing import Optional, List

from measures.models import QuestionnaireResponse
from scores.models import ImageryScore


@dataclass
class ComputedScores:
    vviq_score: Optional[float] = None
    visual: Optional[float] = None
    auditory: Optional[float] = None
    spatial: Optional[float] = None
    tactile: Optional[float] = None
    memory: Optional[float] = None
    source_measures: List[str] = field(default_factory=list)


def compute_scores(participant) -> ComputedScores:
    """
    Derive imagery scores from all of a participant's completed measures.
    Pure function — no DB writes, easy to test.
    """
    responses = QuestionnaireResponse.objects.filter(participant=participant)
    responses_by_type = {r.measure_type: r for r in responses}

    scores = ComputedScores(source_measures=list(responses_by_type.keys()))

    # VVIQ raw score (16–80), used directly for the spectrum
    if 'vviq' in responses_by_type:
        scores.vviq_score = responses_by_type['vviq'].raw_score
        # Visual modality on the radar is derived from VVIQ, scaled to 0–10
        scores.visual = (responses_by_type['vviq'].raw_score - 16) / 64 * 10

    # Auditory imagery from BAIS (Bucknell Auditory Imagery Scale)
    if 'bais' in responses_by_type:
        scores.auditory = responses_by_type['bais'].raw_score / 7  # BAIS max is 70

    # Spatial, tactile, memory from their respective measures...

    return scores


def save_scores(participant):
    """Compute scores and persist them as a new snapshot."""
    computed = compute_scores(participant)
    ImageryScore.objects.create(
        participant=participant,
        vviq_score=computed.vviq_score,
        visual=computed.visual,
        auditory=computed.auditory,
        spatial=computed.spatial,
        tactile=computed.tactile,
        memory=computed.memory,
        source_measures=computed.source_measures,
    )
```

`compute_scores` is pure (no DB writes), easy to unit test. `save_scores` is the orchestration.

### The signal

```python
# measures/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver

from measures.models import QuestionnaireResponse
from scores.pipeline import save_scores


@receiver(post_save, sender=QuestionnaireResponse)
def recalculate_scores_on_response(sender, instance, created, **kwargs):
    if created:
        save_scores(instance.participant)
```

```python
# measures/apps.py
from django.apps import AppConfig

class MeasuresConfig(AppConfig):
    name = 'measures'

    def ready(self):
        from . import signals  # noqa — registers the receiver
```

**Warning about signals:** they hide cause-and-effect. If someone saves a `QuestionnaireResponse` in the Django admin, they might not realise it triggers score recalculation. Keep the signal handler tiny — just call `save_scores`. Don't put business logic in the signal itself.

**Alternative:** skip the signal and have the submission view explicitly call `save_scores()` after saving the response. More code but the flow is visible — someone reading the submission view sees exactly what happens. Preferable for research systems where auditability matters.

### The view

```python
# participants/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def account(request):
    participant = request.user.participant
    latest = participant.imagery_scores.first()  # uses Meta.ordering

    radar_scores = None
    spectrum_position = None

    if latest:
        if latest.vviq_score is not None:
            spectrum_position = _spectrum_position(latest.vviq_score)
        radar_scores = {
            'visual': latest.visual,
            'auditory': latest.auditory,
            'spatial': latest.spatial,
            'tactile': latest.tactile,
            'memory': latest.memory,
        }

    context = {
        'participant': participant,
        'scores': latest,
        'spectrum_position': spectrum_position,
        'radar_scores': radar_scores,
    }
    return render(request, 'account.html', context)


def _spectrum_position(vviq_score):
    """VVIQ range 16–80 → position 0–100%"""
    return round(((vviq_score - 16) / 64) * 100, 1)
```

### The template

```django
{% load json_script %}

<!-- Spectrum marker — position calculated server-side -->
<div class="spectrum-chart" style="--score-position: {{ spectrum_position|default:50 }}%;">
    <!-- SVG curve unchanged -->
</div>

<!-- Legend HTML rendered from server data -->
<div class="radar-legend">
    <h5>Your scores (out of 10)</h5>
    <ul>
        <li><span class="modality">Visual</span><span class="value">{{ radar_scores.visual|floatformat:1 }}</span></li>
        <li><span class="modality">Auditory</span><span class="value">{{ radar_scores.auditory|floatformat:1 }}</span></li>
        <li><span class="modality">Spatial</span><span class="value">{{ radar_scores.spatial|floatformat:1 }}</span></li>
        <li><span class="modality">Tactile</span><span class="value">{{ radar_scores.tactile|floatformat:1 }}</span></li>
        <li><span class="modality">Memory vividness</span><span class="value">{{ radar_scores.memory|floatformat:1 }}</span></li>
    </ul>
</div>

<!-- Data for Chart.js, safely serialised -->
{{ radar_scores|json_script:"radar-data" }}

<script>
  const radarData = JSON.parse(document.getElementById('radar-data').textContent);

  new Chart(radarCtx, {
    type: 'radar',
    data: {
      labels: ['Visual', 'Auditory', 'Spatial', 'Tactile', 'Memory'],
      datasets: [{
        data: [
          radarData.visual, radarData.auditory, radarData.spatial,
          radarData.tactile, radarData.memory
        ],
        // ...styling unchanged from static version
      }]
    },
    // ...
  });
</script>
```

### Gotchas

- **`json_script` with model instances** — handles dicts and basic types, not Django model instances directly. Always pass it a plain dict, not the model.
- **Incomplete data** — participants who've only done one or two measures will have some `None` fields. Decide how to handle visually. Options: show zero for missing modalities (misleading — zero means "no imagery at all"); grey out missing axes on the radar; or hide the chart entirely and show a "Complete more measures to unlock your results" state. The last is most honest.
- **Caching** — the account view is a good candidate for fragment caching since scores only change when new responses come in. But be careful with per-user caching — use `vary_on_headers('Cookie')` or a cache key that includes the user ID.
- **Testing `compute_scores`** — this function should have thorough unit tests. Test edge cases: no responses, one response, all responses, malformed data. If the maths is wrong, every participant sees wrong results. This is probably the most scientifically important code in the system.

---

## 2. Consent record

**Key insight:** a consent record is **immutable historical data**, not mutable state. Once a participant consents, that fact must be preserved exactly as they saw it — even if you later change the wording of the statements. If an ethics review asks "what exactly did this participant agree to in January 2026?", you need to show them.

This means storing the full text of each statement alongside the consent, not just a reference to a current version.

### Models

```python
# consent/models.py
from django.db import models
from django.utils import timezone


class ConsentVersion(models.Model):
    """
    A versioned bundle of consent statements. Create a new version
    whenever wording changes — never edit existing versions.
    """
    version = models.CharField(max_length=10, unique=True)  # 'v1.0', 'v1.1'
    ethics_approval_ref = models.CharField(max_length=50)    # 'PPLS 2026-003'
    study_name = models.CharField(max_length=200)
    introduction = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)  # is this the version offered to new participants?

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Consent {self.version}"


class ConsentStatement(models.Model):
    """An individual statement within a consent version."""
    version = models.ForeignKey(ConsentVersion, on_delete=models.PROTECT, related_name='statements')
    order = models.PositiveSmallIntegerField()
    text = models.TextField()

    class Meta:
        ordering = ['order']
        unique_together = [['version', 'order']]


class ConsentRecord(models.Model):
    """
    A participant's consent. Captures exactly what they agreed to,
    when, and from where. Never modified after creation.
    """
    participant = models.ForeignKey('participants.Participant', on_delete=models.PROTECT)
    version = models.ForeignKey(ConsentVersion, on_delete=models.PROTECT)
    consented_at = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    # A snapshot of the exact statements agreed to.
    # Stored as JSON to survive even if ConsentVersion/Statement rows are lost.
    statements_snapshot = models.JSONField()

    class Meta:
        ordering = ['-consented_at']
```

**Design notes:**

- **`on_delete=models.PROTECT`** on `version` and `participant`. Protect prevents accidental deletion of a `ConsentVersion` while `ConsentRecord`s reference it. You don't want a cleanup migration silently deleting the version a record points to.
- **`statements_snapshot` stores the actual text** as JSON. Technically redundant with the `ConsentVersion → ConsentStatement` relation, but deliberately so. If the `ConsentVersion` row were ever deleted or corrupted, each `ConsentRecord` would still contain a complete, verifiable record of what was agreed to. Belt-and-braces for research ethics.
- **`ip_address` and `user_agent`** — optional but often required by ethics committees for an audit trail. Check with your PPLS committee whether they want these.

### Recording consent at signup

```python
# consent/services.py
from .models import ConsentRecord, ConsentVersion


def record_consent(participant, request):
    """
    Create a consent record from the currently active consent version.
    Called at the end of the signup flow, after all 8 statements are ticked.
    """
    active = ConsentVersion.objects.get(active=True)

    snapshot = {
        'version': active.version,
        'ethics_approval_ref': active.ethics_approval_ref,
        'study_name': active.study_name,
        'introduction': active.introduction,
        'statements': [
            {'order': s.order, 'text': s.text}
            for s in active.statements.all()
        ],
    }

    return ConsentRecord.objects.create(
        participant=participant,
        version=active,
        statements_snapshot=snapshot,
        ip_address=_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
    )


def _client_ip(request):
    """Respect X-Forwarded-For if behind a proxy, else REMOTE_ADDR."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
```

### Displaying the consent record

```python
# participants/views.py
from consent.models import ConsentRecord


@login_required
def account(request):
    participant = request.user.participant
    consent_record = ConsentRecord.objects.filter(participant=participant).first()
    # ...
    context['consent'] = consent_record
    return render(request, 'account.html', context)
```

```django
{% if consent %}
<div class="card">
    <h3>Consent record</h3>

    <dl class="consent-meta">
        <div>
            <dt>Date signed</dt>
            <dd>{{ consent.consented_at|date:"j F Y" }}</dd>
        </div>
        <div>
            <dt>Study version</dt>
            <dd>{{ consent.statements_snapshot.version }}</dd>
        </div>
        <div>
            <dt>Ethics approval</dt>
            <dd>{{ consent.statements_snapshot.ethics_approval_ref }}</dd>
        </div>
    </dl>

    <ul class="consent-list">
        {% for statement in consent.statements_snapshot.statements %}
        <li>
            <span class="tick"></span>
            <span><strong>{{ statement.order }}.</strong> {{ statement.text }}</span>
        </li>
        {% endfor %}
    </ul>
</div>
{% endif %}
```

The template reads from `statements_snapshot` — the frozen copy — not from the current `ConsentVersion`. If you later publish v1.1 with revised wording, James still sees the v1.0 statements he actually agreed to.

---

## 3. Withdrawal

The ethical requirement is "delete my data" — but what that means in practice is subtle because some data legitimately cannot be deleted and some you might want to keep in anonymised form. The consent statement on the signup page already acknowledges this: *"anonymised data already exported for analysis may still be included in that analysis."*

### What actually happens on withdrawal

Four distinct categories of data, each handled differently:

| Category | Example | Treatment |
|---|---|---|
| Personally identifying | name, email | **Delete** |
| Identifying links | user account, participant_id mapping | **Delete** |
| Research responses (raw) | VVIQ answers, task results | **Delete or anonymise** |
| Already exported for analysis | CSV given to a collaborator last week | **Keep, already anonymous** |
| Audit trail | consent record, withdrawal record itself | **Keep** (with personal data redacted) |

Once you anonymise and export research data to a collaborator, you genuinely can't retrieve it. Your system needs to reflect this reality. The consent text already covers this.

### The withdrawal record model

```python
# withdrawal/models.py
from django.db import models


class WithdrawalRecord(models.Model):
    """
    A permanent record that a withdrawal occurred. Created as part
    of the withdrawal transaction; the participant row is deleted
    but this record survives, linked by participant_id string only.
    """
    participant_id_redacted = models.CharField(max_length=20)  # 'PRH-2026-0147'
    withdrawn_at = models.DateTimeField(auto_now_add=True)
    consent_version_at_withdrawal = models.CharField(max_length=10)
    joined_at = models.DateTimeField()
    responses_deleted_count = models.PositiveIntegerField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-withdrawn_at']
```

No foreign key to `Participant` — deliberately. When the participant is deleted, this record needs to survive with just the ID string for reference.

### The withdrawal service

```python
# withdrawal/services.py
from django.db import transaction
from django.contrib.auth import logout

from consent.models import ConsentRecord
from measures.models import QuestionnaireResponse
from scores.models import ImageryScore
from .models import WithdrawalRecord


@transaction.atomic
def withdraw_participant(participant, request):
    """
    Permanently remove a participant's personal data from the system.
    Creates an audit record. Wrapped in a transaction — if any step
    fails, the whole thing rolls back.
    """
    # Capture what we need for the audit record before deletion
    consent = ConsentRecord.objects.filter(participant=participant).first()
    response_count = QuestionnaireResponse.objects.filter(participant=participant).count()

    audit = WithdrawalRecord.objects.create(
        participant_id_redacted=participant.participant_id,
        joined_at=participant.joined_at,
        consent_version_at_withdrawal=consent.version.version if consent else 'unknown',
        responses_deleted_count=response_count,
        ip_address=_client_ip(request),
    )

    # Delete in dependency order
    ImageryScore.objects.filter(participant=participant).delete()
    QuestionnaireResponse.objects.filter(participant=participant).delete()
    ConsentRecord.objects.filter(participant=participant).delete()

    user = participant.user
    participant.delete()
    user.delete()  # cascade handles anything else hanging off the user

    # Log the user out — their session is now invalid anyway
    logout(request)

    return audit
```

**Notes:**

- **`@transaction.atomic`** — if any part fails (DB error, constraint violation, anything), the whole thing rolls back. You never end up with "user deleted but responses still there" or "responses deleted but user still logged in."
- **Deletion order matters** only if you have `on_delete=PROTECT` relationships (recommended for research data so it can't be accidentally orphaned). If everything cascades, `participant.delete()` alone would work — but being explicit about the order is clearer and safer.
- **`WithdrawalRecord` is created inside the transaction** — so if deletion fails and rolls back, the audit record rolls back too. This is correct: you don't want a record of a withdrawal that didn't actually happen. If you need audit logs that survive transaction failures, write them to an external log system, not the DB.
- **`logout(request)`** at the end — important. Otherwise the session still exists, the cookie still points at a now-deleted user, and you'll hit 500 errors on next request.

### The withdrawal view

```python
# withdrawal/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .services import withdraw_participant


@login_required
@require_POST
def withdraw(request):
    # Require explicit confirmation — e.g. typing "DELETE" or a checkbox
    if request.POST.get('confirmation') != 'DELETE':
        return render(request, 'withdraw_confirm.html', {
            'error': 'Please type DELETE to confirm.',
        })

    withdraw_participant(request.user.participant, request)
    return redirect('withdrawal_complete')


def withdrawal_complete(request):
    """Shown after successful withdrawal. User is logged out at this point."""
    return render(request, 'withdrawal_complete.html')
```

### Gotchas and things to consider

- **The "already exported data" problem.** Your system should track which responses have been included in which exports. When a participant withdraws, that export record survives and tells you honestly: "your data was included in export `EXP-2026-04-15` sent to Professor X." You might want a separate `DataExport` model that tracks this. Not essential for v1, but ethics committees may ask about it.
- **GDPR's "right to be forgotten"** is not absolute when the processing is for research in the public interest under UK GDPR Article 14. But consent-based processing under Article 6(1)(a) has stricter deletion requirements. The PPLS ethics application probably specifies which legal basis is being used — worth checking before finalising this flow.
- **Test the withdrawal flow with a real database.** It's the kind of code that looks fine until someone has a foreign key you forgot about. Write a management command that creates test participants with full data, runs withdrawal, and asserts nothing is left behind:

    ```python
    # participants/management/commands/test_withdrawal.py
    from django.core.management.base import BaseCommand

    class Command(BaseCommand):
        def handle(self, *args, **options):
            # Create test participant with full fake data
            # Call withdraw_participant
            # Assert nothing related to participant.participant_id remains
            # Assert WithdrawalRecord was created
    ```

- **Admin cleanup** — make sure the Django admin doesn't accidentally expose withdrawn participants' data. The `WithdrawalRecord` admin should be read-only.

---

## Where this frontend meets the backend

A short summary of which static templates consume what data from the backend above:

| Template | Data source | Notes |
|---|---|---|
| `index.html` (dashboard) | `Participant` + list of `QuestionnaireResponse`s (or "available measures") grouped by domain | Sidebar context switcher controls the list shown |
| `home.html` | Static — no backend | Landing page for unauthenticated visitors |
| `signup.html` | Creates `User`, `Participant`, `ConsentRecord` on submit | All 8 consent checkboxes must be ticked client-side before submit enables |
| `account.html` — Profile | `Participant`, `User` | Editable fields wire up to standard Django form patterns |
| `account.html` — Consent | `ConsentRecord.statements_snapshot` | Read-only display of historical consent |
| `account.html` — Results | Latest `ImageryScore` snapshot | Renders as JSON via `json_script`, Chart.js reads it |

### Testing priorities

If time for tests is limited, test these first:

1. **`compute_scores`** — unit tests across the full range of data completeness scenarios
2. **`withdraw_participant`** — integration test with fully populated test participant
3. **`record_consent`** — verify `statements_snapshot` captures the full current version
4. **Consent versioning** — create v1.0, consent some participants, create v1.1, verify old consents still show v1.0 text

These are the parts where correctness has real-world ethics and data integrity consequences.
