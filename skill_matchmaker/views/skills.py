from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView

from ..forms.skills import UserSkillForm


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
        # select_related loads each skill's name in the same query
        context["user_skills"] = self.request.user.skills.select_related("skill")
        return context

    def form_valid(self, form):
        # The user creates their own skill, so the user is filled in automatically
        self.object = self.request.user.skills.create(**form.cleaned_data)
        # Don't call super().form_valid(form), since that would save the skill a second time
        return redirect(self.get_success_url())


class RemoveSkillView(LoginRequiredMixin, DeleteView):
    """Removes one of the logged-in user's skills."""

    success_url = reverse_lazy("skills")
    # Only allow POST, which skips the confirmation page so a plain link can't delete
    http_method_names = ["post"]

    def get_queryset(self):
        # Only look in the user's own skills, so someone else's skill gives a 404
        return self.request.user.skills.all()
