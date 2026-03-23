from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db import transaction
from django.urls import reverse
from .models import Survey, ParticipantResponse, QuestionGroup
import random
from collections import OrderedDict


def organize_questions_by_group(questions, groups):
    """
    Organize questions into groups for display.
    Returns an OrderedDict where:
    - Keys are (group_order, group_obj or None)
    - Values are lists of questions

    This maintains the order of groups and questions, with ungrouped questions
    appearing in their order position relative to groups.
    """
    # Create a dict mapping group_id to group object
    group_dict = {g.id: g for g in groups}

    # Separate grouped and ungrouped questions
    grouped_questions = {}  # {group_id: [questions]}
    ungrouped_questions = []

    for q in questions:
        if q.group_id:
            if q.group_id not in grouped_questions:
                grouped_questions[q.group_id] = []
            grouped_questions[q.group_id].append(q)
        else:
            ungrouped_questions.append(q)

    # Build ordered structure
    result = OrderedDict()

    # Add all groups in order with their questions
    for group in sorted(groups, key=lambda g: (g.order, g.id)):
        if group.id in grouped_questions:
            result[(group.order, group)] = grouped_questions[group.id]

    # Add ungrouped questions at the end (or we could interleave based on order)
    if ungrouped_questions:
        result[(float('inf'), None)] = ungrouped_questions

    return result


@login_required
def survey_preview(request, pk):
    """
    Preview view for researchers to see how the survey will be rendered.
    Researchers can submit the survey and data is saved with is_test=True (similar to task preview).
    """
    survey = get_object_or_404(Survey, pk=pk)

    # Check if user is researcher or staff
    if not (request.user.is_researcher or request.user.is_staff):
        return HttpResponseForbidden("Only researchers can preview surveys.")

    # Get all questions and groups for this survey
    questions = list(survey.questions.all())
    groups = list(survey.question_groups.all())

    # Randomize questions if enabled (using user ID as seed for consistency)
    if survey.randomize_questions:
        random.seed(request.user.id)
        random.shuffle(questions)
        random.seed()  # Reset seed for other random operations

    # Attach per-question scale options or multiple choice options for template rendering
    for question in questions:
        if question.question_type == 'likert':
            question.scale_options = question.get_scale_options()
        elif question.question_type in ['multiple_choice_single', 'multiple_choice_multi']:
            question.multiple_choice_options = question.get_multiple_choice_options()
        elif question.question_type == 'dropdown_year':
            question.year_options = question.get_year_options()
        elif question.question_type == 'dropdown_month':
            question.month_options = question.get_month_options()
        elif question.question_type == 'dropdown_country':
            question.country_options = question.get_country_options()

    # Organize questions by group
    grouped_questions = organize_questions_by_group(questions, groups)

    test_responses = None

    if request.method == 'POST':
        # Process preview submission - save to database with is_test=True
        errors = []
        responses = {}  # Store as {question: answer_value}
        display_responses = []  # For showing the summary table

        # Build a map of which questions are disabled based on trigger logic
        disabled_questions = set()
        for trigger_q in questions:
            if trigger_q.controls_next_n_questions > 0 and trigger_q.trigger_value:
                # Get the trigger question's answer
                trigger_field_name = f'question_{trigger_q.id}'
                trigger_answer = request.POST.get(trigger_field_name, '').strip()

                # If trigger answer doesn't match trigger_value, disable controlled questions
                if trigger_answer != trigger_q.trigger_value:
                    # Find the N questions that follow this trigger in order
                    for potential_controlled in questions:
                        if potential_controlled.order > trigger_q.order and \
                           potential_controlled.order <= trigger_q.order + trigger_q.controls_next_n_questions:
                            disabled_questions.add(potential_controlled.id)

        for index, q in enumerate(questions, start=1):
            field_name = f'question_{q.id}'

            # Auto-fill disabled questions with default values
            if q.id in disabled_questions:
                if q.question_type == 'likert':
                    # Use minimum value of the scale
                    auto_value = q.effective_min()
                    responses[q] = auto_value
                    # Build display data for auto-filled response
                    stored_value = q.apply_reverse_coding(auto_value) if q.reverse_coded else auto_value
                    stored_value = q.apply_scale_factor(stored_value)
                    if q.likert_scale:
                        answer_label = q.likert_scale.get_label_for_value(auto_value)
                    else:
                        answer_label = survey.get_label_for_value(auto_value)
                    display_responses.append({
                        'question_id': q.get_question_identifier(),
                        'question_text': q.text,
                        'question_type': 'likert',
                        'answer_value': auto_value,
                        'answer_label': answer_label,
                        'stored_value': stored_value,
                        'reverse_coded': q.reverse_coded,
                        'scale_factor': q.scale_factor,
                        'is_auto_filled': True
                    })
                else:
                    # For non-Likert questions, store "NULL"
                    responses[q] = "NULL"
                    display_responses.append({
                        'question_id': q.get_question_identifier(),
                        'question_text': q.text,
                        'question_type': q.question_type,
                        'answer_value': "NULL",
                        'answer_label': '-',
                        'stored_value': "NULL",
                        'reverse_coded': False,
                        'is_auto_filled': True
                    })
                continue

            if q.question_type == 'likert':
                answer = request.POST.get(field_name, '').strip()

                if q.required and not answer:
                    errors.append(f"Question {index} is required.")
                elif answer:
                    try:
                        answer_int = int(answer)
                        if answer_int < q.effective_min() or answer_int > q.effective_max():
                            errors.append(
                                f"Question {index}: Answer must be between "
                                f"{q.effective_min()} and {q.effective_max()}."
                            )
                        else:
                            responses[q] = answer_int
                            # Build display data
                            # Apply reverse coding first (if applicable), then scale factor
                            stored_value = q.apply_reverse_coding(answer_int) if q.reverse_coded else answer_int
                            stored_value = q.apply_scale_factor(stored_value)
                            if q.likert_scale:
                                answer_label = q.likert_scale.get_label_for_value(answer_int)
                            else:
                                answer_label = survey.get_label_for_value(answer_int)
                            display_responses.append({
                                'question_id': q.get_question_identifier(),
                                'question_text': q.text,
                                'question_type': 'likert',
                                'answer_value': answer_int,
                                'answer_label': answer_label,
                                'stored_value': stored_value,
                                'reverse_coded': q.reverse_coded,
                                'scale_factor': q.scale_factor,
                                'is_auto_filled': False
                            })
                    except ValueError:
                        errors.append(f"Question {index}: Invalid answer format.")
                else:
                    # Optional question left blank - record as NULL
                    if not q.required:
                        responses[q] = "NULL"
                        display_responses.append({
                            'question_id': q.get_question_identifier(),
                            'question_text': q.text,
                            'question_type': 'likert',
                            'answer_value': "NULL",
                            'answer_label': '-',
                            'stored_value': "NULL",
                            'reverse_coded': False,
                            'is_auto_filled': False
                        })

            elif q.question_type in ['multiple_choice_single', 'multiple_choice_multi']:
                selected_values = request.POST.getlist(field_name)
                # Filter out any disabled options that might have been submitted
                enabled_keys = q.get_enabled_option_keys()
                filtered_values = [v for v in selected_values if str(v) in enabled_keys]

                is_valid, error_msg = q.validate_multiple_choice_answer(filtered_values)
                if not is_valid:
                    errors.append(f"Question {index}: {error_msg}")
                elif filtered_values:
                    import json
                    responses[q] = json.dumps(filtered_values)
                    # Build display data - extract labels properly
                    labels = []
                    for v in filtered_values:
                        option_value = q.options.get(str(v), str(v))
                        # If it's a list (disabled option), take first element; otherwise use as-is
                        label = option_value[0] if isinstance(option_value, list) else option_value
                        labels.append(label)

                    display_responses.append({
                        'question_id': q.get_question_identifier(),
                        'question_text': q.text,
                        'question_type': q.question_type,
                        'answer_value': filtered_values,
                        'answer_label': ', '.join(labels),
                        'stored_value': filtered_values,
                        'reverse_coded': False,
                        'is_auto_filled': False
                    })
                else:
                    # Optional question left blank - record as NULL
                    if not q.required:
                        responses[q] = "NULL"
                        display_responses.append({
                            'question_id': q.get_question_identifier(),
                            'question_text': q.text,
                            'question_type': q.question_type,
                            'answer_value': "NULL",
                            'answer_label': '-',
                            'stored_value': "NULL",
                            'reverse_coded': False,
                            'is_auto_filled': False
                        })

            elif q.question_type == 'free_text':
                answer = request.POST.get(field_name, '').strip()
                if q.required and not answer:
                    errors.append(f"Question {index} is required.")
                elif answer:
                    responses[q] = answer
                    # Build display data
                    display_responses.append({
                        'question_id': q.get_question_identifier(),
                        'question_text': q.text,
                        'question_type': 'free_text',
                        'answer_value': answer[:50] + '...' if len(answer) > 50 else answer,
                        'answer_label': '-',
                        'stored_value': answer[:50] + '...' if len(answer) > 50 else answer,
                        'reverse_coded': False,
                        'is_auto_filled': False
                    })
                else:
                    # Optional question left blank - record as NULL
                    if not q.required:
                        responses[q] = "NULL"
                        display_responses.append({
                            'question_id': q.get_question_identifier(),
                            'question_text': q.text,
                            'question_type': 'free_text',
                            'answer_value': "NULL",
                            'answer_label': '-',
                            'stored_value': "NULL",
                            'reverse_coded': False,
                            'is_auto_filled': False
                        })

            elif q.question_type in ['dropdown_year', 'dropdown_month', 'dropdown_country']:
                answer = request.POST.get(field_name, '').strip()
                if q.required and not answer:
                    errors.append(f"Question {index} is required.")
                elif answer:
                    responses[q] = answer
                    # Build display data
                    if q.question_type == 'dropdown_year':
                        answer_label = answer  # Year displays as itself
                    elif q.question_type == 'dropdown_month':
                        # Get month name from number
                        month_names = {str(i): name for i, name in q.get_month_options()}
                        answer_label = month_names.get(answer, answer)
                    else:  # dropdown_country
                        answer_label = answer  # Country name displays as itself

                    display_responses.append({
                        'question_id': q.get_question_identifier(),
                        'question_text': q.text,
                        'question_type': q.question_type,
                        'answer_value': answer,
                        'answer_label': answer_label,
                        'stored_value': answer,
                        'reverse_coded': False,
                        'is_auto_filled': False
                    })
                else:
                    # Optional question left blank - record as NULL
                    if not q.required:
                        responses[q] = "NULL"
                        display_responses.append({
                            'question_id': q.get_question_identifier(),
                            'question_text': q.text,
                            'question_type': q.question_type,
                            'answer_value': "NULL",
                            'answer_label': '-',
                            'stored_value': "NULL",
                            'reverse_coded': False,
                            'is_auto_filled': False
                        })

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Save responses to database with is_test=True
            with transaction.atomic():
                for question, answer_value in responses.items():
                    if question.question_type == 'likert' and answer_value != "NULL":
                        # Apply reverse coding first (if applicable), then scale factor
                        stored_value = question.apply_reverse_coding(answer_value) if question.reverse_coded else answer_value
                        stored_value = question.apply_scale_factor(stored_value)
                        ParticipantResponse.objects.update_or_create(
                            survey=survey,
                            question=question,
                            participant=request.user,
                            defaults={'answer': str(stored_value), 'is_test': True}
                        )
                    else:
                        # For multiple choice, free text, and NULL values, store as-is
                        ParticipantResponse.objects.update_or_create(
                            survey=survey,
                            question=question,
                            participant=request.user,
                            defaults={'answer': answer_value, 'is_test': True}
                        )

            messages.success(
                request,
                f"Test data saved for '{survey.title}'. See below for the full response summary."
            )
            test_responses = display_responses

    context = {
        'survey': survey,
        'questions': questions,
        'grouped_questions': grouped_questions,
        'is_preview': True,
        'test_responses': test_responses,
    }

    return render(request, 'surveys/survey_detail.html', context)


@login_required
def survey_take(request, pk):
    """
    View for participants to take a survey and submit their responses.
    Researchers are redirected to test mode.
    """
    survey = get_object_or_404(Survey, pk=pk)

    # Redirect researchers to preview
    if request.user.is_researcher or request.user.is_staff:
        messages.info(
            request,
            "As a researcher, please use Preview & Test from the Survey Management page to test surveys."
        )
        return redirect('surveys:survey_preview', pk=pk)

    # Check if survey is active
    if not survey.is_active:
        messages.error(request, "This survey is not currently active.")
        return redirect('home')

    # Get all questions and groups for this survey
    questions = list(survey.questions.all())
    groups = list(survey.question_groups.all())

    # Randomize questions if enabled (using user ID as seed for consistency)
    if survey.randomize_questions:
        random.seed(request.user.id)
        random.shuffle(questions)
        random.seed()  # Reset seed for other random operations

    # Attach per-question scale options or multiple choice options for template rendering
    for question in questions:
        if question.question_type == 'likert':
            question.scale_options = question.get_scale_options()
        elif question.question_type in ['multiple_choice_single', 'multiple_choice_multi']:
            question.multiple_choice_options = question.get_multiple_choice_options()
        elif question.question_type == 'dropdown_year':
            question.year_options = question.get_year_options()
        elif question.question_type == 'dropdown_month':
            question.month_options = question.get_month_options()
        elif question.question_type == 'dropdown_country':
            question.country_options = question.get_country_options()

    # Organize questions by group
    grouped_questions = organize_questions_by_group(questions, groups)

    # Check if user has already completed this survey
    existing_responses = ParticipantResponse.objects.filter(
        survey=survey,
        participant=request.user
    ).exists()

    if request.method == 'POST':
        # Validate that all required questions are answered
        errors = []
        responses = {}  # Store as {question: answer_value}

        # Build a map of which questions are disabled based on trigger logic
        disabled_questions = set()
        for trigger_q in questions:
            if trigger_q.controls_next_n_questions > 0 and trigger_q.trigger_value:
                # Get the trigger question's answer
                trigger_field_name = f'question_{trigger_q.id}'
                trigger_answer = request.POST.get(trigger_field_name, '').strip()

                # If trigger answer doesn't match trigger_value, disable controlled questions
                if trigger_answer != trigger_q.trigger_value:
                    # Find the N questions that follow this trigger in order
                    for potential_controlled in questions:
                        if potential_controlled.order > trigger_q.order and \
                           potential_controlled.order <= trigger_q.order + trigger_q.controls_next_n_questions:
                            disabled_questions.add(potential_controlled.id)

        for index, q in enumerate(questions, start=1):
            field_name = f'question_{q.id}'

            # Auto-fill disabled questions with default values
            if q.id in disabled_questions:
                if q.question_type == 'likert':
                    # Use minimum value of the scale
                    responses[q] = q.effective_min()
                else:
                    # For non-Likert questions, store "NULL"
                    responses[q] = "NULL"
                continue

            if q.question_type == 'likert':
                answer = request.POST.get(field_name, '').strip()

                if q.required and not answer:
                    errors.append(f"Question {index} is required.")
                elif answer:
                    # Validate that answer is within this question's scale range
                    try:
                        answer_int = int(answer)
                        if answer_int < q.effective_min() or answer_int > q.effective_max():
                            errors.append(
                                f"Question {index}: Answer must be between "
                                f"{q.effective_min()} and {q.effective_max()}."
                            )
                        else:
                            responses[q] = answer_int
                    except ValueError:
                        errors.append(f"Question {index}: Invalid answer format.")
                else:
                    # Optional question left blank - record as NULL
                    if not q.required:
                        responses[q] = "NULL"

            elif q.question_type in ['multiple_choice_single', 'multiple_choice_multi']:
                # Get all selected values (checkboxes return a list)
                selected_values = request.POST.getlist(field_name)
                # Filter out any disabled options that might have been submitted
                enabled_keys = q.get_enabled_option_keys()
                filtered_values = [v for v in selected_values if str(v) in enabled_keys]

                # Validate using the model method
                is_valid, error_msg = q.validate_multiple_choice_answer(filtered_values)
                if not is_valid:
                    errors.append(f"Question {index}: {error_msg}")
                elif filtered_values:
                    # Store as JSON array
                    import json
                    responses[q] = json.dumps(filtered_values)
                else:
                    # Optional question left blank - record as NULL
                    if not q.required:
                        responses[q] = "NULL"

            elif q.question_type == 'free_text':
                answer = request.POST.get(field_name, '').strip()

                if q.required and not answer:
                    errors.append(f"Question {index} is required.")
                elif answer:
                    responses[q] = answer
                else:
                    # Optional question left blank - record as NULL
                    if not q.required:
                        responses[q] = "NULL"

            elif q.question_type in ['dropdown_year', 'dropdown_month', 'dropdown_country']:
                answer = request.POST.get(field_name, '').strip()

                if q.required and not answer:
                    errors.append(f"Question {index} is required.")
                elif answer:
                    responses[q] = answer
                else:
                    # Optional question left blank - record as NULL
                    if not q.required:
                        responses[q] = "NULL"

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Save responses to database (participant data only - is_test defaults to False)
            with transaction.atomic():
                for question, answer_value in responses.items():
                    if question.question_type == 'likert' and answer_value != "NULL":
                        # Apply reverse coding first (if applicable), then scale factor
                        stored_value = question.apply_reverse_coding(answer_value) if question.reverse_coded else answer_value
                        stored_value = question.apply_scale_factor(stored_value)
                        ParticipantResponse.objects.update_or_create(
                            survey=survey,
                            question=question,
                            participant=request.user,
                            defaults={'answer': str(stored_value)}
                        )
                    else:
                        # For multiple choice, free text, and NULL values, store as-is
                        ParticipantResponse.objects.update_or_create(
                            survey=survey,
                            question=question,
                            participant=request.user,
                            defaults={'answer': answer_value}
                        )

            messages.success(
                request,
                f"Thank you! Your responses to '{survey.title}' have been recorded."
            )
            return redirect('home')

    context = {
        'survey': survey,
        'questions': questions,
        'grouped_questions': grouped_questions,
        'is_preview': False,
        'test_mode': False,
        'has_existing_responses': existing_responses,
    }

    return render(request, 'surveys/survey_detail.html', context)


@login_required
def survey_list(request):
    """
    List all surveys for researchers only.
    Participants should use the participant dashboard instead.
    """
    # Check if user is researcher or staff
    if not (request.user.is_researcher or request.user.is_staff):
        messages.error(request, "Only researchers can access the survey management page.")
        return redirect('dashboard:participant_dashboard')

    # Researchers can see all surveys
    surveys = Survey.objects.all()

    context = {
        'surveys': surveys,
        'is_researcher': True,
    }

    return render(request, 'surveys/survey_list.html', context)
