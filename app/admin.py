import hashlib
from flask_admin import Admin, expose, BaseView, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from wtforms import PasswordField
from app import app, db, dao
from app.models import  PriceConfig, UserRole, Room, ServicesItem, Staff, Customer
from flask_login import current_user, logout_user
from flask import redirect, request
from flask import flash
from datetime import datetime, time, timedelta

class authenticated_only(ModelView):
    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.type == UserRole.ADMIN


class AdminView(authenticated_only):
  
    column_list = ['username', 'type', 'avatar']
    form_columns = ['username', 'password', 'fullname']
    form_extra_fields = {
            'password': PasswordField('Mật khẩu')
    }

    def on_model_change(self, form, model, is_created):
        raw_password = form.password.data
      
        if is_created:
            if raw_password:
                model.password = hashlib.md5(raw_password.encode('utf-8')).hexdigest()
        else:
            if raw_password:
                model.password = hashlib.md5(raw_password.encode('utf-8')).hexdigest()
            else:
                existing_model = self.session.query(self.model).get(model.id)
                model.password = existing_model.password
            
        super(AdminView, self).on_model_change(form, model, is_created)
    

class CustomerView(authenticated_only):
     form_columns = ['username', 'password', 'fullname', 'phone_number']

class RoomView(authenticated_only):
    form_columns = ['name', 'note', 'image', 'is_available','type']

class ServicesItemView(authenticated_only):
    form_columns = ['name', 'price', 'image', 'capacity']

    def on_model_delete(self, room):
        if not room.is_available:
            flash('Lỗi: Không được phép xóa phòng khi trạng thái là KHÔNG KHẢ DỤNG!', "danger")

            raise Exception("Chặn xóa do is_available = False")

class ConfigView(authenticated_only):
    form_columns = ['room', 'price_per_hour', 'start_time', 'end_time', 'is_weekend']

class StatsView(BaseView):
    @expose('/')
    def index(self):
        time = request.args.get('type', 'day')
        room_data=dao.get_revenue_stats(time=time)
        room_type_data = dao.get_trend()

        return self.render('admin/stats.html',revenue_data= room_data, usage_data=room_type_data)
    
    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.type == UserRole.ADMIN
    
class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.type == UserRole.ADMIN

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        time = request.args.get('type', 'day')
        return self.render('admin/index.html', revenue_data=dao.get_revenue_stats(time),
                    usage_data=dao.get_trend())


admin = Admin(app=app, name='Karaoke Admin', index_view=MyAdminIndexView())

admin.add_view(AdminView(Staff, db.session, category='Account'))
admin.add_view(CustomerView(Customer, db.session, category='Account'))
admin.add_view(RoomView(Room, db.session, category='Danh mục'))
admin.add_view(ServicesItemView(ServicesItem, db.session, category='Danh mục'))
admin.add_view(ConfigView(PriceConfig, db.session, category='Cấu hình'))

admin.add_view(StatsView(name='Thống kê'))

admin.add_view(LogoutView(name='Đăng xuất'))