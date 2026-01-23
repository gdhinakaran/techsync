import pytest
from app import create_app
from extensions import db
from config import TestConfig
from models.user import User
from models.expert_role import ExpertRole
from models.issue import Issue
from models.comment import Comment


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
def setup_data(app):
    """Create test users and roles."""
    with app.app_context():
        # Create roles
        mech_role = ExpertRole(name='Mechanical Engineer')
        elec_role = ExpertRole(name='Electronics Engineer')
        db.session.add_all([mech_role, elec_role])
        db.session.commit()

        # Create users
        manager = User(username='manager', role_type='manager')
        manager.set_password('pass')

        mech_expert = User(username='mech_expert', role_type='expert', expert_role_id=mech_role.id)
        mech_expert.set_password('pass')

        elec_expert = User(username='elec_expert', role_type='expert', expert_role_id=elec_role.id)
        elec_expert.set_password('pass')

        db.session.add_all([manager, mech_expert, elec_expert])
        db.session.commit()

        return {
            'manager_id': manager.id,
            'mech_expert_id': mech_expert.id,
            'elec_expert_id': elec_expert.id,
            'mech_role_id': mech_role.id,
            'elec_role_id': elec_role.id
        }


class TestDashboard:
    """Tests for dashboard functionality."""

    def test_dashboard_requires_login(self, client):
        """Dashboard redirects to login if not authenticated."""
        response = client.get('/', follow_redirects=True)
        assert b'Login' in response.data

    def test_manager_sees_all_issues(self, client, app, setup_data):
        """Manager sees all issues on dashboard."""
        with app.app_context():
            ids = setup_data
            # Create an issue
            issue = Issue(title='Test Issue', description='Test', created_by=ids['manager_id'])
            role = ExpertRole.query.get(ids['mech_role_id'])
            issue.required_expert_roles.append(role)
            db.session.add(issue)
            db.session.commit()

        client.post('/login', data={'username': 'manager', 'password': 'pass'})
        response = client.get('/')

        assert response.status_code == 200
        assert b'Test Issue' in response.data

    def test_expert_sees_only_assigned_issues(self, client, app, setup_data):
        """Expert only sees issues assigned to their role."""
        with app.app_context():
            ids = setup_data
            # Create issue for mechanical engineer
            issue1 = Issue(title='Mechanical Issue', description='Test', created_by=ids['manager_id'])
            mech_role = ExpertRole.query.get(ids['mech_role_id'])
            issue1.required_expert_roles.append(mech_role)

            # Create issue for electronics engineer only
            issue2 = Issue(title='Electronics Issue', description='Test', created_by=ids['manager_id'])
            elec_role = ExpertRole.query.get(ids['elec_role_id'])
            issue2.required_expert_roles.append(elec_role)

            db.session.add_all([issue1, issue2])
            db.session.commit()

        # Login as mechanical expert
        client.post('/login', data={'username': 'mech_expert', 'password': 'pass'})
        response = client.get('/')

        assert b'Mechanical Issue' in response.data
        assert b'Electronics Issue' not in response.data


class TestIssueCreation:
    """Tests for issue creation."""

    def test_manager_can_create_issue(self, client, app, setup_data):
        """Manager can create a new issue."""
        client.post('/login', data={'username': 'manager', 'password': 'pass'})

        with app.app_context():
            ids = setup_data

        response = client.post('/issues/create', data={
            'title': 'New Problem',
            'description': 'Description of the problem',
            'expert_roles': [str(ids['mech_role_id'])]
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'New Problem' in response.data

        with app.app_context():
            issue = Issue.query.filter_by(title='New Problem').first()
            assert issue is not None
            assert len(issue.required_expert_roles) == 1

    def test_expert_cannot_create_issue(self, client, setup_data):
        """Expert cannot create issues."""
        client.post('/login', data={'username': 'mech_expert', 'password': 'pass'})
        response = client.get('/issues/create', follow_redirects=True)

        # Should be redirected with error
        assert b'Only managers' in response.data or b'Dashboard' in response.data


class TestExpertInput:
    """Tests for expert input submission."""

    def test_expert_can_submit_input(self, client, app, setup_data):
        """Expert can submit input on assigned issue."""
        with app.app_context():
            ids = setup_data
            # Create issue
            issue = Issue(title='Test Issue', description='Test', created_by=ids['manager_id'])
            mech_role = ExpertRole.query.get(ids['mech_role_id'])
            issue.required_expert_roles.append(mech_role)
            db.session.add(issue)
            db.session.commit()
            issue_id = issue.id

        client.post('/login', data={'username': 'mech_expert', 'password': 'pass'})
        response = client.post(f'/issues/{issue_id}/input', data={
            'content': 'My expert input on this mechanical issue.'
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            comment = Comment.query.filter_by(issue_id=issue_id, comment_type='input').first()
            assert comment is not None
            assert 'mechanical' in comment.content

    def test_expert_cannot_submit_twice(self, client, app, setup_data):
        """Expert cannot submit input twice on same issue."""
        with app.app_context():
            ids = setup_data
            issue = Issue(title='Test Issue', description='Test', created_by=ids['manager_id'])
            mech_role = ExpertRole.query.get(ids['mech_role_id'])
            issue.required_expert_roles.append(mech_role)
            db.session.add(issue)
            db.session.commit()
            issue_id = issue.id

        client.post('/login', data={'username': 'mech_expert', 'password': 'pass'})

        # First submission
        client.post(f'/issues/{issue_id}/input', data={'content': 'First input'})

        # Second submission should fail
        response = client.post(f'/issues/{issue_id}/input', data={
            'content': 'Second input'
        }, follow_redirects=True)

        assert b'already submitted' in response.data

    def test_wrong_expert_cannot_submit(self, client, app, setup_data):
        """Expert cannot submit input on issues not assigned to their role."""
        with app.app_context():
            ids = setup_data
            # Create issue for electronics only
            issue = Issue(title='Elec Only Issue', description='Test', created_by=ids['manager_id'])
            elec_role = ExpertRole.query.get(ids['elec_role_id'])
            issue.required_expert_roles.append(elec_role)
            db.session.add(issue)
            db.session.commit()
            issue_id = issue.id

        # Login as mechanical expert and try to submit
        client.post('/login', data={'username': 'mech_expert', 'password': 'pass'})
        response = client.post(f'/issues/{issue_id}/input', data={
            'content': 'Should not work'
        }, follow_redirects=True)

        # Should be redirected with error message
        assert b'not assigned' in response.data or b'not required' in response.data


class TestIssueStatus:
    """Tests for issue status updates."""

    def test_manager_can_update_status(self, client, app, setup_data):
        """Manager can update issue status."""
        with app.app_context():
            ids = setup_data
            issue = Issue(title='Test Issue', description='Test', created_by=ids['manager_id'])
            db.session.add(issue)
            db.session.commit()
            issue_id = issue.id

        client.post('/login', data={'username': 'manager', 'password': 'pass'})
        response = client.post(f'/issues/{issue_id}/status', data={
            'status': 'resolved'
        }, follow_redirects=True)

        assert response.status_code == 200

        with app.app_context():
            issue = Issue.query.get(issue_id)
            assert issue.status == 'resolved'

    def test_expert_cannot_update_status(self, client, app, setup_data):
        """Expert cannot update issue status."""
        with app.app_context():
            ids = setup_data
            issue = Issue(title='Test Issue', description='Test', created_by=ids['manager_id'])
            mech_role = ExpertRole.query.get(ids['mech_role_id'])
            issue.required_expert_roles.append(mech_role)
            db.session.add(issue)
            db.session.commit()
            issue_id = issue.id

        client.post('/login', data={'username': 'mech_expert', 'password': 'pass'})
        response = client.post(f'/issues/{issue_id}/status', data={
            'status': 'resolved'
        }, follow_redirects=True)

        assert b'Only managers' in response.data

        with app.app_context():
            issue = Issue.query.get(issue_id)
            assert issue.status == 'open'  # Status should not change
