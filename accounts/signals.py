from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import User


@receiver(pre_save, sender=User)
def grant_researcher_staff_status(sender, instance, **kwargs):
    if instance.is_researcher:
        instance.is_staff = True
        instance.is_participant = True
