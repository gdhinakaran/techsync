from datetime import datetime
from extensions import db


# Association table for Issue <-> ExpertRole many-to-many relationship
issue_expert_roles = db.Table(
    'issue_expert_roles',
    db.Column('issue_id', db.Integer, db.ForeignKey('issues.id'), primary_key=True),
    db.Column('expert_role_id', db.Integer, db.ForeignKey('expert_roles.id'), primary_key=True)
)


class Issue(db.Model):
    """Issue/Problem that needs multi-disciplinary expert input."""
    __tablename__ = 'issues'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Many-to-many relationship with ExpertRole (which expert types are needed)
    required_expert_roles = db.relationship(
        'ExpertRole',
        secondary=issue_expert_roles,
        backref=db.backref('issues', lazy='dynamic')
    )

    # One-to-many relationship with comments
    comments = db.relationship('Comment', backref='issue', lazy='dynamic', order_by='Comment.created_at')

    def get_expert_inputs(self):
        """Get all expert input comments for this issue."""
        return [c for c in self.comments if c.comment_type == 'input']

    def get_ai_summaries(self):
        """Get all AI-generated summaries for this issue."""
        return [c for c in self.comments if c.is_ai_generated]

    def has_all_expert_inputs(self):
        """Check if all required expert roles have provided input."""
        required_role_ids = {role.id for role in self.required_expert_roles}
        submitted_role_ids = set()

        for comment in self.comments:
            if comment.comment_type == 'input' and comment.author and comment.author.expert_role_id:
                submitted_role_ids.add(comment.author.expert_role_id)

        return required_role_ids <= submitted_role_ids

    def __repr__(self):
        return f'<Issue {self.title}>'
