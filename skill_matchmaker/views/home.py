from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from ..models import Post


class HomeView(LoginRequiredMixin, ListView):
    model = Post
    context_object_name = "posts"
    template_name = "skill_matchmaker/index.html"
