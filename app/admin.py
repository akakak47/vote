from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from .models import Poll, Vote
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
    polls = Poll.query.order_by(Poll.created_at.desc()).all()
    # 确保所有时间都有时区信息
    for poll in polls:
        poll.created_at = localize_time(poll.created_at)
        poll.end_date = localize_time(poll.end_date)
    return render_template('admin/dashboard.html', polls=polls)

@admin.route('/admin/poll/new', methods=['GET', 'POST'])
@login_required
@admin_required
def create_poll():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        options = request.form.getlist('options')
        end_date = request.form.get('end_date')

        if not title or not options:
            flash('请填写标题和至少一个选项。')
            return redirect(url_for('admin.create_poll'))

        # 过滤空选项
        options = [opt.strip() for opt in options if opt.strip()]
        
        if end_date:
            # 将字符串转换为datetime对象并设置为中国时区
            naive_end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
            china_tz = pytz.timezone('Asia/Shanghai')
            end_date = china_tz.localize(naive_end_date)
        
        poll = Poll(
            title=title,
            description=description,
            options=options,
            end_date=end_date,
            created_at=get_current_time()
        )
        
        db.session.add(poll)
        db.session.commit()
        
        flash('投票创建成功！')
        return redirect(url_for('admin.admin_dashboard'))
        
    return render_template('admin/create_poll.html')

@admin.route('/admin/poll/<int:poll_id>')
@login_required
@admin_required
def poll_results(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    # 确保时间有时区信息
    poll.created_at = localize_time(poll.created_at)
    poll.end_date = localize_time(poll.end_date)
    
    votes = Vote.query.filter_by(poll_id=poll_id).all()
    # 确保投票时间有时区信息
    for vote in votes:
        vote.voted_at = localize_time(vote.voted_at)
    
    # 统计结果
    results = {}
    for option in poll.options:
        results[option] = len([v for v in votes if v.choice == option])
        
    total_votes = len(votes)
    
    return render_template('admin/results.html', 
                         poll=poll, 
                         results=results, 
                         total_votes=total_votes)

@admin.route('/admin/poll/<int:poll_id>/toggle')
@login_required
@admin_required
def toggle_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    poll.is_active = not poll.is_active
    db.session.commit()
    
    status = '开启' if poll.is_active else '关闭'
    flash(f'投票已{status}。')
    return redirect(url_for('admin.admin_dashboard'))

@admin.route('/admin/poll/<int:poll_id>/delete')
@login_required
@admin_required
def delete_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    
    # 首先删除所有相关的投票记录
    Vote.query.filter_by(poll_id=poll_id).delete()
    
    # 然后删除投票本身
    db.session.delete(poll)
    db.session.commit()
    
    flash('投票已删除。')
    return redirect(url_for('admin.admin_dashboard')) 