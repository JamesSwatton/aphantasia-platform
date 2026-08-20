import json
from .models import Survey, ParticipantResponse


def get_survey_result(survey, participant, is_test=False):
    """
    Compute a participant's result for a single completed survey.

    Returns a dict ready for the template/chart, or None if the survey has no
    result range configured or the participant has no responses.

    Single-score surveys (no subscale labels):
        {
            'survey': survey,
            'has_subscales': False,
            'score': 3.8,
            'min': 1.0,
            'max': 7.0,
            'chart_json': '{"score": 3.8, "min": 1.0, "max": 7.0}',
        }

    Multi-subscale surveys:
        {
            'survey': survey,
            'has_subscales': True,
            'subscales': [
                {'label': 'Openness', 'label_long': None, 'score': 4.67, 'min': 1.0, 'max': 5.0},
                ...
            ],
            'chart_json': '[{"label": "Openness", "score": 4.67, "min": 1.0, "max": 5.0}, ...]',
        }
    """
    if not survey.has_subscales and (survey.result_min is None or survey.result_max is None):
        return None

    responses = ParticipantResponse.objects.filter(
        survey=survey,
        participant=participant,
        is_test=is_test,
    ).select_related('question__group')

    if not responses.exists():
        return None

    if survey.has_subscales:
        return _subscale_result(survey, responses)
    else:
        return _single_result(survey, responses)


def _aggregate(values, method):
    if not values:
        return None
    if method == Survey.AGGREGATION_SUM:
        return sum(values)
    return sum(values) / len(values)


def _numeric_responses(responses):
    values = []
    for r in responses:
        try:
            values.append(float(r.answer))
        except (ValueError, TypeError):
            pass
    return values


def _single_result(survey, responses):
    values = _numeric_responses(responses)
    score = _aggregate(values, survey.result_aggregation)
    if score is None:
        return None

    chart_data = {
        'score': round(score, 2),
        'min': survey.result_min,
        'max': survey.result_max,
    }
    return {
        'survey': survey,
        'has_subscales': False,
        'score': round(score, 2),
        'min': survey.result_min,
        'max': survey.result_max,
        'chart_json': json.dumps(chart_data),
    }


def _subscale_result(survey, responses):
    groups = survey.question_groups.exclude(result_label='').order_by('order')
    subscales = []

    for group in groups:
        group_responses = [r for r in responses if r.question.group_id == group.id]
        values = _numeric_responses(group_responses)
        score = _aggregate(values, survey.result_aggregation)
        if score is None:
            continue
        subscales.append({
            'label': group.display_label,
            'label_long': group.display_label_long,
            'score': round(score, 2),
            'min': group.effective_result_min,
            'max': group.effective_result_max,
        })

    if not subscales:
        return None

    return {
        'survey': survey,
        'has_subscales': True,
        'subscales': subscales,
        'chart_json': json.dumps(subscales),
    }


def get_all_results(participant):
    """
    Return a list of result dicts for all surveys the participant has completed,
    skipping any surveys with no result range configured.
    """
    completed_surveys = Survey.objects.filter(
        responses__participant=participant,
        responses__is_test=False,
    ).distinct()

    results = []
    for survey in completed_surveys:
        result = get_survey_result(survey, participant)
        if result is not None:
            results.append(result)
    return results
