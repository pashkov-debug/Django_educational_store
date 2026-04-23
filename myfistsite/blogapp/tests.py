from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Article, Author, Category, Tag
from .views import ArticlesListView


class ArticlesListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = Author.objects.create(
            name="Иван Петров",
            bio="Автор технических статей",
        )
        cls.category = Category.objects.create(name="Разработка")

        cls.tag_django = Tag.objects.create(name="django")
        cls.tag_python = Tag.objects.create(name="python")
        cls.tag_db = Tag.objects.create(name="db")

        now = timezone.now()

        cls.article_old = Article.objects.create(
            title="Первая статья",
            content="Полный текст первой статьи",
            pub_date=now - timedelta(days=1),
            author=cls.author,
            category=cls.category,
        )
        cls.article_old.tags.add(cls.tag_python, cls.tag_db)

        cls.article_new = Article.objects.create(
            title="Вторая статья",
            content="Полный текст второй статьи",
            pub_date=now,
            author=cls.author,
            category=cls.category,
        )
        cls.article_new.tags.add(cls.tag_django, cls.tag_python)

    def test_article_list_page_renders_required_data(self):
        response = self.client.get(reverse("blogapp:article_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blogapp/article_list.html")

        self.assertContains(response, "Вторая статья")
        self.assertContains(response, "Первая статья")
        self.assertContains(response, "Иван Петров")
        self.assertContains(response, "Разработка")
        self.assertContains(response, "django")
        self.assertContains(response, "python")
        self.assertContains(response, "db")

    def test_queryset_avoids_n_plus_one_for_author_category_and_tags(self):
        queryset = ArticlesListView().get_queryset().filter(
            pk__in=[self.article_old.pk, self.article_new.pk]
        )

        with self.assertNumQueries(2):
            articles = list(queryset)
            snapshot = [
                {
                    "title": article.title,
                    "author": article.author.name,
                    "category": article.category.name,
                    "tags": [tag.name for tag in article.tags.all()],
                }
                for article in articles
            ]

        self.assertEqual(len(snapshot), 2)
        self.assertEqual(
            {item["title"] for item in snapshot},
            {"Первая статья", "Вторая статья"},
        )

        article_by_title = {item["title"]: item for item in snapshot}

        self.assertEqual(article_by_title["Первая статья"]["author"], "Иван Петров")
        self.assertEqual(article_by_title["Первая статья"]["category"], "Разработка")
        self.assertIn("python", article_by_title["Первая статья"]["tags"])
        self.assertIn("db", article_by_title["Первая статья"]["tags"])

        self.assertEqual(article_by_title["Вторая статья"]["author"], "Иван Петров")
        self.assertEqual(article_by_title["Вторая статья"]["category"], "Разработка")
        self.assertIn("django", article_by_title["Вторая статья"]["tags"])