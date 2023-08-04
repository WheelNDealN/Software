import pytest
import pytest_flask
from main import application

@pytest.fixture()
def app():
    app.config.update({
        "TESTING": True,
    })

    yield app

def test_home_page():
    with application.test_client() as test_client:
        response = test_client.get('/login')
        assert response.status_code == 200

