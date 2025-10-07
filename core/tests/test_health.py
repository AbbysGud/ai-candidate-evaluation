import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_health(client):
    url = reverse("health")
    res = client.get(url)
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
