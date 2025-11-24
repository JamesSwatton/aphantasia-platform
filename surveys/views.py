from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db import transaction
from django.urls import reverse
from .models import Survey, ParticipantResponse
import random


@login_required
def survey_preview(request, pk):
    """
    Preview view for researchers to see how the survey will be rendered.
    Includes a test mode option that allows taking the survey without saving responses.
    """
    survey = get_object_or_404(Survey, pk=pk)

    # Check if user is researcher or staff
    if not (request.user.is_researcher or request.user.is_staff):
        return HttpResponseForbidden("Only researchers can preview surveys.")

    # Get all questions for this survey
    questions = list(survey.questions.all())

    # Randomize questions if enabled (using user ID as seed for consistency)
    if survey.randomize_questions:
        random.seed(request.user.id)
        random.shuffle(questions)
        random.seed()  # Reset seed for other random operations

    # Add scale ranges and labels to each question for template rendering
    scale_range = range(survey.min_value, survey.max_value + 1)
    scale_options = [
        (value, survey.get_label_for_value(value))
        for value in scale_range
    ]
    for question in questions:
        question.scale_range = scale_range
        question.scale_options = scale_options

    # Check if this is a POST request (test mode submission)
    test_mode = request.GET.get('test_mode', 'false') == 'true'
    test_responses = None

    if request.method == 'POST' and test_mode:
        # Process test mode submission (validate but don't save to database)
        errors = []
        responses = []

        for index, q in enumerate(questions, start=1):
            field_name = f'question_{q.id}'
            answer = request.POST.get(field_name, '').strip()

            if q.required and not answer:
                errors.append(f"Question {index} is required.")
            elif answer:
                # Validate that answer is within the Likert scale range
                try:
                    answer_int = int(answer)
                    if answer_int < survey.min_value or answer_int > survey.max_value:
                        errors.append(
                            f"Question {index}: Answer must be between "
                            f"{survey.min_value} and {survey.max_value}."
                        )
                    else:
                        # Apply reverse coding if enabled
                        if q.reverse_coded:
                            stored_value = (survey.max_value + survey.min_value) - answer_int
                        else:
                            stored_value = answer_int

                        # Store the response with its label
                        responses.append({
                            'order': index,
                            'question_text': q.text,
                            'answer_value': answer_int,
                            'answer_label': survey.get_label_for_value(answer_int),
                            'stored_value': stored_value,
                            'reverse_coded': q.reverse_coded
                        })
                except ValueError:
                    errors.append(f"Question {index}: Invalid answer format.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Show success message and display the test data
            messages.success(
                request,
                "Test mode: Survey validation passed! No data was saved to the database. "
                "See below for the data that would have been collected."
            )
            test_responses = responses

    context = {
        'survey': survey,
        'questions': questions,
        'is_preview': True,
        'test_mode': test_mode,
        'test_responses': test_responses,
    }

    return render(request, 'surveys/survey_detail.html', context)


@login_required
def survey_take(request, pk):
    """
    View for participants to take a survey and submit their responses.
    Researchers are redirected to test mode to prevent data contamination.
    """
    survey = get_object_or_404(Survey, pk=pk)

    # Redirect researchers to test mode to prevent data contamination
    if request.user.is_researcher or request.user.is_staff:
        messages.info(
            request,
            "As a researcher, you've been redirected to test mode. "
            "Your responses will not be saved to the database."
        )
        preview_url = reverse('surveys:survey_preview', kwargs={'pk': pk})
        return redirect(f'{preview_url}?test_mode=true')

    # Check if survey is active
    if not survey.is_active:
        messages.error(request, "This survey is not currently active.")
        return redirect('home')

    # Get all questions for this survey
    questions = list(survey.questions.all())

    # Randomize questions if enabled (using user ID as seed for consistency)
    if survey.randomize_questions:
        random.seed(request.user.id)
        random.shuffle(questions)
        random.seed()  # Reset seed for other random operations

    # Add scale ranges and labels to each question for template rendering
    scale_range = range(survey.min_value, survey.max_value + 1)
    scale_options = [
        (value, survey.get_label_for_value(value))
        for value in scale_range
    ]
    for question in questions:
        question.scale_range = scale_range
        question.scale_options = scale_options

    # Check if user has already completed this survey
    existing_responses = ParticipantResponse.objects.filter(
        survey=survey,
        participant=request.user
    ).exists()

    if request.method == 'POST':
        # Validate that all required questions are answered
        errors = []
        responses = {}  # Store as {question: answer_value}

        for index, q in enumerate(questions, start=1):
            field_name = f'question_{q.id}'
            answer = request.POST.get(field_name, '').strip()

            if q.required and not answer:
                errors.append(f"Question {index} is required.")
            elif answer:
                # Validate that answer is within the Likert scale range
                try:
                    answer_int = int(answer)
                    if answer_int < survey.min_value or answer_int > survey.max_value:
                        errors.append(
                            f"Question {index}: Answer must be between "
                            f"{survey.min_value} and {survey.max_value}."
                        )
                    else:
                        responses[q] = answer_int
                except ValueError:
                    errors.append(f"Question {index}: Invalid answer format.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Save responses to database
            with transaction.atomic():
                for question, answer_value in responses.items():
                    # Apply reverse coding if enabled
                    if question.reverse_coded:
                        stored_value = (survey.max_value + survey.min_value) - answer_value
                    else:
                        stored_value = answer_value

                    ParticipantResponse.objects.update_or_create(
                        survey=survey,
                        question=question,
                        participant=request.user,
                        defaults={'answer': str(stored_value)}
                    )

            messages.success(
                request,
                f"Thank you! Your responses to '{survey.title}' have been recorded."
            )
            return redirect('home')

    context = {
        'survey': survey,
        'questions': questions,
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
