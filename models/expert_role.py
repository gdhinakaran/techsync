from datetime import datetime
from extensions import db


class ExpertRole(db.Model):
    """Configurable expert role types (e.g., Mechanical Engineer, Electronics Engineer)."""
    __tablename__ = 'expert_roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ExpertRole {self.name}>'
