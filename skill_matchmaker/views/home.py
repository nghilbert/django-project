from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from ..models import Post


class HomeView(LoginRequiredMixin, ListView):
    model = Post
    context_object_name = "posts"
    template_name = "skill_matchmaker/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for post in context["posts"]:
            post.reaction_list = post.reaction_summary(self.request.user)
        return context
