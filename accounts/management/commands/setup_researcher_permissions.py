from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from surveys.models import Survey, Question, ParticipantResponse
from tasks.models import LabTask, TaskSubmission
from core.models import Domain, DataDownloadLog


class Command(BaseCommand):
    help = 'Sets up a Researcher group with appropriate permissions for managing research data'

    def handle(self, *args, **options):
        # Create or get the Researchers group
        researchers_group, created = Group.objects.get_or_create(name='Researchers')

        if created:
            self.stdout.write(self.style.SUCCESS('Created Researchers group'))
        else:
            self.stdout.write(self.style.WARNING('Researchers group already exists, updating permissions...'))

        # Clear existing permissions
        researchers_group.permissions.clear()

        # Define models and their permissions
        models_full_access = [
            Survey, Question,
            LabTask, Domain
        ]

        models_view_only = [
            ParticipantResponse, TaskSubmission
        ]

        models_with_log_access = [
            DataDownloadLog
        ]

        # Grant full access (add, change, delete, view) to research management models
        for model in models_full_access:
            content_type = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(content_type=content_type)
            for perm in permissions:
                researchers_group.permissions.add(perm)
                self.stdout.write(f'  Added permission: {perm.codename} for {model.__name__}')

        # Grant view and add permissions to participant data models
        for model in models_view_only:
            content_type = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(
                content_type=content_type,
                codename__in=[
                    f'view_{model._meta.model_name}',
                    f'add_{model._meta.model_name}'
                ]
            )
            for perm in permissions:
                researchers_group.permissions.add(perm)
                self.stdout.write(f'  Added permission: {perm.codename} for {model.__name__}')

        # Grant full access to data download logs
        for model in models_with_log_access:
            content_type = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(content_type=content_type)
            for perm in permissions:
                researchers_group.permissions.add(perm)
                self.stdout.write(f'  Added permission: {perm.codename} for {model.__name__}')

        self.stdout.write(self.style.SUCCESS(
            '\nSuccessfully configured Researchers group with appropriate permissions.'
        ))
        self.stdout.write(self.style.SUCCESS(
            'Researchers can now manage surveys, tasks, and view participant data.'
        ))
        self.stdout.write(self.style.WARNING(
            '\nNote: To add users to this group, edit them in the admin panel and assign the "Researchers" group.'
        ))
