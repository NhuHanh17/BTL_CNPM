from datetime import datetime, time, timedelta
import hashlib
import math

from flask import flash, render_template, redirect, request
from app import app, dao, login
from flask_login import current_user, login_user, logout_user, login_required

from app.models import Booking, Room, User, UserRole, BookingStatus
from app import admin, utils

@app.route('/')
def index():
    rooms=dao.get_suggested_rooms()
    return render_template('index.html', rooms=rooms)

@app.route('/cashier')
@login_required
def index_casher():
    bookings = dao.get_pending_bookings()
    return render_template('cashier.html', bookings=bookings)


@app.route('/login')
def login_view():

    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_process():
    username = request.form.get('username')
    password = request.form.get('password')
    next = request.args.get('next')

    user = dao.auth_user(username, password)
    if user:
        login_user(user)
      
        if user.type == UserRole.ADMIN:
            return redirect('/admin')
            
        elif user.type == UserRole.STAFF:
            return redirect('/cashier')
        
        return redirect(next if next else '/')
    
    
    flash('Tên đăng nhập hoặc mật khẩu không chính xác!', 'danger')

    return render_template('login.html')

    
    

@app.route('/logout')
def logout_view():
    logout_user()
    return redirect('/')

@app.route('/register')
def register_view():
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def register_process():
    password = request.form.get('password')
    confirm = request.form.get('confirm')

    if password != confirm:
        return render_template('register.html', err_msg='Password and Confirm Password must be the same!')
    
    try:
        dao.add_user(username=request.form.get('username'),
                     password=password,
                     fullname=request.form.get('fullname'),
                     phone_number=request.form.get('phone_number')
                     )
        return redirect('/login')
    except Exception as ex:
        return render_template('register.html', err_msg=str(ex))


@app.route('/room')
def room_view():
    capacity = request.args.get('capacity', '5') 
    date = request.args.get('date',datetime.now().strftime('%Y-%m-%dT%H:%M'))
    end = request.args.get('time', '23:00:00')
    page=int(request.args.get('page', 1))
    try:

        date_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M')
        search_time = date_obj.strftime('%H:%M:%S')
        rooms, count_rooms = dao.get_all_rooms_info(
            capacity=capacity, 
            date=date_obj, 
            end=end,
            page = page
        )

    except Exception as ex:
        rooms, count_rooms = dao.get_all_rooms_info()
    

    return render_template('room.html', rooms=rooms,
                           capacity=capacity,
                           date = date,
                           end=end,
                           count=count_rooms,
                            pages=math.ceil(count_rooms/app.config['PAGE_SIZE']))



@app.route('/booking/<int:room_id>', methods=['GET'])
@login_required
def booking_page(room_id):
    data = dao.get_room_by_id(room_id)

    room = data.Room
    r_type = data.RoomType
    r_price = data.PriceConfig
    return render_template('booking.html', room=room, r_type=r_type, r_price=r_price)




@app.route('/booking', methods=['POST'])
@login_required
def booking_submit():

    room_id = request.form.get('room_id')
    date_str = request.form.get('date')      
    time_str = request.form.get('time')      
    duration = int(request.form.get('duration'))
    people = int(request.form.get('people'))
    
    data = dao.get_room_by_id(room_id)
    r_price = data.PriceConfig
    room = data.Room    
    r_type = data.RoomType

    check_in = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    check_out = check_in + timedelta(hours=duration)
        
    if check_in < datetime.now():
        err_msg='Thời gian đặt phòng phải lớn hơn thời gian hiện tại.'
        return render_template('booking.html', room=room, r_type=r_type, r_price=r_price, err_msg=err_msg)


    data = dao.get_room_by_id(room_id)
    price = data.PriceConfig.price_per_hour
    room = data.Room
    
    total_price = price * duration

    dao.create_booking(
            room_id=room.id,
            start_datetime=check_in,
            end_datetime=check_out,  
            total_price=total_price,
            customer_id=current_user.id,
            quantity=people
            )

    return redirect('/profile')



@app.route('/menu')
def menu_view():
    categories = dao.get_categories()
    services_items = dao.get_services_by_category(cate_id=request.args.get('category_id'))

    return render_template('menu.html', categories=categories, services_items=services_items)


@app.route('/about')
def about_view():
    return render_template('about.html')

@app.route('/profile')
@login_required
def profile_view():
    histories = dao.get_bookings_by_customer(current_user.id)
    count = len(histories)
    return render_template('profile.html', histories=histories, count = count)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if current_user.type != UserRole.CUSTOMER:
        return redirect('/')

    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        old_password_hashed = str(hashlib.md5(old_password.strip().encode('utf-8')).hexdigest())
        if old_password_hashed != current_user.password:
            flash('Mật khẩu hiện tại không đúng!', 'danger')
            return render_template('profile.html')

        if new_password != confirm_password:
            flash('Mật khẩu mới và xác nhận không khớp!', 'danger')
            return render_template('profile.html')

        if dao.update_password(user_id=current_user.id, new_password=new_password):
            flash('Cập nhật mật khẩu thành công!', 'success')
            return redirect('/profile')
        else:
            flash('Có lỗi xảy ra khi lưu!', 'danger')
            return render_template('profile.html')
        
    return redirect('/profile')


@app.route('/cashier/approve/<int:booking_id>')
def approve_booking(booking_id):
    try: 
        dao.confirm_booking(booking_id)
        flash('Đã duyệt đơn đặt phòng thành công!', 'success')
    except Exception as ex:
        flash('Duyệt đơn đặt phòng thất bại! ' + str(ex), 'danger')
    
    return redirect(request.referrer or '/cashier')

@app.route('/cashier/reject/<int:booking_id>')
def reject_booking(booking_id):
    try: 
        dao.cancel_booking(booking_id)
        flash('Đã hủy đơn đặt phòng thành công!', 'success')
    except Exception as ex:
        flash('Hủy đơn đặt phòng thất bại! ' + str(ex), 'danger')
    
    return redirect(request.referrer or '/cashier')

@app.route('/cashier/rooms')
def cashier_rooms_view():
  
    return render_template('cashier_room.html')


@app.route('/cashier/quick-book', methods=['POST'])
@login_required
def quick_book():
    if current_user.type != UserRole.STAFF:
        return redirect('/')

    room_id = request.form.get('room_id')
    people = request.form.get('people')


    try:
        if utils.check_in(room_id, staff_id=current_user.id, people=people):
            flash('Mở phòng nhanh thành công!', 'success')
    except Exception as ex:
        pass


    return redirect("/cashier/rooms")

@app.route('/cashier/open-room/<int:booking_id>')
@login_required
def open_room_booking(booking_id):
    booking = Booking.query.get(booking_id)
    if utils.check_in(room_id=booking.room_id, staff_id=current_user.id, booking_id=booking_id):
        flash('Đã duyệt đơn và tạo hóa đơn!', 'success')
    return redirect("/cashier/rooms")


@app.route('/api/get-invoice/<int:room_id>')
@login_required
def get_invoice_api(room_id):
    invoice_data = dao.get_active_invoice_by_room(room_id)
    
    if invoice_data:
        room, invoice, service_details, booking = invoice_data
        return render_template('components/invoice_detail.html', 
                               room=room, 
                               invoice=invoice, 
                               booking = booking,
                               service_details=service_details)
    
    
    return "<p class='p-4 text-center text-muted'>Không tìm thấy hóa đơn.</p>"

@app.route('/cashier/checkout/<int:room_id>', methods=['POST'])
@login_required
def checkout_room(room_id):
    if current_user.type != UserRole.STAFF:
        return redirect('/')
    booking_id = request.form.get('booking_id')
    invoice_id = request.form.get('invoice_id')

    try:
        utils.check_out(invoice_id=invoice_id, booking_id=booking_id, end_datetime=datetime.now())
        flash('Thanh toán hóa đơn thành công!', 'success')
    except Exception as ex:
        flash('Thanh toán hóa đơn thất bại! ' + str(ex), 'danger')
    return redirect("/cashier/rooms")



@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.context_processor
def inject_role():
    return dict(UserRole=UserRole)
@app.context_processor
def booking_status():
    return dict(BookingStatus=BookingStatus)

@app.context_processor
def load_common_data():
    rooms, count = dao.get_all_rooms_info()
    all_room = dao.get_all_rooms_with_booking_check()
    return {
        'rooms': rooms,
        'count_rooms': count,
        'all_room': all_room
    }


if __name__ == '__main__':
    app.run(debug=True)

