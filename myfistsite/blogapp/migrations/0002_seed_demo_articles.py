from django.db import migrations
from django.utils import timezone


def seed_demo_articles(apps, schema_editor):
    Author = apps.get_model("blogapp", "Author")
    Category = apps.get_model("blogapp", "Category")
    Tag = apps.get_model("blogapp", "Tag")
    Article = apps.get_model("blogapp", "Article")

    author_1, _ = Author.objects.get_or_create(
        name="[DEMO] Иван Петров",
        defaults={
            "bio": "Пишет о Django, ORM и оптимизации запросов.",
        },
    )
    author_2, _ = Author.objects.get_or_create(
        name="[DEMO] Мария Смирнова",
        defaults={
            "bio": "Пишет о Python, архитектуре и тестировании.",
        },
    )

    category_1, _ = Category.objects.get_or_create(name="[DEMO] Django")
    category_2, _ = Category.objects.get_or_create(name="[DEMO] Python")

    tag_django, _ = Tag.objects.get_or_create(name="django")
    tag_python, _ = Tag.objects.get_or_create(name="python")
    tag_orm, _ = Tag.objects.get_or_create(name="orm")
    tag_queries, _ = Tag.objects.get_or_create(name="queries")
    tag_testing, _ = Tag.objects.get_or_create(name="testing")

    article_1, created = Article.objects.get_or_create(
        title="[DEMO] Как избежать N+1 в Django",
        defaults={
            "content": (
                "Проблема N+1 возникает, когда для списка объектов Django "
                "делает отдельные запросы к связанным данным. "
                "Для ForeignKey используйте select_related, "
                "для ManyToMany — prefetch_related."
            ),
            "pub_date": timezone.now(),
            "author": author_1,
            "category": category_1,
        },
    )
    if created:
        article_1.tags.add(tag_django, tag_orm, tag_queries)

    article_2, created = Article.objects.get_or_create(
        title="[DEMO] Когда использовать select_related",
        defaults={
            "content": (
                "select_related подходит для ForeignKey и OneToOneField. "
                "Он выполняет JOIN и подтягивает связанные сущности "
                "в одном SQL-запросе."
            ),
            "pub_date": timezone.now(),
            "author": author_1,
            "category": category_1,
        },
    )
    if created:
        article_2.tags.add(tag_django, tag_queries)

    article_3, created = Article.objects.get_or_create(
        title="[DEMO] Минимальные тесты для ListView",
        defaults={
            "content": (
                "Для нормальной практической работы полезно проверить, "
                "что страница открывается, связанные сущности отображаются, "
                "а количество запросов не растёт линейно."
            ),
            "pub_date": timezone.now(),
            "author": author_2,
            "category": category_2,
        },
    )
    if created:
        article_3.tags.add(tag_python, tag_testing)


def unseed_demo_articles(apps, schema_editor):
    Author = apps.get_model("blogapp", "Author")
    Category = apps.get_model("blogapp", "Category")
    Tag = apps.get_model("blogapp", "Tag")
    Article = apps.get_model("blogapp", "Article")

    demo_titles = [
        "[DEMO] Как избежать N+1 в Django",
        "[DEMO] Когда использовать select_related",
        "[DEMO] Минимальные тесты для ListView",
    ]

    Article.objects.filter(title__in=demo_titles).delete()

    Author.objects.filter(name__in=[
        "[DEMO] Иван Петров",
        "[DEMO] Мария Смирнова",
    ]).delete()

    Category.objects.filter(name__in=[
        "[DEMO] Django",
        "[DEMO] Python",
    ]).delete()

    for tag_name in ["django", "python", "orm", "queries", "testing"]:
        tag_qs = Tag.objects.filter(name=tag_name)
        for tag in tag_qs:
            if not tag.article_set.exists():
                tag.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("blogapp", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_demo_articles, unseed_demo_articles),
    ]