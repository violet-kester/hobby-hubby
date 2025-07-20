#!/usr/bin/env python3

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'hobby_hubby.settings.development'
    django.setup()
    
    from django.test import TestCase, Client
    from django.urls import reverse
    
    # Quick test
    client = Client()
    url = reverse('forums:api_search')
    print(f"Testing URL: {url}")
    
    response = client.get(url, {'query': 'test'})
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content.decode()[:500]}")