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


class QuestionGroup(models.Model):
    """
    Named section/group within a survey (e.g., "Think of a relative or friend").
    Serves as a section header with optional instructions that appears before related questions.
    Questions reference their group, and get a composite identifier like "1_01", "1_02", etc.
    """
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='question_groups'
    )
    group_code = models.CharField(
        max_length=50,
        help_text="Short code for this group (e.g., '1', '2', 'demographics'). Used in question identifiers like '1_01', '1_02'."
    )
    title = models.CharField(
        max_length=500,
        help_text="The group heading/statement (e.g., 'Think of a relative or friend')"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional additional instructions for this group of questions"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text='Display order of this group. Set to 0 for automatic ordering.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['survey', 'order', 'id']
        verbose_name = 'Question Group'
        verbose_name_plural = 'Question Groups'
        unique_together = ['survey', 'group_code']

    def __str__(self):
        return f"{self.survey.title} - [{self.group_code}] {self.title}"

    def save(self, *args, **kwargs):
        """
        Override save to auto-increment order if not specified (order=0).
        """
        if self.order == 0:
            # Get the maximum order for this survey
            max_order = QuestionGroup.objects.filter(
                survey=self.survey
            ).exclude(
                pk=self.pk if self.pk else None
            ).aggregate(
                models.Max('order')
            )['order__max']

            self.order = (max_order or 0) + 1

        super().save(*args, **kwargs)


class Question(models.Model):
    """
    Individual questions that belong to a single survey.
    Supports multiple question types: Likert scales, multiple choice, and free text.
    """
    QUESTION_TYPES = [
        ('likert', 'Likert Scale'),
        ('multiple_choice_single', 'Multiple Choice (Select One)'),
        ('multiple_choice_multi', 'Multiple Choice (Select Multiple)'),
        ('free_text', 'Free Text'),
    ]

    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    group = models.ForeignKey(
        QuestionGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions',
        help_text="Optional: Assign this question to a group. Questions in groups get identifiers like '1_01', '1_02', etc."
    )
    question_number = models.CharField(
        max_length=10,
        blank=True,
        help_text="Question number within the group (e.g., '01', '02'). Leave blank for ungrouped questions."
    )
    question_id = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        help_text="Composite identifier stored in database (e.g., 'A_01', 'B_02', 'Q5'). Auto-generated from group_code and question_number."
    )
    question_type = models.CharField(
        max_length=30,
        choices=QUESTION_TYPES,
        default='likert',
        help_text='Type of question'
    )
    likert_scale = models.ForeignKey(
        LikertScale,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions',
        help_text="(Likert only) Select a Likert scale for this question. Leave blank to use the survey default."
    )
    text = models.TextField()
    required = models.BooleanField(default=True)
    reverse_coded = models.BooleanField(
        default=False,
        help_text='(Likert only) Reverse code this question (invert scale values before storing). Useful for detecting response patterns.'
    )
    options = models.JSONField(
        default=dict,
        blank=True,
        help_text='(Multiple choice only) Options for multiple choice questions. Format: {"1": "Option A", "2": "Option B", "3": "Option C"}'
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
        identifier = self.get_question_identifier()
        return f"{self.survey.title} - {identifier}: {self.text[:50]}"

    def get_question_identifier(self):
        """
        Returns the question identifier (e.g., '1_01', '2_03', or 'Q5' for ungrouped).
        """
        if self.group and self.question_number:
            return f"{self.group.group_code}_{self.question_number}"
        return f"Q{self.order}"

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
        Only applicable to Likert scale questions.
        """
        return (self.effective_max() + self.effective_min()) - answer_int

    def get_multiple_choice_options(self):
        """
        Returns list of (value, label) tuples for multiple choice rendering.
        Only applicable to multiple choice questions.
        """
        if self.question_type not in ['multiple_choice_single', 'multiple_choice_multi'] or not self.options:
            return []

        # Sort by key (numeric value) for consistent ordering
        return sorted(
            [(int(k), v) for k, v in self.options.items()],
            key=lambda x: x[0]
        )

    def validate_multiple_choice_answer(self, answer_values):
        """
        Validate that all answer values are valid options for this question.
        answer_values can be a single value or a list of values.
        Returns (is_valid, error_message)
        """
        if self.question_type not in ['multiple_choice_single', 'multiple_choice_multi']:
            return True, None

        if not self.options:
            return False, "This question has no options configured."

        # Ensure answer_values is a list
        if not isinstance(answer_values, list):
            answer_values = [answer_values]

        # Check if empty and required
        if self.required and not answer_values:
            return False, "This question is required."

        # Check multiple selections allowed
        if self.question_type == 'multiple_choice_single' and len(answer_values) > 1:
            return False, "Only one selection is allowed for this question."

        # Validate all values are valid options
        valid_values = set(self.options.keys())
        for val in answer_values:
            if str(val) not in valid_values:
                return False, f"Invalid option: {val}"

        return True, None

    def save(self, *args, **kwargs):
        """
        Override save to auto-increment order if not specified (order=0).
        Also auto-generates question_id from group_code and question_number.

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

        # Auto-generate question_id
        self.question_id = self.get_question_identifier()

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
    is_test = models.BooleanField(
        default=False,
        help_text="Marks this as test data submitted by researchers/staff"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Participant Response'
        verbose_name_plural = 'Participant Responses'
        unique_together = ['survey', 'question', 'participant']

    def __str__(self):
        return f"{self.participant.email} - {self.survey.title} - {self.question.text[:30]}"
