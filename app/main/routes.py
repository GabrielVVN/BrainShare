import os
from werkzeug.utils import secure_filename
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.main import bp
from app.models import Post, User, Comment, Notification, Achievement
from app.decorators import admin_required, professor_required

# --- HELPERS ---
@bp.context_processor
def inject_notifications():
    if current_user.is_authenticated:
        return dict(unread_count=current_user.new_notifications())
    return dict(unread_count=0)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# FUNÇÃO MÁGICA: Desbloqueia Conquista
def check_and_unlock(user, achievement_key):
    ach = Achievement.query.filter_by(key=achievement_key).first()
    if ach and ach not in user.achievements:
        user.achievements.append(ach)
        user.add_xp(ach.xp_reward)
        db.session.commit()
        # Flash especial de conquista
        flash(f'🏆 CONQUISTA DESBLOQUEADA: {ach.name} (+{ach.xp_reward} XP)!')
        return True
    return False

# --- ROTAS ---

@bp.route('/')
def index():
    subject_filter = request.args.get('subject')
    query = Post.query
    if subject_filter: query = query.filter_by(subject=subject_filter)
    posts = query.order_by(Post.timestamp.desc()).all()
    
    # Checa conquista de nível no Feed (Ex: Nível 5)
    if current_user.is_authenticated and current_user.level >= 5:
        check_and_unlock(current_user, 'scholar')
        
    return render_template('main/index.html', posts=posts, current_filter=subject_filter)

# --- GALERIA DE CONQUISTAS ---
@bp.route('/achievements')
@login_required
def achievements():
    # Pega todas as conquistas do sistema
    all_achievements = Achievement.query.all()
    # Pega as IDs das que o usuário já tem
    unlocked_ids = [a.id for a in current_user.achievements]
    
    return render_template('main/achievements.html', achievements=all_achievements, unlocked_ids=unlocked_ids)

@bp.route('/post/new', methods=['POST'])
@login_required
def create_post():
    title = request.form.get('title')
    body = request.form.get('body')
    post_type = request.form.get('type')
    subject = request.form.get('subject')
    file = request.files.get('file')
    filename = None

    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

    if not title or not body:
        return redirect(url_for('main.index'))

    post = Post(title=title, body=body, type=post_type, subject=subject, filename=filename, author=current_user)
    
    if post_type == 'material':
        current_user.add_xp(50)
        flash('Material publicado! +50 XP 🚀')
    else:
        current_user.add_xp(10)
        flash('Dúvida publicada! +10 XP')

    db.session.add(post)
    db.session.commit()
    
    # CHECK CONQUISTA: PRIMEIRO POST
    if current_user.posts.count() == 1:
        check_and_unlock(current_user, 'first_post')

    return redirect(url_for('main.index'))

@bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def comment_post(post_id):
    post = Post.query.get_or_404(post_id)
    text = request.form.get('text')
    
    if not text: return redirect(url_for('main.index'))
        
    comment = Comment(body=text, author=current_user, post=post)
    current_user.add_xp(20)
    
    if post.author != current_user:
        notif = Notification(recipient=post.author, sender=current_user, post=post, action='comment')
        db.session.add(notif)
    
    db.session.add(comment)
    db.session.commit()
    
    flash('Comentário enviado! +20 XP')
    
    # CHECK CONQUISTA: MÃO AMIGA (5 Comentários)
    if current_user.comments.count() >= 5:
        check_and_unlock(current_user, 'helper')
        
    return redirect(request.referrer or url_for('main.index'))

@bp.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post in current_user.liked_posts:
        current_user.liked_posts.remove(post)
        action = 'unlike'
        if post.author != current_user: post.author.add_xp(-10)
    else:
        current_user.liked_posts.append(post)
        action = 'like'
        if post.author != current_user:
            post.author.add_xp(10)
            exists = Notification.query.filter_by(recipient=post.author, sender=current_user, post=post, action='like', is_read=False).first()
            if not exists:
                notif = Notification(recipient=post.author, sender=current_user, post=post, action='like')
                db.session.add(notif)
                
                # CHECK CONQUISTA: INFLUENCIADOR (Para o dono do post)
                if post.likes_count >= 10:
                    check_and_unlock(post.author, 'influencer')

    db.session.commit()
    return jsonify({'action': action, 'likes_count': post.likes_count, 'author_xp': post.author.xp})

# ... (MANTENHA AS OUTRAS ROTAS: post_detail, delete_post, admin, profile, etc.) ...
# Vou manter as rotas existentes resumidas aqui para não cortar o código, 
# mas certifique-se de que elas continuem no arquivo.

@bp.route('/post/<int:post_id>')
@login_required
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('main/post_detail.html', post=post)

@bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user and not current_user.is_admin:
        flash('Sem permissão.')
        return redirect(url_for('main.index'))
    db.session.delete(post)
    db.session.commit()
    flash('Post removido.')
    return redirect(url_for('main.index'))

@bp.route('/comment/<int:comment_id>/solve', methods=['POST'])
@login_required
@professor_required
def mark_solution(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post = comment.post
    if any(c.is_best_answer for c in post.comments):
        flash('Já existe uma solução.')
        return redirect(url_for('main.post_detail', post_id=post.id))
    comment.is_best_answer = True
    comment.author.add_xp(100)
    db.session.commit()
    flash('Solução marcada!')
    return redirect(url_for('main.post_detail', post_id=post.id))

@bp.route('/leaderboard')
@login_required
def leaderboard():
    users = User.query.filter((User.role != 'admin') | (User.role == None)).order_by(User.xp.desc()).limit(50).all()
    return render_template('main/leaderboard.html', users=users)

@bp.route('/user/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('main/profile.html', user=user, posts=posts)

@bp.route('/user/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.username = request.form.get('username')
        current_user.about_me = request.form.get('about_me')
        current_user.job_title = request.form.get('job_title')
        current_user.linkedin = request.form.get('linkedin')
        file = request.files.get('avatar')
        if file and file.filename != '':
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext in ['png', 'jpg', 'jpeg', 'gif']:
                filename = f"user_{current_user.id}.{ext}"
                file.save(os.path.join(current_app.config['AVATAR_FOLDER'], filename))
                current_user.avatar_file = filename
        try:
            db.session.commit()
            flash('Perfil atualizado!')
            return redirect(url_for('main.profile', username=current_user.username))
        except:
            db.session.rollback()
    return render_template('main/edit_profile.html')

@bp.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = User.query.all()
    posts_count = Post.query.count()
    return render_template('main/admin_panel.html', users=users, posts_count=posts_count)

@bp.route('/admin/user/<int:user_id>/role', methods=['POST'])
@login_required
@admin_required
def change_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in ['student', 'professor', 'admin']:
        user.role = new_role
        db.session.commit()
        flash(f'Cargo de {user.username} alterado para {new_role}.')
    return redirect(url_for('main.admin_panel'))

@bp.route('/search')
@login_required
def search():
    query = request.args.get('q', '').strip()
    if not query: return redirect(url_for('main.index'))
    users = User.query.filter(User.username.ilike(f'%{query}%')).all()
    posts = Post.query.filter((Post.title.ilike(f'%{query}%')) | (Post.body.ilike(f'%{query}%'))).all()
    return render_template('main/search_results.html', query=query, users=users, posts=posts)

@bp.route('/search/live')
@login_required
def search_live():
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2: return jsonify({'users': [], 'posts': []})
    users = User.query.filter(User.username.ilike(f'%{query}%')).limit(3).all()
    users_data = [{'username': u.username, 'level': u.level} for u in users]
    posts = Post.query.filter((Post.title.ilike(f'%{query}%')) | (Post.body.ilike(f'%{query}%'))).limit(5).all()
    posts_data = [{'id': p.id, 'title': p.title, 'type': p.type} for p in posts]
    return jsonify({'users': users_data, 'posts': posts_data})

@bp.route('/notifications')
@login_required
def notifications():
    notifs = current_user.notifications.order_by(Notification.timestamp.desc()).all()
    for n in notifs: n.is_read = True
    db.session.commit()
    return render_template('main/notifications.html', notifications=notifs)