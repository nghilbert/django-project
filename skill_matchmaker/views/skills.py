from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView

from ..forms.skills import UserSkillForm
from ..models import UserSkill


class SkillsView(LoginRequiredMixin, CreateView):
    """Lists the logged-in user's skills and lets them add new ones."""

    form_class = UserSkillForm
    template_name = "skill_matchmaker/skills.html"
    success_url = reverse_lazy("skills")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_skills"] = UserSkill.objects.filter(user=self.request.user)
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class RemoveSkillView(LoginRequiredMixin, DeleteView):
    """Removes one of the logged-in user's skills."""

    model = UserSkill
    success_url = reverse_lazy("skills")
    # Only allow POST, which skips the confirmation page so a plain link can't delete
    http_method_names = ["post"]

    def get_queryset(self):
        # Only look in the user's own skills, so someone else's skill gives a 404
        return UserSkill.objects.filter(user=self.request.user)
