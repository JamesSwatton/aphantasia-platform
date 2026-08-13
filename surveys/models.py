from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from core.models import Domain


class Survey(models.Model):
    """
    Survey model for collecting participant responses.
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField(
        blank=True,
        help_text="Optional survey-specific instructions shown in the sidebar before the standard how-to-answer points."
    )
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
    is_feedback = models.BooleanField(
        default=False,
        help_text="Mark this as a mid-study feedback survey. Feedback surveys are hidden from the participant dashboard and managed under Core in the admin."
    )
    is_exit_survey = models.BooleanField(
        default=False,
        help_text="Mark this as an exit survey. Exit surveys are shown to participants when they choose to withdraw from the study."
    )
    show_after_n_surveys = models.PositiveIntegerField(
        default=2,
        help_text="(Feedback surveys only) Show this form on the participant account page after they have completed this many regular surveys."
    )
    is_priority = models.BooleanField(
        default=False,
        help_text="Mark this survey as a priority. Priority surveys appear at the top of the list."
    )
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
    AGGREGATION_MEAN = 'mean'
    AGGREGATION_SUM = 'sum'
    AGGREGATION_CHOICES = [
        (AGGREGATION_MEAN, 'Mean (average)'),
        (AGGREGATION_SUM, 'Sum (total)'),
    ]
    result_aggregation = models.CharField(
        max_length=10,
        choices=AGGREGATION_CHOICES,
        default=AGGREGATION_MEAN,
        help_text="How to combine question scores into a group/survey result."
    )
    result_min = models.FloatField(
        null=True,
        blank=True,
        help_text="Minimum of the display range for results (e.g. 0). Leave blank if no mapping is needed."
    )
    result_max = models.FloatField(
        null=True,
        blank=True,
        help_text="Maximum of the display range for results (e.g. 100)."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_priority', '-created_at']
        verbose_name = 'Survey'
        verbose_name_plural = 'Surveys'

    def __str__(self):
        return self.title

    @property
    def has_subscales(self):
        return self.question_groups.exclude(result_label='').exists()

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


class FeedbackSurvey(Survey):
    """
    Proxy model for managing feedback surveys in the Core admin section.
    Feedback surveys are hidden from the participant dashboard and shown
    inline on the participant account page after a threshold is met.
    """
    class Meta:
        proxy = True
        verbose_name = 'Feedback Survey'
        verbose_name_plural = 'Feedback Surveys'

    def save(self, *args, **kwargs):
        self.is_feedback = True
        super().save(*args, **kwargs)


class ExitSurvey(Survey):
    """
    Proxy model for managing exit surveys in the Core admin section.
    Exit surveys are hidden from the participant dashboard and shown
    to participants when they choose to withdraw from the study.
    """
    class Meta:
        proxy = True
        verbose_name = 'Exit Survey'
        verbose_name_plural = 'Exit Surveys'

    def save(self, *args, **kwargs):
        self.is_exit_survey = True
        super().save(*args, **kwargs)


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
    A named group of questions within a survey.

    'title' is the participant-facing prompt shown during the survey (e.g. "Think of a relative or friend").
    'show_title' controls whether that prompt is rendered as a heading in the survey form.
    'result_label' is the short label used on charts/results (e.g. "Scene 1"). Falls back to title if blank.

    Questions in groups get composite identifiers like "1_a", "1_b", "2_a", "2_b", etc.
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
    show_title = models.BooleanField(
        default=True,
        help_text="Show the group title to participants. Uncheck to use this group as a hidden subscale for scoring/analysis only."
    )
    result_label = models.CharField(
        max_length=100,
        blank=True,
        help_text="Short label for this group in charts/results (e.g. 'Scene 1'). Falls back to group title if blank."
    )
    result_min = models.FloatField(
        null=True,
        blank=True,
        help_text="Override the survey-level result_min for this group's display range."
    )
    result_max = models.FloatField(
        null=True,
        blank=True,
        help_text="Override the survey-level result_max for this group's display range."
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text='Display order of this group. Set to 0 for automatic ordering.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def effective_result_min(self):
        if self.result_min is not None:
            return self.result_min
        return self.survey.result_min

    @property
    def effective_result_max(self):
        if self.result_max is not None:
            return self.result_max
        return self.survey.result_max

    @property
    def display_label(self):
        return self.result_label or self.title

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
        Also auto-generates group_code from order.
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

        # Auto-generate group_code from order
        self.group_code = str(self.order)

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
        ('dropdown_year', 'Dropdown (Year)'),
        ('dropdown_month', 'Dropdown (Month)'),
        ('dropdown_country', 'Dropdown (Country)'),
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
    text = models.TextField(
        blank=True,
        help_text="Question text/label. Can be left blank for self-explanatory question types like dropdowns."
    )
    required = models.BooleanField(default=True)
    reverse_coded = models.BooleanField(
        default=False,
        help_text='(Likert only) Reverse code this question (invert scale values before storing). Useful for detecting response patterns.'
    )
    scale_factor = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text='(Likert only) Multiply the answer by this factor before storing. Applied after reverse coding. Example: factor of 2 converts 1-5 scale to 2-10.'
    )
    options = models.JSONField(
        default=dict,
        blank=True,
        help_text='(Multiple choice only) Options for multiple choice questions. Format: {"1": "Option A", "2": "Option B", "3": "Option C"}. To disable an option (visible but not selectable), use an array: {"1": "Option A", "2": ["Option B (disabled)"], "3": "Option C"}'
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text='Set to 0 to automatically add to the end of the survey. Changing to a specific number will replace any question at that position.'
    )
    controls_next_n_questions = models.PositiveIntegerField(
        default=0,
        help_text='Number of following questions controlled by this question. Set to 0 if not a trigger. Example: Set to 3 to control the next 3 questions.'
    )
    trigger_value = models.CharField(
        max_length=50,
        blank=True,
        help_text='The answer value that enables controlled questions (e.g., "2" for Yes on a 1-2 scale). Leave blank if controls_next_n_questions is 0.'
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
        Returns the question identifier (e.g., '1_a', '2_b', or '5' for ungrouped).
        """
        if self.group and self.question_number:
            return f"{self.group.group_code}_{self.question_number}"
        return str(self.order)

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

    def apply_scale_factor(self, answer_int):
        """
        Apply scale factor to a numeric answer value.
        Should be called after reverse coding (if applicable).
        Only applicable to Likert scale questions.
        """
        return answer_int * self.scale_factor

    def get_multiple_choice_options(self):
        """
        Returns list of (value, label, is_disabled) tuples for multiple choice rendering.
        Only applicable to multiple choice questions.

        If an option value is an array like ["Option B"], it's disabled (visible but not selectable).
        Regular string values like "Option A" are selectable.
        """
        if self.question_type not in ['multiple_choice_single', 'multiple_choice_multi'] or not self.options:
            return []

        options_list = []
        for k, v in self.options.items():
            # Check if value is an array (disabled option)
            if isinstance(v, list):
                # Extract label from array
                label = v[0] if v else ""
                is_disabled = True
            else:
                # Regular string value
                label = v
                is_disabled = False
            options_list.append((int(k), label, is_disabled))

        # Sort by key (numeric value) for consistent ordering
        return sorted(options_list, key=lambda x: x[0])

    def get_enabled_option_keys(self):
        """
        Returns a set of option keys that are enabled (selectable).
        Disabled options (array values) are excluded.
        """
        if self.question_type not in ['multiple_choice_single', 'multiple_choice_multi'] or not self.options:
            return set()

        enabled_keys = set()
        for k, v in self.options.items():
            # Only include non-array values (enabled options)
            if not isinstance(v, list):
                enabled_keys.add(k)
        return enabled_keys

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

        # Validate all values are valid and enabled options (silently ignore disabled options)
        enabled_values = self.get_enabled_option_keys()
        valid_answers = []
        for val in answer_values:
            if str(val) in enabled_values:
                valid_answers.append(val)
            # Silently ignore disabled options if somehow submitted

        # Check if we have any valid answers after filtering
        if self.required and not valid_answers:
            return False, "This question is required."

        return True, None

    def get_year_options(self):
        """
        Returns list of (value, label) tuples for year dropdown.
        Covers last 100 years from current year.
        """
        from datetime import datetime
        current_year = datetime.now().year
        # Generate years in descending order (most recent first)
        return [(year, str(year)) for year in range(current_year, current_year - 100, -1)]

    def get_month_options(self):
        """
        Returns list of (value, label) tuples for month dropdown.
        Value is month number (1-12), label is month name.
        """
        months = [
            (1, 'January'),
            (2, 'February'),
            (3, 'March'),
            (4, 'April'),
            (5, 'May'),
            (6, 'June'),
            (7, 'July'),
            (8, 'August'),
            (9, 'September'),
            (10, 'October'),
            (11, 'November'),
            (12, 'December'),
        ]
        return months

    def get_country_options(self):
        """
        Returns list of (value, label) tuples for country dropdown.
        Comprehensive list of countries in alphabetical order.
        Value and label are both the country name for readability.
        """
        countries = [
            'Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Antigua and Barbuda',
            'Argentina', 'Armenia', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain',
            'Bangladesh', 'Barbados', 'Belarus', 'Belgium', 'Belize', 'Benin', 'Bhutan',
            'Bolivia', 'Bosnia and Herzegovina', 'Botswana', 'Brazil', 'Brunei', 'Bulgaria',
            'Burkina Faso', 'Burundi', 'Cambodia', 'Cameroon', 'Canada', 'Cape Verde',
            'Central African Republic', 'Chad', 'Chile', 'China', 'Colombia', 'Comoros',
            'Congo', 'Costa Rica', 'Croatia', 'Cuba', 'Cyprus', 'Czech Republic',
            'Democratic Republic of the Congo', 'Denmark', 'Djibouti', 'Dominica',
            'Dominican Republic', 'East Timor', 'Ecuador', 'Egypt', 'El Salvador',
            'Equatorial Guinea', 'Eritrea', 'Estonia', 'Eswatini', 'Ethiopia', 'Fiji',
            'Finland', 'France', 'Gabon', 'Gambia', 'Georgia', 'Germany', 'Ghana', 'Greece',
            'Grenada', 'Guatemala', 'Guinea', 'Guinea-Bissau', 'Guyana', 'Haiti', 'Honduras',
            'Hungary', 'Iceland', 'India', 'Indonesia', 'Iran', 'Iraq', 'Ireland', 'Israel',
            'Italy', 'Ivory Coast', 'Jamaica', 'Japan', 'Jordan', 'Kazakhstan', 'Kenya',
            'Kiribati', 'Kosovo', 'Kuwait', 'Kyrgyzstan', 'Laos', 'Latvia', 'Lebanon',
            'Lesotho', 'Liberia', 'Libya', 'Liechtenstein', 'Lithuania', 'Luxembourg',
            'Madagascar', 'Malawi', 'Malaysia', 'Maldives', 'Mali', 'Malta', 'Marshall Islands',
            'Mauritania', 'Mauritius', 'Mexico', 'Micronesia', 'Moldova', 'Monaco', 'Mongolia',
            'Montenegro', 'Morocco', 'Mozambique', 'Myanmar', 'Namibia', 'Nauru', 'Nepal',
            'Netherlands', 'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'North Korea',
            'North Macedonia', 'Norway', 'Oman', 'Pakistan', 'Palau', 'Palestine', 'Panama',
            'Papua New Guinea', 'Paraguay', 'Peru', 'Philippines', 'Poland', 'Portugal',
            'Qatar', 'Romania', 'Russia', 'Rwanda', 'Saint Kitts and Nevis', 'Saint Lucia',
            'Saint Vincent and the Grenadines', 'Samoa', 'San Marino', 'Sao Tome and Principe',
            'Saudi Arabia', 'Senegal', 'Serbia', 'Seychelles', 'Sierra Leone', 'Singapore',
            'Slovakia', 'Slovenia', 'Solomon Islands', 'Somalia', 'South Africa', 'South Korea',
            'South Sudan', 'Spain', 'Sri Lanka', 'Sudan', 'Suriname', 'Sweden', 'Switzerland',
            'Syria', 'Taiwan', 'Tajikistan', 'Tanzania', 'Thailand', 'Togo', 'Tonga',
            'Trinidad and Tobago', 'Tunisia', 'Turkey', 'Turkmenistan', 'Tuvalu', 'Uganda',
            'Ukraine', 'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay',
            'Uzbekistan', 'Vanuatu', 'Vatican City', 'Venezuela', 'Vietnam', 'Yemen', 'Zambia',
            'Zimbabwe'
        ]
        return [(country, country) for country in countries]

    def save(self, *args, **kwargs):
        """
        Override save to auto-increment order if not specified (order=0).
        Also auto-generates question_number (as letter) and question_id.

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

        # Auto-generate question_number as letter (a-z) if question is in a group
        if self.group:
            # Get all questions in this group, ordered by order field
            # This gives us all existing questions in the group
            group_questions = list(Question.objects.filter(
                survey=self.survey,
                group=self.group
            ).exclude(
                pk=self.pk if self.pk else None
            ).order_by('order', 'id'))

            # Find position of this question within the group (0-indexed)
            # We simply count how many questions in the group come before this one
            position = len([q for q in group_questions if q.order < self.order or (q.order == self.order and self.pk and q.id < self.pk)])

            # Convert position to letter (0=a, 1=b, etc.)
            if position < 26:
                self.question_number = chr(ord('a') + position)
            else:
                # Handle more than 26 questions: aa, ab, ac, etc.
                first_letter = chr(ord('a') + (position // 26) - 1)
                second_letter = chr(ord('a') + (position % 26))
                self.question_number = f"{first_letter}{second_letter}"

            # Generate question_id for grouped questions
            self.question_id = f"{self.group.group_code}_{self.question_number}"
        else:
            # For ungrouped questions, use order as the identifier
            self.question_id = str(self.order)

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
