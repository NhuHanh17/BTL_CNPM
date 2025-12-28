import os
from datetime import datetime, time
from sqlalchemy import  Column, DateTime, Integer, String, Boolean, Enum, ForeignKey, Time, Float
from sqlalchemy.orm import relationship
from app import app, db
from flask_login import UserMixin
import hashlib
from enum import Enum as pyEnum


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True)

class CreatedAt(BaseModel):
    __abstract__ = True
    created_at = Column(db.DateTime, default=datetime.now)

class UserRole(pyEnum):
    ADMIN = "admin"
    STAFF = "staff"
    CUSTOMER = "customer"


class BookingStatus(pyEnum):
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    COMPLETED = 'completed'
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
    __tablename__ = 'admin'
    id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    __mapper_args__ = {
        'polymorphic_identity': UserRole.ADMIN
    }


class Staff(User):
    id = Column(Integer,ForeignKey('user.id',ondelete='CASCADE'), primary_key=True)
    fullname = Column (String(200), nullable=False)
    
    __mapper_args__ = {
        'polymorphic_identity': UserRole.STAFF
        }
    
    invoice = relationship('Invoice', backref='staff_member', lazy=True)


class Customer(User):
    id = Column(Integer, ForeignKey('user.id',ondelete='CASCADE'), primary_key=True)

    fullname = Column (String(200), nullable=False)
    phone_number = Column(String(200), nullable=False, unique=True)

    bookings = relationship('Booking', backref='customer', lazy=True)

    member_card = relationship('MemberCard', 
                               back_populates='customer', 
                               uselist=False, 
                               cascade="all, delete-orphan")

    __mapper_args__ = {'polymorphic_identity': UserRole.CUSTOMER}

    def __str__(self):
        return self.fullname

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
    type_id = Column(Integer, ForeignKey(RoomType.id,ondelete='RESTRICT'), nullable=False)


    def __str__(self):
        return self.name


class PriceConfig(BaseModel):
    start_time= Column(Time, nullable=False)  
    end_time = Column(Time, nullable=False)    
    price_per_hour = Column(Float, nullable=False)
    is_weekend = Column(Boolean, default=False)

    room_type_id = Column(Integer, ForeignKey(RoomType.id,ondelete='CASCADE'), nullable=False)



class Booking(BaseModel):
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=True)
    total_price = Column(Float, nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    quantity = Column(Integer, default=1, nullable=False)

    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)
    customer_id = Column(Integer, ForeignKey(Customer.id), nullable=True)

class MemberCard(CreatedAt):

    total_points = Column(Integer, default=0, nullable=False)
    is_Active = Column(Boolean, default=True, nullable=False)

    # ondelete='CASCADE' để database tự xóa khi xóa Customer ở tầng SQL
    customer_id = Column(Integer, ForeignKey('customer.id', ondelete='CASCADE'), unique=True)
    customer = relationship('Customer', back_populates='member_card')

class Category(BaseModel):
    name = Column(String(200))

    services_items = relationship('ServicesItem', backref='category', lazy=True)

    def __str__(self):
        return self.name

class ServicesItem(BaseModel):
    __tablename__ = 'services_item'
    name = Column(String(200) , nullable=False)
    price = Column(Float, nullable=False)
    unit = Column(String(50))
    image = Column(String(200), default='https://images.unsplash.com/photo-1600093463592-8e36ae95ef56?w=500&q=80')
    capacity = Column(Integer, default=0, nullable=False)

    category_id = Column(Integer, ForeignKey(Category.id,ondelete='CASCADE'), nullable=False)
    services = relationship('InvoiceService',
                            back_populates='service_item',
                            )

    def __str__(self):
        return self.name 
    
class InvoiceService(BaseModel):
    quantity = Column(Integer, default=1, nullable=False)
    total_price = Column(Float, nullable=False)

    invoice_id = Column(Integer, ForeignKey('invoice.id',ondelete='CASCADE'))
    service_item_id = Column(Integer, ForeignKey('services_item.id',ondelete='CASCADE'))
    invoice = relationship("Invoice", back_populates="invoices")
    service_item = relationship("ServicesItem", back_populates="services")

class Invoice(CreatedAt):
    __tablename__ = 'invoice'
    room_price = Column(Float, default=0.0)
    service_price = Column(Float, default=0.0)
    discount = Column(Float, default=0.0, nullable=True)
    tax = Column(Float, default=0.1)
    total_price = Column(Float, default=0.0)
    is_cash = Column(Boolean, default=True)
    is_paid = Column(Boolean, default=False)

    booking_id = Column(Integer, ForeignKey(Booking.id), nullable=False, unique=True)
    total_amount = Column(Float, default=0.0)
    staff_id = Column(Integer, ForeignKey(Staff.id), nullable=False)
    member_card_id = Column(Integer, ForeignKey(MemberCard.id), nullable=True)
    invoices = relationship('InvoiceService',
                                 back_populates='invoice',
                                 cascade="all, delete-orphan")


