from sqlalchemy import func
from app.models import User, Customer, Room, RoomType, PriceConfig, Category, ServicesItem
from app.models import Booking, BookingStatus, Invoice, InvoiceService
from app import app, db
from sqlalchemy.exc import IntegrityError

import hashlib
from datetime import datetime, date, timedelta


def is_weekend_now():
    return datetime.now().weekday() >= 5


def get_all_rooms_info(capacity=None, date=None, end=None, page=None):
    query = db.session.query(Room, RoomType, PriceConfig). \
        join(RoomType, Room.type_id == RoomType.id). \
        join(PriceConfig, RoomType.id == PriceConfig.room_type_id). \
        filter(PriceConfig.is_weekend == is_weekend_now()). \
        filter(Room.is_available == True)

    if date:
        if isinstance(date, str):
            search_time = datetime.strptime(date, '%Y-%m-%dT%H:%M').time()
        else:
            search_time = date.time()
    else:
        search_time = datetime.now().time()

    query = query.filter(PriceConfig.start_time <= search_time). \
        filter(PriceConfig.end_time >= search_time)

    if capacity:
        query = query.filter(RoomType.max_capacity >= int(capacity))

    count = query.count()

    if page:
        page_size = app.config.get('PAGE_SIZE', 8)
        start = (int(page) - 1) * page_size
        query = query.offset(start).limit(page_size)

    return query.all(), count


def get_suggested_rooms():
    current_time_str = datetime.now().time()
    results = db.session.query(Room, RoomType, PriceConfig). \
        join(RoomType, Room.type_id == RoomType.id). \
        outerjoin(PriceConfig, (RoomType.id == PriceConfig.room_type_id) &
                  (PriceConfig.start_time <= current_time_str) &
                  (PriceConfig.end_time >= current_time_str)). \
        filter(Room.is_available == True). \
        filter(PriceConfig.is_weekend == is_weekend_now()). \
        order_by(func.random()). \
        limit(4).all()

    return results

def get_room_hourly_price(room_id):
    now = datetime.now()
    current_time = now.time()
    is_weekend = now.weekday() >= 5

    room = Room.query.get(room_id)
    if not room:
        return 0

    price_cfg = PriceConfig.query.filter(
        PriceConfig.room_type_id == room.type_id,
        PriceConfig.is_weekend == is_weekend,
        PriceConfig.start_time <= current_time,
        PriceConfig.end_time >= current_time
    ).first()

    if not price_cfg:
        price_cfg = PriceConfig.query.filter_by(
            room_type_id=room.type_id,
            is_weekend=is_weekend
        ).first()

    return price_cfg.price_per_hour if price_cfg else 0

def get_categories():
    return Category.query.all()


def get_services_by_category(cate_id=None):
    query = db.session.query(Category, ServicesItem). \
        join(ServicesItem, Category.id == ServicesItem.category_id)

    if cate_id:
        query = query.filter(Category.id == int(cate_id))

    return query.all()


def get_user_by_id(id):
    return User.query.get(id)


def auth_user(username, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return User.query.filter(User.username == username,
                             User.password == password).first()


def add_user(username, password, fullname, phone_number):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    user = Customer(username=username.strip(),
                    password=password,
                    fullname=fullname,
                    phone_number=phone_number)
    db.session.add(user)

    try:
        db.session.commit()
    except IntegrityError :
        db.session.rollback()
        raise Exception('Username đã tồn tại!')


def get_all_cate():
    return Category.query.all()

def create_booking(start_datetime, end_datetime, total_price, room_id, quantity, customer_id=None):
    try:
        booking = Booking(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            total_price=total_price,
            room_id=room_id,
            quantity=quantity,
            customer_id=customer_id
        )

        now = datetime.now()
        if abs((start_datetime - now).total_seconds()) < 300:
            room = Room.query.get(room_id)
            if room:
                room.is_available = False
                booking.status = BookingStatus.CONFIRMED

        db.session.add(booking)
        db.session.commit()
    except:
        db.session.rollback()
        raise Exception('Lỗi khi tạo booking!')



def get_room_by_id(room_id):
    result = db.session.query(Room, RoomType, PriceConfig). \
        join(RoomType, Room.type_id == RoomType.id). \
        join(PriceConfig, RoomType.id == PriceConfig.room_type_id). \
        filter(PriceConfig.is_weekend == is_weekend_now()). \
        filter(Room.is_available == True). \
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


def get_pending_bookings():
    return db.session.query(Booking, Customer) \
        .join(Customer, Booking.customer_id == Customer.id) \
        .filter(Booking.status == 'PENDING').all()


def confirm_booking(booking_id):
    try:
        booking = Booking.query.get(booking_id)
        if booking:
            booking.status = BookingStatus.CONFIRMED
            db.session.commit()
            return True
    except Exception as e:
        db.session.rollback()


def cancel_booking(booking_id):
    try:
        booking = Booking.query.get(booking_id)
        if booking:
            booking.status = BookingStatus.CANCELLED
            db.session.commit()
            return True
    except Exception as e:
        db.session.rollback()

def create_invoice(room_price, service_price, total_price, booking_id, staff_id, member_card_id=None,
                   services_used=None, discount=None, tax=0.1):
    try:

        booking = Booking.query.get(booking_id)
        if booking:
            booking.status = BookingStatus.CONFIRMED

            room = Room.query.get(booking.room_id)
            if room:
                room.is_available = False

            new_invoice = Invoice(
                room_price=room_price,
                service_price=service_price,
                total_price=total_price,
                booking_id=booking.id,
                staff_id=staff_id
            )

            if discount:
                new_invoice.discount = discount
            if tax:
                new_invoice.tax = tax
            if member_card_id:
                new_invoice.member_card_id = member_card_id
            if services_used:
                for service in services_used:
                    service_item = ServicesItem.query.get(service['service_item_id'])
                    if service_item:
                        invoice_service = InvoiceService(
                            invoice=new_invoice,
                            service_item=service_item,
                            quantity=service['quantity'],
                            total_price=service['total_price']
                        )
                        db.session.add(invoice_service)

            db.session.add(new_invoice)
            db.session.commit()
            return True
    except Exception as e:
        db.session.rollback()



def update_invoice(invoice_id):
    invoice = Invoice.query.get(invoice_id)
    details = InvoiceService.query.filter_by(invoice_id=invoice_id).all()
    current_service_price = sum(detail.total_price for detail in details)

    invoice.service_price = current_service_price
    db.session.commit()

def get_all_rooms_with_booking_check(name=None, capacity=None) :
    search_time = datetime.now().time()
    query = db.session.query(Room, RoomType, PriceConfig). \
        join(RoomType, Room.type_id == RoomType.id). \
        join(PriceConfig, RoomType.id == PriceConfig.room_type_id). \
        filter(PriceConfig.is_weekend == is_weekend_now()). \
        filter(PriceConfig.start_time <= search_time). \
        filter(PriceConfig.end_time >= search_time)

    if name:
        query = query.filter(Room.name.ilike(f'%{name}%'))
    if capacity:
        query = query.filter(RoomType.max_capacity >= int(capacity))

    rooms_data = query.all()
    now = datetime.now()
    one_hour_later = now + timedelta(hours=2)

    results = []
    for r, rt, rp in rooms_data:
        upcoming = Booking.query.filter(
            Booking.room_id == r.id,
            Booking.status == BookingStatus.CONFIRMED,
            Booking.start_datetime >= now,
            Booking.start_datetime <= one_hour_later
        ).first()

        r.is_locked_soon = True if upcoming else False
        r.next_booking_time = upcoming.start_datetime.strftime('%H:%M') if upcoming else ""
        r.upcoming_booking_id = upcoming.id if upcoming else None
        results.append((r, rt, rp))
    return results


def get_active_invoice_by_room(room_id):
    result = db.session.query(Invoice, Booking, Room, PriceConfig)\
        .join(Booking, Invoice.booking_id == Booking.id)\
        .join(Room, Booking.room_id == Room.id)\
        .join(RoomType, Room.type_id == RoomType.id)\
        .join(PriceConfig, RoomType.id == PriceConfig.room_type_id)\
        .filter(Room.id == room_id, 
                Invoice.is_paid == False,
                PriceConfig.is_weekend == is_weekend_now(),
                PriceConfig.start_time <= datetime.now().time(),
                PriceConfig.end_time >= datetime.now().time()).first()

    if result:
        invoice, booking, room, price_config = result
        
        now = datetime.now()
        duration_delta = now - booking.start_datetime
        duration_hours =abs( duration_delta.total_seconds()) / 3600
        
        invoice.room_price = round(duration_hours * price_config.price_per_hour)
        
        invoice.total_price = invoice.room_price + invoice.service_price
        invoice.total_amount = invoice.total_price * (1+ invoice.tax)
        
        service_details = db.session.query(InvoiceService, ServicesItem)\
            .join(ServicesItem, InvoiceService.service_item_id == ServicesItem.id)\
            .filter(InvoiceService.invoice_id == invoice.id).all()
            
        return room, invoice, service_details, booking
    return None

def get_invoice_service(invoice_id, service_id):
    from app.models import InvoiceService
    return InvoiceService.query.filter_by(
        invoice_id=invoice_id, 
        service_item_id=service_id
    ).first()

def get_service_item_by_id(service_id):
    return ServicesItem.query.get(service_id)


def get_revenue_stats(time='day'):
    now = datetime.now()
    query = db.session.query(
        Room.name,
        func.sum(Invoice.total_amount)
    ).join(Booking, Room.id == Booking.room_id) \
        .join(Invoice, Booking.id == Invoice.booking_id) \
        .filter(Invoice.is_paid == True)

    if time == 'day':

        query = query.filter(func.date(Invoice.created_at) == now.date())
    elif time == 'week':

        start_date = now.date() - timedelta(days=7)
        query = query.filter(func.date(Invoice.created_at) >= start_date)

    return query.group_by(Room.id, Room.name).all()

def get_trend():
    return db.session.query(RoomType.name, func.count(Invoice.id)) \
        .join(Room, RoomType.id == Room.type_id) \
        .join(Booking, Room.id == Booking.room_id) \
        .join(Invoice, Booking.id == Invoice.booking_id) \
        .filter(func.date(Invoice.created_at) == func.current_date()) \
        .group_by(RoomType.name) \
        .all()


