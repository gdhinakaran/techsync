from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models.user import User
from models.expert_role import ExpertRole

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler."""
    if current_user.is_authenticated:
        return redirect(url_for('issues.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('issues.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page and handler."""
    if current_user.is_authenticated:
        return redirect(url_for('issues.dashboard'))

    expert_roles = ExpertRole.query.all()

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role_type = request.form.get('role_type')
        expert_role_id = request.form.get('expert_role_id')

        # Validation
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', expert_roles=expert_roles)

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('register.html', expert_roles=expert_roles)

        if role_type not in ['manager', 'expert']:
            flash('Invalid role type.', 'danger')
            return render_template('register.html', expert_roles=expert_roles)

        if role_type == 'expert' and not expert_role_id:
            flash('Please select an expert specialty.', 'danger')
            return render_template('register.html', expert_roles=expert_roles)

        # Create user
        user = User(
            username=username,
            role_type=role_type,
            expert_role_id=int(expert_role_id) if expert_role_id else None
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', expert_roles=expert_roles)


@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/manage-roles', methods=['GET', 'POST'])
@login_required
def manage_roles():
    """Manage expert roles (manager only)."""
    if not current_user.is_manager():
        flash('Only managers can manage roles.', 'danger')
        return redirect(url_for('issues.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        if ExpertRole.query.filter_by(name=name).first():
            flash('A role with this name already exists.', 'danger')
        else:
            role = ExpertRole(name=name, description=description)
            db.session.add(role)
            db.session.commit()
            flash(f'Expert role "{name}" created successfully!', 'success')

    roles = ExpertRole.query.all()
    return render_template('manage_roles.html', roles=roles)
