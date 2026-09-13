from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'win_wid_gizli_kalit'

# Bazanın yaradılması və cədvəllərin qurulması
def init_db():
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            nickname TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            profile_pic TEXT
        )
    ''')
    # Əgər əvvəlki bazada profile_pic sütunu yoxdursa əlavə etmək üçün
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT")
    except sqlite3.OperationalError:
        pass
        
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Giriş və Qeydiyyat Səhifəsi
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Giriş</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            background-color: #1e3a8a; 
            color: #ffffff; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
        }
        .container { 
            width: 320px; 
            padding: 30px; 
            background: #172554; 
            border-radius: 12px; 
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3); 
            text-align: center; 
            border: 1px solid #3b82f6; 
        }
        h1 { 
            font-size: 20px; 
            margin-bottom: 20px; 
            color: #ffffff; 
        }
        input { 
            width: 100%; 
            padding: 12px; 
            margin: 10px 0; 
            border: 1px solid #3b82f6; 
            border-radius: 6px; 
            background: #1e3a8a; 
            color: #ffffff; 
            box-sizing: border-box; 
        }
        input::placeholder { color: #93c5fd; }
        button { 
            width: 100%; 
            padding: 12px; 
            margin: 8px 0; 
            background: #2563eb; 
            color: white; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            font-weight: bold; 
        }
        button:hover { background: #1d4ed8; }
        .error { color: #f87171; font-size: 14px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>WİN_WİD'Ə XOŞ GƏLMİSİZ</h1>
        {% if error %}
            <p class="error">{{ error }}</p>
        {% endif %}
        <form method="POST">
            <input type="text" name="nickname" placeholder="Nik name" required>
            <input type="password" name="password" placeholder="Kod" required>
            <button type="submit" name="action" value="login">Daxil Ol</button>
            <button type="submit" name="action" value="register">Qeydiyyat Keç</button>
        </form>
    </div>
</body>
</html>
'''

# Üfüqi Menyu Paneli
NAV_TEMPLATE = '''
    <div class="header">
        <h2>WİN_WİD, {{ session.get('user', '') }}</h2>
        <a href="/logout" class="logout">Çıxış</a>
    </div>
    <div class="nav-bar">
        <a href="/chat" class="nav-item {% if active == 'chat' %}active{% endif %}">
            <span class="icon">💬</span>
            <span>Çat</span>
        </a>
        <a href="/sekil" class="nav-item {% if active == 'sekil' %}active{% endif %}">
            <span class="icon">📷</span>
            <span>Şəkil</span>
        </a>
        <a href="/vidyo" class="nav-item {% if active == 'vidyo' %}active{% endif %}">
            <span class="icon">📹</span>
            <span>Vidyo</span>
        </a>
        <a href="/oyun" class="nav-item {% if active == 'oyun' %}active{% endif %}">
            <span class="icon">🎮</span>
            <span>Oyun</span>
        </a>
        <a href="/magaza" class="nav-item {% if active == 'magaza' %}active{% endif %}">
            <span class="icon">🛍️</span>
            <span>Mağaza</span>
        </a>
        <a href="/profil" class="nav-item {% if active == 'profil' %}active{% endif %}">
            <span class="icon">👤</span>
            <span>Profil</span>
        </a>
    </div>
'''

# Ümumi CSS Stilleri
COMMON_STYLE = '''
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 15px; 
            background: #1e3a8a; 
            color: #ffffff; 
            display: flex; 
            flex-direction: column; 
            height: 100vh; 
            box-sizing: border-box; 
        }
        .header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            background: #172554; 
            color: white; 
            padding: 10px 15px; 
            border-radius: 8px; 
            border: 1px solid #3b82f6; 
            margin-bottom: 10px;
        }
        .header h2 {
            font-size: 15px;
            margin: 0;
        }
        .nav-bar { 
            background: #172554; 
            border: 2px solid #f97316; 
            border-radius: 12px; 
            padding: 10px; 
            display: flex; 
            justify-content: space-around; 
            align-items: center; 
            margin-bottom: 12px;
            gap: 5px;
            overflow-x: auto;
        }
        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-decoration: none;
            color: #cbd5e1;
            padding: 8px 12px;
            border-radius: 10px;
            font-size: 13px;
            font-weight: bold;
            transition: 0.2s;
            white-space: nowrap;
        }
        .nav-item .icon {
            font-size: 18px;
            margin-bottom: 3px;
        }
        .nav-item:hover {
            color: #ffffff;
            background: rgba(59, 130, 246, 0.2);
        }
        .nav-item.active {
            background: #0284c7;
            color: #ffffff;
            box-shadow: 0 2px 10px rgba(2, 132, 199, 0.4);
        }
        a.logout { 
            color: white; 
            text-decoration: none; 
            background: #dc2626; 
            padding: 5px 10px; 
            border-radius: 6px; 
            font-size: 12px; 
        }
        a.logout:hover { background: #b91c1c; }
    </style>
'''

# Çat Səhifəsi Şablonu
CHAT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Çat</title>
    ''' + COMMON_STYLE + '''
    <style>
        .chat-box { 
            background: #172554; 
            height: 52vh; 
            border: 2px solid #f97316; 
            border-radius: 8px; 
            padding: 12px; 
            overflow-y: auto; 
            color: #ffffff; 
            margin-bottom: 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .chat-box p {
            background: #1e3a8a;
            padding: 8px 12px;
            border-radius: 6px;
            margin: 0;
            border-left: 4px solid #3b82f6;
            word-break: break-all;
            font-size: 14px;
        }
        .message-form { 
            display: flex; 
            gap: 10px; 
            background: #172554;
            padding: 10px;
            border: 2px solid #f97316;
            border-radius: 8px;
            align-items: center;
        }
        input[type="text"] { 
            flex: 1; 
            padding: 10px 12px; 
            border: 1px solid #3b82f6; 
            border-radius: 6px; 
            background: #1e3a8a; 
            color: #ffffff; 
            font-size: 14px;
        }
        input[type="text"]::placeholder { color: #93c5fd; }
        button[type="submit"] { 
            padding: 10px 20px; 
            background: #22c55e; 
            color: white; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            font-weight: bold; 
            font-size: 14px;
        }
        button[type="submit"]:hover { background: #16a34a; }
    </style>
</head>
<body>
    ''' + NAV_TEMPLATE + '''
    <div class="chat-box">
        {% if messages %}
            {% for msg in messages %}
                <p>{{ msg }}</p>
            {% endfor %}
        {% else %}
            <p style="color: #93c5fd; text-align: center; border-left: none; background: transparent;">Hələ ki mesaj yoxdur. İlk mesajı sən yaz!</p>
        {% endif %}
    </div>
    <form method="POST" class="message-form">
        <input type="text" name="message" placeholder="Mesajınızı yazın..." autocomplete="off" required>
        <button type="submit">Göndər</button>
    </form>
</body>
</html>
'''

# Profil Səhifəsi Şablonu (Şəkildəki dizayn və funksiyalar)
PROFIL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Profil</title>
    ''' + COMMON_STYLE + '''
    <style>
        .profile-container {
            background: #172554;
            flex: 1;
            border: 2px solid #f97316;
            border-radius: 12px;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .profile-title {
            font-size: 16px;
            font-weight: bold;
            color: #ffffff;
            border-bottom: 1px solid #3b82f6;
            padding-bottom: 8px;
            margin: 0;
        }
        .profile-header {
            display: flex;
            align-items: center;
            gap: 15px;
            background: #1e3a8a;
            padding: 12px;
            border-radius: 10px;
            border: 1px solid #3b82f6;
        }
        .avatar-wrapper {
            position: relative;
            width: 70px;
            height: 70px;
            border-radius: 50%;
            border: 3px solid #f97316;
            overflow: hidden;
            background: #111;
            box-shadow: 0 0 10px rgba(249, 115, 22, 0.5);
            flex-shrink: 0;
        }
        .avatar-wrapper img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .crown-icon {
            position: absolute;
            bottom: -2px;
            right: 50%;
            transform: translateX(50%);
            font-size: 12px;
        }
        .profile-info h3 {
            margin: 0 0 5px 0;
            font-size: 18px;
            color: #ffffff;
        }
        .profile-info .status {
            color: #22c55e;
            font-size: 13px;
            font-weight: bold;
            margin: 0;
        }
        form {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin: 0;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #3b82f6;
            border-radius: 8px;
            background: #1e3a8a;
            color: #ffffff;
            font-size: 14px;
            box-sizing: border-box;
            text-align: center;
        }
        input[type="text"]::placeholder { color: #93c5fd; }
        .btn-blue {
            background: #0284c7;
            color: white;
            border: none;
            padding: 12px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 14px;
            cursor: pointer;
            text-align: center;
            width: 100%;
        }
        .btn-blue:hover { background: #0369a1; }
        .btn-gray {
            background: #334155;
            color: white;
            border: 1px solid #475569;
            padding: 12px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 14px;
            cursor: pointer;
            text-align: center;
            width: 100%;
        }
        .btn-gray:hover { background: #475569; }
        .btn-red {
            background: #dc2626;
            color: white;
            border: none;
            padding: 12px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 14px;
            cursor: pointer;
            text-align: center;
            width: 100%;
        }
        .btn-red:hover { background: #b91c1c; }
        .msg-alert {
            font-size: 13px;
            text-align: center;
            margin: 0;
        }
    </style>
</head>
<body>
    ''' + NAV_TEMPLATE + '''

    <div class="profile-container">
        <p class="profile-title">Mənim Profilim</p>
        
        {% if message %}
            <p class="msg-alert" style="color: {% if error %}#f87171{% else %}#22c55e{% endif %};">{{ message }}</p>
        {% endif %}

        <div class="profile-header">
            <div class="avatar-wrapper">
                <img src="{{ pic if pic else 'https://i.imgur.com/6VBx3io.png' }}" alt="Profil Şəkli">
                <div class="crown-icon">👑</div>
            </div>
            <div class="profile-info">
                <h3>@{{ user }} 👑</h3>
                <p class="status">● Aktivdir</p>
            </div>
        </div>

        <!-- 1. Nik Adını Dəyiş -->
        <form method="POST">
            <input type="hidden" name="action" value="change_name">
            <input type="text" name="new_nickname" placeholder="Yeni nik adı (max 7 hərf)" maxlength="7" required>
            <button type="submit" class="btn-blue">Adı Dəyiş</button>
        </form>

        <!-- 2. Şəkil URL-i Daxil Etmək Üçün Form -->
        <form method="POST">
            <input type="hidden" name="action" value="change_pic">
            <input type="text" name="pic_url" placeholder="Profil şəklinin linkini (URL) bura yapışdır" required>
            <button type="submit" class="btn-gray">Profil Şəklini Dəyiş</button>
            <button type="submit" class="btn-blue">Şəkli Yadda Saxla</button>
        </form>

        <!-- 3. Hesabı Sil -->
        <form method="POST" onsubmit="return confirm('Hesabınızı silmək istədiyinizə əminsinizmi?');">
            <input type="hidden" name="action" value="delete_account">
            <button type="submit" class="btn-red">Hesabımı Sil</button>
        </form>

        <!-- 4. Çıxış Et -->
        <a href="/logout" class="btn-gray" style="text-decoration: none; box-sizing: border-box; display: block;">Çıxış Et</a>
    </div>
</body>
</html>
'''

# Digər Səhifələr Üçün Şablon
SUB_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - {{ title }}</title>
    ''' + COMMON_STYLE + '''
    <style>
        .content-box { 
            background: #172554; 
            flex: 1; 
            border: 2px solid #f97316; 
            border-radius: 8px; 
            padding: 20px; 
            text-align: center;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 18px;
            color: #93c5fd;
        }
    </style>
</head>
<body>
    ''' + NAV_TEMPLATE + '''
    <div class="content-box">
        <p>{{ title }} bölməsi tezliklə aktiv olacaq!</p>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        action = request.form.get('action')
        nickname = request.form.get('nickname').strip()
        password = request.form.get('password').strip()
        
        if not nickname or not password:
            error = "Xanalar boş ola bilməz!"
        else:
            conn = sqlite3.connect('win_wid.db')
            cursor = conn.cursor()
            
            if action == 'register':
                cursor.execute("SELECT * FROM users WHERE nickname = ?", (nickname,))
                if cursor.fetchone():
                    error = "Bu nikname artıq istifadədədir!"
                else:
                    cursor.execute("INSERT INTO users (nickname, password, profile_pic) VALUES (?, ?, ?)", (nickname, password, ''))
                    conn.commit()
                    session['user'] = nickname
                    conn.close()
                    return redirect(url_for('chat'))
                    
            elif action == 'login':
                cursor.execute("SELECT password FROM users WHERE nickname = ?", (nickname,))
                row = cursor.fetchone()
                if row and row[0] == password:
                    session['user'] = nickname
                    conn.close()
                    return redirect(url_for('chat'))
                else:
                    error = "Yanlış nikname və ya kod!"
            conn.close()
                
    return render_template_string(INDEX_TEMPLATE, error=error)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        msg = request.form.get('message').strip()
        if msg:
            full_msg = f"{session['user']}: {msg}"
            cursor.execute("INSERT INTO messages (content) VALUES (?)", (full_msg,))
            conn.commit()
        conn.close()
        return redirect(url_for('chat'))
        
    cursor.execute("SELECT content FROM messages")
    messages = [row[0] for row in cursor.fetchall()]
    conn.close()
        
    return render_template_string(CHAT_TEMPLATE, messages=messages, active='chat')

@app.route('/profil', methods=['GET', 'POST'])
def profil():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    
    message = None
    error = False
    
    if request.method == 'POST':
        action = request.form.get('action')
        current_user = session['user']
        
        if action == 'change_name':
            new_name = request.form.get('new_nickname').strip()
            if len(new_name) > 7:
                message = "Nik adı maksimum 7 hərf ola bilər!"
                error = True
            elif not new_name:
                message = "Nik adı boş ola bilməz!"
                error = True
            else:
                cursor.execute("SELECT * FROM users WHERE nickname = ?", (new_name,))
                if cursor.fetchone():
                    message = "Bu nik adı artıq istifadədədir!"
                    error = True
                else:
                    cursor.execute("UPDATE users SET nickname = ? WHERE nickname = ?", (new_name, current_user))
                    conn.commit()
                    session['user'] = new_name
                    message = "Nik adı uğurla dəyişdirildi!"
                    
        elif action == 'change_pic':
            pic_url = request.form.get('pic_url').strip()
            if pic_url:
                cursor.execute("UPDATE users SET profile_pic = ? WHERE nickname = ?", (pic_url, current_user))
                conn.commit()
                message = "Profil şəkli uğurla yadda saxlandı!"
            else:
                message = "Şəkil linki boş ola bilməz!"
                error = True
                
        elif action == 'delete_account':
            cursor.execute("DELETE FROM users WHERE nickname = ?", (current_user,))
            conn.commit()
            conn.close()
            session.pop('user', None)
            return redirect(url_for('index'))
            
    # İstifadəçinin cari şəkil məlumatını çəkək
    cursor.execute("SELECT profile_pic FROM users WHERE nickname = ?", (session['user'],))
    row = cursor.fetchone()
    pic = row[0] if row and row[0] else ''
    
    conn.close()
    return render_template_string(PROFIL_TEMPLATE, user=session['user'], pic=pic, message=message, error=error, active='profil')

@app.route('/sekil')
def sekil():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template_string(SUB_TEMPLATE, title="Şəkil", active='sekil')

@app.route('/vidyo')
def vidyo():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template_string(SUB_TEMPLATE, title="Vidyo", active='vidyo')

@app.route('/oyun')
def oyun():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template_string(SUB_TEMPLATE, title="Oyun", active='oyun')

@app.route('/magaza')
def magaza():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template_string(SUB_TEMPLATE, title="Mağaza", active='magaza')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
