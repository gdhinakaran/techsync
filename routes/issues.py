from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models.issue import Issue
from models.expert_role import ExpertRole
from models.comment import Comment

issues_bp = Blueprint('issues', __name__)


@issues_bp.route('/')
@login_required
def dashboard():
    """Main dashboard - shows list of issues."""
    if current_user.is_manager():
        # Managers see all issues
        issues = Issue.query.order_by(Issue.created_at.desc()).all()
    else:
        # Experts see only issues assigned to their role
        if current_user.expert_role_id:
            issues = Issue.query.filter(
                Issue.required_expert_roles.any(id=current_user.expert_role_id)
            ).order_by(Issue.created_at.desc()).all()
        else:
            issues = []

    return render_template('dashboard.html', issues=issues)


@issues_bp.route('/issues/create', methods=['GET', 'POST'])
@login_required
def create_issue():
    """Create a new issue (manager only)."""
    if not current_user.is_manager():
        flash('Only managers can create issues.', 'danger')
        return redirect(url_for('issues.dashboard'))

    expert_roles = ExpertRole.query.all()

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        role_ids = request.form.getlist('expert_roles')

        if not title or not description:
            flash('Please fill in all required fields.', 'danger')
            return render_template('create_issue.html', expert_roles=expert_roles)

        if not role_ids:
            flash('Please select at least one expert role.', 'danger')
            return render_template('create_issue.html', expert_roles=expert_roles)

        issue = Issue(
            title=title,
            description=description,
            created_by=current_user.id
        )

        # Add required expert roles
        for role_id in role_ids:
            role = ExpertRole.query.get(int(role_id))
            if role:
                issue.required_expert_roles.append(role)

        db.session.add(issue)
        db.session.commit()

        flash('Issue created successfully!', 'success')
        return redirect(url_for('issues.view_issue', issue_id=issue.id))

    return render_template('create_issue.html', expert_roles=expert_roles)


@issues_bp.route('/issues/<int:issue_id>')
@login_required
def view_issue(issue_id):
    """View a single issue with comments."""
    issue = Issue.query.get_or_404(issue_id)

    # Check if expert can view this issue
    if current_user.is_expert():
        if not current_user.expert_role_id:
            flash('You need an expert role assigned to view issues.', 'danger')
            return redirect(url_for('issues.dashboard'))

        if current_user.expert_role_id not in [r.id for r in issue.required_expert_roles]:
            flash('This issue is not assigned to your expertise area.', 'danger')
            return redirect(url_for('issues.dashboard'))

    comments = Comment.query.filter_by(issue_id=issue_id).order_by(Comment.created_at).all()

    # Check if current expert can submit input (hasn't already)
    can_submit_input = False
    if current_user.is_expert() and current_user.expert_role_id:
        existing_input = Comment.query.filter_by(
            issue_id=issue_id,
            user_id=current_user.id,
            comment_type='input'
        ).first()
        if not existing_input:
            can_submit_input = True

    return render_template('issue_detail.html',
                          issue=issue,
                          comments=comments,
                          can_submit_input=can_submit_input)


@issues_bp.route('/issues/<int:issue_id>/input', methods=['POST'])
@login_required
def submit_input(issue_id):
    """Submit expert input on an issue."""
    issue = Issue.query.get_or_404(issue_id)

    if not current_user.is_expert():
        flash('Only experts can submit input.', 'danger')
        return redirect(url_for('issues.view_issue', issue_id=issue_id))

    # Check if expert's role is required for this issue
    if current_user.expert_role_id not in [r.id for r in issue.required_expert_roles]:
        flash('Your expertise is not required for this issue.', 'danger')
        return redirect(url_for('issues.view_issue', issue_id=issue_id))

    # Check if already submitted
    existing = Comment.query.filter_by(
        issue_id=issue_id,
        user_id=current_user.id,
        comment_type='input'
    ).first()

    if existing:
        flash('You have already submitted your input for this issue.', 'warning')
        return redirect(url_for('issues.view_issue', issue_id=issue_id))

    content = request.form.get('content')
    if not content:
        flash('Please provide your input.', 'danger')
        return redirect(url_for('issues.view_issue', issue_id=issue_id))

    comment = Comment(
        issue_id=issue_id,
        user_id=current_user.id,
        content=content,
        comment_type='input'
    )

    db.session.add(comment)

    # Update issue status to in_progress if it was open
    if issue.status == 'open':
        issue.status = 'in_progress'

    db.session.commit()

    flash('Your expert input has been submitted.', 'success')
    return redirect(url_for('issues.view_issue', issue_id=issue_id))


@issues_bp.route('/issues/<int:issue_id>/status', methods=['POST'])
@login_required
def update_status(issue_id):
    """Update issue status (manager only)."""
    if not current_user.is_manager():
        flash('Only managers can update issue status.', 'danger')
        return redirect(url_for('issues.view_issue', issue_id=issue_id))

    issue = Issue.query.get_or_404(issue_id)
    new_status = request.form.get('status')

    if new_status in ['open', 'in_progress', 'resolved']:
        issue.status = new_status
        db.session.commit()
        flash(f'Issue status updated to {new_status.replace("_", " ").title()}.', 'success')

    return redirect(url_for('issues.view_issue', issue_id=issue_id))
