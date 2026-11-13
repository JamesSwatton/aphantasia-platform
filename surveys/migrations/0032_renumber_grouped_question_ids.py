from django.db import migrations


def renumber_grouped_question_ids(apps, schema_editor):
    """
    Re-letter every grouped question by order within its group. Before this,
    moving or reordering a question left the other questions in its old and
    new group with stale letters (e.g. 1_a, 1_b, 1_c, 2_b with no 2_a).
    """
    QuestionGroup = apps.get_model('surveys', 'QuestionGroup')
    Question = apps.get_model('surveys', 'Question')

    for group in QuestionGroup.objects.all():
        questions = Question.objects.filter(group=group).order_by('order', 'id')
        for position, question in enumerate(questions):
            if position < 26:
                question_number = chr(ord('a') + position)
            else:
                question_number = chr(ord('a') + (position // 26) - 1) + chr(ord('a') + (position % 26))
            question_id = f"{group.group_code}_{question_number}"
            if (question.question_number, question.question_id) != (question_number, question_id):
                Question.objects.filter(pk=question.pk).update(
                    question_number=question_number,
                    question_id=question_id,
                )


class Migration(migrations.Migration):

    dependencies = [
        ('surveys', '0031_alter_question_text'),
    ]

    operations = [
        migrations.RunPython(renumber_grouped_question_ids, migrations.RunPython.noop),
    ]
