from flask_admin import Admin, expose
from flask_admin.contrib.sqla import ModelView
from app import app, db
from app.models import User, PriceConfig, UserRole, Room
from flask_login import current_user, logout_user
from flask import redirect



class AdminView(ModelView):
    def is_accessible(self) ->bool:
        return current_user.is_authenticated and current_user.type == UserRole.ADMIN


class LogoutView(ModelView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect()

    def is_accessible(self) -> bool:
        return current_user.is_authenticated


admin = Admin(app=app, name='Karaoke Admin')


admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Room, db.session))
admin.add_view(ModelView(PriceConfig, db.session))
# admin.add_view(LogoutView(name='Đăng xuất'))