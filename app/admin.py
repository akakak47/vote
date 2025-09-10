from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from .models import PostdocApplication, Review
from . import db
from datetime import datetime
import pytz
from functools import wraps

admin = Blueprint('admin', __name__)

def get_current_time():
    return datetime.now(pytz.timezone('Asia/Shanghai'))

def localize_time(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        china_tz = pytz.timezone('Asia/Shanghai')
        return china_tz.localize(dt)
    return dt

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('您没有权限访问此页面。')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    applications = PostdocApplication.query.order_by(PostdocApplication.created_at.desc()).all()
    # 确保所有时间都有时区信息
    for app in applications:
        app.created_at = localize_time(app.created_at)
    return render_template('admin/dashboard.html', applications=applications)

@admin.route('/admin/application/<int:app_id>')
@login_required
@admin_required
def application_details(app_id):
    application = PostdocApplication.query.get_or_404(app_id)
    # 确保时间有时区信息
    application.created_at = localize_time(application.created_at)
    
    reviews = Review.query.filter_by(application_id=app_id).all()
    # 确保审批时间有时区信息
    for review in reviews:
        review.reviewed_at = localize_time(review.reviewed_at)
    
    return render_template('admin/application_details.html', 
                         application=application, 
                         reviews=reviews)

@admin.route('/admin/application/<int:app_id>/status', methods=['POST'])
@login_required
@admin_required
def update_application_status(app_id):
    application = PostdocApplication.query.get_or_404(app_id)
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'approved', 'rejected']:
        application.status = new_status
        db.session.commit()
        flash(f'申请状态已更新为{new_status}。')
    
    return redirect(url_for('admin.application_details', app_id=app_id))

@admin.route('/admin/application/<int:app_id>/delete')
@login_required
@admin_required
def delete_application(app_id):
    application = PostdocApplication.query.get_or_404(app_id)
    
    # 首先删除所有相关的审批记录
    Review.query.filter_by(application_id=app_id).delete()
    
    # 然后删除申请本身
    db.session.delete(application)
    db.session.commit()
    
    flash('申请已删除。')
    return redirect(url_for('admin.admin_dashboard')) 