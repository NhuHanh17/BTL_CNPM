from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from app import app, db
from app.models import User, PriceConfig, Room

admin = Admin(app=app, name='Karaoke Admin')



admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Room, db.session))
admin.add_view(ModelView(PriceConfig, db.session))