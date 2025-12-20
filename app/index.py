from datetime import datetime
import hashlib
import math

from flask import render_template, redirect, request
from app import app, dao, login
from flask_login import current_user, login_user, logout_user, login_required

from app.models import User
from app import admin

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

    user = dao.auth_user(username, password)
    if user:
        login_user(user)

        next = request.form.get('next')
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
                     phone_number=request.form.get('phone_number'),
                     avatar=request.files.get('avatar'))
        return redirect('/login')
    except Exception as ex:
        return render_template('register.html', err_msg=str(ex))




@app.route('/room')
def room_view():
    capacity = request.args.get('capacity', '5') 
    date = request.args.get('date',datetime.now().strftime('%Y-%m-%dT%H:%M'))
    end = request.args.get('end', '23:59:59')

    print( capacity, date, end)
    
    try:

        date_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M')
        search_time = date_obj.strftime('%H:%M:%S')

        rooms, count_rooms = dao.get_all_rooms_info(
            capacity=capacity, 
            date=date_obj, 
            end=end
        )

    except Exception as ex:
        print (ex)
        rooms, count_rooms = dao.get_all_rooms_info()

    

    return render_template('room.html', rooms=rooms,
                           capacity=capacity,
                           date = date,
                           end=end,
                           count=count_rooms)


@app.route('/menu')
def menu_view():
    return render_template('menu.html')

@app.route('/about')
def about_view():
    return render_template('about.html')

@app.route('/profile')
@login_required
def profile_view():
    return render_template('profile.html')

@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)


if __name__ == '__main__':
    app.run(debug=True)

