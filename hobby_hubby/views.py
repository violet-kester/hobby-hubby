"""
Views for the main hobby_hubby project.
"""

from django.shortcuts import render


def home(request):
    """Home page view."""
    return render(request, 'home.html')