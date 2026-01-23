from flask import Blueprint, redirect, url_for, flash
from flask_login import login_required
from extensions import db
from models.issue import Issue
from models.comment import Comment
from services.llm_service import generate_summary

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/issues/<int:issue_id>/ai-summary', methods=['POST'])
@login_required
def generate_summary_route(issue_id):
    """Generate AI summary for an issue."""
    issue = Issue.query.get_or_404(issue_id)

    # Get all expert inputs for this issue
    expert_inputs = Comment.query.filter_by(
        issue_id=issue_id,
        comment_type='input',
        is_ai_generated=False
    ).all()

    if not expert_inputs:
        flash('No expert inputs yet. Please wait for experts to provide their input.', 'warning')
        return redirect(url_for('issues.view_issue', issue_id=issue_id))

    try:
        summary_content = generate_summary(issue, expert_inputs)

        # Create AI summary comment
        ai_comment = Comment(
            issue_id=issue_id,
            user_id=None,
            content=summary_content,
            is_ai_generated=True,
            comment_type='summary'
        )
        db.session.add(ai_comment)
        db.session.commit()

        flash('AI summary generated successfully!', 'success')
    except Exception as e:
        flash(f'Error generating AI summary: {str(e)}', 'danger')

    return redirect(url_for('issues.view_issue', issue_id=issue_id))
