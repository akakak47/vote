from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from .models import PostdocApplication, Review
from . import db
from datetime import datetime
import pytz

main = Blueprint('main', __name__)

def get_current_time():
    return datetime.now(pytz.timezone('Asia/Shanghai'))

def localize_time(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        china_tz = pytz.timezone('Asia/Shanghai')
        return china_tz.localize(dt)
    return dt

@main.route('/')
def index():
    # 获取所有待审批的申请
    pending_applications = PostdocApplication.query.filter_by(status='pending').all()
    return render_template('main/index.html', applications=pending_applications)

@main.route('/application/<int:app_id>')
@login_required
def view_application(app_id):
    application = PostdocApplication.query.get_or_404(app_id)
    user_review = Review.query.filter_by(reviewer_id=current_user.id, application_id=app_id).first()
    return render_template('main/application.html', application=application, user_review=user_review)

@main.route('/application/new', methods=['GET', 'POST'])
@login_required
def submit_application():
    if request.method == 'POST':
        applicant_name = request.form.get('applicant_name')
        applicant_email = request.form.get('applicant_email')
        phone = request.form.get('phone')
        education_background = request.form.get('education_background')
        research_proposal = request.form.get('research_proposal')
        mentor_recommendation = request.form.get('mentor_recommendation')

        if not applicant_name or not applicant_email or not research_proposal:
            flash('请填写必填项目。')
            return redirect(url_for('main.submit_application'))

        application = PostdocApplication(
            applicant_name=applicant_name,
            applicant_email=applicant_email,
            phone=phone,
            education_background=education_background,
            research_proposal=research_proposal,
            mentor_recommendation=mentor_recommendation,
            submitted_by=current_user.id,
            created_at=get_current_time()
        )
        
        db.session.add(application)
        db.session.commit()
        
        flash('申请提交成功！')
        return redirect(url_for('main.index'))
    
    return render_template('main/submit_application.html')

@main.route('/application/<int:app_id>/review', methods=['POST'])
@login_required  
def submit_review(app_id):
    application = PostdocApplication.query.get_or_404(app_id)
    
    # 检查用户是否有审批权限（管理员）
    if not current_user.is_admin:
        flash('您没有权限进行审批。')
        return redirect(url_for('main.view_application', app_id=app_id))

    # 检查是否已经审批过
    existing_review = Review.query.filter_by(reviewer_id=current_user.id, application_id=app_id).first()
    if existing_review:
        flash('您已经审批过此申请。')
        return redirect(url_for('main.view_application', app_id=app_id))

    decision = request.form.get('decision')
    comments = request.form.get('comments')
    
    if decision not in ['approved', 'rejected']:
        flash('请选择有效的审批结果。')
        return redirect(url_for('main.view_application', app_id=app_id))

    review = Review(
        reviewer_id=current_user.id,
        application_id=app_id,
        decision=decision,
        comments=comments,
        reviewed_at=get_current_time()
    )
    
    # 更新申请状态
    application.status = decision
    
    db.session.add(review)
    db.session.commit()

    flash('审批完成！')
    return redirect(url_for('main.view_application', app_id=app_id)) 