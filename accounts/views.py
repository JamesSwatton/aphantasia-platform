from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from .models import ResearcherInvitation, ConsentForm
from .forms import ResearcherSignupForm
from surveys.utils import get_all_results


@login_required
def account(request):
    user = request.user
    consent_form = ConsentForm.objects.filter(is_active=True).first()
    participant_id = f"PRH-{user.date_joined.year}-{user.id:04d}"
    results = get_all_results(user)
    return render(request, 'accounts/account.html', {
        'participant_id': participant_id,
        'consent_form': consent_form,
        'results': results,
    })


def accept_invitation(request, token):
    """
    View for accepting a researcher invitation and registering.
    """
    # Get the invitation by token
    invitation = get_object_or_404(ResearcherInvitation, token=token)

    # Check if the invitation is valid
    if invitation.used:
        messages.error(request, 'This invitation has already been used.')
        return redirect('account_login')

    if invitation.is_expired():
        messages.error(request, 'This invitation has expired. Please contact the person who invited you to request a new invitation.')
        return redirect('account_login')

    # Handle form submission
    if request.method == 'POST':
        form = ResearcherSignupForm(request.POST, invitation=invitation)
        if form.is_valid():
            # Create the user
            user = form.save()

            # Log the user in
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            # Show success message
            messages.success(
                request,
                f'Welcome! Your researcher account has been created successfully. You now have access to the admin panel.'
            )

            # Redirect to admin panel
            return redirect('admin:index')
    else:
        form = ResearcherSignupForm(invitation=invitation)

    context = {
        'form': form,
        'invitation': invitation,
    }

    return render(request, 'accounts/accept_invitation.html', context)
