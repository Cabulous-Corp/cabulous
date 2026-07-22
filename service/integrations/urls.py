from django.urls import path

from integrations.views import GithubWebhookView

urlpatterns = [
    path("github/webhook/", GithubWebhookView.as_view(), name="github-webhook"),
]
