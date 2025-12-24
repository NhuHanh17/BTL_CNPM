import os
from datetime import datetime, time
from sqlalchemy import  Column, Integer, String, Boolean, Enum, ForeignKey, Time, Float
from sqlalchemy.orm import relationship
from app import app, db
from flask_login import UserMixin
import hashlib
from enum import Enum as pyEnum


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True)

class CreatedTime(BaseModel):
    __abstract__ = True
    created_at = Column(db.DateTime, default=datetime.now())

class UserRole(pyEnum):
    ADMIN = "admin"
    STAFF = "staff"
    CUSTOMER = "customer"

class BookingStatus(pyEnum):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'

class PaymentMethod(pyEnum):
    CASH = 'cash'
    BANKING = 'banking'    



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


class Staff(User):
    id = Column(Integer,ForeignKey('user.id'), primary_key=True)

    role = Column(db.Enum(UserRole), default=UserRole.STAFF)
    
    __mapper_args__ = {
        'polymorphic_identity': role
        }
    
    invoice = relationship('Invoice', backref='staff', lazy=True)


class Customer(User):
    id = Column(Integer, ForeignKey('user.id'), primary_key=True)

    fullname = Column (String(200), nullable=False)
    phone_number = Column(String(200), nullable=False)


    bookings = relationship('Booking', backref='customer', lazy=True)    
    __mapper_args__ = {'polymorphic_identity': UserRole.CUSTOMER}


class RoomType(BaseModel):
    name = Column(String(200), nullable=False)
    max_capacity = Column(Integer, nullable=False)


    price = relationship('PriceConfig', backref='room', lazy=True)
    rooms = relationship('Room', backref='type', lazy=True)
    def __str__(self):
        return self.name
    

class Room(BaseModel):
    name = Column(String(200), nullable=False, unique=True)
    is_available = Column(Boolean, default=True)
    note =Column(String(250), nullable=True)
    image = Column(String(200), default='https://res.cloudinary.com/dinusoo6h/image/upload/v1766109939/Gemini_Generated_Image_j0d0nbj0d0nbj0d0_otxroh.png')
    bookings = relationship('Booking', backref='room', lazy=True)

    type_id = Column(Integer, ForeignKey(RoomType.id), nullable=False)

    def __str__(self):
        return self.name



class PriceConfig(BaseModel):
    start_time= Column(Time, nullable=False)  
    end_time = Column(Time, nullable=False)    
    price_per_hour = Column(Integer, nullable=False)
    is_weekend = Column(Boolean, default=False)

    room_type_id = Column(Integer, ForeignKey(RoomType.id), nullable=False)



class Booking(BaseModel):
    start_datetime = Column(db.DateTime, nullable=False)
    end_datetime = Column(db.DateTime, nullable=False)
    total_price = Column(Integer, nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)

    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)
    customer_id = Column(Integer, ForeignKey(Customer.id), nullable=False)



class Category(BaseModel):
    name = Column(String(200))

    services_items = relationship('ServicesItem', backref='category', lazy=True)

    def __str__(self):
        return self.name

class ServicesItem(BaseModel):
    name = Column(String(200))
    price = Column(Integer, nullable=False)
    unit = Column(String(50))

    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)

    def __str__(self):
        return self.name

class OrderDetail(BaseModel):
    quantity = Column(Integer)
    total_price = Column(Float, default=0.0)

    service_item_id = Column(Integer, ForeignKey(ServicesItem.id), nullable=False)
    booking_id = Column(Integer, ForeignKey(Booking.id), nullable=False)


class Invoice(BaseModel):
    room_price = Column(Float, default=0.0)
    service_price = Column(Float, default=0.0)
    discount = Column(Float, default=0.0, nullable=True)
    tax = Column(Float, default=0.05)
    total_price = Column(Float, default=0.0)
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.CASH)


    booking_id = Column(Integer, ForeignKey(Booking.id), nullable=False)
    total_amount = Column(Float, default=0.0)
    staff_id = Column(Integer, ForeignKey(Staff.id), nullable=False)





if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # u = Staff(username='admin',
        #          password=str(hashlib.md5('1111'.encode('utf-8')).hexdigest()),
        #          role=UserRole.ADMIN)
        # db.session.add(u)

        # db.session.commit()
