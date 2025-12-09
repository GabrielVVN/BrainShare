from datetime import datetime
from flask import url_for
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from math import floor, sqrt

# Tabelas de Associação
post_likes = db.Table('post_likes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'))
)

user_achievements = db.Table('user_achievements',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('achievement_id', db.Integer, db.ForeignKey('achievement.id')),
    db.Column('unlocked_at', db.DateTime, default=datetime.utcnow)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    xp = db.Column(db.Integer, default=0)
    role = db.Column(db.String(20), default='student')
    
    # Perfil
    about_me = db.Column(db.String(500))
    avatar_file = db.Column(db.String(120))
    job_title = db.Column(db.String(100))
    linkedin = db.Column(db.String(200))

    # Limites
    daily_likes = db.Column(db.Integer, default=0)
    daily_comments = db.Column(db.Integer, default=0)
    last_activity_reset = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    liked_posts = db.relationship('Post', secondary=post_likes, backref=db.backref('liked_by', lazy='dynamic'))
    notifications = db.relationship('Notification', foreign_keys='Notification.recipient_id', backref='recipient', lazy='dynamic')
    
    # NOVO: Conquistas
    achievements = db.relationship('Achievement', secondary=user_achievements, backref=db.backref('users', lazy='dynamic'))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def level(self):
        if self.xp is None or self.xp < 10: return 1
        calculated_level = int(floor(sqrt(self.xp / 10)))
        return 100 if calculated_level > 100 else calculated_level

    @property
    def avatar(self):
        if self.avatar_file:
            return url_for('static', filename='uploads/avatars/' + self.avatar_file)
        return f"https://ui-avatars.com/api/?name={self.username}&background=171717&color=fff&bold=true&size=128"

    def new_notifications(self):
        return Notification.query.filter_by(recipient_id=self.id, is_read=False).count()

    def add_xp(self, amount):
        if self.xp is None: self.xp = 0
        self.xp += amount
        db.session.add(self)
        db.session.commit()
    
    @property
    def is_admin(self): return self.role == 'admin'
    
    @property
    def is_professor(self): return self.role == 'professor'

    def __repr__(self): return f'<User {self.username}>'

@login.user_loader
def load_user(id): return User.query.get(int(id))

# --- NOVA CLASSE: CONQUISTA ---
class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True) # Identificador no código (ex: 'first_post')
    name = db.Column(db.String(100))
    description = db.Column(db.String(255))
    xp_reward = db.Column(db.Integer)
    icon = db.Column(db.String(50)) # Classe do Bootstrap Icon (ex: 'bi-star')

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    action = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    sender = db.relationship('User', foreign_keys=[sender_id])
    post = db.relationship('Post', foreign_keys=[post_id])

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140))
    body = db.Column(db.Text)
    type = db.Column(db.String(20))
    subject = db.Column(db.String(50), default='Geral')
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    filename = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='normal') # normal | denunciada | removida
    comments = db.relationship('Comment', backref='post', lazy='dynamic', cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='related_post', lazy='dynamic', cascade="all, delete-orphan")

    @property
    def likes_count(self): return self.liked_by.count()

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    is_best_answer = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))