import pytest
from app import create_app
from extensions import db
from config import TestConfig
from models.user import User
from models.expert_role import ExpertRole


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def app_with_roles(app):
    """Create app with some predefined roles."""
    with app.app_context():
        role = ExpertRole(name='Mechanical Engineer')
        db.session.add(role)
        db.session.commit()
    return app


class TestRegistration:
    """Tests for user registration."""

    def test_register_page_loads(self, client):
        """Registration page should load."""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Register' in response.data

    def test_register_manager_success(self, client, app):
        """Can register a manager user."""
        response = client.post('/register', data={
            'username': 'newmanager',
            'password': 'password123',
            'confirm_password': 'password123',
            'role_type': 'manager'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Registration successful' in response.data

        with app.app_context():
            user = User.query.filter_by(username='newmanager').first()
            assert user is not None
            assert user.role_type == 'manager'

    def test_register_expert_success(self, client, app_with_roles):
        """Can register an expert user with a role."""
        with app_with_roles.app_context():
            role = ExpertRole.query.first()
            role_id = role.id

        response = client.post('/register', data={
            'username': 'newexpert',
            'password': 'password123',
            'confirm_password': 'password123',
            'role_type': 'expert',
            'expert_role_id': str(role_id)
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Registration successful' in response.data

        with app_with_roles.app_context():
            user = User.query.filter_by(username='newexpert').first()
            assert user is not None
            assert user.role_type == 'expert'
            assert user.expert_role_id == role_id

    def test_register_password_mismatch(self, client):
        """Registration fails if passwords don't match."""
        response = client.post('/register', data={
            'username': 'testuser',
            'password': 'password123',
            'confirm_password': 'different',
            'role_type': 'manager'
        }, follow_redirects=True)

        assert b'Passwords do not match' in response.data

    def test_register_duplicate_username(self, client, app):
        """Registration fails if username exists."""
        with app.app_context():
            user = User(username='existing', role_type='manager')
            user.set_password('pass')
            db.session.add(user)
            db.session.commit()

        response = client.post('/register', data={
            'username': 'existing',
            'password': 'password123',
            'confirm_password': 'password123',
            'role_type': 'manager'
        }, follow_redirects=True)

        assert b'Username already exists' in response.data


class TestLogin:
    """Tests for user login."""

    def test_login_page_loads(self, client):
        """Login page should load."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_login_success(self, client, app):
        """User can log in with correct credentials."""
        with app.app_context():
            user = User(username='testuser', role_type='manager')
            user.set_password('correctpass')
            db.session.add(user)
            db.session.commit()

        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'correctpass'
        }, follow_redirects=True)

        assert response.status_code == 200
        # After successful login, user is redirected to dashboard
        assert b'Dashboard' in response.data

    def test_login_wrong_password(self, client, app):
        """Login fails with wrong password."""
        with app.app_context():
            user = User(username='testuser', role_type='manager')
            user.set_password('correctpass')
            db.session.add(user)
            db.session.commit()

        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpass'
        }, follow_redirects=True)

        assert b'Invalid username or password' in response.data

    def test_login_nonexistent_user(self, client):
        """Login fails for non-existent user."""
        response = client.post('/login', data={
            'username': 'nobody',
            'password': 'password'
        }, follow_redirects=True)

        assert b'Invalid username or password' in response.data


class TestLogout:
    """Tests for user logout."""

    def test_logout(self, client, app):
        """User can log out."""
        with app.app_context():
            user = User(username='testuser', role_type='manager')
            user.set_password('pass')
            db.session.add(user)
            db.session.commit()

        # Login first
        client.post('/login', data={
            'username': 'testuser',
            'password': 'pass'
        })

        # Then logout
        response = client.get('/logout', follow_redirects=True)

        assert response.status_code == 200
        assert b'logged out' in response.data


class TestRoleManagement:
    """Tests for expert role management."""

    def test_manager_can_access_role_management(self, client, app):
        """Manager can access role management page."""
        with app.app_context():
            user = User(username='manager', role_type='manager')
            user.set_password('pass')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={
            'username': 'manager',
            'password': 'pass'
        })

        response = client.get('/manage-roles')
        assert response.status_code == 200
        assert b'Add New Expert Role' in response.data or b'Role Name' in response.data

    def test_manager_can_create_role(self, client, app):
        """Manager can create a new expert role."""
        with app.app_context():
            user = User(username='manager', role_type='manager')
            user.set_password('pass')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={
            'username': 'manager',
            'password': 'pass'
        })

        response = client.post('/manage-roles', data={
            'name': 'Electronics Engineer',
            'description': 'Handles electronics systems'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'created successfully' in response.data

        with app.app_context():
            role = ExpertRole.query.filter_by(name='Electronics Engineer').first()
            assert role is not None

    def test_expert_cannot_manage_roles(self, client, app_with_roles):
        """Expert cannot access role management - gets redirected to dashboard."""
        with app_with_roles.app_context():
            role = ExpertRole.query.first()
            user = User(username='expert', role_type='expert', expert_role_id=role.id)
            user.set_password('pass')
            db.session.add(user)
            db.session.commit()

        client.post('/login', data={
            'username': 'expert',
            'password': 'pass'
        })

        response = client.get('/manage-roles', follow_redirects=True)

        # Expert should be redirected to dashboard, not see the role management page
        assert b'Dashboard' in response.data
        assert b'Add New Expert Role' not in response.data
