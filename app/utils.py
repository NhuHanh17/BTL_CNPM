from app import db, dao
from app.models import Booking, Room, Invoice, BookingStatus, ServicesItem, InvoiceService
from datetime import datetime, timedelta

def check_in(room_id, staff_id, booking_id=None, people = 1):
    try:
        now = datetime.now()
        if booking_id:
            target_booking = Booking.query.get(booking_id)

            if target_booking:
                target_booking.status = BookingStatus.CONFIRMED

        else:

            target_booking = Booking(
                    start_datetime=now,
                    end_datetime=None,
                    room_id=room_id,
                    status=BookingStatus.CONFIRMED,
                    total_price=dao.get_room_hourly_price(room_id),
                    quantity = people 
            )

            db.session.add(target_booking)
            db.session.flush()
        room = Room.query.get(room_id)
        room.is_available = False


        d = dao.create_invoice(
                room_price=0,
                service_price=0,
                total_price=0,
                booking_id=target_booking.id,
                staff_id=staff_id
            )

        print(d)

        db.session.commit()
    except Exception as e:
        db.session.rollback()


def check_out(invoice_id, booking_id, end_datetime):
    try:
        booking = Booking.query.get(booking_id)
        invoice = Invoice.query.get(invoice_id)

        start = booking.start_datetime
        end_db = booking.end_datetime if booking.end_datetime else (start + timedelta(hours=1))

        duration_original = (end_db - start).total_seconds() / 3600
        unit_price = booking.total_price / duration_original if duration_original > 0 else booking.total_price
        duration_real = (end_datetime - start).total_seconds() / 3600
        room_price = round(duration_real * unit_price)
        print(duration_real)
        service_details = InvoiceService.query.filter_by(invoice_id=invoice_id).all()
        service_price = sum(item.total_price for item in service_details)

        booking.status = BookingStatus.COMPLETED
        booking.end_datetime = end_datetime
        booking.total_price = room_price

        room = Room.query.get(booking.room_id)
        if room:
            room.is_available = True

        invoice.room_price = room_price
        invoice.service_price = service_price
        invoice.is_paid = True
        db.session.commit()


    except Exception as e:
        db.session.rollback()
        raise e


def add_service_to_invoice(room_id, service_id, quantity):
 
    booking = Booking.query.filter_by(room_id=room_id, status=BookingStatus.CONFIRMED).first()
    invoice = Invoice.query.filter_by(booking_id=booking.id, is_paid=False).first()
    service_item = dao.get_service_item_by_id(service_id)

    detail = dao.get_invoice_service(invoice.id, service_id)
    
    if detail:
        detail.quantity += quantity
        detail.total_price = detail.quantity * service_item.price
    else:
        detail = InvoiceService(
            invoice_id=invoice.id,
            service_item_id=service_id, 
            quantity=quantity,
            total_price=quantity * service_item.price
        )
        db.session.add(detail)

    
    service_item.capacity -= quantity
    
    try:
        db.session.commit()
        dao.update_invoice(invoice.id)
        return True, "Thêm dịch vụ thành công!"
    except Exception as e:
        db.session.rollback()
        return False, str(e)

