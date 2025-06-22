from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from .models import Poll, Vote
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
    current_time = get_current_time()
    # 获取活跃的投票，同时检查截止日期
    active_polls = Poll.query.filter(
        (Poll.is_active == True) & 
        ((Poll.end_date == None) | (Poll.end_date > current_time))
    ).all()
    return render_template('main/index.html', polls=active_polls)

@main.route('/poll/<int:poll_id>')
@login_required
def view_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    user_vote = Vote.query.filter_by(user_id=current_user.id, poll_id=poll_id).first()
    return render_template('main/poll.html', poll=poll, user_vote=user_vote)

@main.route('/poll/<int:poll_id>/vote', methods=['POST'])
@login_required
def submit_vote(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    current_time = get_current_time()
    
    if not poll.is_active:
        flash('该投票已结束。')
        return redirect(url_for('main.view_poll', poll_id=poll_id))
        
    if poll.end_date:
        end_date = localize_time(poll.end_date)
        if end_date < current_time:
            poll.is_active = False
            db.session.commit()
            flash('该投票已结束。')
            return redirect(url_for('main.view_poll', poll_id=poll_id))

    existing_vote = Vote.query.filter_by(user_id=current_user.id, poll_id=poll_id).first()
    if existing_vote:
        flash('您已经参与过此投票。')
        return redirect(url_for('main.view_poll', poll_id=poll_id))

    choice = request.form.get('choice')
    if not choice or choice not in poll.options:
        flash('请选择有效的选项。')
        return redirect(url_for('main.view_poll', poll_id=poll_id))

    vote = Vote(
        user_id=current_user.id,
        poll_id=poll_id,
        choice=choice,
        voted_at=current_time
    )
    db.session.add(vote)
    db.session.commit()

    flash('投票成功！')
    return redirect(url_for('main.view_poll', poll_id=poll_id)) 