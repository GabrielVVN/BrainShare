from app import create_app, db
from app.models import User, Post, Comment, Achievement

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Comment': Comment, 'Achievement': Achievement}

# --- CRIA ADMIN E CONQUISTAS ---
def init_db_data():
    with app.app_context():
        # 1. Admin
        admin = User.query.filter_by(email='admin@brainshare.com').first()
        if not admin:
            u = User(username='Admin', email='admin@brainshare.com', role='admin')
            u.set_password('admin123')
            u.xp = 5000 
            u.job_title = "Administrador"
            db.session.add(u)
            db.session.commit()
            print(">> Admin criado.")

        # 2. Conquistas (Achievements)
        achievements_data = [
            {'key': 'welcome', 'name': 'Bem-vindo a Bordo', 'desc': 'Crie sua conta no BrainShare.', 'xp': 50, 'icon': 'bi-door-open-fill'},
            {'key': 'first_post', 'name': 'Primeira Voz', 'desc': 'Faça sua primeira publicação.', 'xp': 100, 'icon': 'bi-megaphone-fill'},
            {'key': 'influencer', 'name': 'Influenciador', 'desc': 'Receba 10 curtidas em um post.', 'xp': 300, 'icon': 'bi-stars'},
            {'key': 'helper', 'name': 'Mão Amiga', 'desc': 'Faça 5 comentários ajudando outros.', 'xp': 150, 'icon': 'bi-chat-heart-fill'},
            {'key': 'scholar', 'name': 'Erudito', 'desc': 'Chegue ao Nível 5.', 'xp': 500, 'icon': 'bi-mortarboard-fill'}
        ]

        for data in achievements_data:
            exists = Achievement.query.filter_by(key=data['key']).first()
            if not exists:
                ach = Achievement(key=data['key'], name=data['name'], description=data['desc'], xp_reward=data['xp'], icon=data['icon'])
                db.session.add(ach)
                print(f">> Conquista criada: {data['name']}")
        
        db.session.commit()

if __name__ == '__main__':
    init_db_data()
    app.run(debug=True)