from datetime import datetime
from extensions import db


class Comment(db.Model):
    """Comment/Input on an issue - can be from expert or AI-generated."""
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    issue_id = db.Column(db.Integer, db.ForeignKey('issues.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Null for AI comments
    content = db.Column(db.Text, nullable=False)
    is_ai_generated = db.Column(db.Boolean, default=False)
    comment_type = db.Column(db.String(20), default='input')  # input, summary, clarification
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        if self.is_ai_generated:
            return f'<Comment AI {self.comment_type}>'
        return f'<Comment by User {self.user_id}>'
