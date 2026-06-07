from django.http import JsonResponse
from django.shortcuts import render


def index(request):
    """M0 landing page. Builder / Vol / Backtest tabs land here in M7."""
    return render(request, "lab/index.html")


def healthz(request):
    """Liveness probe for the host (Render) and smoke tests."""
    return JsonResponse({"status": "ok"})
