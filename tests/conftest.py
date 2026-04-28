import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import django
import pytest

def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.test_settings')
    django.setup()

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()