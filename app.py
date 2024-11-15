from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Message
from forms import LoginForm, RegisterForm, MessageForm
from config import Config
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
bcrypt = Bcrypt(app)

socketio = SocketIO(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('chat'))
        else:
            flash('Login Unsuccessful. Check username and password.', 'danger')
    return render_template('login.html', form=form)

with app.app_context():
    db.create_all()
    
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    messages = Message.query.order_by(Message.timestamp.asc()).all()
    existing_messages = [
        {
            'username': msg.user.username, 
            'message': msg.text, 
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } for msg in messages
    ]
    
    return render_template('chat.html', existing_messages=existing_messages)

@socketio.on('send_message')
def handle_message(data):
    user = User.query.filter_by(username=data['username']).first()
    
    if user:
        message = Message(text=data['message'], user=user)
        db.session.add(message)
        db.session.commit()

        emit('receive_message', {
            'username': data['username'],
            'message': data['message'],
            'timestamp': data['timestamp']
        }, broadcast=True)

@socketio.on('connect', namespace='/chat')
def handle_connect():
    print(f'{request.sid} connected to the chat namespace')

@socketio.on('disconnect', namespace='/chat')
def handle_disconnect():
    print(f'{request.sid} disconnected from the chat namespace')

if __name__ == '__main__':
    socketio.run(app, debug=True)
