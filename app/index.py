from datetime import datetime, timedelta
import hashlib
import math

from flask import flash, render_template, redirect, request
from app import app, dao, login
from flask_login import current_user, login_user, logout_user, login_required

from app.models import Booking, Room, User, UserRole
from app import admin, db

@app.route('/')
def index():
    rooms=dao.get_suggested_rooms()
    return render_template('index.html', rooms=rooms)

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

      
        return redirect(next if next else '/')
    return render_template('login.html', err_msg='Invalid username or password')

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
    end = request.args.get('end', '23:59:59')

    try:

        date_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M')
        search_time = date_obj.strftime('%H:%M:%S')
        rooms, count_rooms = dao.get_all_rooms_info(
            capacity=capacity, 
            date=date_obj, 
            end=end
        )

    except Exception as ex:
        rooms, count_rooms = dao.get_all_rooms_info()

    print (rooms)

    return render_template('room.html', rooms=rooms,
                           capacity=capacity,
                           date = date,
                           end=end,
                           count=count_rooms)



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


    conflict = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.status != 'cancelled',     
        Booking.start_datetime < check_out, 
        Booking.end_datetime > check_in 
    ).first()

    data = dao.get_room_by_id(room_id)
    price = data.PriceConfig.price_per_hour
    room = data.Room
    
    total_price = price * duration

    new_booking = dao.create_booking(
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

@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)


if __name__ == '__main__':
    app.run(debug=True)

