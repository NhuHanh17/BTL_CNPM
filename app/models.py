import os
from datetime import time
from sqlalchemy import  Column, Integer, String, Boolean, Enum, ForeignKey, Time
from sqlalchemy.orm import relationship
from app import app, db
from flask_login import UserMixin
import hashlib
from enum import Enum as pyEnum


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True)

class UserRole(pyEnum):
    ADMIN = "admin"
    STAFF = "staff"
    CUSTOMER = "customer"

class RoomStatus(pyEnum):
    AVAILABLE = 'available'
    ACTIVATE = 'activate'
    MAINTENANCE = 'maintenance'

class BookingStatus(pyEnum):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
    

class User(BaseModel, UserMixin):
    username = Column(String(150), unique=True, nullable=False)
    password = Column(String(256), nullable=False)
    avatar = Column (String(200), default = 'https://thumbs.dreamstime.com/b/default-avatar-profile-icon-vector-social-media-user-photo-183042379.jpg')

    type = db.Column(Enum(UserRole), default=UserRole.CUSTOMER)
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type
    }

    def __str__(self):
        return self.username

class Admin(User):
    id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    # Admin chỉ có các thông tin cơ bản từ User
    __mapper_args__ = {'polymorphic_identity': UserRole.ADMIN}


class Staff(User):
    id = Column(Integer,ForeignKey('user.id'), primary_key=True)
    role = Column(String(50))
    __mapper_args__ = {
        'polymorphic_identity': UserRole.STAFF
        }


class Customer(User):
    id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    fullname = Column (String(200), nullable=False)
    phone_number = Column(String(200), nullable=False)
    bookings = relationship('Booking', backref='customer', lazy=True)    
    __mapper_args__ = {'polymorphic_identity': UserRole.CUSTOMER}


class RoomType(BaseModel):
    name = Column(String(200), nullable=False)
    rooms = relationship('Room', backref='type', lazy=True)
    max_capacity = Column(Integer, nullable=False)
    price = relationship('PriceConfig', backref='room', lazy=True)

    def __str__(self):
        return self.name
    

class Room(BaseModel):
    name = Column(String(200), nullable=False, unique=True)
    status = Column(Enum(RoomStatus), default='AVAILABLE')
    note =Column(String(250), nullable=True)
    type_id = Column(Integer, ForeignKey(RoomType.id), nullable=False)
    image = Column(String(200), default='https://res.cloudinary.com/dinusoo6h/image/upload/v1766109939/Gemini_Generated_Image_j0d0nbj0d0nbj0d0_otxroh.png')
    bookings = relationship('Booking', backref='room', lazy=True)

    def __str__(self):
        return self.name

class PriceConfig(BaseModel):
    room_type_id = Column(Integer, ForeignKey(RoomType.id), nullable=False)
    start_time= Column(Time, nullable=False)  
    end_time = Column(Time, nullable=False)    
    price_per_hour = Column(Integer, nullable=False)
    day_of_week = Column(String(50), nullable=False) 


class Booking(BaseModel):
    customer_id = Column(Integer, ForeignKey(Customer.id), nullable=False)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)
    start_datetime = Column(db.DateTime, nullable=False)
    end_datetime = Column(db.DateTime, nullable=False)
    total_price = Column(Integer, nullable=False)
    status = Column(String(50), default='PENDING')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        u = Admin(username='admin',
                 password=str(hashlib.md5('1111'.encode('utf-8')).hexdigest()),)
        # db.session.add(u)

        t1 = RoomType(name='Phòng thường', max_capacity=5)
        t2 = RoomType(name='Phòng VIP', max_capacity=10)
        t3 = RoomType(name='Super Party', max_capacity=15)

        # db.session.add_all([t1, t2, t3])
        # db.session.commit()

        prices = [
            # Giá phòng thường ngày thường
            PriceConfig(room_type_id=1, day_of_week='Weekday', 
                        start_time=time(8,0), end_time=time(17, 0), price_per_hour=150000),
            PriceConfig(room_type_id=1, day_of_week='Weekday', 
                        start_time=time(17, 0), end_time=time(23, 59), price_per_hour=250000),

            # Giá phòng VIP ngày thường
            PriceConfig(room_type_id=2, day_of_week='Weekday', 
                        start_time=time(8, 0), end_time=time(17, 0), price_per_hour=300000),
            PriceConfig(room_type_id=2, day_of_week='Weekday', 
                        start_time=time(17, 0), end_time=time(23, 59), price_per_hour=500000),

            # Giá phòng Super Party ngày thường
            PriceConfig(room_type_id=3, day_of_week='Weekday', 
                        start_time=time(8, 0), end_time=time(17, 0), price_per_hour=400000),
            PriceConfig(room_type_id=3, day_of_week='Weekday',
                        start_time=time(17, 0), end_time=time(23, 59), price_per_hour=700000)
        ]

        # db.session.add_all(prices)
        # db.session.commit()
