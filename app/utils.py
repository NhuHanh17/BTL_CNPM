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
                    total_price=0.0,
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
        if not booking:
            return

        start = booking.start_datetime
        end_db = booking.end_datetime if booking.end_datetime else (start + timedelta(hours=1))
        
        duration_original = (end_db - start).total_seconds() / 3600
        unit_price = booking.total_price / duration_original if duration_original > 0 else booking.total_price

        duration_real = (end_datetime - start).total_seconds() / 3600
        room_price = round(duration_real * unit_price)

        

        service_details = InvoiceService.query.filter_by(invoice_id=invoice_id).all()
        service_price = sum(item.total_price for item in service_details)

        booking.status = BookingStatus.COMPLETED
        booking.end_datetime = end_datetime
        
        room = Room.query.get(booking.room_id)
        if room:
            room.is_available = True

        dao.update_invoice(
            invoice_id=invoice_id,
            room_price=room_price,
            service_price=service_price,
            is_paid=True
        )

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


def add_service_to_invoice(room_id, service_id, quantity):
    booking = Booking.query.filter_by(room_id=room_id, ).first()
    if not booking:
        return False

    service_item = dao.get_invoice_service_by_id(service_id)
    if not service_item:
        return False
    
    if service_item.capacity < quantity:
        return False

    invoice = Invoice.query.filter_by(booking_id=booking.id).first()

    service_item.capacity -= quantity 

    detail = dao.get_all_invoice_services(
                        invoice_id=invoice.id,
                        service_id=service_id).first()

    if detail:
        detail.quantity += quantity
    else:
        detail = InvoiceService(
            invoice_id=invoice.id,
            service_id=service_id,
            quantity=quantity,
            price=service_item.price
        )
        db.session.add(detail)

    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()