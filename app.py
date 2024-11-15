from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import (
    db, User, GlobalMessages, DirectMessage, 
    GroupChat, GroupMessage, GroupChatMembership
)
from forms import LoginForm, RegisterForm, MessageForm, GroupChatForm, GroupMessageForm
from config import Config
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@app.route('/')
def index():
    return redirect(url_for('login'))

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
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        user = User.create_user(
            username=form.username.data, 
            password=hashed_password
        )

        try:
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Username already exists. Please choose a different username.', 'danger')
    
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
    messages = GlobalMessages.query.filter_by(is_deleted=False).order_by(GlobalMessages.timestamp.asc()).all()
    
    existing_messages = [
        {
            'username': msg.global_user.username, 
            'message': msg.text, 
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        } for msg in messages
    ]
    
    return render_template('chat.html', existing_messages=existing_messages)

@socketio.on('send_message')
def handle_message(data):
    user = User.query.filter_by(username=data['username']).first()
    
    if user:
        message = GlobalMessages(
            text=data['message'], 
            user_id=user.id,
            timestamp=datetime.utcnow()
        )
        
        try:
            db.session.add(message)
            db.session.commit()
            #Emit message to user
            emit('receive_message', {
                'username': data['username'],
                'message': data['message'],
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }, broadcast=True)
        except Exception as e:
            db.session.rollback()
            print(f"Error saving message: {e}")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/direct_messages')
@login_required
def direct_messages():
    sent_messages = DirectMessage.query.filter_by(sender_id=current_user.id).distinct(DirectMessage.recipient_id)
    received_messages = DirectMessage.query.filter_by(recipient_id=current_user.id).distinct(DirectMessage.sender_id)

    message_users = set()
    for msg in sent_messages:
        message_users.add(msg.recipient)
    for msg in received_messages:
        message_users.add(msg.sender)
    
    return render_template('direct_messages.html', message_users=message_users)

@app.route('/dm/<int:recipient_id>')
@login_required
def direct_message(recipient_id):
    recipient = User.query.get_or_404(recipient_id)

    messages = DirectMessage.query.filter(
        ((DirectMessage.sender_id == current_user.id) & (DirectMessage.recipient_id == recipient_id)) |
        ((DirectMessage.sender_id == recipient_id) & (DirectMessage.recipient_id == current_user.id))
    ).order_by(DirectMessage.timestamp).all()

    return render_template('direct_message.html', recipient=recipient, messages=messages)

@app.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    form = GroupChatForm()
    if form.validate_on_submit():
        new_group = GroupChat(
            name = form.name.data,
            description = form.description.data,
        )
        db.session.add(new_group)
        db.session.flush()

        membership = GroupChatMembership(
            user_id = current_user.id,
            group_id = new_group.id,
            role='admin'
        )

        db.session.add(membership)

        try:
            db.session.commit()
            flash('Group created successfully', 'success')
            return redirect(url_for('group_chat', group_id=new_group.id))
        except Exception as e:
            db.session.rollback()
            flash('Error creating group', 'danger')
    
    return render_template('create_group.html', form=form)

@socketio.on('send_direct_messaage')
def handle_direct_message(data):
    try:
        recipient = User.query.filter_by(username=data['Recipient']).first()

        if not recipient:
            return { 'status': 'error', 'message' : 'Recipient not found' }

        new_message = DirectMessage(
            sender_id = current_user.id,
            recipient_id = recipient.id,
            message = data['message']
        )
        db.session.add(new_message)
        db.session.commit()
        emit('receive_direct_message', {
            'sender':current_user.username,
            'recipient': recipient.username,
            'message':data['message'],
            'timestamp':datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }, room=recipient.id)

        return { 'status': 'success', 'message' : 'Message sent successfully' }
    except Exception as e:
        db.session.rollback()
        print(f"{e}")
        return { 'status': 'error', 'message' : 'Error sending message' }

@socketio.on('connect', namespace='/chat')
def handle_connect():
    print(f'{request.sid} connected to the chat namespace')

@socketio.on('disconnect', namespace='/chat')
def handle_disconnect():
    print(f'{request.sid} disconnected from the chat namespace')

if __name__ == '__main__':
    socketio.run(app, debug=True, ssl_context="adhoc")

#HelloWorld!