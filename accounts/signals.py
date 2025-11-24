from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import User


@receiver(pre_save, sender=User)
def grant_researcher_staff_status(sender, instance, **kwargs):
    """
    Automatically grant staff status when a user is marked as a researcher.
    This allows researchers to access the Django admin panel.
    """
    if instance.is_researcher:
        instance.is_staff = True
        # Also ensure they remain a participant
        instance.is_participant = True


@receiver(post_save, sender=User)
def add_researcher_to_group(sender, instance, created, **kwargs):
    """
    Automatically add researchers to the Researchers group for permissions.
    """
    if instance.is_researcher:
        try:
            researchers_group = Group.objects.get(name='Researchers')
            instance.groups.add(researchers_group)
        except Group.DoesNotExist:
            # Group doesn't exist yet, skip silently
            pass
    else:
        # Remove from group if researcher status is removed
        try:
            researchers_group = Group.objects.get(name='Researchers')
            instance.groups.remove(researchers_group)
        except Group.DoesNotExist:
            pass
