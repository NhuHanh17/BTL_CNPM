import os
import json
import hashlib
from app import db, app

from app.models import Room, RoomType, PriceConfig,Category, Admin, ServicesItem

def load_mock_data(path):
    file_path = os.path.join(app.root_path, path)
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()


        u = Admin(username='admin',
                 password=str(hashlib.md5('1111'.encode('utf-8')).hexdigest()))
        db.session.add(u)
     

        data = load_mock_data('static/json/data.json')
        for rt_data in data['room_type']:
            rt = RoomType(**rt_data)
            db.session.add(rt)

        for r_data in data['room']:
            r = Room(**r_data)
            db.session.add(r)
        for pc_data in data['price_config']:
            pc = PriceConfig(**pc_data)
            db.session.add(pc)
        for c_data in data['categories']:
            c = Category(**c_data)
            db.session.add(c)
        for st_data in data['services_items']:
            st = ServicesItem(**st_data)
            db.session.add(st)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("Error !!!", e)

        

