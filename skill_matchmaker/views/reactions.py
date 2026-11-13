from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic.detail import SingleObjectMixin

from ..models import Post, Reaction


class ReactView(LoginRequiredMixin, SingleObjectMixin, View):
    """Toggles the logged-in user's emoji reaction on a post."""

    model = Post

    def post(self, request, *args, **kwargs):
        post = self.get_object()  # 404 if the post doesn't exist

        emoji = request.POST.get("emoji")
        if emoji not in Reaction.Emoji.values:
            return HttpResponseBadRequest()

        Reaction.toggle(post, request.user, emoji)

        next_url = request.POST.get("next")
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        
        return redirect(post)
