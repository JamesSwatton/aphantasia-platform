import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from surveys.models import Survey, QuestionGroup, Question, LikertScale, ParticipantResponse

User = get_user_model()

PARTICIPANT_EMAIL = 'participant@test.com'


class Command(BaseCommand):
    help = 'Seeds surveys with result metadata and fake participant responses for results page testing.'

    def handle(self, *args, **options):
        try:
            participant = User.objects.get(email=PARTICIPANT_EMAIL)
        except User.DoesNotExist:
            self.stderr.write(f'Participant {PARTICIPANT_EMAIL!r} not found. Aborting.')
            return

        self._configure_vviq()
        self._configure_assist_lite()
        self._configure_sbsds()
        self._create_big_five(participant)
        self._seed_responses(participant)

        self.stdout.write(self.style.SUCCESS('Done. Seed data applied successfully.'))

    # ------------------------------------------------------------------
    # Configure existing surveys
    # ------------------------------------------------------------------

    def _configure_vviq(self):
        try:
            survey = Survey.objects.get(title='VVIQ')
        except Survey.DoesNotExist:
            self.stdout.write('VVIQ not found, skipping.')
            return

        survey.result_min = 1
        survey.result_max = 5
        survey.result_aggregation = Survey.AGGREGATION_MEAN
        survey.save()

        labels = ['Relative / Friend', 'Rising Sun', 'Shop Front', 'Country Scene']
        for group, label in zip(survey.question_groups.order_by('order'), labels):
            group.result_label = label
            group.result_min = 1
            group.result_max = 5
            group.save()

        self.stdout.write('  Configured VVIQ.')

    def _configure_assist_lite(self):
        try:
            survey = Survey.objects.get(title='ASSIST-Lite')
        except Survey.DoesNotExist:
            self.stdout.write('ASSIST-Lite not found, skipping.')
            return

        survey.result_min = 0
        survey.result_max = 7
        survey.result_aggregation = Survey.AGGREGATION_SUM
        survey.save()

        self.stdout.write('  Configured ASSIST-Lite.')

    def _configure_sbsds(self):
        try:
            survey = Survey.objects.get(title='Santa Barbara Sense-of-Direction Scale')
        except Survey.DoesNotExist:
            self.stdout.write('Santa Barbara Sense-of-Direction Scale not found, skipping.')
            return

        survey.result_min = 1
        survey.result_max = 7
        survey.result_aggregation = Survey.AGGREGATION_MEAN
        survey.save()

        self.stdout.write('  Configured Santa Barbara Sense-of-Direction Scale.')

    # ------------------------------------------------------------------
    # Create fictional Big Five survey
    # ------------------------------------------------------------------

    def _create_big_five(self, participant):
        survey, created = Survey.objects.get_or_create(
            title='Big Five Personality Inventory (Test)',
            defaults={
                'description': (
                    'A fictional personality questionnaire for testing purposes. '
                    'Measures five broad personality dimensions.'
                ),
                'researcher': User.objects.filter(is_staff=True).first(),
                'is_active': True,
                'min_value': 1,
                'max_value': 5,
                'scale_labels': {
                    '1': 'Disagree strongly',
                    '2': 'Disagree a little',
                    '3': 'Neither agree nor disagree',
                    '4': 'Agree a little',
                    '5': 'Agree strongly',
                },
                'result_min': 1,
                'result_max': 5,
                'result_aggregation': Survey.AGGREGATION_MEAN,
            }
        )

        if not created:
            self.stdout.write('  Big Five survey already exists, skipping creation.')
            return

        subscales = [
            ('Openness', [
                'I have a vivid imagination.',
                'I enjoy thinking about abstract concepts.',
                'I am full of ideas.',
            ]),
            ('Conscientiousness', [
                'I am always prepared.',
                'I pay attention to details.',
                'I follow a schedule.',
            ]),
            ('Extraversion', [
                'I feel comfortable around people.',
                'I start conversations.',
                'I enjoy being the centre of attention.',
            ]),
            ('Agreeableness', [
                'I am interested in other people.',
                'I feel others\' emotions.',
                'I make people feel at ease.',
            ]),
            ('Neuroticism', [
                'I get stressed out easily.',
                'I worry about things.',
                'I get upset easily.',
            ]),
        ]

        for order, (label, questions) in enumerate(subscales, start=1):
            group = QuestionGroup.objects.create(
                survey=survey,
                title=label,
                show_title=True,
                result_label=label,
                result_min=1,
                result_max=5,
                order=order,
            )
            for q_order, text in enumerate(questions, start=1):
                Question.objects.create(
                    survey=survey,
                    group=group,
                    question_type='likert',
                    text=text,
                    order=((order - 1) * len(questions)) + q_order,
                    required=True,
                )

        self.stdout.write('  Created Big Five Personality Inventory (Test).')

    # ------------------------------------------------------------------
    # Seed participant responses
    # ------------------------------------------------------------------

    def _seed_responses(self, participant):
        rng = random.Random(participant.id)

        for survey in Survey.objects.filter(is_active=True):
            likert_questions = survey.questions.filter(question_type='likert')
            if not likert_questions.exists():
                continue

            count = 0
            for question in likert_questions:
                min_v = question.effective_min()
                max_v = question.effective_max()
                answer = rng.randint(min_v, max_v)

                if question.reverse_coded:
                    answer = question.apply_reverse_coding(answer)
                answer = question.apply_scale_factor(answer)

                ParticipantResponse.objects.update_or_create(
                    survey=survey,
                    question=question,
                    participant=participant,
                    defaults={'answer': str(answer), 'is_test': False},
                )
                count += 1

            self.stdout.write(f'  Seeded {count} responses for {survey.title!r}.')
