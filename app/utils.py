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
        booking.status = BookingStatus.COMPLETED
        room = Room.query.get(booking.room_id)

        if room:
            room.is_available = True

        invoice = Invoice.query.filter_by(id=invoice_id).first()

        service_details = InvoiceService.query.filter_by(invoice_id=invoice.id).all()
        service_price = sum(item.quantity * item.unit_price for item in service_details)

        duration = (end_datetime - booking.start_datetime).total_seconds() / 3600
        room_price = duration * booking.total_price
        total_amount = room_price + service_price


        dao.update_invoice(invoice.id,
                                    total_price=room_price,
                                    service_price=service_price,
                                    total_amount=total_amount,
                                    is_paid=True
                                  )

    except Exception as e:
        db.session.rollback()


def add_service_to_invoice(invoice_id, service_id, quantity):
    try:
        service = dao.get_services_item_by_id(service_id)
        if not service:
            return False

        detail = InvoiceService.query.filter_by(invoice_id=invoice_id,
                                                    services_item_id=service_id).first()

        if detail:
            detail.quantity += int(quantity)

        else:
            detail = InvoiceService(
                invoice_id=invoice_id,
                services_item_id=service_id,
                quantity=int(quantity),
                unit_price=service.price
                )
            db.session.add(detail)

            db.session.commit()
    except Exception as ex:
        db.session.rollback()