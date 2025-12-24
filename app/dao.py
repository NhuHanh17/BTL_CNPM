from sqlalchemy import func
from app.models import User, Customer, Room, RoomType, PriceConfig, Category, ServicesItem
from app.models import Booking
from app import app, db
from sqlalchemy.exc import IntegrityError


import hashlib
from datetime import datetime

def is_weekend_now():
    return datetime.now().weekday() >= 5

def get_all_rooms_info(capacity=None, date=None, end=None, page=None):

    query = db.session.query(Room, RoomType, PriceConfig).\
        join(RoomType, Room.type_id == RoomType.id).\
        join(PriceConfig, RoomType.id == PriceConfig.room_type_id).\
        filter(PriceConfig.is_weekend == is_weekend_now()).\
        filter(Room.is_available == True)

    if date:
        if isinstance(date, str):
            search_time = datetime.strptime(date, '%Y-%m-%dT%H:%M').time()
        else:
            search_time = date.time()
    else:
        search_time = datetime.now().time()

    query = query.filter(PriceConfig.start_time <= search_time).\
                  filter(PriceConfig.end_time >= search_time)

    if capacity:
        query = query.filter(RoomType.max_capacity >= int(capacity))

    count = query.count()

    if page:
        page_size = app.config.get('PAGE_SIZE', 6)
        start = (int(page) - 1) * page_size
        query = query.offset(start).limit(page_size)

    return query.all(), count


def get_suggested_rooms():
    current_time_str = datetime.now().time()
    results = db.session.query(Room, RoomType, PriceConfig).\
        join(RoomType, Room.type_id == RoomType.id).\
        outerjoin(PriceConfig, (RoomType.id == PriceConfig.room_type_id) & 
                  (PriceConfig.start_time <= current_time_str) & 
                  (PriceConfig.end_time >= current_time_str)).\
        filter(Room.is_available == True).\
        filter(PriceConfig.is_weekend == is_weekend_now()).\
        order_by(func.random()).\
        limit(4).all()
    
    return results


def get_categories():
    return Category.query.all()

def get_services_by_category(cate_id=None):
    query = db.session.query(Category, ServicesItem).\
        join(ServicesItem, Category.id == ServicesItem.category_id)

    if cate_id:
        query = query.filter(Category.id == int(cate_id))

    return query.all()



def get_user_by_id(id):
    return User.query.get(id)

def auth_user(username, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return User.query.filter(User.username==username,
                             User.password==password).first()

def add_user(username, password, fullname, phone_number):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    user = Customer(username=username.strip(),
                password=password,
                fullname=fullname,
                phone_number=phone_number)
    db.session.add(user)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Exception('Username đã tồn tại!')


def get_all_cate():
    return Category.query.all()


def create_booking(start_datetime, end_datetime, total_price, room_id, customer_id, quantity):
    booking = Booking(
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        total_price=total_price,
        room_id=room_id,
        quantity = quantity
    )

    if customer_id:
        booking.customer_id = customer_id

    booking.is_available = False
    try:
        db.session.add(booking)
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        print(str(ex))

def get_room_by_id(room_id):
    result = db.session.query(Room, RoomType, PriceConfig).\
        join(RoomType, Room.type_id == RoomType.id).\
        join(PriceConfig, RoomType.id == PriceConfig.room_type_id).\
        filter(PriceConfig.is_weekend == is_weekend_now()).\
        filter(Room.is_available == True).\
        filter(Room.id == room_id).first()

    return result


def get_bookings_by_customer(customer_id):
    return Booking.query.filter(Booking.customer_id == customer_id).all()

def update_password(user_id, new_password):
    user = User.query.get(user_id)
    if user:
        password_hashed = str(hashlib.md5(new_password.strip().encode('utf-8')).hexdigest())
        user.password = password_hashed
        db.session.commit()
        return True
    return False