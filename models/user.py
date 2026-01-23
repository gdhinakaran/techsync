from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db, login_manager


class User(UserMixin, db.Model):
    """User model for authentication and role management."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role_type = db.Column(db.String(20), nullable=False)  # 'manager' or 'expert'
    expert_role_id = db.Column(db.Integer, db.ForeignKey('expert_roles.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    expert_role = db.relationship('ExpertRole', backref='users')
    created_issues = db.relationship('Issue', backref='creator', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if provided password matches the hash."""
        return check_password_hash(self.password_hash, password)

    def is_manager(self):
        """Check if user is a manager."""
        return self.role_type == 'manager'

    def is_expert(self):
        """Check if user is an expert."""
        return self.role_type == 'expert'

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))
