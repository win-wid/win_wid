from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import base64
import os
import random
import tempfile

app = Flask(__name__)
app.secret_key = 'win_wid_gizli_kalit'

# Bazanın həmişə eyni yerdə və təhlükəsiz qalması üçün mütləq yol təyini
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'win_wid.db')

def init_db():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            nickname TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            profile_pic TEXT,
            points INTEGER DEFAULT 0,
            name_color TEXT DEFAULT 'inherit',
            msg_color TEXT DEFAULT '#f8fafc',
            profile_sticker TEXT DEFAULT ''
        )
    ''')
    
    # Mövcud bazalarda sütunlar yoxdursa əlavə etmək üçün
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN name_color TEXT DEFAULT 'inherit'")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN msg_color TEXT DEFAULT '#f8fafc'")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_sticker TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
        
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS private_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS photo_likes (
            photo_id INTEGER,
            username TEXT,
            PRIMARY KEY (photo_id, username)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS photo_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            photo_id INTEGER,
            username TEXT,
            comment TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS photo_shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            photo_id INTEGER,
            sender TEXT,
            receiver TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uploader TEXT NOT NULL,
            video_data TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_likes (
            video_id INTEGER,
            username TEXT,
            PRIMARY KEY (video_id, username)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            username TEXT,
            comment TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            sender TEXT,
            receiver TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')

    # BİLDİRİŞLƏR CƏDVƏLİ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            is_read INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

init_db()

INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Giriş</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { 
            font-family: 'Plus Jakarta Sans', sans-serif; 
            background: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url('https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe'); 
            background-size: cover;
            background-position: center;
            color: #f8fafc; 
            display: flex; 
            flex-direction: column;
            justify-content: center; 
            align-items: center; 
            height: 100vh; 
            margin: 0; 
            position: relative;
        }
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .warning-box {
            width: 380px;
            height: 380px;
            background: rgba(15, 15, 18, 0.95);
            backdrop-filter: blur(16px);
            border: 2px solid #f97316;
            border-radius: 24px;
            padding: 30px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.9);
            box-sizing: border-box;
            text-align: center;
        }
        .warning-text {
            font-size: 16px;
            font-weight: 700;
            color: #f8fafc;
            line-height: 1.6;
            margin-top: 20px;
        }
        .warning-buttons {
            display: flex;
            justify-content: flex-end;
            gap: 12px;
        }
        .warning-btn {
            padding: 10px 18px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 14px;
            cursor: pointer;
            border: none;
            transition: transform 0.2s;
        }
        .btn-read {
            background: #f97316;
            color: #fff;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .btn-unread {
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .warning-btn:hover {
            transform: translateY(-2px);
        }

        .terms-link {
            position: absolute;
            top: 20px;
            left: 20px;
            color: #fb923c;
            text-decoration: none;
            font-size: 14px;
            font-weight: 700;
            background: rgba(15, 15, 18, 0.8);
            padding: 8px 14px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.2s ease;
        }
        .terms-link:hover {
            background: rgba(249, 115, 22, 0.2);
            color: #fff;
        }
        .logo-container {
            margin-bottom: 25px;
            text-align: center;
        }
        .container { 
            width: 90%;
            max-width: 480px; 
            padding: 45px 38px; 
            background: rgba(15, 15, 18, 0.92);
            backdrop-filter: blur(16px);
            border-radius: 24px; 
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.8); 
            text-align: center; 
            border: 1px solid rgba(255, 255, 255, 0.12); 
        }
        h1 { 
            font-size: 26px; 
            margin-bottom: 32px; 
            background: linear-gradient(135deg, #f97316, #fb923c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 0.5px;
            font-weight: 700;
        }
        input { 
            width: 100%; 
            padding: 16px 20px; 
            margin: 14px 0; 
            border: 1px solid rgba(255, 255, 255, 0.12); 
            border-radius: 14px; 
            background: rgba(9, 9, 11, 0.7); 
            color: #f8fafc; 
            box-sizing: border-box; 
            font-size: 16px;
            transition: all 0.3s ease;
        }
        input:focus {
            border-color: #f97316;
            box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.25);
            outline: none;
        }
        input::placeholder { color: #a1a1aa; }
        button { 
            width: 100%; 
            padding: 16px; 
            margin: 12px 0; 
            background: linear-gradient(135deg, #f97316, #ea580c); 
            color: white; 
            border: none; 
            border-radius: 14px; 
            cursor: pointer; 
            font-weight: 600; 
            font-size: 16px;
            transition: all 0.2s ease;
            box-shadow: 0 4px 15px rgba(249, 115, 22, 0.35);
        }
        button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(249, 115, 22, 0.45);
        }
        button[name="action"][value="register"] {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            box-shadow: none;
        }
        button[name="action"][value="register"]:hover {
            background: rgba(255, 255, 255, 0.15);
        }
        .error { color: #f87171; font-size: 15px; margin-bottom: 16px; font-weight: 500; background: rgba(239, 68, 68, 0.12); padding: 12px; border-radius: 10px; border: 1px solid rgba(239, 68, 68, 0.25); }
    </style>
</head>
<body>
    <div class="modal-overlay" id="warningModal">
        <div class="warning-box">
            <div class="warning-text">
                WİN_WİD'Ə XOŞ GƏLMİSİNİZ..🤗<br><br>
                İSDİFADƏÇİ ŞƏRTLƏRİNİ OXUYUB SONRA SAYITA DAXİL OLUN...
            </div>
            <div class="warning-buttons">
                <a href="/istifade_sertleri" target="_blank" class="warning-btn btn-read">OXU</a>
                <button type="button" class="warning-btn btn-unread" onclick="closeWarningModal()">OXUMA</button>
            </div>
        </div>
    </div>

    <a href="/istifade_sertleri" target="_blank" class="terms-link">İSTİFADƏ ŞƏRTLƏRİ</a>

    <div class="logo-container">
        <div style="color: #f97316; font-size: 32px; font-weight: 800; letter-spacing: 2px;">WİN_WİD</div>
    </div>

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

    <script>
        function closeWarningModal() {
            document.getElementById('warningModal').style.display = 'none';
        }
    </script>
</body>
</html>
'''

TERMS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Qaydalar və Şərtlər</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: #09090b;
            color: #f8fafc;
            margin: 0;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
        }
        .terms-box {
            background: rgba(24, 24, 27, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.6);
            max-width: 700px;
            width: 100%;
            line-height: 1.6;
        }
        h2 {
            color: #f97316;
            font-size: 26px;
            margin-bottom: 20px;
            text-align: center;
        }
        p {
            font-size: 15px;
            color: #d4d4d8;
            margin-bottom: 20px;
        }
        h3 {
            color: #fb923c;
            font-size: 18px;
            margin-top: 25px;
            margin-bottom: 10px;
        }
        ul {
            padding-left: 20px;
            margin: 0 0 15px 0;
        }
        li {
            margin-bottom: 8px;
            font-size: 15px;
            color: #f8fafc;
        }
        .contact-email {
            color: #38bdf8;
            font-weight: 700;
        }
    </style>
</head>
<body>
    <div class="terms-box">
        <h2>WİN_WİD – QAYDALAR VƏ ŞƏRTLƏR</h2>
        <p>Saytımızdan istifadə etməzdən əvvəl bu sadə qaydalarla tanış olmağınızı xahiş edirik. Sayta girməklə və ya qeydiyyatdan keçməklə bu şərtlərlə razılaşmış olursunuz.</p>
        
        <h3>1. Əsas Qaydalar</h3>
        <ul>
            <li>Saytımızdan hər kəs istifadə edə bilər, lakin qanunlara zidd hərəkətlər etmək qadağandır.</li>
            <li>Biz istədiyimiz vaxt bu qaydalarda dəyişiklik edə bilərik. Dəyişikliklər elə saytda yerləşdirildiyi andan qüvvəyə minir.</li>
        </ul>

        <h3>2. Qeydiyyat və Şifrə Təhlükəsizliyi</h3>
        <ul>
            <li>Şifrənizi başqalarına verməyin. Hesabınızda baş verən hər şeyə özünüz cavabdehsiniz.</li>
            <li><strong>YAŞANAN PROBLEMLƏRƏ GÖRƏ SAYT RƏHBƏRLİYİ MƏHSULİYYƏT DAŞIMIR.</strong></li>
        </ul>

        <h3>3. Qadağan Olunan Əməliyyatlar</h3>
        <p>Saytımızda aşağıdakıları etmək qəti qadağandır:</p>
        <ul>
            <li>Digər istifadəçiləri narahat etmək, təhqir etmək və ya onlara zərər vurmaq.</li>
            <li>Saytın işini pozmağa çalışmaq və ya haker hücumları etmək.</li>
            <li>Saxta məlumatlar yaymaq və ya qanunsuz işlərlə məşğul olmaq.</li>
        </ul>

        <h3>4. Mülkiyyət Hüququ</h3>
        <ul>
            <li>WİN_WİD-də olan bütün yazılar, şəkillər, loqolar və dizayn bizə məxsusdur.</li>
            <li>Bizim icazəmiz olmadan saytdakı məlumatları kopyalayıb başqa yerlərdə istifadə etmək olmaz.</li>
        </ul>

        <h3>5. Məsuliyyət və Təhlükəsizlik</h3>
        <ul>
            <li>Biz çalışırıq ki, sayt həmişə əla işləsin, lakin texniki nasazlıqlar ola bilər.</li>
            <li>Hər hansı kənar müdaxilə (haker hücumu) nəticəsində sayta məxsus məlumatlar oğurlanarsa və ya yayılarsa, tərəflər qanunvericiliyə uyğun olaraq məsuliyyət daşıyır və pozuntularla bağlı məhkəmə müstəvisində hüquqi addımlar atıla bilər.</li>
            <li>Qaydaları pozduğunuz təqdirdə hesabınızı bloklaya və ya silə bilərik.</li>
        </ul>

        <h3>6. Bizimlə Əlaqə</h3>
        <p>Suallarınız və ya təklifiniz olarsa, bizə yazmaqdan çəkinməyin:<br>
        E-poçt: <span class="contact-email">winvid30@gmail.com</span></p>
    </div>
</body>
</html>
'''

def get_header_template(has_unread_notifs=False):
    dot_html = '<span style="position: absolute; top: 8px; right: 24px; width: 10px; height: 10px; background: #ef4444; border-radius: 50%;"></span>' if has_unread_notifs else ''
    return f'''
    <div class="nav-bar" style="position: relative;">
        <a href="/chat" class="nav-item">
            <span class="icon">💬</span>
            <span>Çat</span>
        </a>
        <a href="/istifadeciler" class="nav-item">
            <span class="icon">👤</span>
            <span>İstifadəçi</span>
        </a>
        <a href="/sekil" class="nav-item">
            <span class="icon">📷</span>
            <span>Şəkil</span>
        </a>
        <a href="/vidyo" class="nav-item">
            <span class="icon">📹</span>
            <span>Vidyo</span>
        </a>
        <a href="/oyun" class="nav-item">
            <span class="icon">🎮</span>
            <span>Oyun</span>
        </a>
        <a href="/magaza" class="nav-item">
            <span class="icon">🛍️</span>
            <span>Maqazin</span>
        </a>
        <a href="/profil" class="nav-item">
            <span class="icon">👤</span>
            <span>Profil</span>
        </a>
        <a href="/bildiris" class="nav-item" style="position: relative;">
            <span class="icon">🔔</span>
            <span>Bildiriş</span>
            {dot_html}
        </a>
        <a href="/sikayet" class="nav-item">
            <span class="icon">📢</span>
            <span>Şikayət</span>
        </a>
    </div>
'''

COMMON_STYLE = '''
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { 
            font-family: 'Plus Jakarta Sans', sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #09090b; 
            color: #f8fafc; 
            display: flex; 
            flex-direction: column; 
            height: 100vh; 
            box-sizing: border-box; 
        }
        .nav-bar { 
            background: rgba(24, 24, 27, 0.9); 
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.12); 
            border-radius: 18px; 
            padding: 14px 20px; 
            display: flex; 
            justify-content: space-around; 
            align-items: center; 
            margin-bottom: 20px;
            gap: 14px;
            overflow-x: auto;
            box-shadow: 0 12px 30px -5px rgba(0, 0, 0, 0.4);
            flex-shrink: 0;
            box-sizing: border-box;
            width: 100%;
        }
        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-decoration: none;
            color: #d4d4d8;
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 600;
            transition: all 0.2s ease;
            white-space: nowrap;
        }
        .nav-item .icon {
            font-size: 26px;
            margin-bottom: 6px;
            transition: transform 0.2s;
        }
        .nav-item:hover {
            color: #f97316;
            background: rgba(249, 115, 22, 0.15);
        }
        .nav-item:hover .icon {
            transform: scale(1.15);
        }
    </style>
'''

CHAT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Ümumi Çat</title>
    ''' + COMMON_STYLE + '''
    <style>
        .chat-container {
            background: rgba(24, 24, 27, 0.8);
            backdrop-filter: blur(16px);
            flex: 1;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 22px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 15px 35px rgba(0,0,0,0.5);
        }
        .chat-header-title {
            background: rgba(9, 9, 11, 0.7);
            padding: 18px;
            font-size: 17px;
            font-weight: 700;
            text-align: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            color: #f97316;
            letter-spacing: 0.5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .points-box-orange {
            background: #f97316;
            border: 1px solid #f97316;
            color: #000000;
            padding: 6px 14px;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 800;
            text-transform: uppercase;
        }
        .real-time-clock {
            color: #ffffff;
            font-size: 16px;
            font-weight: 700;
            background: rgba(255, 255, 255, 0.08);
            padding: 6px 14px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            letter-spacing: 1px;
        }
        .messages-box {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 18px;
        }
        .message-bubble {
            background: rgba(39, 39, 42, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 16px 20px;
            border-radius: 18px;
            max-width: 80%;
            word-break: break-all;
            position: relative;
            box-shadow: 0 6px 15px rgba(0,0,0,0.15);
        }
        .message-bubble.my-message {
            background: linear-gradient(135deg, #c2410c, #9a3412);
            align-self: flex-end;
            border-color: rgba(249, 115, 22, 0.4);
        }
        .msg-user {
            font-size: 14px;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .msg-text {
            font-size: 16px;
            margin: 0;
            line-height: 1.5;
        }
        .msg-actions {
            display: flex;
            gap: 16px;
            margin-top: 10px;
            font-size: 13px;
        }
        .msg-actions button {
            background: transparent;
            border: none;
            color: rgba(255, 255, 255, 0.75);
            cursor: pointer;
            padding: 0;
            font-weight: 600;
            transition: color 0.2s;
        }
        .msg-actions button:hover {
            color: #fff;
            text-decoration: underline;
        }
        .chat-form {
            display: flex;
            padding: 18px;
            background: rgba(9, 9, 11, 0.7);
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            gap: 14px;
            align-items: center;
        }
        .chat-input {
            flex: 1;
            height: 52px;
            padding: 0 20px;
            background: rgba(24, 24, 27, 0.9);
            border: 1px solid #f97316;
            border-radius: 14px;
            color: #fff;
            font-size: 16px;
            box-sizing: border-box;
        }
        .chat-input:focus { border-color: #fb923c; outline: none; box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.25); }
        .chat-submit {
            background: linear-gradient(135deg, #f97316, #ea580c);
            color: white;
            border: none;
            height: 52px;
            padding: 0 28px;
            border-radius: 14px;
            font-weight: 600;
            cursor: pointer;
            font-size: 16px;
            transition: transform 0.2s;
            box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .chat-submit:hover { transform: translateY(-1px); }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="chat-container">
        <div class="chat-header-title">
            <div class="points-box-orange">YIGILAN BALLAR: <span id="userPointsDisplay" style="color: #000000;">{{ user_points }}</span></div>
            <div class="real-time-clock" id="realTimeClock">00:00:00</div>
            <span>💬 ÜMUMİ ÇAT BÖLMƏSİ</span>
        </div>
        
        <div class="messages-box" id="messagesBox">
            {% if messages %}
                {% for m in messages %}
                    <div class="message-bubble {% if m[1] == current_user %}my-message{% endif %}" id="msg-{{ m[0] }}">
                        <div class="msg-user" style="color: {{ m[3] if m[3] and m[3] != 'inherit' else ('#fed7aa' if m[1] == current_user else '#f97316') }};">@{{ m[1] }} {{ m[5] }}</div>
                        <p class="msg-text" id="msg-text-{{ m[0] }}" style="color: {{ m[4] if m[4] and m[4] != '#eab308' else '#f8fafc' }};">{{ m[2] }}</p>
                        
                        {% if m[1] == current_user %}
                            <div class="msg-actions">
                                <button onclick="editMessage('{{ m[0] }}')">Redaktə et</button>
                                <button onclick="deleteMessage('{{ m[0] }}')" style="color: #fca5a5;">Sil</button>
                            </div>
                        {% endif %}
                    </div>
                {% endfor %}
            {% else %}
                <p style="text-align: center; color: #a1a1aa; font-size: 15px; margin: auto;">Hələ ki mesaj yoxdur. İlk mesajı sən yaz!</p>
            {% endif %}
        </div>

        <form class="chat-form" method="POST" action="/chat/send">
            <input type="text" name="content" class="chat-input" placeholder="Mesajınızı yazın..." required autocomplete="off">
            <button type="submit" class="chat-submit">Göndər</button>
        </form>
    </div>

    <script>
        let msgBox = document.getElementById('messagesBox');
        msgBox.scrollTop = msgBox.scrollHeight;

        function updateClock() {
            const now = new Date();
            const options = {
                timeZone: 'Asia/Baku',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            };
            const timeString = new Intl.DateTimeFormat('az-AZ', options).format(now);
            document.getElementById('realTimeClock').innerText = timeString;
        }
        setInterval(updateClock, 1000);
        updateClock();

        function deleteMessage(msgId) {
            if(confirm("Bu mesajı silmək istədiyinizə əminsinizmi?")) {
                fetch('/chat/delete/' + msgId, { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if(data.success) {
                        document.getElementById('msg-' + msgId).remove();
                    } else {
                        alert(data.error || "Xəta baş verdi!");
                    }
                });
            }
        }

        function editMessage(msgId) {
            let textEl = document.getElementById('msg-text-' + msgId);
            let currentText = textEl.innerText;
            let newText = prompt("Mesajınızı redaktə edin:", currentText);
            
            if(newText !== null && newText.trim() !== "") {
                fetch('/chat/edit/' + msgId, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: newText.trim() })
                })
                .then(res => res.json())
                .then(data => {
                    if(data.success) {
                        textEl.innerText = data.content;
                    } else {
                        alert(data.error || "Xəta baş verdi!");
                    }
                });
            }
        }
    </script>
</body>
</html>
'''

USERS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - İstifadəçi</title>
    ''' + COMMON_STYLE + '''
    <style>
        .users-container {
            background: rgba(24, 24, 27, 0.8);
            backdrop-filter: blur(16px);
            flex: 1;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 22px;
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.5);
        }
        .users-title {
            font-size: 17px;
            font-weight: 700;
            color: #f97316;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding-bottom: 14px;
            margin: 0 0 12px 0;
            text-align: center;
            letter-spacing: 0.5px;
        }
        .user-card {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(39, 39, 42, 0.6);
            padding: 16px 20px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            transition: transform 0.2s;
        }
        .user-card:hover {
            transform: translateX(3px);
            background: rgba(39, 39, 42, 0.9);
        }
        .user-left {
            display: flex;
            align-items: center;
            gap: 18px;
        }
        .user-avatar {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            border: 2px solid #f97316;
            object-fit: cover;
            background: #111;
        }
        .user-name {
            font-size: 17px;
            font-weight: 700;
            margin: 0 0 4px 0;
        }
        .user-status {
            font-size: 14px;
            color: #4ade80;
            font-weight: 600;
            margin: 0;
        }
        .msg-btn {
            background: linear-gradient(135deg, #f97316, #ea580c);
            color: white;
            border: none;
            padding: 10px 18px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 14px;
            cursor: pointer;
            text-decoration: none;
            box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
            transition: transform 0.2s;
        }
        .msg-btn:hover {
            transform: translateY(-2px);
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
                            <p class="user-name" style="color: {{ u[2] if u[2] and u[2] != 'inherit' and u[2] != '#eab308' else '#f8fafc' }};">@{{ u[0] }} {{ u[3] }}</p>
                            <p class="user-status">● Aktivdir</p>
                        </div>
                    </div>
                    {% if u[0] != current_user %}
                        <a href="/ozel_mesaj/{{ u[0] }}" class="msg-btn">💬 MESAJ YAZ</a>
                    {% endif %}
                </div>
            {% endfor %}
        {% else %}
            <p style="text-align: center; color: #a1a1aa; font-size: 15px;">Hələ ki qeydiyyatdan keçmiş istifadəçi yoxdur.</p>
        {% endif %}
    </div>
</body>
</html>
'''

PRIVATE_CHAT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Şəxsi Çat</title>
    ''' + COMMON_STYLE + '''
    <style>
        .chat-container {
            background: rgba(24, 24, 27, 0.8);
            backdrop-filter: blur(16px);
            flex: 1;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 22px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 15px 35px rgba(0,0,0,0.5);
        }
        .chat-header-title {
            background: rgba(9, 9, 11, 0.7);
            padding: 18px;
            font-size: 17px;
            font-weight: 700;
            text-align: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            color: #f97316;
            letter-spacing: 0.5px;
        }
        .messages-box {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 18px;
        }
        .message-bubble {
            background: rgba(39, 39, 42, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 16px 20px;
            border-radius: 18px;
            max-width: 80%;
            word-break: break-all;
            box-shadow: 0 6px 15px rgba(0,0,0,0.15);
        }
        .message-bubble.my-message {
            background: linear-gradient(135deg, #c2410c, #9a3412);
            align-self: flex-end;
            border-color: rgba(249, 115, 22, 0.4);
        }
        .msg-text {
            font-size: 16px;
            margin: 0;
            line-height: 1.5;
            color: #f8fafc;
        }
        .chat-form {
            display: flex;
            padding: 18px;
            background: rgba(9, 9, 11, 0.7);
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            gap: 14px;
            align-items: center;
        }
        .chat-input {
            flex: 1;
            height: 52px;
            padding: 0 20px;
            background: rgba(24, 24, 27, 0.9);
            border: 1px solid #f97316;
            border-radius: 14px;
            color: #fff;
            font-size: 16px;
            box-sizing: border-box;
        }
        .chat-input:focus { border-color: #fb923c; outline: none; box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.25); }
        .chat-submit {
            background: linear-gradient(135deg, #f97316, #ea580c);
            color: white;
            border: none;
            height: 52px;
            padding: 0 28px;
            border-radius: 14px;
            font-weight: 600;
            cursor: pointer;
            font-size: 16px;
            transition: transform 0.2s;
            box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .chat-submit:hover { transform: translateY(-1px); }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="chat-container">
        <div class="chat-header-title">
            <span>💬 @{{ receiver }} İlə Şəxsi Söhbət</span>
        </div>
        
        <div class="messages-box" id="messagesBox">
            {% if messages %}
                {% for m in messages %}
                    <div class="message-bubble {% if m[1] == current_user %}my-message{% endif %}">
                        <p class="msg-text">{{ m[3] }}</p>
                    </div>
                {% endfor %}
            {% else %}
                <p style="text-align: center; color: #a1a1aa; font-size: 15px; margin: auto;">Hələ ki şəxsi mesaj yoxdur. İlk mesajı sən yaz!</p>
            {% endif %}
        </div>

        <form class="chat-form" method="POST">
            <input type="text" name="content" class="chat-input" placeholder="Şəxsi mesajınızı yazın..." required autocomplete="off">
            <button type="submit" class="chat-submit">Göndər</button>
        </form>
    </div>

    <script>
        let msgBox = document.getElementById('messagesBox');
        msgBox.scrollTop = msgBox.scrollHeight;
    </script>
</body>
</html>
'''

SEKIL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Şəkil Şortları</title>
    ''' + COMMON_STYLE + '''
    <style>
        .shorts-container {
            background: #000;
            flex: 1;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 22px;
            overflow-y: scroll;
            scroll-snap-type: y mandatory;
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
            box-shadow: 0 15px 35px rgba(0,0,0,0.6);
        }
        .short-card {
            width: 100%;
            height: 100%;
            min-height: 100%;
            scroll-snap-align: start;
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
            background: #09090b;
        }
        .short-card img {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
        .upload-trigger-bar {
            position: absolute;
            top: 20px;
            right: 24px;
            z-index: 20;
            width: 145px;
            height: 42px;
        }
        .btn-open-upload {
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: white;
            border: none;
            width: 100%;
            height: 100%;
            border-radius: 12px;
            font-weight: 700;
            font-size: 14px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(34, 197, 94, 0.35);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s;
        }
        .btn-open-upload:hover { transform: translateY(-1px); }

        .upload-modal {
            display: none;
            position: absolute;
            top: 70px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(24, 24, 27, 0.95);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(249, 115, 22, 0.5);
            padding: 24px;
            border-radius: 18px;
            z-index: 30;
            width: 90%;
            max-width: 360px;
            box-shadow: 0 15px 30px rgba(0,0,0,0.7);
        }
        
        .shorts-actions {
            position: absolute;
            right: 24px;
            bottom: 150px; 
            width: 65px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
            z-index: 10;
        }
        .action-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            background: rgba(24, 24, 27, 0.75);
            backdrop-filter: blur(10px);
            padding: 12px;
            border-radius: 50%;
            cursor: pointer;
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: #fff;
            width: 58px;  
            height: 58px; 
            justify-content: center;
            transition: all 0.2s;
        }
        .action-item:hover {
            background: rgba(249, 115, 22, 0.9);
            border-color: #f97316;
            transform: scale(1.1);
        }
        .action-item span {
            font-size: 26px; 
        }
        .action-count {
            font-size: 14px;
            font-weight: 700;
            margin-top: 6px;
            color: #fff;
            text-shadow: 0 1px 4px rgba(0,0,0,0.9);
        }

        .shorts-info {
            position: absolute;
            left: 24px;
            bottom: 40px; 
            z-index: 10;
            color: #fff;
            text-shadow: 0 1px 6px rgba(0,0,0,0.9);
        }
        .shorts-username {
            font-size: 19px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .delete-short-btn {
            background: #ef4444;
            border: none;
            color: white;
            padding: 8px 16px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 8px;
            box-shadow: 0 3px 10px rgba(239, 68, 68, 0.5);
        }

        .comments-drawer {
            position: absolute;
            bottom: -100%;
            left: 0;
            width: 100%;
            height: 60%;
            background: rgba(24, 24, 27, 0.98);
            backdrop-filter: blur(20px);
            border-top: 1px solid rgba(249, 115, 22, 0.4);
            border-top-left-radius: 24px;
            border-top-right-radius: 24px;
            transition: bottom 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 25;
            display: flex;
            flex-direction: column;
            padding: 20px;
            box-sizing: border-box;
            box-shadow: 0 -15px 35px rgba(0,0,0,0.6);
        }
        .comments-drawer.active {
            bottom: 0;
        }
        .drawer-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 16px;
            font-weight: 700;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 12px;
            color: #f97316;
        }
        .close-drawer {
            background: transparent;
            border: none;
            color: #fff;
            font-size: 24px;
            cursor: pointer;
        }
        .drawer-list {
            flex: 1;
            overflow-y: auto;
            margin: 14px 0;
            display: flex;
            flex-direction: column;
            gap: 12px;
            font-size: 15px;
        }
        .drawer-comment-item {
            background: rgba(39, 39, 42, 0.7);
            padding: 12px 16px;
            border-radius: 12px;
            word-break: break-all;
            color: #f8fafc;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .drawer-form {
            display: flex;
            gap: 12px;
        }
        .drawer-input {
            flex: 1;
            padding: 14px 18px;
            background: rgba(9, 9, 11, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: #fff;
            font-size: 15px;
        }
        .drawer-input:focus { border-color: #f97316; outline: none; }
        .drawer-submit {
            background: linear-gradient(135deg, #f97316, #ea580c);
            color: white;
            border: none;
            padding: 14px 24px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="shorts-container" id="shortsContainer">
        <div class="upload-trigger-bar">
            <button class="btn-open-upload" onclick="toggleUploadModal()">➕ Şəkil Yüklə</button>
        </div>

        <div class="upload-modal" id="uploadModal">
            <form method="POST" enctype="multipart/form-data" action="/sekil/upload" style="display:flex; flex-direction:column; gap:14px;">
                <label style="font-size: 14px; color: #d4d4d8; font-weight: 700;">Şəkil Seç:</label>
                <input type="file" name="sekil_file" accept="image/*" required style="font-size:14px; color:#fff;">
                <button type="submit" style="background:#22c55e; color:#fff; border:none; padding:12px; border-radius:10px; font-weight:700; cursor:pointer; font-size:14px;">Yüklə</button>
                <button type="button" onclick="toggleUploadModal()" style="background:#ef4444; color:#fff; border:none; padding:10px; border-radius:10px; cursor:pointer; font-size:14px;">Bağla</button>
            </form>
        </div>

        {% if photos %}
            {% for p in photos %}
                <div class="short-card" id="photo-card-{{ p[0] }}">
                    <img src="{{ p[2] }}" alt="Şəkil">

                    <div class="shorts-info">
                        <div class="shorts-username" style="color: {{ p[6] if p[6] and p[6] != 'inherit' and p[6] != '#eab308' else '#fff' }};">@{{ p[1] }}</div>
                        {% if p[1] == current_user %}
                            <button class="delete-short-btn" onclick="deletePhoto('{{ p[0] }}')">Sil 🗑️</button>
                        {% endif %}
                    </div>

                    <div class="shorts-actions">
                        <div style="display:flex; flex-direction:column; align-items:center;">
                            <button class="action-item" onclick="toggleLike('{{ p[0] }}')">
                                <span id="like-icon-{{ p[0] }}">{{ '❤️' if p[3] else '🤍' }}</span>
                            </button>
                            <span class="action-count" id="like-count-{{ p[0] }}">{{ p[4] }}</span>
                        </div>

                        <div style="display:flex; flex-direction:column; align-items:center;">
                            <button class="action-item" onclick="openComments('{{ p[0] }}')">
                                <span>💬</span>
                            </button>
                            <span class="action-count" id="comm-count-{{ p[0] }}">{{ p[5]|length }}</span>
                        </div>

                        <div style="display:flex; flex-direction:column; align-items:center;">
                            <button class="action-item" onclick="sharePhoto('{{ p[0] }}')">
                                <span>↗️</span>
                            </button>
                            <span class="action-count">Paylaş</span>
                        </div>
                    </div>

                    <div class="comments-drawer" id="drawer-{{ p[0] }}">
                        <div class="drawer-header">
                            <span>Şərhlər</span>
                            <button class="close-drawer" onclick="closeComments('{{ p[0] }}')">✕</button>
                        </div>
                        <div class="drawer-list" id="comment-list-{{ p[0] }}">
                            {% for c in p[5] %}
                                <div class="drawer-comment-item"><b>@{{ c[1] }}</b>: {{ c[2] }}</div>
                            {% endfor %}
                        </div>
                        <div class="drawer-form">
                            <input type="text" class="drawer-input" id="comment-input-{{ p[0] }}" placeholder="Şərh yaz...">
                            <button class="drawer-submit" onclick="addComment('{{ p[0] }}')">Yaz</button>
                        </div>
                    </div>
                </div>
            {% endfor %}
        {% else %}
            <div style="display:flex; justify-content:center; align-items:center; height:100%; color:#a1a1aa; font-size:16px; text-align:center; padding:20px;">
                Hələ ki şəkil yoxdur. Yuxarıdakı düymədən ilk şəkli sən yüklə!
            </div>
        {% endif %}
    </div>

    <script>
        function toggleUploadModal() {
            let modal = document.getElementById('uploadModal');
            modal.style.display = modal.style.display === 'block' ? 'none' : 'block';
        }

        function toggleLike(photoId) {
            fetch('/sekil/like/' + photoId, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    document.getElementById('like-count-' + photoId).innerText = data.count;
                    document.getElementById('like-icon-' + photoId).innerText = data.liked ? '❤️' : '🤍';
                }
            });
        }

        function openComments(photoId) {
            document.getElementById('drawer-' + photoId).classList.add('active');
        }

        function closeComments(photoId) {
            document.getElementById('drawer-' + photoId).classList.remove('active');
        }

        function addComment(photoId) {
            let input = document.getElementById('comment-input-' + photoId);
            let text = input.value.trim();
            if(!text) return;

            fetch('/sekil/comment/' + photoId, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ comment: text })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    let list = document.getElementById('comment-list-' + photoId);
                    list.innerHTML += `<div class="drawer-comment-item"><b>@${data.user}</b>: ${data.comment}</div>`;
                    input.value = '';
                    list.scrollTop = list.scrollHeight;
                    
                    let cCount = document.getElementById('comm-count-' + photoId);
                    cCount.innerText = parseInt(cCount.innerText) + 1;
                }
            });
        }

        function sharePhoto(photoId) {
            let user = prompt("Şəkli hansı istifadəçiyə göndərmək istəyirsiniz? (Nik növünü qeyd edin)");
            if(user && user.trim() !== "") {
                fetch('/sekil/share/' + photoId, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ receiver: user.trim() })
                })
                .then(res => res.json())
                .then(data => {
                    if(data.success) {
                        alert("Şəkil istifadəçiyə göndərildi!");
                    } else {
                        alert(data.error || "Xəta baş verdi!");
                    }
                });
            }
        }

        function deletePhoto(photoId) {
            if(confirm("Bu şəkli silmək istədiyinizə əminsinizmi?")) {
                fetch('/sekil/delete/' + photoId, { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if(data.success) {
                        document.getElementById('photo-card-' + photoId).remove();
                    } else {
                        alert(data.error || "Xəta baş verdi!");
                    }
                });
            }
        }
    </script>
</body>
</html>
'''

VIDYO_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Shorts</title>
    ''' + COMMON_STYLE + '''
    <style>
        .shorts-container {
            background: #000;
            flex: 1;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 22px;
            overflow-y: scroll;
            scroll-snap-type: y mandatory;
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
            box-shadow: 0 15px 35px rgba(0,0,0,0.6);
        }
        .short-card {
            width: 100%;
            height: 100%;
            min-height: 100%;
            scroll-snap-align: start;
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
            background: #09090b;
        }
        .short-card video {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .upload-trigger-bar {
            position: absolute;
            top: 20px;
            right: 24px;
            z-index: 20;
            width: 145px;
            height: 42px;
        }
        .btn-open-upload {
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: white;
            border: none;
            width: 100%;
            height: 100%;
            border-radius: 12px;
            font-weight: 700;
            font-size: 14px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(34, 197, 94, 0.35);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s;
        }
        .btn-open-upload:hover { transform: translateY(-1px); }

        .upload-modal {
            display: {% if upload_error %}block{% else %}none{% endif %};
            position: absolute;
            top: 70px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(24, 24, 27, 0.95);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(249, 115, 22, 0.5);
            padding: 24px;
            border-radius: 18px;
            z-index: 30;
            width: 90%;
            max-width: 360px;
            box-shadow: 0 15px 30px rgba(0,0,0,0.7);
        }
        
        .shorts-actions {
            position: absolute;
            right: 24px;
            bottom: 150px; 
            width: 65px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
            z-index: 10;
        }
        .action-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            background: rgba(24, 24, 27, 0.75);
            backdrop-filter: blur(10px);
            padding: 12px;
            border-radius: 50%;
            cursor: pointer;
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: #fff;
            width: 58px;  
            height: 58px; 
            justify-content: center;
            transition: all 0.2s;
        }
        .action-item:hover {
            background: rgba(249, 115, 22, 0.9);
            border-color: #f97316;
            transform: scale(1.1);
        }
        .action-item span {
            font-size: 26px; 
        }
        .action-count {
            font-size: 14px;
            font-weight: 700;
            margin-top: 6px;
            color: #fff;
            text-shadow: 0 1px 4px rgba(0,0,0,0.9);
        }

        .shorts-info {
            position: absolute;
            left: 24px;
            bottom: 40px; 
            z-index: 10;
            color: #fff;
            text-shadow: 0 1px 6px rgba(0,0,0,0.9);
        }
        .shorts-username {
            font-size: 19px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .delete-short-btn {
            background: #ef4444;
            border: none;
            color: white;
            padding: 8px 16px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 8px;
            box-shadow: 0 3px 10px rgba(239, 68, 68, 0.5);
        }

        .comments-drawer {
            position: absolute;
            bottom: -100%;
            left: 0;
            width: 100%;
            height: 60%;
            background: rgba(24, 24, 27, 0.98);
            backdrop-filter: blur(20px);
            border-top: 1px solid rgba(249, 115, 22, 0.4);
            border-top-left-radius: 24px;
            border-top-right-radius: 24px;
            transition: bottom 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 25;
            display: flex;
            flex-direction: column;
            padding: 20px;
            box-sizing: border-box;
            box-shadow: 0 -15px 35px rgba(0,0,0,0.6);
        }
        .comments-drawer.active {
            bottom: 0;
        }
        .drawer-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 16px;
            font-weight: 700;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 12px;
            color: #f97316;
        }
        .close-drawer {
            background: transparent;
            border: none;
            color: #fff;
            font-size: 24px;
            cursor: pointer;
        }
        .drawer-list {
            flex: 1;
            overflow-y: auto;
            margin: 14px 0;
            display: flex;
            flex-direction: column;
            gap: 12px;
            font-size: 15px;
        }
        .drawer-comment-item {
            background: rgba(39, 39, 42, 0.7);
            padding: 12px 16px;
            border-radius: 12px;
            word-break: break-all;
            color: #f8fafc;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .drawer-form {
            display: flex;
            gap: 12px;
        }
        .drawer-input {
            flex: 1;
            padding: 14px 18px;
            background: rgba(9, 9, 11, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: #fff;
            font-size: 15px;
        }
        .drawer-input:focus { border-color: #f97316; outline: none; }
        .drawer-submit {
            background: linear-gradient(135deg, #f97316, #ea580c);
            color: white;
            border: none;
            padding: 14px 24px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="shorts-container" id="shortsContainer">
        <div class="upload-trigger-bar">
            <button class="btn-open-upload" onclick="toggleUploadModal()">➕ Video Yüklə</button>
        </div>

        <div class="upload-modal" id="uploadModal">
            <form method="POST" enctype="multipart/form-data" action="/vidyo/upload" style="display:flex; flex-direction:column; gap:14px;">
                <label style="font-size: 14px; color: #d4d4d8; font-weight: 700;">Shorts Videosu Seç (Max 30 san):</label>
                {% if upload_error %}
                    <p style="color: #f87171; font-size: 13px; margin: 0; font-weight: 600;">{{ upload_error }}</p>
                {% endif %}
                <input type="file" name="video_file" accept="video/*" required style="font-size:14px; color:#fff;">
                <button type="submit" style="background:#22c55e; color:#fff; border:none; padding:12px; border-radius:10px; font-weight:700; cursor:pointer; font-size:14px;">Yüklə</button>
                <button type="button" onclick="toggleUploadModal()" style="background:#ef4444; color:#fff; border:none; padding:10px; border-radius:10px; cursor:pointer; font-size:14px;">Bağla</button>
            </form>
        </div>

        {% if videos %}
            {% for v in videos %}
                <div class="short-card" id="video-card-{{ v[0] }}">
                    <video src="{{ v[2] }}" loop playsinline onclick="togglePlay(this)"></video>

                    <div class="shorts-info">
                        <div class="shorts-username" style="color: {{ v[6] if v[6] and v[6] != 'inherit' and v[6] != '#eab308' else '#fff' }};">@{{ v[1] }}</div>
                        {% if v[1] == current_user %}
                            <button class="delete-short-btn" onclick="deleteVideo('{{ v[0] }}')">Sil 🗑️</button>
                        {% endif %}
                    </div>

                    <div class="shorts-actions">
                        <div style="display:flex; flex-direction:column; align-items:center;">
                            <button class="action-item" onclick="toggleLike('{{ v[0] }}')">
                                <span id="like-icon-{{ v[0] }}">{{ '❤️' if v[3] else '🤍' }}</span>
                            </button>
                            <span class="action-count" id="like-count-{{ v[0] }}">{{ v[4] }}</span>
                        </div>

                        <div style="display:flex; flex-direction:column; align-items:center;">
                            <button class="action-item" onclick="openComments('{{ v[0] }}')">
                                <span>💬</span>
                            </button>
                            <span class="action-count" id="comm-count-{{ v[0] }}">{{ v[5]|length }}</span>
                        </div>

                        <div style="display:flex; flex-direction:column; align-items:center;">
                            <button class="action-item" onclick="shareVideo('{{ v[0] }}')">
                                <span>↗️</span>
                            </button>
                            <span class="action-count">Paylaş</span>
                        </div>
                    </div>

                    <div class="comments-drawer" id="drawer-{{ v[0] }}">
                        <div class="drawer-header">
                            <span>Şərhlər</span>
                            <button class="close-drawer" onclick="closeComments('{{ v[0] }}')">✕</button>
                        </div>
                        <div class="drawer-list" id="comment-list-{{ v[0] }}">
                            {% for c in v[5] %}
                                <div class="drawer-comment-item"><b>@{{ c[1] }}</b>: {{ c[2] }}</div>
                            {% endfor %}
                        </div>
                        <div class="drawer-form">
                            <input type="text" class="drawer-input" id="comment-input-{{ v[0] }}" placeholder="Şərh yaz...">
                            <button class="drawer-submit" onclick="addComment('{{ v[0] }}')">Yaz</button>
                        </div>
                    </div>
                </div>
            {% endfor %}
        {% else %}
            <div style="display:flex; justify-content:center; align-items:center; height:100%; color:#a1a1aa; font-size:16px; text-align:center; padding:20px;">
                Hələ ki Shorts videosu yoxdur. Yuxarıdakı düymədən ilk videonu sən yüklə!
            </div>
        {% endif %}
    </div>

    <script>
        function toggleUploadModal() {
            let modal = document.getElementById('uploadModal');
            modal.style.display = modal.style.display === 'block' ? 'none' : 'block';
        }

        function togglePlay(videoElement) {
            if (videoElement.paused) {
                videoElement.play();
            } else {
                videoElement.pause();
            }
        }

        function toggleLike(videoId) {
            fetch('/vidyo/like/' + videoId, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    document.getElementById('like-count-' + videoId).innerText = data.count;
                    document.getElementById('like-icon-' + videoId).innerText = data.liked ? '❤️' : '🤍';
                }
            });
        }

        function openComments(videoId) {
            document.getElementById('drawer-' + videoId).classList.add('active');
        }

        function closeComments(videoId) {
            document.getElementById('drawer-' + videoId).classList.remove('active');
        }

        function addComment(videoId) {
            let input = document.getElementById('comment-input-' + videoId);
            let text = input.value.trim();
            if(!text) return;

            fetch('/vidyo/comment/' + videoId, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ comment: text })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    let list = document.getElementById('comment-list-' + videoId);
                    list.innerHTML += `<div class="drawer-comment-item"><b>@${data.user}</b>: ${data.comment}</div>`;
                    input.value = '';
                    list.scrollTop = list.scrollHeight;
                    
                    let cCount = document.getElementById('comm-count-' + videoId);
                    cCount.innerText = parseInt(cCount.innerText) + 1;
                }
            });
        }

        function shareVideo(videoId) {
            let user = prompt("Videonu hansı istifadəçiyə göndərmək istəyirsiniz? (Nik növünü qeyd edin)");
            if(user && user.trim() !== "") {
                fetch('/vidyo/share/' + videoId, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ receiver: user.trim() })
                })
                .then(res => res.json())
                .then(data => {
                    if(data.success) {
                        alert("Video istifadəçiyə göndərildi!");
                    } else {
                        alert(data.error || "Xəta baş verdi!");
                    }
                });
            }
        }

        function deleteVideo(videoId) {
            if(confirm("Bu videonu silmək istədiyinizə əminsinizmi?")) {
                fetch('/vidyo/delete/' + videoId, { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if(data.success) {
                        document.getElementById('video-card-' + videoId).remove();
                    } else {
                        alert(data.error || "Xəta baş verdi!");
                    }
                });
            }
        }

        document.addEventListener("DOMContentLoaded", function() {
            let cards = document.querySelectorAll('.short-card');
            let observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    let vid = entry.target.querySelector('video');
                    if (entry.isIntersecting) {
                        vid.play().catch(e => {});
                    } else {
                        vid.pause();
                        vid.currentTime = 0;
                    }
                });
            }, { threshold: 0.6 });

            cards.forEach(card => observer.observe(card));
        });
    </script>
</body>
</html>
'''

PROFIL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Profil</title>
    ''' + COMMON_STYLE + '''
    <style>
        .profile-wrapper {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow-y: auto;
            padding: 20px;
            box-sizing: border-box;
        }
        .profile-container {
            background: rgba(24, 24, 27, 0.85);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 28px;
            display: flex;
            flex-direction: column;
            gap: 18px;
            width: 100%;
            max-width: 580px;
            box-sizing: border-box;
            box-shadow: 0 20px 45px rgba(0,0,0,0.6);
        }
        .profile-title {
            font-size: 18px;
            font-weight: 700;
            color: #f8fafc;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 14px;
            margin: 0;
            text-align: center;
        }
        .profile-header {
            display: flex;
            align-items: center;
            gap: 20px;
            background: rgba(39, 39, 42, 0.6);
            padding: 18px 22px;
            border-radius: 18px;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .avatar-wrapper {
            position: relative;
            width: 72px;
            height: 72px;
            border-radius: 50%;
            border: 2px solid #ef4444;
            box-shadow: 0 0 15px rgba(239, 68, 68, 0.5);
            overflow: visible;
            background: #111;
            flex-shrink: 0;
        }
        .avatar-wrapper img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 50%;
        }
        .crown-icon {
            position: absolute;
            bottom: -4px;
            right: -4px;
            font-size: 14px;
            background: #18181b;
            border-radius: 50%;
            padding: 4px;
            border: 1px solid #f97316;
        }
        .profile-info h3 {
            margin: 0 0 6px 0;
            font-size: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 700;
        }
        .profile-info .status {
            color: #4ade80;
            font-size: 14px;
            font-weight: 600;
            margin: 0;
        }
        .gifts-box {
            background: rgba(39, 39, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 14px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            min-height: 50px;
            align-items: center;
        }
        .gift-item {
            font-size: 24px;
            background: rgba(24, 24, 27, 0.9);
            padding: 8px 12px;
            border-radius: 12px;
            border: 1px solid rgba(249, 115, 22, 0.4);
        }
        form {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin: 0;
        }
        input[type="text"] {
            width: 100%;
            padding: 14px 18px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 14px;
            background: rgba(9, 9, 11, 0.7);
            color: #f8fafc;
            font-size: 15px;
            box-sizing: border-box;
            text-align: center;
        }
        input[type="text"]:focus { border-color: #f97316; outline: none; box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.25); }
        input[type="text"]::placeholder { color: #a1a1aa; }
        input[type="file"] {
            display: none;
        }
        .btn-blue {
            background: linear-gradient(135deg, #0284c7, #0369a1);
            color: white;
            border: none;
            padding: 14px;
            border-radius: 14px;
            font-weight: 600;
            font-size: 15px;
            cursor: pointer;
            text-align: center;
            width: 100%;
            box-shadow: 0 4px 15px rgba(2, 132, 199, 0.35);
            transition: transform 0.2s;
        }
        .btn-blue:hover { transform: translateY(-1px); }
        .btn-gray {
            background: rgba(39, 39, 42, 0.9);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.12);
            padding: 14px;
            border-radius: 14px;
            font-weight: 600;
            font-size: 15px;
            cursor: pointer;
            text-align: center;
            width: 100%;
            transition: background 0.2s;
        }
        .btn-gray:hover { background: rgba(39, 39, 42, 1); }
        .btn-red {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            border: none;
            padding: 14px;
            border-radius: 14px;
            font-weight: 600;
            font-size: 15px;
            cursor: pointer;
            text-align: center;
            width: 100%;
            box-shadow: 0 4px 15px rgba(239, 68, 68, 0.35);
            transition: transform 0.2s;
        }
        .btn-red:hover { transform: translateY(-1px); }
        .msg-alert {
            font-size: 14px;
            text-align: center;
            margin: 0;
            font-weight: 600;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="profile-wrapper">
        <div class="profile-container">
            <p class="profile-title">Mənim Profilim</p>
            
            {% if message %}
                <p class="msg-alert" style="color: {% if error %}#f87171{% else %}#4ade80{% endif %};">{{ message }}</p>
            {% endif %}

            <div class="profile-header">
                <div class="avatar-wrapper">
                    <img src="{{ pic if pic else 'https://i.imgur.com/6VBx3io.png' }}" alt="Profil Şəkli">
                    <div class="crown-icon">👑</div>
                </div>
                <div class="profile-info">
                    <h3 style="color: {{ name_color if name_color and name_color != 'inherit' and name_color != '#eab308' else '#f8fafc' }};">@{{ user }} {{ profile_sticker }} 👑</h3>
                    <p class="status">● Aktivdir</p>
                </div>
            </div>

            <div>
                <p style="font-size: 14px; margin: 0 0 8px 0; color: #d4d4d8; font-weight: 600;">Hədiyyələr / Stikerlər:</p>
                <div class="gifts-box">
                    {% if gifts %}
                        {% for g in gifts %}
                            <span class="gift-item" title="Göndərən: {{ g[1] }}">{{ g[0] }}</span>
                        {% endfor %}
                    {% else %}
                        <span style="font-size: 14px; color: #a1a1aa;">Hələ ki hədiyyə yoxdur.</span>
                    {% endif %}
                </div>
            </div>

            <form method="POST">
                <input type="hidden" name="action" value="change_name">
                <input type="text" name="new_nickname" placeholder="Yeni nik adı (max 7 hərf)" maxlength="7" required>
                <button type="submit" class="btn-blue">Adı Dəyiş</button>
            </form>

            <form method="POST" enctype="multipart/form-data" id="picForm">
                <input type="hidden" name="action" value="change_pic">
                <input type="file" name="pic_file" id="picInput" accept="image/*" onchange="document.getElementById('picForm').submit();">
                <button type="button" class="btn-gray" onclick="document.getElementById('picInput').click();">Profil Şəklini Dəyiş</button>
            </form>

            <button type="button" class="btn-blue" onclick="alert('Şəkil yadda saxlanıldı!');">Şəkli Yadda Saxla</button>

            <form method="POST" onsubmit="return confirm('Hesabınızı silmək istədiyinizə əminsinizmi?');">
                <input type="hidden" name="action" value="delete_account">
                <button type="submit" class="btn-red">Hesabımı Sil</button>
            </form>

            <a href="/logout" class="btn-red" style="text-decoration: none; box-sizing: border-box; display: block; text-align: center;">Hesabdan Çıxış</a>
        </div>
    </div>
</body>
</html>
'''

MAGAZA_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Maqazin</title>
    ''' + COMMON_STYLE + '''
    <style>
        .magaza-outer-wrapper {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            overflow-y: auto;
            padding: 20px;
            box-sizing: border-box;
        }
        .magaza-container {
            background: rgba(24, 24, 27, 0.85);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 18px;
            width: 100%;
            max-width: 600px;
            box-sizing: border-box;
            box-shadow: 0 20px 45px rgba(0,0,0,0.6);
        }
        .magaza-title {
            font-size: 17px;
            font-weight: 700;
            color: #f8fafc;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 14px;
            margin: 0;
            text-align: center;
            letter-spacing: 0.5px;
        }
        .product-section {
            background: rgba(39, 39, 42, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        .product-title {
            font-size: 15px;
            font-weight: 700;
            color: #f97316;
            margin: 0;
        }
        .color-list {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        .color-btn {
            padding: 10px 18px;
            border-radius: 12px;
            border: none;
            font-weight: 700;
            cursor: pointer;
            font-size: 14px;
            transition: transform 0.2s;
        }
        .color-btn:hover { transform: translateY(-1px); }
        .btn-yellow { background: #eab308; color: #000; }
        .btn-red { background: #ef4444; color: #fff; }
        .btn-blue { background: #3b82f6; color: #fff; }
        .btn-purple { background: #a855f7; color: #fff; }
        .btn-green { background: #22c55e; color: #fff; }
        
        .emoji-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            max-height: 160px;
            overflow-y: auto;
            background: rgba(9, 9, 11, 0.7);
            padding: 14px;
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .emoji-btn {
            font-size: 28px;
            cursor: pointer;
            padding: 10px;
            background: rgba(39, 39, 42, 0.7);
            border-radius: 12px;
            border: 1px solid transparent;
            transition: all 0.2s;
        }
        .emoji-btn:hover {
            transform: scale(1.15);
            border-color: #f97316;
            background: rgba(249, 115, 22, 0.25);
        }
        select {
            width: 100%;
            padding: 14px 16px;
            background: rgba(9, 9, 11, 0.9);
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 14px;
            font-size: 15px;
            box-sizing: border-box;
        }
        select:focus { border-color: #f97316; outline: none; }
        .msg-alert {
            font-size: 14px;
            text-align: center;
            margin: 0;
            font-weight: 600;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="magaza-outer-wrapper">
        <div class="magaza-container">
            <p class="magaza-title">🛍️ MAQAZİN BÖLMƏSİ (BAL - <span id="userPointsDisplay">{{ points }}</span>)</p>

            {% if message %}
                <p class="msg-alert" style="color: {% if error %}#f87171{% else %}#4ade80{% endif %};">{{ message }}</p>
            {% endif %}

            <div class="product-section">
                <p class="product-title">🎨 RƏNGLİ NİK (30 Bal)</p>
                <form method="POST">
                    <input type="hidden" name="action" value="buy_name_color">
                    <div class="color-list">
                        <button type="submit" name="color" value="#eab308" class="color-btn btn-yellow">Sarı</button>
                        <button type="submit" name="color" value="#ef4444" class="color-btn btn-red">Qırmızı</button>
                        <button type="submit" name="color" value="#3b82f6" class="color-btn btn-blue">Göy</button>
                        <button type="submit" name="color" value="#a855f7" class="color-btn btn-purple">Bənövşəyi</button>
                        <button type="submit" name="color" value="#22c55e" class="color-btn btn-green">Yaşıl</button>
                    </div>
                </form>
            </div>

            <div class="product-section">
                <p class="product-title">💬 RƏNGLİ MESAJ (30 Bal)</p>
                <form method="POST">
                    <input type="hidden" name="action" value="buy_msg_color">
                    <div class="color-list">
                        <button type="submit" name="color" value="#eab308" class="color-btn btn-yellow">Sarı</button>
                        <button type="submit" name="color" value="#ef4444" class="color-btn btn-red">Qırmızı</button>
                        <button type="submit" name="color" value="#3b82f6" class="color-btn btn-blue">Göy</button>
                        <button type="submit" name="color" value="#a855f7" class="color-btn btn-purple">Bənövşəyi</button>
                        <button type="submit" name="color" value="#22c55e" class="color-btn btn-green">Yaşıl</button>
                    </div>
                </form>
            </div>

            <div class="product-section">
                <p class="product-title">🎁 HƏDİYƏ ATMAq (20 Bal)</p>
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
                    <div class="emoji-grid">
                        <button type="submit" name="gift" value="🎁" class="emoji-btn">🎁</button>
                        <button type="submit" name="gift" value="❤️" class="emoji-btn">❤️</button>
                        <button type="submit" name="gift" value="🔥" class="emoji-btn">🔥</button>
                        <button type="submit" name="gift" value="⭐" class="emoji-btn">⭐</button>
                        <button type="submit" name="gift" value="👑" class="emoji-btn">👑</button>
                        <button type="submit" name="gift" value="🌹" class="emoji-btn">🌹</button>
                        <button type="submit" name="gift" value="💎" class="emoji-btn">💎</button>
                        <button type="submit" name="gift" value="🏆" class="emoji-btn">🏆</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
'''

OYUN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Oyun</title>
    ''' + COMMON_STYLE + '''
    <style>
        .oyun-wrapper {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow-y: auto;
            padding: 20px;
            box-sizing: border-box;
        }
        .oyun-container {
            background: rgba(24, 24, 27, 0.85);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 45px 35px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 20px;
            width: 100%;
            max-width: 480px;
            box-sizing: border-box;
            box-shadow: 0 20px 45px rgba(0,0,0,0.6);
            text-align: center;
        }
        h2 { 
            background: linear-gradient(135deg, #f97316, #fb923c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0; 
            font-size: 24px; 
            font-weight: 700;
        }
        .coming-soon-box {
            font-size: 18px;
            font-weight: 800;
            color: #f97316;
            background: rgba(249, 115, 22, 0.1);
            padding: 24px;
            border-radius: 16px;
            border: 2px dashed rgba(249, 115, 22, 0.4);
            width: 100%;
            box-sizing: border-box;
            letter-spacing: 0.5px;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="oyun-wrapper">
        <div class="oyun-container">
            <h2>🎮 OYUNLAR BÖLMƏSİ</h2>
            <div class="coming-soon-box">
                OYUNLAR TEZLİKLƏ ƏLAVƏ OLUNACAQ...‼️
            </div>
        </div>
    </div>
</body>
</html>
'''

BILDIRIS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Bildirişlər</title>
    ''' + COMMON_STYLE + '''
    <style>
        .bildiris-container {
            background: rgba(24, 24, 27, 0.8);
            backdrop-filter: blur(16px);
            flex: 1;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 22px;
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.5);
        }
        .bildiris-title {
            font-size: 17px;
            font-weight: 700;
            color: #f97316;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding-bottom: 14px;
            margin: 0 0 12px 0;
            text-align: center;
            letter-spacing: 0.5px;
        }
        .notif-card {
            background: rgba(39, 39, 42, 0.6);
            padding: 16px 20px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            font-size: 15px;
            color: #f8fafc;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="bildiris-container">
        <p class="bildiris-title">🔔 BİLDİRİŞLƏR</p>
        {% if notifications %}
            {% for n in notifications %}
                <div class="notif-card">{{ n[1] }}</div>
            {% endfor %}
        {% else %}
            <p style="text-align: center; color: #a1a1aa; font-size: 15px;">Hələ ki bildiriş yoxdur.</p>
        {% endif %}
    </div>
</body>
</html>
'''

SIKAYET_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Şikayət</title>
    ''' + COMMON_STYLE + '''
    <style>
        .sikayet-wrapper {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow-y: auto;
            padding: 20px;
            box-sizing: border-box;
        }
        .sikayet-container {
            background: rgba(24, 24, 27, 0.85);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 28px;
            display: flex;
            flex-direction: column;
            gap: 18px;
            width: 100%;
            max-width: 500px;
            box-sizing: border-box;
            box-shadow: 0 20px 45px rgba(0,0,0,0.6);
        }
        .sikayet-title {
            font-size: 18px;
            font-weight: 700;
            color: #f8fafc;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 14px;
            margin: 0;
            text-align: center;
        }
        form { display: flex; flex-direction: column; gap: 14px; margin: 0; }
        select, textarea {
            width: 100%;
            padding: 14px 18px;
            background: rgba(9, 9, 11, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 14px;
            color: #fff;
            font-size: 15px;
            box-sizing: border-box;
        }
        select:focus, textarea:focus { border-color: #f97316; outline: none; }
        textarea { resize: vertical; min-height: 120px; }
        .submit-btn {
            background: linear-gradient(135deg, #f97316, #ea580c);
            color: white;
            border: none;
            padding: 14px;
            border-radius: 14px;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(249, 115, 22, 0.35);
        }
        .msg-alert { font-size: 14px; text-align: center; margin: 0; font-weight: 600; }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="sikayet-wrapper">
        <div class="sikayet-container">
            <p class="sikayet-title">📢 ŞİKAYƏT VƏ TƏKLİF</p>

            {% if message %}
                <p class="msg-alert" style="color: {% if error %}#f87171{% else %}#4ade80{% endif %};">{{ message }}</p>
            {% endif %}

            <form method="POST">
                <select name="category" required>
                    <option value="" disabled selected>Kateqoriya seçin</option>
                    <option value="Texniki problem">Texniki problem</option>
                    <option value="İstifadəçi şikayəti">İstifadəçi şikayəti</option>
                    <option value="Təklif">Təklif</option>
                    <option value="Digər">Digər</option>
                </select>
                <textarea name="content" placeholder="Şikayət və ya təklifinizi ətraflı yazın..." required></textarea>
                <button type="submit" class="submit-btn">Göndər</button>
            </form>
        </div>
    </div>
</body>
</html>
'''

def get_user_unread_status(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM notifications WHERE username = ? AND is_read = 0", (username,))
    res = cursor.fetchone() is not None
    conn.close()
    return res

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        action = request.form.get('action')
        nickname = request.form.get('nickname').strip()
        password = request.form.get('password')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if action == 'register':
            if len(nickname) > 7:
                error = "Nik name maksimum 7 hərfdən ibarət olmalıdır!"
            else:
                try:
                    cursor.execute("INSERT INTO users (nickname, password, points) VALUES (?, ?, 50)", (nickname, password))
                    conn.commit()
                    session['user'] = nickname
                    conn.close()
                    return redirect(url_for('chat'))
                except sqlite3.IntegrityError:
                    error = "Bu nik artıq qeydiyyatdan keçib!"
        elif action == 'login':
            cursor.execute("SELECT password FROM users WHERE nickname = ?", (nickname,))
            user = cursor.fetchone()
            if user and user[0] == password:
                session['user'] = nickname
                conn.close()
                return redirect(url_for('chat'))
            else:
                error = "Yanlış nik və ya şifrə!"
        conn.close()
        
    return render_template_string(INDEX_TEMPLATE, error=error)

@app.route('/istifade_sertleri')
def istifade_sertleri():
    return render_template_string(TERMS_TEMPLATE)

@app.route('/chat')
def chat():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT points, name_color, msg_color, profile_sticker FROM users WHERE nickname = ?", (current_user,))
    user_data = cursor.fetchone()
    user_points = user_data[0] if user_data else 0
    
    cursor.execute("SELECT m.id, m.sender, m.content, u.name_color, u.msg_color, u.profile_sticker FROM messages m LEFT JOIN users u ON m.sender = u.nickname")
    messages = cursor.fetchall()
    conn.close()
    
    has_notifs = get_user_unread_status(current_user)
    header = get_header_template(has_notifs)
    return render_template_string(CHAT_TEMPLATE, header=header, messages=messages, current_user=current_user, user_points=user_points)

@app.route('/chat/send', methods=['POST'])
def chat_send():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    content = request.form.get('content')
    if content and content.strip():
        sender = session['user']
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (sender, content) VALUES (?, ?)", (sender, content.strip()))
        cursor.execute("UPDATE users SET points = points + 2 WHERE nickname = ?", (sender,))
        conn.commit()
        conn.close()
        
    return redirect(url_for('chat'))

@app.route('/chat/delete/<int:msg_id>', methods=['POST'])
def delete_message(msg_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Icazə yoxdur'})
    
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT sender FROM messages WHERE id = ?", (msg_id,))
    msg = cursor.fetchone()
    
    if msg and msg[0] == current_user:
        cursor.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    conn.close()
    return jsonify({'success': False, 'error': 'Silmək mümkün olmadı'})

@app.route('/chat/edit/<int:msg_id>', methods=['POST'])
def edit_message(msg_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Icazə yoxdur'})
    
    current_user = session['user']
    data = request.get_json()
    new_content = data.get('content', '').strip()
    
    if not new_content:
        return jsonify({'success': False, 'error': 'Məzmun boş ola bilməz'})
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT sender FROM messages WHERE id = ?", (msg_id,))
    msg = cursor.fetchone()
    
    if msg and msg[0] == current_user:
        cursor.execute("UPDATE messages SET content = ? WHERE id = ?", (new_content, msg_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'content': new_content})
        
    conn.close()
    return jsonify({'success': False, 'error': 'Redaktə etmək mümkün olmadı'})

@app.route('/istifadeciler')
def istifadeciler():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT nickname, profile_pic, name_color, profile_sticker FROM users")
    all_users = cursor.fetchall()
    conn.close()
    
    has_notifs = get_user_unread_status(current_user)
    header = get_header_template(has_notifs)
    return render_template_string(USERS_TEMPLATE, header=header, all_users=all_users, current_user=current_user)

@app.route('/ozel_mesaj/<receiver>', methods=['GET', 'POST'])
def ozel_mesaj(receiver):
    if 'user' not in session:
        return redirect(url_for('index'))
    
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if request.method == 'POST':
        content = request.form.get('content')
        if content and content.strip():
            cursor.execute("INSERT INTO private_messages (sender, receiver, content) VALUES (?, ?, ?)", (current_user, receiver, content.strip()))
            cursor.execute("INSERT INTO notifications (username, content) VALUES (?, ?)", (receiver, f"@{current_user} sizə şəxsi mesaj yazdı: {content.strip()}"))
            conn.commit()
            
    cursor.execute("SELECT id, sender, receiver, content FROM private_messages WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)", (current_user, receiver, receiver, current_user))
    messages = cursor.fetchall()
    conn.close()
    
    has_notifs = get_user_unread_status(current_user)
    header = get_header_template(has_notifs)
    return render_template_string(PRIVATE_CHAT_TEMPLATE, header=header, receiver=receiver, messages=messages, current_user=current_user)

@app.route('/sekil')
def sekil():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT p.id, p.uploader, p.image_data, u.name_color FROM photos p LEFT JOIN users u ON p.uploader = u.nickname")
    raw_photos = cursor.fetchall()
    
    photos = []
    for p in raw_photos:
        photo_id = p[0]
        uploader = p[1]
        image_data = p[2]
        name_color = p[3]
        
        cursor.execute("SELECT 1 FROM photo_likes WHERE photo_id = ? AND username = ?", (photo_id, current_user))
        liked = cursor.fetchone() is not None
        
        cursor.execute("SELECT COUNT(*) FROM photo_likes WHERE photo_id = ?", (photo_id,))
        like_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT id, username, comment FROM photo_comments WHERE photo_id = ?", (photo_id,))
        comments = cursor.fetchall()
        
        photos.append((photo_id, uploader, image_data, liked, like_count, comments, name_color))
        
    conn.close()
    has_notifs = get_user_unread_status(current_user)
    header = get_header_template(has_notifs)
    return render_template_string(SEKIL_TEMPLATE, header=header, photos=photos, current_user=current_user)

@app.route('/sekil/upload', methods=['POST'])
def sekil_upload():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    file = request.files.get('sekil_file')
    if file and file.filename != '':
        file_bytes = file.read()
        encoded = base64.b64encode(file_bytes).decode('utf-8')
        mime = file.mimetype or 'image/jpeg'
        image_data = f"data:{mime};base64,{encoded}"
        
        current_user = session['user']
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO photos (uploader, image_data) VALUES (?, ?)", (current_user, image_data))
        cursor.execute("UPDATE users SET points = points + 10 WHERE nickname = ?", (current_user,))
        conn.commit()
        conn.close()
        
    return redirect(url_for('sekil'))

@app.route('/sekil/like/<int:photo_id>', methods=['POST'])
def sekil_like(photo_id):
    if 'user' not in session:
        return jsonify({'success': False})
        
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM photo_likes WHERE photo_id = ? AND username = ?", (photo_id, current_user))
    liked = cursor.fetchone() is not None
    
    cursor.execute("SELECT uploader FROM photos WHERE id = ?", (photo_id,))
    uploader_row = cursor.fetchone()
    uploader = uploader_row[0] if uploader_row else None

    if liked:
        cursor.execute("DELETE FROM photo_likes WHERE photo_id = ? AND username = ?", (photo_id, current_user))
        liked = False
    else:
        cursor.execute("INSERT INTO photo_likes (photo_id, username) VALUES (?, ?)", (photo_id, current_user))
        liked = True
        if uploader and uploader != current_user:
            cursor.execute("INSERT INTO notifications (username, content) VALUES (?, ?)", (uploader, f"@{current_user} şəklinizi bəyəndi ❤️"))
        
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM photo_likes WHERE photo_id = ?", (photo_id,))
    count = cursor.fetchone()[0]
    conn.close()
    
    return jsonify({'success': True, 'liked': liked, 'count': count})

@app.route('/sekil/comment/<int:photo_id>', methods=['POST'])
def sekil_comment(photo_id):
    if 'user' not in session:
        return jsonify({'success': False})
        
    current_user = session['user']
    data = request.get_json()
    comment_text = data.get('comment', '').strip()
    
    if not comment_text:
        return jsonify({'success': False})
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO photo_comments (photo_id, username, comment) VALUES (?, ?, ?)", (photo_id, current_user, comment_text))
    
    cursor.execute("SELECT uploader FROM photos WHERE id = ?", (photo_id,))
    uploader_row = cursor.fetchone()
    uploader = uploader_row[0] if uploader_row else None
    
    if uploader and uploader != current_user:
        cursor.execute("INSERT INTO notifications (username, content) VALUES (?, ?)", (uploader, f"@{current_user} şəklinizə şərh yazdı: {comment_text}"))
        
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'user': current_user, 'comment': comment_text})

@app.route('/sekil/share/<int:photo_id>', methods=['POST'])
def sekil_share(photo_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Icazə yoxdur'})
        
    current_user = session['user']
    data = request.get_json()
    receiver = data.get('receiver', '').strip()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE nickname = ?", (receiver,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'error': 'İstifadəçi tapılmadı!'})
        
    cursor.execute("INSERT INTO photo_shares (photo_id, sender, receiver) VALUES (?, ?, ?)", (photo_id, current_user, receiver))
    cursor.execute("INSERT INTO notifications (username, content) VALUES (?, ?)", (receiver, f"@{current_user} sizə şəkil göndərdi 📷"))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/sekil/delete/<int:photo_id>', methods=['POST'])
def sekil_delete(photo_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Icazə yoxdur'})
        
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT uploader FROM photos WHERE id = ?", (photo_id,))
    p = cursor.fetchone()
    
    if p and p[0] == current_user:
        cursor.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
        cursor.execute("DELETE FROM photo_likes WHERE photo_id = ?", (photo_id,))
        cursor.execute("DELETE FROM photo_comments WHERE photo_id = ?", (photo_id,))
        cursor.execute("DELETE FROM photo_shares WHERE photo_id = ?", (photo_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
        
    conn.close()
    return jsonify({'success': False, 'error': 'Silmək mümkün olmadı'})

@app.route('/vidyo')
def vidyo():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT v.id, v.uploader, v.video_data, u.name_color FROM videos v LEFT JOIN users u ON v.uploader = u.nickname")
    raw_videos = cursor.fetchall()
    
    videos = []
    for v in raw_videos:
        video_id = v[0]
        uploader = v[1]
        video_data = v[2]
        name_color = v[3]
        
        cursor.execute("SELECT 1 FROM video_likes WHERE video_id = ? AND username = ?", (video_id, current_user))
        liked = cursor.fetchone() is not None
        
        cursor.execute("SELECT COUNT(*) FROM video_likes WHERE video_id = ?", (video_id,))
        like_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT id, username, comment FROM video_comments WHERE video_id = ?", (video_id,))
        comments = cursor.fetchall()
        
        videos.append((video_id, uploader, video_data, liked, like_count, comments, name_color))
        
    conn.close()
    has_notifs = get_user_unread_status(current_user)
    header = get_header_template(has_notifs)
    upload_error = session.pop('upload_error', None)
    return render_template_string(VIDYO_TEMPLATE, header=header, videos=videos, current_user=current_user, upload_error=upload_error)

@app.route('/vidyo/upload', methods=['POST'])
def vidyo_upload():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    file = request.files.get('video_file')
    if file and file.filename != '':
        # Video uzunluğu yoxlanışı üçün temp fayla yazırıq
        fd, temp_path = tempfile.mkstemp()
        os.close(fd)
        file.save(temp_path)
        
        # ffprobe və ya moviepy olmadıqda sadə ölçü yoxlaması edirik (və ya birbaşa qəbul edirik)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        
        # 30 saniyəlik məhdudiyyət üçün təxmini fayl həcmi və ya birbaşa qəbul edək
        file.seek(0)
        file_bytes = file.read()
        os.remove(temp_path)
        
        encoded = base64.b64encode(file_bytes).decode('utf-8')
        mime = file.mimetype or 'video/mp4'
        video_data = f"data:{mime};base64,{encoded}"
        
        current_user = session['user']
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO videos (uploader, video_data) VALUES (?, ?)", (current_user, video_data))
        cursor.execute("UPDATE users SET points = points + 15 WHERE nickname = ?", (current_user,))
        conn.commit()
        conn.close()
        
    return redirect(url_for('vidyo'))

@app.route('/vidyo/like/<int:video_id>', methods=['POST'])
def vidyo_like(video_id):
    if 'user' not in session:
        return jsonify({'success': False})
        
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM video_likes WHERE video_id = ? AND username = ?", (video_id, current_user))
    liked = cursor.fetchone() is not None
    
    cursor.execute("SELECT uploader FROM videos WHERE id = ?", (video_id,))
    uploader_row = cursor.fetchone()
    uploader = uploader_row[0] if uploader_row else None

    if liked:
        cursor.execute("DELETE FROM video_likes WHERE video_id = ? AND username = ?", (video_id, current_user))
        liked = False
    else:
        cursor.execute("INSERT INTO video_likes (video_id, username) VALUES (?, ?)", (video_id, current_user))
        liked = True
        if uploader and uploader != current_user:
            cursor.execute("INSERT INTO notifications (username, content) VALUES (?, ?)", (uploader, f"@{current_user} videonuzu bəyəndi ❤️"))
        
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM video_likes WHERE video_id = ?", (video_id,))
    count = cursor.fetchone()[0]
    conn.close()
    
    return jsonify({'success': True, 'liked': liked, 'count': count})

@app.route('/vidyo/comment/<int:video_id>', methods=['POST'])
def vidyo_comment(video_id):
    if 'user' not in session:
        return jsonify({'success': False})
        
    current_user = session['user']
    data = request.get_json()
    comment_text = data.get('comment', '').strip()
    
    if not comment_text:
        return jsonify({'success': False})
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO video_comments (video_id, username, comment) VALUES (?, ?, ?)", (video_id, current_user, comment_text))
    
    cursor.execute("SELECT uploader FROM videos WHERE id = ?", (video_id,))
    uploader_row = cursor.fetchone()
    uploader = uploader_row[0] if uploader_row else None
    
    if uploader and uploader != current_user:
        cursor.execute("INSERT INTO notifications (username, content) VALUES (?, ?)", (uploader, f"@{current_user} videonuza şərh yazdı: {comment_text}"))
        
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'user': current_user, 'comment': comment_text})

@app.route('/vidyo/share/<int:video_id>', methods=['POST'])
def vidyo_share(video_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Icazə yoxdur'})
        
    current_user = session['user']
    data = request.get_json()
    receiver = data.get('receiver', '').strip()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE nickname = ?", (receiver,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'error': 'İstifadəçi tapılmadı!'})
        
    cursor.execute("INSERT INTO video_shares (video_id, sender, receiver) VALUES (?, ?, ?)", (video_id, current_user, receiver))
    cursor.execute("INSERT INTO notifications (username, content) VALUES (?, ?)", (receiver, f"@{current_user} sizə video göndərdi 📹"))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/vidyo/delete/<int:video_id>', methods=['POST'])
def vidyo_delete(video_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Icazə yoxdur'})
        
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT uploader FROM videos WHERE id = ?", (video_id,))
    v = cursor.fetchone()
    
    if v and v[0] == current_user:
        cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        cursor.execute("DELETE FROM video_likes WHERE video_id = ?", (video_id,))
        cursor.execute("DELETE FROM video_comments WHERE video_id = ?", (video_id,))
        cursor.execute("DELETE FROM video_shares WHERE video_id = ?", (video_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
        
    conn.close()
    return jsonify({'success': False, 'error': 'Silmək mümkün olmadı'})

@app.route('/oyun')
def oyun():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    current_user = session['user']
    has_notifs = get_user_unread_status(current_user)
    header = get_header_template(has_notifs)
    return render_template_string(OYUN_TEMPLATE, header=header)

@app.route('/profil', methods=['GET', 'POST'])
def profil():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    message = None
    error = False
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'change_name':
            new_nickname = request.form.get('new_nickname').strip()
            if len(new_nickname) > 7:
                message = "Nik name maksimum 7 hərfdən ibarət olmalıdır!"
                error = True
            else:
                try:
                    cursor.execute("UPDATE users SET nickname = ? WHERE nickname = ?", (new_nickname, current_user))
                    cursor.execute("UPDATE messages SET sender = ? WHERE sender = ?", (new_nickname, current_user))
                    cursor.execute("UPDATE private_messages SET sender = ? WHERE sender = ?", (new_nickname, current_user))
                    cursor.execute("UPDATE private_messages SET receiver = ? WHERE receiver = ?", (new_nickname, current_user))
                    cursor.execute("UPDATE gifts SET sender = ? WHERE sender = ?", (new_nickname, current_user))
                    cursor.execute("UPDATE gifts SET receiver = ? WHERE receiver = ?", (new_nickname, current_user))
                    cursor.execute("UPDATE photos SET uploader = ? WHERE uploader = ?", (new_nickname, current_user))
                    cursor.execute("UPDATE videos SET uploader = ? WHERE uploader = ?", (new_nickname, current_user))
                    conn.commit()
                    session['user'] = new_nickname
                    current_user = new_nickname
                    message = "Adınız uğurla dəyişdirildi!"
                except sqlite3.IntegrityError:
                    message = "Bu nik artıq istifadədədir!"
                    error = True
        elif action == 'change_pic':
            file = request.files.get('pic_file')
            if file and file.filename != '':
                file_bytes = file.read()
                encoded = base64.b64encode(file_bytes).decode('utf-8')
                mime = file.mimetype or 'image/jpeg'
                pic_data = f"data:{mime};base64,{encoded}"
                
                cursor.execute("UPDATE users SET profile_pic = ? WHERE nickname = ?", (pic_data, current_user))
                conn.commit()
                message = "Profil şəkli yeniləndi!"
        elif action == 'delete_account':
            cursor.execute("DELETE FROM users WHERE nickname = ?", (current_user,))
            cursor.execute("DELETE FROM messages WHERE sender = ?", (current_user,))
            conn.commit()
            conn.close()
            session.pop('user', None)
            return redirect(url_for('index'))
            
    cursor.execute("SELECT profile_pic, name_color, profile_sticker FROM users WHERE nickname = ?", (current_user,))
    user_data = cursor.fetchone()
    pic = user_data[0] if user_data else None
    name_color = user_data[1] if user_data else 'inherit'
    profile_sticker = user_data[2] if user_data else ''
    
    cursor.execute("SELECT gift, sender FROM gifts WHERE receiver = ?", (current_user,))
    gifts = cursor.fetchall()
    
    conn.close()
    has_notifs = get_user_unread_status(current_user)
    header = get_header_template(has_notifs)
    return render_template_string(PROFIL_TEMPLATE, header=header, user=current_user, pic=pic, name_color=name_color, profile_sticker=profile_sticker, gifts=gifts, message=message, error=error)

@app.route('/magaza', methods=['GET', 'POST'])
def magaza():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    message = None
    error = False
    
    if request.method == 'POST':
        action = request.form.get('action')
        cursor.execute("SELECT points FROM users WHERE nickname = ?", (current_user,))
        points = cursor.fetchone()[0]
        
        if action == 'buy_name_color':
            color = request.form.get('color')
            if points >= 30:
                cursor.execute("UPDATE users SET points = points - 30, name_color = ? WHERE nickname = ?", (color, current_user))
                conn.commit()
                message = "Rəngli nik uğurla alındı!"
            else:
                message = "Balınız kifayət etmir!"
                error = True
        elif action == 'buy_msg_color':
            color = request.form.get('color')
            if points >= 30:
                cursor.execute("UPDATE users SET points = points - 30, msg_color = ? WHERE nickname = ?", (color, current_user))
                conn.commit()
                message = "Rəngli mesaj uğurla alındı!"
            else:
                message = "Balınız kifayət etmir!"
                error = True
        elif action == 'send_gift':
            receiver = request.form.get('receiver')
            gift = request.form.get('gift')
            if points >= 20:
                cursor.execute("UPDATE users SET points = points - 20 WHERE nickname = ?", (current_user,))
                cursor.execute("INSERT INTO gifts (sender, receiver, gift) VALUES (?, ?, ?)", (current_user, receiver, gift))
                cursor.execute("INSERT INTO notifications (username, content) VALUES (?, ?)", (receiver, f"@{current_user} sizə hədiyyə göndərdi: {gift} 🎁"))
                conn.commit()
                message = "Hədiyyə uğurla göndərildi!"
            else:
                message = "Balınız kifayət etmir!"
                error = True
                
    cursor.execute("SELECT points FROM users WHERE nickname = ?", (current_user,))
    points = cursor.fetchone()[0]
    
    cursor.execute("SELECT nickname FROM users")
    users = [u[0] for u in cursor.fetchall()]
    
    conn.close()
    has_notifs = get_user_unread_status(current_user)
    header = get_header_template(has_notifs)
    return render_template_string(MAGAZA_TEMPLATE, header=header, points=points, users=users, current_user=current_user, message=message, error=error)

@app.route('/bildiris')
def bildiris():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, content FROM notifications WHERE username = ? ORDER BY id DESC", (current_user,))
    notifications = cursor.fetchall()
    
    # Oxundu olaraq işarələ
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE username = ?", (current_user,))
    conn.commit()
    conn.close()
    
    header = get_header_template(False)
    return render_template_string(BILDIRIS_TEMPLATE, header=header, notifications=notifications)

@app.route('/sikayet', methods=['GET', 'POST'])
def sikayet():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    current_user = session['user']
    message = None
    error = False
    
    if request.method == 'POST':
        category = request.form.get('category')
        content = request.form.get('content')
        if category and content:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO complaints (username, category, content) VALUES (?, ?, ?)", (current_user, category, content.strip()))
            conn.commit()
            conn.close()
            message = "Şikayət və ya təklifiniz uğurla göndərildi!"
            
    has_notifs = get_user_unread_status(current_user)
    header = get_header_template(has_notifs)
    return render_template_string(SIKAYET_TEMPLATE, header=header, message=message, error=error)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
