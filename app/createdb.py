import os
import json
from app import db, app

from app.models import Room, RoomType, PriceConfig, User, Customer, Category

def load_mock_data(path):
    file_path = os.path.join(app.root_path, path)
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

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
        for c_data in data['category']:
            c = Category(**c_data)
            db.session.add(c)

        db.session.commit()

        

