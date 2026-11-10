from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView

from ..forms.posts import PostForm
from ..models import Post


class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
