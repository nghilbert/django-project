from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView
from django.views.generic.edit import FormMixin

from ..forms.comments import CommentForm
from ..forms.posts import PostForm
from ..models import Post


class PostDetailView(LoginRequiredMixin, FormMixin, DetailView):
    """Shows a post with its comments and a form to add one."""

    model = Post
    form_class = CommentForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reaction_list"] = self.object.reaction_summary(self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        # DetailView only handles GET, so load the post before handling the comment form
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        form.instance.post = self.object
        form.instance.author = self.request.user
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        # Redirecting means refreshing the page won't post the comment twice
        return self.object.get_absolute_url()


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)

