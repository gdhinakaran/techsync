from flask import Flask
from config import Config
from extensions import db, login_manager


def create_app(config_class=Config):
    """Application factory function."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)

    # Import models to ensure they're registered with SQLAlchemy
    from models.expert_role import ExpertRole
    from models.user import User
    from models.issue import Issue
    from models.comment import Comment

    # Register blueprints (routes)
    from routes.auth import auth_bp
    from routes.issues import issues_bp
    from routes.ai import ai_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(issues_bp)
    app.register_blueprint(ai_bp)

    # Health check endpoint
    @app.route('/health')
    def health():
        """Health check endpoint."""
        return {'status': 'healthy', 'app': 'TechSync'}

    # Create database tables
    with app.app_context():
        db.create_all()

    return app


# Create app instance for running directly
app = create_app()


if __name__ == '__main__':
    app.run(debug=True, port=5000)
