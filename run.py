from app import create_app, db
from app.models import User, Post, Comment, Achievement, Mascote, MascoteUsuario
from sqlalchemy.exc import OperationalError

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Comment': Comment, 'Achievement': Achievement, 'Mascote': Mascote, 'MascoteUsuario': MascoteUsuario}

# --- CRIA ADMIN E CONQUISTAS ---
def init_db_data():
    with app.app_context():
        # 1. Admin
        try:
            admin = User.query.filter_by(email='admin@brainshare.com').first()
        except OperationalError:
            # DB schema is not yet updated to match models (missing columns) - instruct the user
            print("Database schema appears to be out-of-date or missing. Run: flask db upgrade")
            return
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

def init_mascotes():
    """Inicializa as mascotes do sistema"""
    with app.app_context():
        from app.models import Mascote

        # Limpar mascotes existentes para garantir apenas as desejadas
        Mascote.query.delete()
        db.session.commit()

        mascotes_data = [
            # SERPENTE DA SABEDORIA
            {'nome': 'Serpente Bebê', 'tipo': 'sabedoria', 'evolucao': 1, 'xp_necessario': 0, 'imagem': 'serpente1.png', 'descricao': 'Uma pequena serpente curiosa, sempre buscando conhecimento!'},
            {'nome': 'Serpente Jovem', 'tipo': 'sabedoria', 'evolucao': 2, 'xp_necessario': 30, 'imagem': 'serpente2.png', 'descricao': 'Suas escamas brilham com sabedoria acumulada.'},
            {'nome': 'Serpente Anciã', 'tipo': 'sabedoria', 'evolucao': 3, 'xp_necessario': 60, 'imagem': 'serpente3.png', 'descricao': 'Uma guardiã da sabedoria ancestral, mestre do conhecimento!'},

            # FÊNIX DA ESPERANÇA
            {'nome': 'Fênix Bebê', 'tipo': 'esperanca', 'evolucao': 1, 'xp_necessario': 0, 'imagem': 'fenix1.png', 'descricao': 'Uma pequena ave flamejante cheia de esperança e energia!'},
            {'nome': 'Fênix Jovem', 'tipo': 'esperanca', 'evolucao': 2, 'xp_necessario': 30, 'imagem': 'fenix2.png', 'descricao': 'Suas asas começam a brilhar com fogo renovador.'},
            {'nome': 'Fênix Ancião', 'tipo': 'esperanca', 'evolucao': 3, 'xp_necessario': 60, 'imagem': 'fenix3.png', 'descricao': 'Um majestoso pássaro de fogo, símbolo eterno da esperança!'},

            # ZEBRA DO EQUILÍBRIO
            {'nome': 'Zebra Bebê', 'tipo': 'equilibrio', 'evolucao': 1, 'xp_necessario': 0, 'imagem': 'zebra1.png', 'descricao': 'Uma zebrinha brincalhona que busca harmonia em tudo!'},
            {'nome': 'Zebra Jovem', 'tipo': 'equilibrio', 'evolucao': 2, 'xp_necessario': 30, 'imagem': 'zebra2.png', 'descricao': 'Suas listras representam o perfeito equilíbrio.'},
            {'nome': 'Zebra Anciã', 'tipo': 'equilibrio', 'evolucao': 3, 'xp_necessario': 60, 'imagem': 'zebra3.png', 'descricao': 'Uma guardiã do equilíbrio cósmico, mantenedora da harmonia!'}
        ]

        for data in mascotes_data:
            mascote = Mascote(
                nome=data['nome'],
                tipo=data['tipo'],
                evolucao=data['evolucao'],
                xp_necessario=data['xp_necessario'],
                imagem=data['imagem'],
                descricao=data['descricao']
            )
            db.session.add(mascote)
            print(f">> Mascote criada: {data['nome']}")

        db.session.commit()

def grant_retroactive_achievements():
    """Concede conquistas retroativamente para usuários existentes"""
    with app.app_context():
        users = User.query.all()
        for user in users:
            # Conquista welcome para todos os usuários existentes
            check_and_unlock(user, 'welcome')

            # Conquista first_post se tiver posts
            if user.posts.count() >= 1:
                check_and_unlock(user, 'first_post')

            # Conquista helper se tiver 5+ comentários
            if user.comments.count() >= 5:
                check_and_unlock(user, 'helper')

            # Conquista influencer se algum post tiver 10+ likes
            has_influencer_post = any(post.likes_count >= 10 for post in user.posts)
            if has_influencer_post:
                check_and_unlock(user, 'influencer')

            # Conquista scholar se nível >= 5
            if user.level >= 5:
                check_and_unlock(user, 'scholar')

        db.session.commit()
        print(">> Conquistas retroativas concedidas!")

def check_and_unlock(user, achievement_key):
    ach = Achievement.query.filter_by(key=achievement_key).first()
    if ach and ach not in user.achievements:
        user.achievements.append(ach)
        user.add_xp(ach.xp_reward)
        print(f"🏆 {user.username} desbloqueou: {ach.name} (+{ach.xp_reward} XP)")
        return True
    return False

if __name__ == '__main__':
    init_db_data()
    init_mascotes()
    grant_retroactive_achievements()
    app.run(debug=False)