import pytest
from app import create_app
from config import TestConfig


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(TestConfig)
    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_returns_200(self, client):
        """Health endpoint should return 200 status."""
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        """Health endpoint should return JSON with status."""
        response = client.get('/health')
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['app'] == 'TechSync'


class TestBasicRoutes:
    """Tests for basic application routes."""

    def test_dashboard_redirects_to_login(self, client):
        """Dashboard redirects to login when not authenticated."""
        response = client.get('/')
        assert response.status_code == 302  # Redirects to login

    def test_login_route_exists(self, client):
        """Login route should exist."""
        response = client.get('/login')
        assert response.status_code == 200

    def test_register_route_exists(self, client):
        """Register route should exist."""
        response = client.get('/register')
        assert response.status_code == 200
