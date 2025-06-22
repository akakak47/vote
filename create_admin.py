from app import create_app, db
from app.models import User

def make_admin(email):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            user.is_admin = True
            db.session.commit()
            print(f"用户 {user.username} (邮箱: {user.email}) 已被设置为管理员")
        else:
            print(f"未找到邮箱为 {email} 的用户")

if __name__ == '__main__':
    email = input("请输入要设置为管理员的用户邮箱: ")
    make_admin(email) 