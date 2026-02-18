from django.db import models
from django.conf import settings
from core.models import Domain


class Survey(models.Model):
    """
    Survey model for collecting participant responses.
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    researcher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='surveys'
    )
    domain = models.ForeignKey(
        Domain,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='surveys'
    )
    is_active = models.BooleanField(default=True)
    randomize_questions = models.BooleanField(
        default=False,
        help_text="Randomize question order for each participant (using participant ID as seed for consistency)"
    )
    min_value = models.IntegerField(
        default=1,
        help_text="Minimum value for the Likert scale used in this survey"
    )
    max_value = models.IntegerField(
        default=5,
        help_text="Maximum value for the Likert scale used in this survey"
    )
    scale_labels = models.JSONField(
        default=dict,
        blank=True,
        help_text='Labels for each scale value. Example: {"1": "Strongly Disagree", "2": "Disagree", "3": "Neutral", "4": "Agree", "5": "Strongly Agree"}'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Survey'
        verbose_name_plural = 'Surveys'

    def __str__(self):
        return self.title

    def get_label_for_value(self, value):
        """
        Get the label for a specific scale value.
        Returns the label if it exists, otherwise returns the value as a string.
        """
        if self.scale_labels and str(value) in self.scale_labels:
            return self.scale_labels[str(value)]
        return str(value)

    def normalize_question_order(self):
        """
        Renumber all questions sequentially (1, 2, 3...) based on current order.
        Uses ID as tiebreaker for questions with duplicate order numbers.

        This is useful after manual reordering creates gaps or duplicates.
        Does not affect participant responses (they're linked by question ID).
        """
        questions = self.questions.all().order_by('order', 'id')
        for index, question in enumerate(questions, start=1):
            if question.order != index:
                question.order = index
                question.save()


class LikertScale(models.Model):
    """
    A named, reusable Likert scale defined within a survey.
    Questions can select one of these scales via a dropdown.
    If no scale is selected on a question, the survey-level defaults are used.
    """
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='likert_scales'
    )
    name = models.CharField(
        max_length=200,
        help_text="Descriptive name for this scale, e.g. 'Agreement 1-5' or 'Vividness 0-10'"
    )
    min_value = models.IntegerField(default=1)
    max_value = models.IntegerField(default=5)
    scale_labels = models.JSONField(
        default=dict,
        blank=True,
        help_text='Labels for each scale value. Example: {"1": "Never", "2": "Rarely", "3": "Sometimes", "4": "Often", "5": "Always"}'
    )

    class Meta:
        ordering = ['survey', 'name']
        verbose_name = 'Likert Scale'
        verbose_name_plural = 'Likert Scales'

    def __str__(self):
        return f"{self.name} ({self.min_value}–{self.max_value})"

    def get_label_for_value(self, value):
        if self.scale_labels and str(value) in self.scale_labels:
            return self.scale_labels[str(value)]
        return str(value)

    def get_scale_options(self):
        return [
            (v, self.get_label_for_value(v))
            for v in range(self.min_value, self.max_value + 1)
        ]


class Question(models.Model):
    """
    Individual questions that belong to a single survey.
    The Likert scale settings are defined at the survey level.
    """
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    likert_scale = models.ForeignKey(
        LikertScale,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions',
        help_text="Select a Likert scale for this question. Leave blank to use the survey default."
    )
    text = models.TextField()
    required = models.BooleanField(default=True)
    reverse_coded = models.BooleanField(
        default=False,
        help_text='Reverse code this question (invert scale values before storing). Useful for detecting response patterns.'
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text='Set to 0 to automatically add to the end of the survey. Changing to a specific number will replace any question at that position.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['survey', 'order']
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'

    def __str__(self):
        return f"{self.survey.title} - Q{self.order}: {self.text[:50]}"

    def effective_scale(self):
        """
        Returns the LikertScale to use for this question, or None if using survey defaults.
        """
        return self.likert_scale

    def effective_min(self):
        if self.likert_scale:
            return self.likert_scale.min_value
        return self.survey.min_value

    def effective_max(self):
        if self.likert_scale:
            return self.likert_scale.max_value
        return self.survey.max_value

    def get_scale_options(self):
        """
        Returns list of (value, label) tuples for Likert rendering.
        Uses the question's assigned scale, falling back to survey defaults.
        """
        if self.likert_scale:
            return self.likert_scale.get_scale_options()
        return [
            (v, self.survey.get_label_for_value(v))
            for v in range(self.survey.min_value, self.survey.max_value + 1)
        ]

    def apply_reverse_coding(self, answer_int):
        """
        Apply reverse coding to a numeric answer value.
        """
        return (self.effective_max() + self.effective_min()) - answer_int

    def save(self, *args, **kwargs):
        """
        Override save to auto-increment order if not specified (order=0).

        Note: Order is purely for display/rendering. Duplicate order numbers
        are allowed - use Survey.normalize_question_order() to clean up.
        """
        # Auto-increment order if not specified
        if self.order == 0:
            # Get the maximum order for this survey
            max_order = Question.objects.filter(
                survey=self.survey
            ).exclude(
                pk=self.pk if self.pk else None
            ).aggregate(
                models.Max('order')
            )['order__max']

            self.order = (max_order or 0) + 1

        super().save(*args, **kwargs)


class ParticipantResponse(models.Model):
    """
    Stores individual participant responses to survey questions.
    """
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='responses'
    )
    participant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='survey_responses'
    )
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Participant Response'
        verbose_name_plural = 'Participant Responses'
        unique_together = ['survey', 'question', 'participant']

    def __str__(self):
        return f"{self.participant.email} - {self.survey.title} - {self.question.text[:30]}"
