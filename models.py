from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import random
import uuid

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(10), unique=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    messages = db.relationship('GlobalMessages', backref='global_user', lazy=True)  # Changed backref name
    sent_direct_messages = db.relationship('DirectMessage', foreign_keys='DirectMessage.sender_id', backref='sender', lazy=True)
    received_direct_messages = db.relationship('DirectMessage', foreign_keys='DirectMessage.recipient_id', backref='recipient', lazy=True)
    group_memberships = db.relationship('GroupChatMembership', backref='user', lazy=True)

    @classmethod
    def generate_unique_user_id(cls):
        """
        Generate a 10-digit user ID
        """
        while True:
            new_user_id = ''.join([str(random.randint(0, 9)) for _ in range(10)])
            existing_user = cls.query.filter_by(user_id=new_user_id).first()
            if not existing_user:
                return new_user_id

    @classmethod
    def create_user(cls, username, password):
        """
        Class method to create a new user with a unique user_id
        """
        unique_user_id = cls.generate_unique_user_id()
        
        new_user = cls(
            user_id=unique_user_id,
            username=username,
            password=password
        )
        
        return new_user
    
class GroupChat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    messages = db.relationship('GroupMessage', backref='group', lazy=True)
    members = db.relationship('GroupChatMembership', backref='group', lazy=True)

class GroupChatMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group_chat.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(50), default='member')  # admin, member, etc.

class DirectMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

class GroupMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group_chat.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('User', backref='group_messages')

class GlobalMessages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_deleted = db.Column(db.Integer, default=0)  
