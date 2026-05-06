import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.utils import secure_filename, safe_join

app = Flask(__name__)
app.secret_key = 'pato_secreto_777'

UPLOAD_FOLDER = "/home/patodestroyer/cloud/archivos_nube"

if not os.path.exists(UPLOAD_FOLDER):
    print(f"⚠️ Creando carpeta: {UPLOAD_FOLDER}")
    os.makedirs(UPLOAD_FOLDER)

# ----------------------------
# CLASIFICACIÓN
# ----------------------------
def clasificar_y_medir(nombre):
    _, extension = os.path.splitext(nombre)
    ext = extension.lower().replace('.', '')

    ruta = os.path.join(UPLOAD_FOLDER, nombre)

    try:
        size_bytes = os.path.getsize(ruta)
        if size_bytes < 1024:
            size = f"{size_bytes} B"
        elif size_bytes < 1024**2:
            size = f"{round(size_bytes / 1024, 1)} KB"
        else:
            size = f"{round(size_bytes / (1024**2), 1)} MB"
    except:
        size = "0 B"

    categorias = {
        'imagenes': {
            'exts': ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'bmp'],
            'icon': '🖼️',
            'type': 'Imagen'
        },
        'documentos': {
            'exts': ['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'ppt', 'pptx'],
            'icon': '📄',
            'type': 'Documento'
        },
        'video': {
            'exts': ['mp4', 'mkv', 'mov', 'avi'],
            'icon': '🎬',
            'type': 'Video'
        },
        'musica': {
            'exts': ['mp3', 'wav', 'ogg'],
            'icon': '🎵',
            'type': 'Audio'
        }
    }

    for cat, info in categorias.items():
        if ext in info['exts']:
            return {
                'cat': cat,
                'icon': info['icon'],
                'type': info['type'],
                'size': size
            }

    return {
        'cat': 'otros',
        'icon': '📦',
        'type': 'Archivo',
        'size': size
    }

# ----------------------------
# LOGIN
# ----------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# ----------------------------
# LOGIN ROUTES
# ----------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if username == 'pato' and password == 'pato3':
            login_user(User('pato'))
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# ----------------------------
# MAIN (CORRECTO)
# ----------------------------
@app.route('/')
@login_required
def index():
    archivos = os.listdir(UPLOAD_FOLDER)

    db = {
        'recientes': [],
        'documentos': [],
        'imagenes': [],
        'video': [],
        'musica': [],
        'otros': [],
        'destacados': [],
        'papelera': []
    }

    for f in archivos:
        ruta = os.path.join(UPLOAD_FOLDER, f)

        if f.startswith('.') or not os.path.isfile(ruta):
            continue

        meta = clasificar_y_medir(f)

        item = {
            'name': f,
            'type': meta['type'],
            'size': meta['size'],
            'icon': meta['icon'],
            'is_image': meta['cat'] == 'imagenes',
            'preview_url': url_for('descargar', nombre=f)
        }

        db[meta['cat']].append(item)
        db['recientes'].append(item)

    return render_template('index.html', user=current_user.id, data=db)

# ----------------------------
# SUBIR
# ----------------------------
@app.route('/subir', methods=['POST'])
@login_required
def subir():
    file = request.files.get('file')

    if file and file.filename != '':
        filename = secure_filename(file.filename)
        ruta = os.path.join(UPLOAD_FOLDER, filename)
        file.save(ruta)
        return jsonify({"success": True})

    return jsonify({"success": False}), 400

# ----------------------------
# DESCARGAR
# ----------------------------
@app.route('/descargar/<path:nombre>')
@login_required
def descargar(nombre):
    ruta = safe_join(UPLOAD_FOLDER, nombre)

    if not ruta or not os.path.exists(ruta):
        return "Archivo no encontrado", 404

    return send_from_directory(UPLOAD_FOLDER, nombre, as_attachment=True)

# ----------------------------
# ELIMINAR
# ----------------------------
@app.route('/eliminar/<path:nombre>', methods=['POST'])
@login_required
def eliminar(nombre):
    ruta = os.path.join(UPLOAD_FOLDER, nombre)

    try:
        if os.path.exists(ruta):
            os.remove(ruta)
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "No existe"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# ----------------------------
# RUN
# ----------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082, debug=True)  
