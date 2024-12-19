from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
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
        
        if not user:
            return redirect(url_for('loading',
                                  message='Username does not exist.',
                                  redirect_url=url_for('login')))
        elif not bcrypt.check_password_hash(user.password, form.password.data):
            return redirect(url_for('loading',
                                  message='Incorrect password.',
                                  redirect_url=url_for('login')))
        else:
            login_user(user)
            return redirect(url_for('loading',
                                  message='Logging in!',
                                  redirect_url=url_for('chat')))
            
    return render_template('login.html', form=form)


with app.app_context():
    db.create_all()


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User.create_user(form.username.data, hashed_password)
        
        try:
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('loading',
                                  message='Account created successfully!',
                                  redirect_url=url_for('login')))
        except IntegrityError:
            db.session.rollback()
            return redirect(url_for('register'))
    
    return render_template('register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('loading', 
                          message='Logging out!',
                          redirect_url=url_for('login')))


@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    messages = GlobalMessages.query.filter_by(
        is_deleted=False).order_by(GlobalMessages.timestamp.asc()).all()

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
            # Emit message to user
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
    sent_messages = DirectMessage.query.filter_by(
        sender_id=current_user.id).distinct(DirectMessage.recipient_id)
    received_messages = DirectMessage.query.filter_by(
        recipient_id=current_user.id).distinct(DirectMessage.sender_id)

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
        ((DirectMessage.sender_id == recipient_id) &
         (DirectMessage.recipient_id == current_user.id))
    ).order_by(DirectMessage.timestamp).all()

    return render_template('direct_message.html', recipient=recipient, messages=messages)


@app.route('/create_group', methods=['GET', 'POST'])
@login_required
def create_group():
    form = GroupChatForm()
    if form.validate_on_submit():
        new_group = GroupChat(
            name=form.name.data,
            description=form.description.data,
        )
        db.session.add(new_group)
        db.session.flush()

        # Add creator as admin
        creator_membership = GroupChatMembership(
            user_id=current_user.id,
            group_id=new_group.id,
            role='admin'
        )
        db.session.add(creator_membership)

        # Add other members
        member_ids = request.form.get('member_ids', '').split(',')
        added_members = set()  # Keep track of already added members
        
        for member_id in member_ids:
            member_id = member_id.strip()
            if member_id:
                # Skip if it's the creator's ID
                if member_id == current_user.user_id:
                    flash('You cannot add yourself as a member.', 'error')
                    continue
                
                # Skip if this ID was already processed
                if member_id in added_members:
                    flash(f'Duplicate ID {member_id} was skipped.', 'warning')
                    continue
                
                user = User.query.filter_by(user_id=member_id).first()
                if user:
                    membership = GroupChatMembership(
                        user_id=user.id,
                        group_id=new_group.id,
                        role='member'
                    )
                    db.session.add(membership)
                    added_members.add(member_id)
                else:
                    flash(f'User ID {member_id} not found.', 'error')
                    db.session.rollback()
                    return redirect(url_for('create_group'))

        try:
            db.session.commit()
            flash('Group created successfully!', 'success')
            return redirect(url_for('group_chat', group_id=new_group.id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating the group.', 'error')
            return redirect(url_for('create_group'))

    return render_template('groups.html', form=form)


@socketio.on('send_direct_messaage')
def handle_direct_message(data):
    try:
        recipient = User.query.filter_by(username=data['Recipient']).first()

        if not recipient:
            return {'status': 'error', 'message': 'Recipient not found'}

        new_message = DirectMessage(
            sender_id=current_user.id,
            recipient_id=recipient.id,
            message=data['message']
        )
        db.session.add(new_message)
        db.session.commit()
        emit('receive_direct_message', {
            'sender': current_user.username,
            'recipient': recipient.username,
            'message': data['message'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }, room=recipient.id)

        return {'status': 'success', 'message': 'Message sent successfully'}
    except Exception as e:
        db.session.rollback()
        print(f"{e}")
        return {'status': 'error', 'message': 'Error sending message'}


@socketio.on('connect', namespace='/chat')
def handle_connect():
    print(f'{request.sid} connected to the chat namespace')


@socketio.on('disconnect', namespace='/chat')
def handle_disconnect():
    print(f'{request.sid} disconnected from the chat namespace')


@app.route('/check_username', methods=['POST'])
def check_username():
    username = request.json.get('username')
    user = User.query.filter_by(username=username).first()
    return jsonify({'exists': user is not None})


@app.route('/loading')
def loading():
    message = request.args.get('message', 'Loading...')
    redirect_url = request.args.get('redirect_url', url_for('login'))
    return render_template('loading.html', message=message, redirect_url=redirect_url)


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


@app.route('/group/<int:group_id>')
@login_required
def group_chat(group_id):
    group = GroupChat.query.get_or_404(group_id)
    membership = GroupChatMembership.query.filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first()

    if not membership:
        return redirect(url_for('chat'))

    messages = GroupMessage.query.filter_by(group_id=group_id).order_by(GroupMessage.timestamp.asc()).all()
    return render_template('group_chat.html', group=group, messages=messages)


@socketio.on('send_group_message')
def handle_group_message(data):
    group_id = data['group_id']
    message = data['message']
    
    # Check if user is member of the group
    membership = GroupChatMembership.query.filter_by(
        user_id=current_user.id,
        group_id=group_id
    ).first()
    
    if membership:
        new_message = GroupMessage(
            group_id=group_id,
            sender_id=current_user.id,
            message=message,
            timestamp=datetime.utcnow()
        )
        
        try:
            db.session.add(new_message)
            db.session.commit()
            
            # Emit to all group members
            emit('receive_group_message', {
                'group_id': group_id,
                'username': current_user.username,
                'message': message,
                'timestamp': datetime.utcnow().strftime('%H:%M')
            }, broadcast=True)
            
        except Exception as e:
            db.session.rollback()
            print(f"Error saving group message: {e}")


if __name__ == '__main__':
    socketio.run(app, debug=True, ssl_context="adhoc")
