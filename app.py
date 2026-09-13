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
            profile_pic TEXT,
            points INTEGER DEFAULT 500
        )
    ''')
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 500")
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

# Üst hissə şablonu (Bal dinamik gəlir)
def get_header_template(points=500):
    return f'''
    <div class="top-header-bar">
        <div class="bal-box">BALI<br>{points}</div>
        <div class="user-box">İSTİFADƏÇİ</div>
        <div class="bell-icon">🔔</div>
        <a href="/logout" class="logout-btn">Çıxış</a>
    </div>
    <div class="nav-bar">
        <a href="/chat" class="nav-item">
            <span class="icon">💬</span>
            <span>Çat</span>
        </a>
        <a href="/sekil" class="nav-item">
            <span class="icon">📷</span>
            <span>Şəkillər</span>
        </a>
        <a href="/vidyo" class="nav-item">
            <span class="icon">📹</span>
            <span>Videolar</span>
        </a>
        <a href="/oyun" class="nav-item">
            <span class="icon">🎮</span>
            <span>Oyunlar</span>
        </a>
        <a href="/magaza" class="nav-item">
            <span class="icon">🛍️</span>
            <span>Mağaza</span>
        </a>
        <a href="/profil" class="nav-item">
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
            padding: 12px; 
            background: #1e3a8a; 
            color: #ffffff; 
            display: flex; 
            flex-direction: column; 
            height: 100vh; 
            box-sizing: border-box; 
        }
        .top-header-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #172554;
            padding: 8px 12px;
            border-radius: 12px;
            border: 1px solid #3b82f6;
            margin-bottom: 8px;
            gap: 8px;
        }
        .bal-box {
            background: #f97316;
            color: #000;
            font-weight: bold;
            padding: 6px 10px;
            border-radius: 8px;
            font-size: 11px;
            text-align: center;
            line-height: 1.1;
        }
        .user-box {
            background: #f97316;
            color: #000;
            font-weight: bold;
            padding: 9px 15px;
            border-radius: 8px;
            font-size: 11px;
            text-align: center;
            white-space: nowrap;
            flex: 1;
        }
        .bell-icon {
            background: #f97316;
            color: #000;
            padding: 9px 12px;
            border-radius: 8px;
            font-size: 13px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .logout-btn {
            background: #dc2626;
            color: white;
            text-decoration: none;
            padding: 9px 12px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: bold;
            white-space: nowrap;
        }
        .logout-btn:hover { background: #b91c1c; }

        .nav-bar { 
            background: #172554; 
            border: 2px solid #f97316; 
            border-radius: 12px; 
            padding: 8px; 
            display: flex; 
            justify-content: space-around; 
            align-items: center; 
            margin-bottom: 10px;
            gap: 4px;
            overflow-x: auto;
        }
        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-decoration: none;
            color: #cbd5e1;
            padding: 6px 8px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: bold;
            transition: 0.2s;
            white-space: nowrap;
        }
        .nav-item .icon {
            font-size: 16px;
            margin-bottom: 2px;
        }
        .nav-item:hover {
            color: #ffffff;
            background: rgba(59, 130, 246, 0.2);
        }
        .nav-item.active {
            background: #0284c7;
            color: #ffffff;
            box-shadow: 0 2px 8px rgba(2, 132, 199, 0.4);
        }
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
            margin-bottom: 10px;
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
    {{ header|safe }}
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

# Profil Səhifəsi Şablonu
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
            padding: 15px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .profile-title {
            font-size: 15px;
            font-weight: bold;
            color: #ffffff;
            border-bottom: 1px solid #3b82f6;
            padding-bottom: 6px;
            margin: 0;
        }
        .profile-header {
            display: flex;
            align-items: center;
            gap: 12px;
            background: #1e3a8a;
            padding: 10px;
            border-radius: 10px;
            border: 1px solid #3b82f6;
        }
        .avatar-wrapper {
            position: relative;
            width: 60px;
            height: 60px;
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
            font-size: 10px;
        }
        .profile-info h3 {
            margin: 0 0 4px 0;
            font-size: 16px;
            color: #ffffff;
        }
        .profile-info .status {
            color: #22c55e;
            font-size: 12px;
            font-weight: bold;
            margin: 0;
        }
        form {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin: 0;
        }
        input[type="text"] {
            width: 100%;
            padding: 10px;
            border: 1px solid #3b82f6;
            border-radius: 8px;
            background: #1e3a8a;
            color: #ffffff;
            font-size: 13px;
            box-sizing: border-box;
            text-align: center;
        }
        input[type="text"]::placeholder { color: #93c5fd; }
        .btn-blue {
            background: #0284c7;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 13px;
            cursor: pointer;
            text-align: center;
            width: 100%;
        }
        .btn-blue:hover { background: #0369a1; }
        .btn-gray {
            background: #334155;
            color: white;
            border: 1px solid #475569;
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 13px;
            cursor: pointer;
            text-align: center;
            width: 100%;
        }
        .btn-gray:hover { background: #475569; }
        .btn-red {
            background: #dc2626;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 13px;
            cursor: pointer;
            text-align: center;
            width: 100%;
        }
        .btn-red:hover { background: #b91c1c; }
        .msg-alert {
            font-size: 12px;
            text-align: center;
            margin: 0;
        }
    </style>
</head>
<body>
    {{ header|safe }}

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

        <form method="POST">
            <input type="hidden" name="action" value="change_name">
            <input type="text" name="new_nickname" placeholder="Yeni nik adı (max 7 hərf)" maxlength="7" required>
            <button type="submit" class="btn-blue">Adı Dəyiş</button>
        </form>

        <form method="POST">
            <input type="hidden" name="action" value="change_pic">
            <input type="text" name="pic_url" placeholder="Profil şəklinin linkini (URL) bura yapışdır" required>
            <button type="submit" class="btn-gray">Profil Şəklini Dəyiş</button>
            <button type="submit" class="btn-blue">Şəkli Yadda Saxla</button>
        </form>

        <form method="POST" onsubmit="return confirm('Hesabınızı silmək istədiyinizə əminsinizmi?');">
            <input type="hidden" name="action" value="delete_account">
            <button type="submit" class="btn-red">Hesabımı Sil</button>
        </form>

        <a href="/logout" class="btn-gray" style="text-decoration: none; box-sizing: border-box; display: block; text-align: center;">Çıxış Et</a>
    </div>
</body>
</html>
'''

# Mağaza Səhifəsi Şablonu
MAGAZA_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Mağaza</title>
    ''' + COMMON_STYLE + '''
    <style>
        .magaza-container {
            background: #172554;
            flex: 1;
            border: 2px solid #f97316;
            border-radius: 12px;
            padding: 15px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .magaza-title {
            font-size: 16px;
            font-weight: bold;
            color: #ffffff;
            border-bottom: 1px solid #3b82f6;
            padding-bottom: 8px;
            margin: 0;
            text-align: center;
        }
        .product-section {
            background: #1e3a8a;
            border: 1px solid #3b82f6;
            border-radius: 10px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .product-title {
            font-size: 14px;
            font-weight: bold;
            color: #f97316;
            margin: 0;
        }
        .color-list {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .color-btn {
            padding: 6px 12px;
            border-radius: 6px;
            border: none;
            font-weight: bold;
            cursor: pointer;
            font-size: 12px;
        }
        .btn-yellow { background: #eab308; color: #000; }
        .btn-red { background: #ef4444; color: #fff; }
        .btn-blue { background: #3b82f6; color: #fff; }
        .btn-purple { background: #a855f7; color: #fff; }
        .btn-green { background: #22c55e; color: #fff; }
        
        .price-tag {
            font-size: 12px;
            color: #93c5fd;
            font-weight: bold;
        }
        .emoji-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            max-height: 100px;
            overflow-y: auto;
            background: #172554;
            padding: 8px;
            border-radius: 8px;
            border: 1px solid #3b82f6;
        }
        .emoji-item {
            font-size: 18px;
            cursor: pointer;
            padding: 2px 4px;
            background: #1e3a8a;
            border-radius: 4px;
            transition: 0.1s;
        }
        .emoji-item:hover {
            transform: scale(1.2);
            background: #2563eb;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="magaza-container">
        <p class="magaza-title">🛍️ MAĞAZA BÖLMƏSİ</p>

        <!-- 1. Rəngli Nik -->
        <div class="product-section">
            <p class="product-title">🎨 RƏNGLİ NİK</p>
            <p class="price-tag">Qiyməti: 30 Bal</p>
            <div class="color-list">
                <button class="color-btn btn-yellow">Sarı</button>
                <button class="color-btn btn-red">Qırmızı</button>
                <button class="color-btn btn-blue">Göy</button>
                <button class="color-btn btn-purple">Bənövşəyi</button>
                <button class="color-btn btn-green">Yaşıl</button>
            </div>
        </div>

        <!-- 2. Rəngli Mesaj -->
        <div class="product-section">
            <p class="product-title">💬 RƏNGLİ MESAJ</p>
            <p class="price-tag">Qiyməti: 30 Bal</p>
            <div class="color-list">
                <button class="color-btn btn-yellow">Sarı</button>
                <button class="color-btn btn-red">Qırmızı</button>
                <button class="color-btn btn-blue">Göy</button>
                <button class="color-btn btn-purple">Bənövşəyi</button>
                <button class="color-btn btn-green">Yaşıl</button>
            </div>
        </div>

        <!-- 3. Hədiyyə Atmaq -->
        <div class="product-section">
            <p class="product-title">🎁 HƏDİYƏ ATMAQ</p>
            <p class="price-tag">Hədiyyənin Qiyməti: 20 Bal</p>
            <div class="emoji-grid">
                <span class="emoji-item">😇</span><span class="emoji-item">🤣</span><span class="emoji-item">🫠</span><span class="emoji-item">🤩</span><span class="emoji-item">🤗</span><span class="emoji-item">🤭</span><span class="emoji-item">😜</span><span class="emoji-item">🤔</span><span class="emoji-item">🤤</span><span class="emoji-item">🤠</span><span class="emoji-item">🤒</span><span class="emoji-item">😎</span><span class="emoji-item">😱</span><span class="emoji-item">🥺</span><span class="emoji-item">🥳</span><span class="emoji-item">🫪</span><span class="emoji-item">☠️</span><span class="emoji-item">👻</span><span class="emoji-item">😸</span><span class="emoji-item">😹</span><span class="emoji-item">🙀</span><span class="emoji-item">🙊</span><span class="emoji-item">🙈</span><span class="emoji-item">💌</span><span class="emoji-item">❤️‍🔥</span><span class="emoji-item">💬</span><span class="emoji-item">👋</span><span class="emoji-item">🤘</span><span class="emoji-item">🫶</span><span class="emoji-item">🙏</span><span class="emoji-item">🫰</span><span class="emoji-item">🐻</span><span class="emoji-item">🐹</span><span class="emoji-item">🐼</span><span class="emoji-item">🐸</span><span class="emoji-item">🌹</span><span class="emoji-item">🍻</span><span class="emoji-item">🗽</span><span class="emoji-item">✈️</span><span class="emoji-item">✨</span><span class="emoji-item">🧨</span><span class="emoji-item">🎉</span><span class="emoji-item">🎖️</span><span class="emoji-item">💰</span>
            </div>
        </div>

        <!-- 4. Profili Stikeri Hədiyyələrlə -->
        <div class="product-section">
            <p class="product-title">⭐ PROFİLƏ STİKƏRİ HƏDİYƏRLƏ</p>
            <div class="emoji-grid">
                <span class="emoji-item">😇</span><span class="emoji-item">🤣</span><span class="emoji-item">🫠</span><span class="emoji-item">🤩</span><span class="emoji-item">🤗</span><span class="emoji-item">🤭</span><span class="emoji-item">😜</span><span class="emoji-item">🤔</span><span class="emoji-item">🤤</span><span class="emoji-item">🤠</span><span class="emoji-item">🤒</span><span class="emoji-item">😎</span><span class="emoji-item">😱</span><span class="emoji-item">🥺</span><span class="emoji-item">🥳</span><span class="emoji-item">🫪</span><span class="emoji-item">☠️</span><span class="emoji-item">👻</span><span class="emoji-item">😸</span><span class="emoji-item">😹</span><span class="emoji-item">🙀</span><span class="emoji-item">🙊</span><span class="emoji-item">🙈</span><span class="emoji-item">💌</span><span class="emoji-item">❤️‍🔥</span><span class="emoji-item">💬</span><span class="emoji-item">👋</span><span class="emoji-item">🤘</span><span class="emoji-item">🫶</span><span class="emoji-item">🙏</span><span class="emoji-item">🫰</span><span class="emoji-item">🐻</span><span class="emoji-item">🐹</span><span class="emoji-item">🐼</span><span class="emoji-item">🐸</span><span class="emoji-item">🌹</span><span class="emoji-item">🍻</span><span class="emoji-item">🗽</span><span class="emoji-item">✈️</span><span class="emoji-item">✨</span><span class="emoji-item">🧨</span><span class="emoji-item">🎉</span><span class="emoji-item">🎖️</span><span class="emoji-item">💰</span>
            </div>
        </div>

    </div>
</body>
</html>
'''

# Digər Səhifələr Üçün Şablon (Şəkil, Vidyo, Oyun)
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
            border-radius: 12px; 
            padding: 20px; 
            text-align: center;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 16px;
            color: #93c5fd;
        }
    </style>
</head>
<body>
    {{ header|safe }}
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
                    cursor.execute("INSERT INTO users (nickname, password, profile_pic, points) VALUES (?, ?, ?, ?)", (nickname, password, '', 500))
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

def get_user_points(username):
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE nickname = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] is not None else 500

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
    
    points = get_user_points(session['user'])
    header = get_header_template(points)
        
    return render_template_string(CHAT_TEMPLATE, messages=messages, header=header)

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
            
    cursor.execute("SELECT profile_pic FROM users WHERE nickname = ?", (session['user'],))
    row = cursor.fetchone()
    pic = row[0] if row and row[0] else ''
    
    conn.close()
    points = get_user_points(session['user'])
    header = get_header_template(points)
    
    return render_template_string(PROFIL_TEMPLATE, user=session['user'], pic=pic, message=message, error=error, header=header)

@app.route('/magaza')
def magaza():
    if 'user' not in session:
        return redirect(url_for('index'))
    points = get_user_points(session['user'])
    header = get_header_template(points)
    return render_template_string(MAGAZA_TEMPLATE, header=header)

@app.route('/sekil')
def sekil():
    if 'user' not in session:
        return redirect(url_for('index'))
    points = get_user_points(session['user'])
    header = get_header_template(points)
    return render_template_string(SUB_TEMPLATE, title="Şəkillər", header=header)

@app.route('/vidyo')
def vidyo():
    if 'user' not in session:
        return redirect(url_for('index'))
    points = get_user_points(session['user'])
    header = get_header_template(points)
    return render_template_string(SUB_TEMPLATE, title="Videolar", header=header)

@app.route('/oyun')
def oyun():
    if 'user' not in session:
        return redirect(url_for('index'))
    points = get_user_points(session['user'])
    header = get_header_template(points)
    return render_template_string(SUB_TEMPLATE, title="Oyunlar", header=header)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
