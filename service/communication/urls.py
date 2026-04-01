from django.urls import path

from communication.views import GithubWebhookView

urlpatterns = [
    path("webhook/github/", GithubWebhookView.as_view(), name="github-webhook"),
]
