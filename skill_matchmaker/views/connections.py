from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
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
