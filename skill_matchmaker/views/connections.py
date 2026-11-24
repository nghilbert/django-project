from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView
from django.views.generic.detail import SingleObjectMixin

from ..models import Connection, User


class ConnectView(LoginRequiredMixin, SingleObjectMixin, View):
    """Sends a connection request from the logged-in user to a member."""

    model = User

    def post(self, request, *args, **kwargs):
        member = self.get_object()  # 404 if the member doesn't exist

        # Checking first avoids an IntegrityError page; the DB constraints are the backstop
        if member != request.user and not Connection.objects.between(request.user, member).exists():
            Connection.objects.create(from_user=request.user, to_user=member)

        return redirect(member)


class ConnectionsView(LoginRequiredMixin, TemplateView):
    """Lists pending requests sent to the logged-in user, then the people they're connected to."""

    template_name = "skill_matchmaker/connections.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["requests"] = (
            Connection.objects.pending().filter(to_user=user).select_related("from_user")
        )
        connections = (
            Connection.objects.accepted().involving(user).select_related("from_user", "to_user")
        )
        # Templates cannot call other_user(user), so build the list of people here
        context["connected_users"] = [c.other_user(user) for c in connections]

        return context


class AcceptConnectionView(LoginRequiredMixin, SingleObjectMixin, View):
    """Accepts a pending request sent to the logged-in user. Only allows POST."""

    def get_queryset(self):
        # Limiting the queryset means get_object() returns 404 for any other request
        return Connection.objects.pending().filter(to_user=self.request.user)

    def post(self, request, *args, **kwargs):
        self.get_object().accept()
        return redirect("connections")
