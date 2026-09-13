from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import base64

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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            gift TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uploader TEXT NOT NULL,
            image_data TEXT NOT NULL
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
            width: 280px; 
            padding: 20px; 
            background: #172554; 
            border-radius: 10px; 
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3); 
            text-align: center; 
            border: 1px solid #3b82f6; 
        }
        h1 { 
            font-size: 16px; 
            margin-bottom: 15px; 
            color: #ffffff; 
        }
        input { 
            width: 100%; 
            padding: 8px 10px; 
            margin: 6px 0; 
            border: 1px solid #3b82f6; 
            border-radius: 5px; 
            background: #1e3a8a; 
            color: #ffffff; 
            box-sizing: border-box; 
            font-size: 12px;
        }
        input::placeholder { color: #93c5fd; }
        button { 
            width: 100%; 
            padding: 8px; 
            margin: 5px 0; 
            background: #2563eb; 
            color: white; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            font-weight: bold; 
            font-size: 12px;
        }
        button:hover { background: #1d4ed8; }
        .error { color: #f87171; font-size: 12px; margin-bottom: 8px; }
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

# Üst menyu şablonu (Yuxarıdakı silinən hissələr çıxarıldı, yalnız naviqasiya qaldı)
def get_header_template(points=500):
    return f'''
    <div class="nav-bar">
        <a href="/chat" class="nav-item">
            <span class="icon">💬</span>
            <span>Çat</span>
        </a>
        <a href="/istifadeciler" class="nav-item">
            <span class="icon">👥</span>
            <span>İstifadəçilər</span>
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

# Ümumi Yığcam CSS Stilleri
COMMON_STYLE = '''
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 8px; 
            background: #1e3a8a; 
            color: #ffffff; 
            display: flex; 
            flex-direction: column; 
            height: 100vh; 
            box-sizing: border-box; 
        }
        .nav-bar { 
            background: #172554; 
            border: 1px solid #f97316; 
            border-radius: 8px; 
            padding: 6px; 
            display: flex; 
            justify-content: space-around; 
            align-items: center; 
            margin-bottom: 6px;
            gap: 2px;
            overflow-x: auto;
        }
        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-decoration: none;
            color: #cbd5e1;
            padding: 4px 6px;
            border-radius: 6px;
            font-size: 10px;
            font-weight: bold;
            transition: 0.2s;
            white-space: nowrap;
        }
        .nav-item .icon {
            font-size: 14px;
            margin-bottom: 1px;
        }
        .nav-item:hover {
            color: #ffffff;
            background: rgba(59, 130, 246, 0.2);
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
            flex: 1; 
            border: 1px solid #f97316; 
            border-radius: 8px; 
            padding: 8px; 
            overflow-y: auto; 
            color: #ffffff; 
            margin-bottom: 6px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .chat-box p {
            background: #1e3a8a;
            padding: 6px 8px;
            border-radius: 5px;
            margin: 0;
            border-left: 3px solid #3b82f6;
            word-break: break-all;
            font-size: 12px;
        }
        .message-form { 
            display: flex; 
            gap: 6px; 
            background: #172554;
            padding: 6px;
            border: 1px solid #f97316;
            border-radius: 8px;
            align-items: center;
        }
        input[type="text"] { 
            flex: 1; 
            padding: 7px 10px; 
            border: 1px solid #3b82f6; 
            border-radius: 5px; 
            background: #1e3a8a; 
            color: #ffffff; 
            font-size: 12px;
        }
        input[type="text"]::placeholder { color: #93c5fd; }
        button[type="submit"] { 
            padding: 7px 14px; 
            background: #22c55e; 
            color: white; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            font-weight: bold; 
            font-size: 12px;
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
            <p style="color: #93c5fd; text-align: center; border-left: none; background: transparent; font-size: 11px;">Hələ ki mesaj yoxdur. İlk mesajı sən yaz!</p>
        {% endif %}
    </div>
    <form method="POST" class="message-form">
        <input type="text" name="message" placeholder="Mesajınızı yazın..." autocomplete="off" required>
        <button type="submit">Göndər</button>
    </form>
</body>
</html>
'''

# İstifadəçilər Səhifəsi Şablonu
USERS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - İstifadəçilər</title>
    ''' + COMMON_STYLE + '''
    <style>
        .users-container {
            background: #172554;
            flex: 1;
            border: 1px solid #f97316;
            border-radius: 8px;
            padding: 10px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .users-title {
            font-size: 13px;
            font-weight: bold;
            color: #ffffff;
            border-bottom: 1px solid #3b82f6;
            padding-bottom: 5px;
            margin: 0 0 4px 0;
            text-align: center;
        }
        .user-card {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #1e3a8a;
            padding: 6px 10px;
            border-radius: 6px;
            border: 1px solid #3b82f6;
        }
        .user-left {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .user-avatar {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            border: 1px solid #f97316;
            object-fit: cover;
            background: #111;
        }
        .user-name {
            font-size: 12px;
            font-weight: bold;
            color: #ffffff;
            margin: 0 0 2px 0;
        }
        .user-status {
            font-size: 10px;
            color: #22c55e;
            font-weight: bold;
            margin: 0;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="users-container">
        <p class="users-title">👥 SAYTIN İSTİFADƏÇİLƏRİ</p>
        
        {% if all_users %}
            {% for u in all_users %}
                <div class="user-card">
                    <div class="user-left">
                        <img src="{{ u[1] if u[1] else 'https://i.imgur.com/6VBx3io.png' }}" class="user-avatar" alt="Profil">
                        <div>
                            <p class="user-name">@{{ u[0] }} 👑</p>
                            <p class="user-status">● Aktivdir</p>
                        </div>
                    </div>
                </div>
            {% endfor %}
        {% else %}
            <p style="text-align: center; color: #93c5fd; font-size: 11px;">Hələ ki qeydiyyatdan keçmiş istifadəçi yoxdur.</p>
        {% endif %}
    </div>
</body>
</html>
'''

# Şəkillər Səhifəsi Şablonu
SEKIL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Şəkillər</title>
    ''' + COMMON_STYLE + '''
    <style>
        .sekil-container {
            background: #172554;
            flex: 1;
            border: 1px solid #f97316;
            border-radius: 8px;
            padding: 10px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .sekil-title {
            font-size: 13px;
            font-weight: bold;
            color: #ffffff;
            border-bottom: 1px solid #3b82f6;
            padding-bottom: 5px;
            margin: 0;
            text-align: center;
        }
        .upload-box {
            background: #1e3a8a;
            border: 1px solid #3b82f6;
            border-radius: 6px;
            padding: 8px;
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        input[type="file"] {
            color: #93c5fd;
            font-size: 11px;
        }
        .btn-upload {
            background: #22c55e;
            color: white;
            border: none;
            padding: 6px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 11px;
            cursor: pointer;
            text-align: center;
        }
        .btn-upload:hover { background: #16a34a; }
        .gallery-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
            gap: 6px;
        }
        .gallery-item {
            background: #1e3a8a;
            border: 1px solid #3b82f6;
            border-radius: 6px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        .gallery-item img {
            width: 100%;
            height: 80px;
            object-fit: cover;
        }
        .gallery-user {
            font-size: 9px;
            color: #93c5fd;
            padding: 3px;
            text-align: center;
            background: #172554;
            margin: 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="sekil-container">
        <p class="sekil-title">📷 QALEREYA VƏ ŞƏKİLLƏR</p>

        <form method="POST" enctype="multipart/form-data" class="upload-box">
            <label style="font-size: 11px; color: #93c5fd; font-weight: bold;">Qalereyadan şəkil seç:</label>
            <input type="file" name="sekil_file" accept="image/*" required>
            <button type="submit" class="btn-upload">Şəkli Yüklə</button>
        </form>

        <div class="gallery-grid">
            {% if photos %}
                {% for p in photos %}
                    <div class="gallery-item">
                        <img src="{{ p[1] }}" alt="Şəkil">
                        <p class="gallery-user">@{{ p[0] }}</p>
                    </div>
                {% endfor %}
            {% else %}
                <p style="grid-column: 1 / -1; text-align: center; color: #93c5fd; font-size: 11px;">Hələ ki şəkil yüklənməyib.</p>
            {% endif %}
        </div>
    </div>
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
            border: 1px solid #f97316;
            border-radius: 8px;
            padding: 10px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .profile-title {
            font-size: 13px;
            font-weight: bold;
            color: #ffffff;
            border-bottom: 1px solid #3b82f6;
            padding-bottom: 4px;
            margin: 0;
        }
        .profile-header {
            display: flex;
            align-items: center;
            gap: 10px;
            background: #1e3a8a;
            padding: 8px;
            border-radius: 6px;
            border: 1px solid #3b82f6;
        }
        .avatar-wrapper {
            position: relative;
            width: 45px;
            height: 45px;
            border-radius: 50%;
            border: 2px solid #f97316;
            overflow: hidden;
            background: #111;
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
            font-size: 8px;
        }
        .profile-info h3 {
            margin: 0 0 2px 0;
            font-size: 13px;
            color: #ffffff;
        }
        .profile-info .status {
            color: #22c55e;
            font-size: 10px;
            font-weight: bold;
            margin: 0;
        }
        .gifts-box {
            background: #1e3a8a;
            border: 1px solid #3b82f6;
            border-radius: 6px;
            padding: 6px;
            display: flex;
            gap: 4px;
            flex-wrap: wrap;
            min-height: 30px;
            align-items: center;
        }
        .gift-item {
            font-size: 16px;
            background: #172554;
            padding: 2px 4px;
            border-radius: 4px;
            border: 1px solid #f97316;
        }
        form {
            display: flex;
            flex-direction: column;
            gap: 5px;
            margin: 0;
        }
        input[type="text"] {
            width: 100%;
            padding: 6px 8px;
            border: 1px solid #3b82f6;
            border-radius: 5px;
            background: #1e3a8a;
            color: #ffffff;
            font-size: 11px;
            box-sizing: border-box;
            text-align: center;
        }
        input[type="text"]::placeholder { color: #93c5fd; }
        input[type="file"] {
            color: #93c5fd;
            font-size: 10px;
        }
        .btn-blue {
            background: #0284c7;
            color: white;
            border: none;
            padding: 6px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 11px;
            cursor: pointer;
            text-align: center;
            width: 100%;
        }
        .btn-blue:hover { background: #0369a1; }
        .btn-gray {
            background: #334155;
            color: white;
            border: 1px solid #475569;
            padding: 6px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 11px;
            cursor: pointer;
            text-align: center;
            width: 100%;
        }
        .btn-gray:hover { background: #475569; }
        .btn-red {
            background: #dc2626;
            color: white;
            border: none;
            padding: 6px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 11px;
            cursor: pointer;
            text-align: center;
            width: 100%;
        }
        .btn-red:hover { background: #b91c1c; }
        .msg-alert {
            font-size: 11px;
            text-align: center;
            margin: 0;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="profile-container">
        <p class="profile-title">Mənim Profilim (Bal: {{ points }})</p>
        
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

        <div>
            <p style="font-size: 11px; margin: 0 0 3px 0; color: #93c5fd;">Hədiyyələr / Stikerlər:</p>
            <div class="gifts-box">
                {% if gifts %}
                    {% for g in gifts %}
                        <span class="gift-item" title="Göndərən: {{ g[1] }}">{{ g[0] }}</span>
                    {% endfor %}
                {% else %}
                    <span style="font-size: 11px; color: #93c5fd;">Hələ ki hədiyyə yoxdur.</span>
                {% endif %}
            </div>
        </div>

        <form method="POST">
            <input type="hidden" name="action" value="change_name">
            <input type="text" name="new_nickname" placeholder="Yeni nik (max 7 hərf)" maxlength="7" required>
            <button type="submit" class="btn-blue">Adı Dəyiş</button>
        </form>

        <form method="POST" enctype="multipart/form-data">
            <input type="hidden" name="action" value="change_pic">
            <input type="file" name="pic_file" accept="image/*" required>
            <button type="submit" class="btn-blue">Profil Şəklini Yüklə</button>
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
            border: 1px solid #f97316;
            border-radius: 8px;
            padding: 10px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .magaza-title {
            font-size: 13px;
            font-weight: bold;
            color: #ffffff;
            border-bottom: 1px solid #3b82f6;
            padding-bottom: 5px;
            margin: 0;
            text-align: center;
        }
        .product-section {
            background: #1e3a8a;
            border: 1px solid #3b82f6;
            border-radius: 6px;
            padding: 8px;
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        .product-title {
            font-size: 12px;
            font-weight: bold;
            color: #f97316;
            margin: 0;
        }
        .color-list {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }
        .color-btn {
            padding: 4px 8px;
            border-radius: 4px;
            border: none;
            font-weight: bold;
            cursor: pointer;
            font-size: 11px;
        }
        .btn-yellow { background: #eab308; color: #000; }
        .btn-red { background: #ef4444; color: #fff; }
        .btn-blue { background: #3b82f6; color: #fff; }
        .btn-purple { background: #a855f7; color: #fff; }
        .btn-green { background: #22c55e; color: #fff; }
        
        .price-tag {
            font-size: 11px;
            color: #93c5fd;
            font-weight: bold;
        }
        .emoji-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            max-height: 85px;
            overflow-y: auto;
            background: #172554;
            padding: 6px;
            border-radius: 6px;
            border: 1px solid #3b82f6;
        }
        .emoji-btn {
            font-size: 15px;
            cursor: pointer;
            padding: 2px;
            background: #1e3a8a;
            border-radius: 4px;
            border: 1px solid transparent;
        }
        .emoji-btn:hover {
            transform: scale(1.1);
            border-color: #f97316;
            background: #2563eb;
        }
        select {
            width: 100%;
            padding: 6px;
            background: #172554;
            color: #fff;
            border: 1px solid #3b82f6;
            border-radius: 5px;
            font-size: 11px;
        }
        .msg-alert {
            font-size: 11px;
            text-align: center;
            margin: 0;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="magaza-container">
        <p class="magaza-title">🛍️ MAĞAZA BÖLMƏSİ (Balın: {{ points }})</p>

        {% if message %}
            <p class="msg-alert" style="color: {% if error %}#f87171{% else %}#22c55e{% endif %};">{{ message }}</p>
        {% endif %}

        <!-- 1. Rəngli Nik -->
        <div class="product-section">
            <p class="product-title">🎨 RƏNGLİ NİK (30 Bal)</p>
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
            <p class="product-title">💬 RƏNGLİ MESAJ (30 Bal)</p>
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
            <p class="product-title">🎁 HƏDİYƏ ATMAQ (20 Bal)</p>
            <form method="POST">
                <input type="hidden" name="action" value="send_gift">
                <select name="receiver" required>
                    <option value="" disabled selected>İstifadəçini seçin</option>
                    {% for u in users %}
                        {% if u != current_user %}
                            <option value="{{ u }}">{{ u }}</option>
                        {% endif %}
                    {% endfor %}
                </select>
                <div class="emoji-grid" style="margin-top: 4px;">
                    {% set emojis = ['😇', '🤣', '🫠', '🤩', '🤗', '🤭', '😜', '🤔', '🤤', '🤠', '🤒', '😎', '😱', '🥺', '🥳', '☠️', '👻', '😸', '😹', '🙊', '🙈', '💌', '❤️‍🔥', '💬', '👋', '🤘', '🫶', '🙏', '🐻', '🐼', '🐸', '🌹', '🍻', '✈️', '✨', '🎉', '💰'] %}
                    {% for emo in emojis %}
                        <button type="submit" name="gift" value="{{ emo }}" class="emoji-btn">{{ emo }}</button>
                    {% endfor %}
                </div>
            </form>
        </div>

        <!-- 4. Profil Stikerləri -->
        <div class="product-section">
            <p class="product-title">⭐ PROFİL STİKƏRLƏRİ (25 Bal)</p>
            <div class="emoji-grid">
                {% for emo in emojis %}
                    <span class="emoji-btn" style="cursor: default;">{{ emo }}</span>
                {% endfor %}
            </div>
        </div>

    </div>
</body>
</html>
'''

# Digər Səhifələr Üçün Şablon (Vidyo, Oyun)
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
            border: 1px solid #f97316; 
            border-radius: 8px; 
            padding: 15px; 
            text-align: center;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 13px;
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

@app.route('/istifadeciler')
def istifadeciler():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nickname, profile_pic FROM users")
    all_users = cursor.fetchall()
    conn.close()
    
    points = get_user_points(session['user'])
    header = get_header_template(points)
    return render_template_string(USERS_TEMPLATE, all_users=all_users, header=header)

@app.route('/sekil', methods=['GET', 'POST'])
def sekil():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        file = request.files.get('sekil_file')
        if file and file.filename != '':
            file_bytes = file.read()
            encoded = base64.b64encode(file_bytes).decode('utf-8')
            mime_type = file.content_type or 'image/jpeg'
            img_data = f"data:{mime_type};base64,{encoded}"
            
            cursor.execute("INSERT INTO photos (uploader, image_data) VALUES (?, ?)", (session['user'], img_data))
            conn.commit()
        conn.close()
        return redirect(url_for('sekil'))
        
    cursor.execute("SELECT uploader, image_data FROM photos ORDER BY id DESC")
    photos = cursor.fetchall()
    conn.close()
    
    points = get_user_points(session['user'])
    header = get_header_template(points)
    return render_template_string(SEKIL_TEMPLATE, photos=photos, header=header)

@app.route('/profil', methods=['GET', 'POST'])
def profil():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    
    message = None
    error = False
    current_user = session['user']
    
    if request.method == 'POST':
        action = request.form.get('action')
        
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
                    cursor.execute("UPDATE gifts SET receiver = ? WHERE receiver = ?", (new_name, current_user))
                    cursor.execute("UPDATE gifts SET sender = ? WHERE sender = ?", (new_name, current_user))
                    cursor.execute("UPDATE photos SET uploader = ? WHERE uploader = ?", (new_name, current_user))
                    conn.commit()
                    session['user'] = new_name
                    current_user = new_name
                    message = "Nik adı uğurla dəyişdirildi!"
                    
        elif action == 'change_pic':
            file = request.files.get('pic_file')
            if file and file.filename != '':
                file_bytes = file.read()
                encoded = base64.b64encode(file_bytes).decode('utf-8')
                mime_type = file.content_type or 'image/jpeg'
                pic_url = f"data:{mime_type};base64,{encoded}"
                
                cursor.execute("UPDATE users SET profile_pic = ? WHERE nickname = ?", (pic_url, current_user))
                conn.commit()
                message = "Profil şəkli yeniləndi!"
            else:
                message = "Şəkil seçilmədi!"
                error = True
                
        elif action == 'delete_account':
            cursor.execute("DELETE FROM users WHERE nickname = ?", (current_user,))
            cursor.execute("DELETE FROM gifts WHERE receiver = ? OR sender = ?", (current_user, current_user))
            cursor.execute("DELETE FROM photos WHERE uploader = ?", (current_user,))
            conn.commit()
            conn.close()
            session.pop('user', None)
            return redirect(url_for('index'))
            
    cursor.execute("SELECT profile_pic FROM users WHERE nickname = ?", (current_user,))
    row = cursor.fetchone()
    pic = row[0] if row and row[0] else ''
    
    cursor.execute("SELECT gift, sender FROM gifts WHERE receiver = ?", (current_user,))
    gifts = cursor.fetchall()
    
    conn.close()
    points = get_user_points(current_user)
    header = get_header_template(points)
    
    return render_template_string(PROFIL_TEMPLATE, user=current_user, pic=pic, gifts=gifts, message=message, error=error, header=header, points=points)

@app.route('/magaza', methods=['GET', 'POST'])
def magaza():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    current_user = session['user']
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    
    message = None
    error = False
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'send_gift':
            receiver = request.form.get('receiver')
            gift = request.form.get('gift')
            points = get_user_points(current_user)
            
            if points >= 20:
                cursor.execute("UPDATE users SET points = points - 20 WHERE nickname = ?", (current_user,))
                cursor.execute("INSERT INTO gifts (sender, receiver, gift) VALUES (?, ?, ?)", (current_user, receiver, gift))
                conn.commit()
                message = f"{receiver} istifadəçisinə hədiyyə göndərildi!"
            else:
                message = "Balınız kifayət etmir (20 bal lazımdır)!"
                error = True
                
    cursor.execute("SELECT nickname FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    points = get_user_points(current_user)
    header = get_header_template(points)
    return render_template_string(MAGAZA_TEMPLATE, header=header, users=users, current_user=current_user, message=message, error=error, points=points)

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
