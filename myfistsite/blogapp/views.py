from django.db.models import Prefetch
from django.views.generic import ListView

from .models import Article, Tag


class ArticlesListView(ListView):
    model = Article
    template_name = "blogapp/article_list.html"
    context_object_name = "articles"

    def get_queryset(self):
        return (
            Article.objects.select_related("author", "category")
            .prefetch_related(
                Prefetch(
                    "tags",
                    queryset=Tag.objects.only("id", "name").order_by("name"),
                )
            )
            .defer("content", "author__bio")
            .order_by("-pub_date")
        )
