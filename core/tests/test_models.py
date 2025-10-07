import pytest

from core.models import Candidate


@pytest.mark.django_db
def test_create_candidate():
    c = Candidate.objects.create(name="Ariq", email="ariq@example.com")
    assert c.id is not None  # pyright: ignore[reportAttributeAccessIssue]
