from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth import bp
from app.models import User, Achievement

# FUNÇÃO PARA CONQUISTAS
def check_and_unlock(user, achievement_key):
    ach = Achievement.query.filter_by(key=achievement_key).first()
    if ach and ach not in user.achievements:
        user.achievements.append(ach)
        user.add_xp(ach.xp_reward)
        db.session.commit()
        return True
    return False

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user is None or not user.check_password(password):
            flash('Email ou senha inválidos.')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        return redirect(url_for('main.index'))
        
    return render_template('auth/login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role') # Captura a escolha do usuário

        # Validação simples para evitar que alguém tente virar admin via HTML
        if role not in ['student', 'professor']:
            role = 'student'

        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe.')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.')
            return redirect(url_for('auth.register'))

        # Cria usuário com a role escolhida
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # CONCEDE CONQUISTA DE BEM-VINDO
        check_and_unlock(user, 'welcome')
        
        flash('Cadastro realizado! Bem-vindo ao BrainShare.')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))