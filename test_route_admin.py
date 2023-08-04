import pytest
from main import application

@pytest.fixture()
def app():
    app.config.update({
        "TESTING": True,
    })

    yield app

#expected to fail as you shouldnt be able to access the page without admin account
def test_admin():
    with application.test_client() as test_client:
        response = test_client.get('/admin')
        assert response.status_code == 500
