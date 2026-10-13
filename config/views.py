from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse


def custom_404(request, exception):
    if request.path.startswith("/api/"):
        return JsonResponse({"detail": "Not found."}, status=404)

    if request.user.is_authenticated:
        action_url = reverse("dashboard:summaries")
        action_label = "Go to Dashboard"
        secondary_url = reverse("projects:lists")
        secondary_label = "View Projects"
    else:
        action_url = reverse("auth:login")
        action_label = "Sign In"
        secondary_url = reverse("download-lists")
        secondary_label = "Download App"

    return render(
        request,
        "errors/404.html",
        {
            "title": "Page not found",
            "action_url": action_url,
            "action_label": action_label,
            "secondary_url": secondary_url,
            "secondary_label": secondary_label,
            "breadcrumbs": [
                {"name": "Page not found", "url": ""},
            ],
        },
        status=404,
    )
