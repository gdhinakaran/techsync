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
def session(app):
    """Create database session for testing."""
    with app.app_context():
        yield db.session


class TestExpertRoleModel:
    """Tests for the ExpertRole model."""

    def test_create_expert_role(self, app):
        """Can create an expert role."""
        with app.app_context():
            role = ExpertRole(name='Mechanical Engineer', description='Handles mechanical systems')
            db.session.add(role)
            db.session.commit()

            saved_role = ExpertRole.query.filter_by(name='Mechanical Engineer').first()
            assert saved_role is not None
            assert saved_role.name == 'Mechanical Engineer'
            assert saved_role.description == 'Handles mechanical systems'

    def test_expert_role_name_unique(self, app):
        """Expert role names must be unique."""
        with app.app_context():
            role1 = ExpertRole(name='Electronics Engineer')
            db.session.add(role1)
            db.session.commit()

            role2 = ExpertRole(name='Electronics Engineer')
            db.session.add(role2)
            with pytest.raises(Exception):
                db.session.commit()


class TestUserModel:
    """Tests for the User model."""

    def test_create_manager_user(self, app):
        """Can create a manager user."""
        with app.app_context():
            user = User(username='manager1', role_type='manager')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()

            saved_user = User.query.filter_by(username='manager1').first()
            assert saved_user is not None
            assert saved_user.role_type == 'manager'
            assert saved_user.is_manager() is True
            assert saved_user.is_expert() is False

    def test_create_expert_user(self, app):
        """Can create an expert user with a role."""
        with app.app_context():
            role = ExpertRole(name='Process Engineer')
            db.session.add(role)
            db.session.commit()

            user = User(username='expert1', role_type='expert', expert_role_id=role.id)
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()

            saved_user = User.query.filter_by(username='expert1').first()
            assert saved_user is not None
            assert saved_user.role_type == 'expert'
            assert saved_user.is_expert() is True
            assert saved_user.expert_role.name == 'Process Engineer'

    def test_password_hashing(self, app):
        """Password should be hashed and verifiable."""
        with app.app_context():
            user = User(username='testuser', role_type='manager')
            user.set_password('mypassword')

            assert user.password_hash != 'mypassword'
            assert user.check_password('mypassword') is True
            assert user.check_password('wrongpassword') is False

    def test_username_unique(self, app):
        """Usernames must be unique."""
        with app.app_context():
            user1 = User(username='uniquename', role_type='manager')
            user1.set_password('pass1')
            db.session.add(user1)
            db.session.commit()

            user2 = User(username='uniquename', role_type='expert')
            user2.set_password('pass2')
            db.session.add(user2)
            with pytest.raises(Exception):
                db.session.commit()


class TestIssueModel:
    """Tests for the Issue model."""

    def test_create_issue(self, app):
        """Can create an issue."""
        with app.app_context():
            manager = User(username='mgr', role_type='manager')
            manager.set_password('pass')
            db.session.add(manager)
            db.session.commit()

            issue = Issue(
                title='Motor Overheating',
                description='The main motor is overheating during peak operations.',
                created_by=manager.id
            )
            db.session.add(issue)
            db.session.commit()

            saved_issue = Issue.query.first()
            assert saved_issue.title == 'Motor Overheating'
            assert saved_issue.status == 'open'
            assert saved_issue.creator.username == 'mgr'

    def test_issue_with_required_roles(self, app):
        """Can assign required expert roles to an issue."""
        with app.app_context():
            manager = User(username='mgr', role_type='manager')
            manager.set_password('pass')
            db.session.add(manager)

            mech_role = ExpertRole(name='Mechanical')
            elec_role = ExpertRole(name='Electronics')
            db.session.add_all([mech_role, elec_role])
            db.session.commit()

            issue = Issue(
                title='Complex Problem',
                description='Needs multiple experts.',
                created_by=manager.id
            )
            issue.required_expert_roles.append(mech_role)
            issue.required_expert_roles.append(elec_role)
            db.session.add(issue)
            db.session.commit()

            saved_issue = Issue.query.first()
            assert len(saved_issue.required_expert_roles) == 2
            role_names = [r.name for r in saved_issue.required_expert_roles]
            assert 'Mechanical' in role_names
            assert 'Electronics' in role_names


class TestCommentModel:
    """Tests for the Comment model."""

    def test_create_expert_comment(self, app):
        """Expert can add a comment/input to an issue."""
        with app.app_context():
            manager = User(username='mgr', role_type='manager')
            manager.set_password('pass')
            db.session.add(manager)
            db.session.commit()

            role = ExpertRole(name='Mechanical')
            db.session.add(role)
            db.session.commit()

            expert = User(username='expert', role_type='expert', expert_role_id=role.id)
            expert.set_password('pass')
            db.session.add(expert)
            db.session.commit()

            issue = Issue(title='Test', description='Test desc', created_by=manager.id)
            db.session.add(issue)
            db.session.commit()

            comment = Comment(
                issue_id=issue.id,
                user_id=expert.id,
                content='From a mechanical perspective, the issue is...',
                comment_type='input'
            )
            db.session.add(comment)
            db.session.commit()

            saved_comment = Comment.query.first()
            assert saved_comment.content == 'From a mechanical perspective, the issue is...'
            assert saved_comment.author.username == 'expert'
            assert saved_comment.is_ai_generated is False

    def test_create_ai_comment(self, app):
        """Can create AI-generated summary comment."""
        with app.app_context():
            manager = User(username='mgr', role_type='manager')
            manager.set_password('pass')
            db.session.add(manager)
            db.session.commit()

            issue = Issue(title='Test', description='Test desc', created_by=manager.id)
            db.session.add(issue)
            db.session.commit()

            ai_comment = Comment(
                issue_id=issue.id,
                user_id=None,
                content='AI Summary: All experts agree that...',
                is_ai_generated=True,
                comment_type='summary'
            )
            db.session.add(ai_comment)
            db.session.commit()

            saved_comment = Comment.query.first()
            assert saved_comment.is_ai_generated is True
            assert saved_comment.comment_type == 'summary'
            assert saved_comment.author is None


class TestIssueExpertInputTracking:
    """Tests for checking if all experts have provided input."""

    def test_has_all_expert_inputs_true(self, app):
        """Returns True when all required experts have provided input."""
        with app.app_context():
            manager = User(username='mgr', role_type='manager')
            manager.set_password('pass')
            db.session.add(manager)

            mech_role = ExpertRole(name='Mechanical')
            elec_role = ExpertRole(name='Electronics')
            db.session.add_all([mech_role, elec_role])
            db.session.commit()

            mech_expert = User(username='mech_exp', role_type='expert', expert_role_id=mech_role.id)
            mech_expert.set_password('pass')
            elec_expert = User(username='elec_exp', role_type='expert', expert_role_id=elec_role.id)
            elec_expert.set_password('pass')
            db.session.add_all([mech_expert, elec_expert])
            db.session.commit()

            issue = Issue(title='Test', description='Test', created_by=manager.id)
            issue.required_expert_roles.extend([mech_role, elec_role])
            db.session.add(issue)
            db.session.commit()

            # Add inputs from both experts
            c1 = Comment(issue_id=issue.id, user_id=mech_expert.id, content='Mech input', comment_type='input')
            c2 = Comment(issue_id=issue.id, user_id=elec_expert.id, content='Elec input', comment_type='input')
            db.session.add_all([c1, c2])
            db.session.commit()

            assert issue.has_all_expert_inputs() is True

    def test_has_all_expert_inputs_false(self, app):
        """Returns False when not all required experts have provided input."""
        with app.app_context():
            manager = User(username='mgr', role_type='manager')
            manager.set_password('pass')
            db.session.add(manager)

            mech_role = ExpertRole(name='Mechanical')
            elec_role = ExpertRole(name='Electronics')
            db.session.add_all([mech_role, elec_role])
            db.session.commit()

            mech_expert = User(username='mech_exp', role_type='expert', expert_role_id=mech_role.id)
            mech_expert.set_password('pass')
            db.session.add(mech_expert)
            db.session.commit()

            issue = Issue(title='Test', description='Test', created_by=manager.id)
            issue.required_expert_roles.extend([mech_role, elec_role])
            db.session.add(issue)
            db.session.commit()

            # Only one expert provides input
            c1 = Comment(issue_id=issue.id, user_id=mech_expert.id, content='Mech input', comment_type='input')
            db.session.add(c1)
            db.session.commit()

            assert issue.has_all_expert_inputs() is False
