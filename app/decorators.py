from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Se não for admin, erro 403 (Proibido)
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def professor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Admin também pode acessar coisas de professor
        if not current_user.is_authenticated or (current_user.role != 'professor' and current_user.role != 'admin'):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function