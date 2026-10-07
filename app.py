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

    # CANLI YAYIM CƏDVƏLİ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            host TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    ''')

    # CANLI HƏDİYƏLƏRİ CƏDVƏLİ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS live_gifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            live_id INTEGER,
            sender TEXT,
            gift TEXT
        )
    ''')

    # CANLI MESAJLARI CƏDVƏLİ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS live_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            live_id INTEGER,
            sender TEXT,
            content TEXT
        )
    ''')

    # CANLI BƏYƏNMƏLƏR CƏDVƏLİ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS live_likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            live_id INTEGER,
            username TEXT
        )
    ''')

    # POLİS SİSTEMİ CƏDVƏLLƏRİ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS police_officers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            regiment TEXT NOT NULL,
            role TEXT DEFAULT 'Police'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS court_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            accused_user TEXT NOT NULL,
            reason TEXT NOT NULL,
            verdict TEXT DEFAULT 'Araşdırılır',
            judge TEXT DEFAULT 'Sayt Rəhbərliyi'
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
            <span class="icon">👥</span>
            <span>İstifadəçilər</span>
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
            <span class="icon">🛍</span>
            <span>Maqazin</span>
        </a>
        <a href="/profil" class="nav-item">
            <span class="icon">👤</span>
            <span>Profil</span>
        </a>
        <a href="/canli" class="nav-item">
            <span class="icon">🔴</span>
            <span>Canlı</span>
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
        <a href="/idare_merkezi" class="nav-item">
            <span class="icon">🛡️</span>
            <span>İDARƏ MƏRKƏZİ</span>
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
                        
                        {% if m[1] == current_user or is_admin %}
                            <div class="msg-actions">
                                {% if m[1] == current_user %}
                                    <button onclick="editMessage('{{ m[0] }}')">Redaktə et</button>
                                {% endif %}
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

OYUN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Sual-Cavab Oyunu</title>
    ''' + COMMON_STYLE + '''
    <style>
        .game-wrapper {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 20px;
            box-sizing: border-box;
        }
        .game-card {
            background: rgba(24, 24, 27, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 35px;
            width: 100%;
            max-width: 550px;
            box-shadow: 0 20px 45px rgba(0,0,0,0.7);
            text-align: center;
            box-sizing: border-box;
        }
        .timer-box {
            font-size: 24px;
            font-weight: 800;
            color: #ef4444;
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            padding: 10px 20px;
            border-radius: 14px;
            display: inline-block;
            margin-bottom: 20px;
        }
        .question-text {
            font-size: 20px;
            font-weight: 700;
            color: #f8fafc;
            margin-bottom: 20px;
            line-height: 1.5;
        }
        .hint-text {
            font-size: 15px;
            color: #fb923c;
            margin-bottom: 25px;
            font-weight: 600;
            background: rgba(249, 115, 22, 0.1);
            padding: 10px;
            border-radius: 10px;
            border: 1px solid rgba(249, 115, 22, 0.2);
        }
        input[type="text"] {
            width: 100%;
            padding: 15px 20px;
            background: rgba(9, 9, 11, 0.8);
            border: 1px solid #f97316;
            border-radius: 14px;
            color: #fff;
            font-size: 16px;
            box-sizing: border-box;
            margin-bottom: 15px;
            text-align: center;
        }
        input[type="text"]:focus { outline: none; box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.3); }
        .game-btn {
            background: linear-gradient(135deg, #f97316, #ea580c);
            color: white;
            border: none;
            width: 100%;
            padding: 15px;
            border-radius: 14px;
            font-weight: 700;
            font-size: 16px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(249, 115, 22, 0.35);
            transition: transform 0.2s;
        }
        .game-btn:hover { transform: translateY(-2px); }
        .score-badge {
            margin-top: 20px;
            font-size: 16px;
            font-weight: 700;
            color: #4ade80;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="game-wrapper">
        <div class="game-card">
            <h2 style="color: #f97316; margin-top: 0; font-size: 22px;">🎮 SUAL-CAVAB OYUNU</h2>
            
            {% if not question %}
                <form method="POST">
                    <p style="color: #d4d4d8; font-size: 15px; margin-bottom: 20px;">Oynamaq istədiyiniz mövzunu qeyd edin (məsələn: Tarix, Coğrafiya, İdman, Elm və s.):</p>
                    <input type="text" name="topic" placeholder="Mövzu daxil edin..." required autocomplete="off">
                    <button type="submit" class="game-btn">Oyuna Başla 🚀</button>
                </form>
            {% else %}
                <div class="timer-box" id="timer">30</div>
                <p class="question-text">❓ {{ question }}</p>
                <div class="hint-text">💡 İpucu: {{ hint }}</div>

                <form method="POST" action="/oyun/cavabla" id="answerForm">
                    <input type="hidden" name="correct_answer" value="{{ answer }}">
                    <input type="hidden" name="topic" value="{{ topic }}">
                    <input type="text" name="user_answer" placeholder="Cavabınızı yazın..." required autocomplete="off" autofocus>
                    <button type="submit" class="game-btn">Cavabı Göndər (Düzgün cavab: +5 bal)</button>
                </form>

                <p class="score-badge">Seçilən Mövzu: {{ topic }}</p>

                <script>
                    let timeLeft = 30;
                    let timerElement = document.getElementById('timer');
                    let countdown = setInterval(function() {
                        timeLeft--;
                        timerElement.innerText = timeLeft;
                        if(timeLeft <= 0) {
                            clearInterval(countdown);
                            alert("Vaxt bitdi! Növbəti suala keçilir.");
                            window.location.href = "/oyun?topic={{ topic }}";
                        }
                    }, 1000);
                </script>
            {% endif %}
            
            {% if message %}
                <p style="margin-top: 15px; font-weight: 700; color: {% if success %}#4ade80{% else %}#f87171{% endif %};">{{ message }}</p>
            {% endif %}
        </div>
    </div>
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
        .user-right-actions {
            display: flex;
            gap: 10px;
            align-items: center;
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
        .admin-action-btn {
            background: #ef4444;
            color: white;
            border: none;
            padding: 10px 14px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 14px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .admin-action-btn:hover {
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
                <div class="user-card" id="user-row-{{ u[0] }}">
                    <div class="user-left">
                        <img src="{{ u[1] if u[1] else 'https://i.imgur.com/6VBx3io.png' }}" class="user-avatar" alt="Profil">
                        <div>
                            <p class="user-name" style="color: {{ u[2] if u[2] and u[2] != 'inherit' and u[2] != '#eab308' else '#f8fafc' }};">@{{ u[0] }} {{ u[3] }}</p>
                            <p class="user-status">● Aktivdir</p>
                        </div>
                    </div>
                    <div class="user-right-actions">
                        {% if u[0] != current_user %}
                            <a href="/ozel_mesaj/{{ u[0] }}" class="msg-btn">💬 MESAJ YAZ</a>
                            {% if is_admin %}
                                <button class="admin-action-btn" onclick="deleteUserAccount('{{ u[0] }}')">Sil / Bloka at</button>
                            {% endif %}
                        {% endif %}
                    </div>
                </div>
            {% endfor %}
        {% else %}
            <p style="text-align: center; color: #a1a1aa; font-size: 15px;">Hələ ki qeydiyyatdan keçmiş istifadəçi yoxdur.</p>
        {% endif %}
    </div>

    <script>
        function deleteUserAccount(username) {
            if(confirm("@" + username + " istifadəçisini bloka atmaq və silmək istədiyinizə əminsinizmi?")) {
                fetch('/admin/delete_user/' + username, { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if(data.success) {
                        document.getElementById('user-row-' + username).remove();
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
                        {% if v[1] == current_user or is_admin %}
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
        .btn-admin {
            background: linear-gradient(135deg, #f97316, #ea580c);
            color: white;
            border: none;
            padding: 14px;
            border-radius: 14px;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            text-align: center;
            width: 100%;
            text-decoration: none;
            box-sizing: border-box;
            box-shadow: 0 4px 15px rgba(249, 115, 22, 0.35);
        }
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

            {% if is_admin %}
                <a href="/admin/sikayetler" class="btn-admin">⚙ Şikayət İdarəetmə Paneli (Admin)</a>
            {% endif %}

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

# CANLI SƏHİFƏSİ TEMPLATE-İ
CANLI_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Canlı Yayım</title>
    ''' + COMMON_STYLE + '''
    <style>
        .live-wrapper {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 20px;
            overflow-y: auto;
            box-sizing: border-box;
        }
        .live-top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(24, 24, 27, 0.85);
            padding: 16px 24px;
            border-radius: 18px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .btn-start-live {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4);
            transition: transform 0.2s;
        }
        .btn-start-live:hover { transform: translateY(-1px); }
        
        .active-lives-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
        }
        .live-card {
            background: rgba(24, 24, 27, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            position: relative;
        }
        .live-badge {
            position: absolute;
            top: 15px;
            right: 15px;
            background: #ef4444;
            color: #fff;
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 800;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .btn-join-live {
            background: linear-gradient(135deg, #f97316, #ea580c);
            color: white;
            border: none;
            padding: 12px;
            border-radius: 12px;
            font-weight: 700;
            text-align: center;
            text-decoration: none;
            display: block;
            box-shadow: 0 4px 12px rgba(249, 115, 22, 0.3);
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="live-wrapper">
        <div class="live-top-bar">
            <div>
                <h2 style="margin: 0; color: #f97316; font-size: 20px;">🔴 CANLI YAYIMLAR</h2>
                <p style="margin: 4px 0 0 0; color: #a1a1aa; font-size: 14px;">Canlı açmaq üçün balansınızda ən azı 60 bal olmalıdır.</p>
            </div>
            <form method="POST" action="/canli/ac" style="margin:0;">
                <button type="submit" class="btn-start-live">🎥 CANLI AÇ (60 Bal)</button>
            </form>
        </div>

        {% if error %}
            <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); color: #f87171; padding: 14px 20px; border-radius: 14px; font-weight: 600; text-align: center;">
                {{ error }}
            </div>
        {% endif %}

        <div class="active-lives-grid">
            {% if lives %}
                {% for l in lives %}
                    <div class="live-card">
                        <span class="live-badge">CANLI</span>
                        <div style="display: flex; align-items: center; gap: 14px;">
                            <img src="{{ l[2] if l[2] else 'https://i.imgur.com/6VBx3io.png' }}" style="width: 50px; height: 50px; border-radius: 50%; border: 2px solid #f97316; object-fit: cover;">
                            <div>
                                <h3 style="margin: 0; font-size: 18px; color: #f8fafc;">@{{ l[1] }}</h3>
                                <p style="margin: 4px 0 0 0; color: #4ade80; font-size: 13px; font-weight: 600;">Canlı yayım davam edir...</p>
                            </div>
                        </div>
                        <a href="/canli/izle/{{ l[0] }}" class="btn-join-live">Canlıya Bax 📺</a>
                    </div>
                {% endfor %}
            {% else %}
                <div style="grid-column: 1 / -1; text-align: center; color: #a1a1aa; padding: 40px; font-size: 16px;">
                    Hazırda aktiv canlı yayım yoxdur. İlk canlıyı sən aç!
                </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

# CANLI Otağı (Kamera, Söhbət, Bəyənmə və Hədiyyələr daxil olmaqla)
CANLI_ROOM_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Canlı Yayım Otağı</title>
    ''' + COMMON_STYLE + '''
    <style>
        .room-container {
            flex: 1;
            background: rgba(24, 24, 27, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 22px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 15px 35px rgba(0,0,0,0.6);
            position: relative;
        }
        .room-header {
            background: rgba(9, 9, 11, 0.9);
            padding: 14px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            z-index: 10;
        }
        .stream-viewport {
            flex: 1;
            position: relative;
            background: #000;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }
        #webcamVideo {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transform: scaleX(-1);
        }
        .viewer-placeholder {
            font-size: 22px;
            color: #fff;
            text-align: center;
            font-weight: 700;
            background: rgba(0,0,0,0.6);
            padding: 20px;
            border-radius: 16px;
        }
        .live-likes-counter {
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 8px 16px;
            border-radius: 14px;
            font-size: 16px;
            font-weight: 800;
            color: #ef4444;
            z-index: 5;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .live-chat-overlay {
            position: absolute;
            bottom: 20px;
            left: 20px;
            width: 320px;
            height: 200px;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            z-index: 5;
            pointer-events: none;
        }
        .live-messages-list {
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 8px;
            max-height: 160px;
            padding-right: 10px;
            pointer-events: auto;
        }
        .live-msg-bubble {
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(8px);
            padding: 8px 12px;
            border-radius: 10px;
            font-size: 13px;
            color: #fff;
            word-break: break-all;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .live-chat-form {
            display: flex;
            gap: 8px;
            margin-top: 8px;
            pointer-events: auto;
        }
        .live-chat-input {
            flex: 1;
            padding: 8px 12px;
            background: rgba(0, 0, 0, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            color: #fff;
            font-size: 13px;
        }
        .live-chat-submit {
            background: #f97316;
            color: #fff;
            border: none;
            padding: 0 14px;
            border-radius: 10px;
            font-weight: 700;
            cursor: pointer;
            font-size: 13px;
        }
        .floating-like-btn {
            position: absolute;
            bottom: 25px;
            right: 25px;
            background: rgba(239, 68, 68, 0.9);
            border: 2px solid #fff;
            width: 65px;
            height: 65px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 30px;
            cursor: pointer;
            z-index: 10;
            box-shadow: 0 6px 20px rgba(239, 68, 68, 0.6);
            transition: transform 0.1s;
        }
        .floating-like-btn:active {
            transform: scale(0.85);
        }
        .gifts-bar {
            background: rgba(9, 9, 11, 0.9);
            padding: 14px 20px;
            display: flex;
            justify-content: center;
            gap: 12px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            flex-wrap: wrap;
            z-index: 10;
        }
        .gift-btn {
            background: rgba(39, 39, 42, 0.9);
            border: 1px solid rgba(249, 115, 22, 0.4);
            font-size: 24px;
            padding: 8px 12px;
            border-radius: 12px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .gift-btn:hover { transform: scale(1.15); }
        .btn-end-stream {
            background: #ef4444;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 10px;
            font-weight: 700;
            cursor: pointer;
            font-size: 13px;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="room-container">
        <div class="room-header">
            <div style="display: flex; align-items: center; gap: 12px;">
                <img src="{{ host_pic if host_pic else 'https://i.imgur.com/6VBx3io.png' }}" style="width: 40px; height: 40px; border-radius: 50%; border: 2px solid #ef4444; object-fit: cover;">
                <div>
                    <h3 style="margin: 0; color: #f8fafc; font-size: 15px;">@{{ host }} - Canlı Yayımdadır 🔴</h3>
                    <p style="margin: 2px 0 0 0; color: #f97316; font-size: 12px; font-weight: 700;">Hədiyyələr: <span id="giftCount">{{ gifts|length }}</span></p>
                </div>
            </div>
            
            {% if current_user == host %}
                <form method="POST" action="/canli/bitir/{{ live_id }}" style="margin:0;">
                    <button type="submit" class="btn-end-stream">Canlıyı Bitir ⏹️</button>
                </form>
            {% else %}
                <a href="/canli" style="color: #a1a1aa; text-decoration: none; font-weight: 600; font-size: 14px;">Çıxış ✕</a>
            {% endif %}
        </div>

        <div class="stream-viewport">
            <div class="live-likes-counter">
                ❤️ <span id="likeCountDisplay">0</span>
            </div>

            {% if current_user == host %}
                <video id="webcamVideo" autoplay playsinline muted></video>
            {% else %}
                <div class="viewer-placeholder">
                    🎥 @{{ host }} canlı yayım edir<br>
                    <span style="font-size: 14px; color: #a1a1aa; font-weight: normal;">Söhbətə qoşulun və bəyəni atın!</span>
                </div>
            {% endif %}

            <div class="live-chat-overlay">
                <div class="live-messages-list" id="liveMessagesList">
                </div>
                <form class="live-chat-form" id="liveChatForm" onsubmit="sendLiveMessage(event)">
                    <input type="text" id="liveMsgInput" class="live-chat-input" placeholder="Şərh yaz..." required autocomplete="off">
                    <button type="submit" class="live-chat-submit">Yaz</button>
                </form>
            </div>

            <button class="floating-like-btn" onclick="sendLike()">❤️</button>
        </div>

        <div class="gifts-bar">
            {% set gift_list = ['👅', '❤️‍🔥', '🤠', '💋', '🫶', '🔥', '🧨', '🎀', '👑'] %}
            {% for gift in gift_list %}
                <button class="gift-btn" onclick="sendGift('{{ gift }}')">{{ gift }}</button>
            {% endfor %}
        </div>
    </div>

    <script>
        const isHost = {{ 'true' if current_user == host else 'false' }};
        const liveId = '{{ live_id }}';

        if (isHost) {
            navigator.mediaDevices.getUserMedia({ video: true, audio: true })
                .then(stream => {
                    const videoEl = document.getElementById('webcamVideo');
                    videoEl.srcObject = stream;
                })
                .catch(err => {
                    alert("Kameraya girişə icazə verilmədi və ya kamera tapılmadı!");
                });
        }

        function sendLike() {
            fetch('/canli/like/' + liveId, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    document.getElementById('likeCountDisplay').innerText = data.likes_count;
                }
            });
        }

        function sendLiveMessage(e) {
            e.preventDefault();
            let input = document.getElementById('liveMsgInput');
            let text = input.value.trim();
            if(!text) return;

            fetch('/canli/mesaj/' + liveId, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: text })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    input.value = '';
                    fetchLiveUpdates();
                }
            });
        }

        function sendGift(giftSymbol) {
            fetch('/canli/hediyye/' + liveId, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ gift: giftSymbol })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    document.getElementById('giftCount').innerText = data.gifts_count;
                } else {
                    alert(data.error || "Xəta baş verdi!");
                }
            });
        }

        function fetchLiveUpdates() {
            fetch('/canli/yenile/' + liveId)
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    document.getElementById('likeCountDisplay').innerText = data.likes_count;
                    
                    let list = document.getElementById('liveMessagesList');
                    list.innerHTML = '';
                    data.messages.forEach(m => {
                        list.innerHTML += `<div class="live-msg-bubble"><b>@${m.sender}</b>: ${m.content}</div>`;
                    });
                    list.scrollTop = list.scrollHeight;
                }
            });
        }

        setInterval(fetchLiveUpdates, 2000);
        fetchLiveUpdates();
    </script>
</body>
</html>
'''

# İDARƏ MƏRKƏZİ VƏ POLİS SİSTEMİ TEMPLATE-İ
IDARE_MERKEZI_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - İdarə Mərkəzi</title>
    ''' + COMMON_STYLE + '''
    <style>
        .control-container {
            background: rgba(24, 24, 27, 0.9);
            backdrop-filter: blur(16px);
            flex: 1;
            border-radius: 22px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            overflow-y: auto;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
        }
        .police-header {
            background: linear-gradient(135deg, #ef4444, #991b1b);
            color: white;
            padding: 20px;
            border-radius: 18px;
            text-align: center;
            font-weight: 800;
            font-size: 20px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(239, 68, 68, 0.4);
            letter-spacing: 0.5px;
        }
        .login-box {
            max-width: 420px;
            margin: 40px auto;
            background: rgba(39, 39, 42, 0.8);
            border: 1px solid #ef4444;
            padding: 30px;
            border-radius: 20px;
            text-align: center;
        }
        .login-box input, .login-box select {
            width: 100%;
            padding: 14px;
            margin: 10px 0;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            background: #09090b;
            color: #fff;
            box-sizing: border-box;
            font-size: 15px;
        }
        .login-box button {
            background: #ef4444;
            color: #fff;
            border: none;
            padding: 14px;
            width: 100%;
            border-radius: 12px;
            font-weight: 700;
            cursor: pointer;
            margin-top: 10px;
            font-size: 16px;
        }
        .regiment-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .regiment-card {
            background: rgba(39, 39, 42, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 18px;
            padding: 20px;
        }
        .regiment-title {
            color: #f97316;
            font-size: 18px;
            font-weight: 700;
            margin: 0 0 12px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .officer-item {
            display: flex;
            justify-content: space-between;
            background: rgba(9, 9, 11, 0.5);
            padding: 8px 12px;
            border-radius: 10px;
            margin-bottom: 8px;
            font-size: 14px;
        }
        .court-section {
            margin-top: 35px;
            background: rgba(39, 39, 42, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 18px;
            padding: 20px;
        }
        .btn-add-officer {
            background: #22c55e;
            color: white;
            border: none;
            padding: 10px 18px;
            border-radius: 10px;
            font-weight: 700;
            cursor: pointer;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="control-container">
        <div class="police-header">
            🛡️ 370 SAYLI BAŞ QƏRƏRGAH - POLİS İDARƏ MƏRKƏZİ
        </div>

        {% if not is_police_logged %}
            <div class="login-box">
                <h3 style="margin-top:0; color:#ef4444;">🛡️ POLİS XİDMƏTİ GİRİŞİ</h3>
                <p style="font-size:14px; color:#d4d4d8;">İdarə mərkəzinə daxil olmaq üçün 6 RƏQƏMLİ ŞƏXSİ KODU və xidmət etdiyiniz ALAYI qeyd edin.</p>
                {% if error %}
                    <p style="color:#ef4444; font-weight:700;">{{ error }}</p>
                {% endif %}
                <form method="POST" action="/idare_merkezi/login">
                    <input type="password" name="code" placeholder="ŞƏXSİ KOD (6 rəqəmli)..." maxlength="6" minlength="6" pattern="\d{6}" required>
                    <select name="regiment" required>
                        <option value="" disabled selected>Əmrində olduğunuz alayı seçin...</option>
                        <option value="POLİS ALAYI 222">🛡️ POLİS ALAYI 222</option>
                        <option value="POLİS ALAYI 333">🛡️ POLİS ALAYI 333</option>
                        <option value="POLİS ALAYI 444">🛡️ POLİS ALAYI 444</option>
                        <option value="POLİS ALAYI 555">🛡️ POLİS ALAYI 555</option>
                        <option value="POLİS ALAYI 666">🛡️ POLİS ALAYI 666</option>
                    </select>
                    <button type="submit">İdarə Mərkəzinə Daxil Ol 🔓</button>
                </form>
            </div>
        {% else %}
            <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(39,39,42,0.8); padding:16px 20px; border-radius:14px; margin-bottom:20px;">
                <div>
                    <b>Xoş gəldiniz:</b> @{{ current_user }} | <b>Sizin Alay:</b> <span style="color:#f97316;">{{ active_regiment }}</span>
                </div>
                <a href="/idare_merkezi/logout" style="background:#ef4444; color:#fff; padding:8px 14px; border-radius:10px; text-decoration:none; font-weight:700; font-size:13px;">Çıxış Et</a>
            </div>

            {% if is_admin %}
                <div style="background:rgba(39,39,42,0.6); padding:20px; border-radius:18px; margin-bottom:24px; border:1px solid #22c55e;">
                    <h4 style="margin:0 0 12px 0; color:#22c55e;">➕ Yeni Polis / Alay Rəisi Təyin Et (Admin: win_wid)</h4>
                    <form method="POST" action="/idare_merkezi/add_officer" style="display:flex; gap:12px; flex-wrap:wrap;">
                        <input type="text" name="officer_name" placeholder="İstifadəçi adı (Nik)" required style="flex:1; padding:10px; border-radius:10px; background:#09090b; border:1px solid rgba(255,255,255,0.2); color:#fff;">
                        <select name="regiment" required style="padding:10px; border-radius:10px; background:#09090b; border:1px solid rgba(255,255,255,0.2); color:#fff;">
                            <option value="POLİS ALAYI 222">POLİS ALAYI 222</option>
                            <option value="POLİS ALAYI 333">POLİS ALAYI 333</option>
                            <option value="POLİS ALAYI 444">POLİS ALAYI 444</option>
                            <option value="POLİS ALAYI 555">POLİS ALAYI 555</option>
                            <option value="POLİS ALAYI 666">POLİS ALAYI 666</option>
                        </select>
                        <select name="role" style="padding:10px; border-radius:10px; background:#09090b; border:1px solid rgba(255,255,255,0.2); color:#fff;">
                            <option value="Police">Polis Əməkdaşı</option>
                            <option value="Commander">Alay Rəisi 👑</option>
                        </select>
                        <button type="submit" class="btn-add-officer">Əlavə Et</button>
                    </form>
                </div>
            {% endif %}

            <h3 style="color:#f97316;">🛡️ ALAYLAR VƏ HEYƏT STRUKTURU (25 POLİS, 5 RƏİS)</h3>
            <div class="regiment-grid">
                {% set regiments = ['POLİS ALAYI 222', 'POLİS ALAYI 333', 'POLİS ALAYI 444', 'POLİS ALAYI 555', 'POLİS ALAYI 666'] %}
                {% for reg in regiments %}
                    <div class="regiment-card">
                        <div class="regiment-title">
                            <span>🛡️ {{ reg }}</span>
                        </div>
                        
                        <div style="margin-bottom:10px; font-weight:700; color:#fb923c; font-size:14px;">
                            👑 Alay Rəisi: 
                            {% set commander = officers | selectattr(1, 'equalto', reg) | selectattr(2, 'equalto', 'Commander') | list %}
                            {% if commander %}
                                <span style="color:#4ade80;">@{{ commander[0][0] }}</span>
                            {% else %}
                                <span style="color:#a1a1aa; font-weight:normal;">Təyin edilməyib</span>
                            {% endif %}
                        </div>

                        <div style="font-size:13px; color:#d4d4d8; font-weight:700; margin-bottom:6px;">Polis Əməkdaşları:</div>
                        {% set reg_officers = officers | selectattr(1, 'equalto', reg) | selectattr(2, 'equalto', 'Police') | list %}
                        {% if reg_officers %}
                            {% for off in reg_officers %}
                                <div class="officer-item">
                                    <span>👮 @{{ off[0] }}</span>
                                    <span style="color:#22c55e; font-weight:700;">Növbədə</span>
                                </div>
                            {% endfor %}
                        {% else %}
                            <div style="font-size:12px; color:#a1a1aa;">Hələ ki bu alayda polis yoxdur.</div>
                        {% endif %}
                    </div>
                {% endfor %}
            </div>

            <div class="court-section">
                <h3 style="color:#ef4444; margin-top:0;">⚖️ MƏHKƏMƏ SİSTEMİ VƏ İŞLƏR</h3>
                <p style="font-size:14px; color:#d4d4d8;">Qaydaları pozub saxlanılan istifadəçilərin işləri Sayt Rəhbərliyi (Hakim) tərəfindən araşdırılır.</p>
                
                <form method="POST" action="/idare_merkezi/add_case" style="display:flex; gap:12px; margin-bottom:20px; flex-wrap:wrap;">
                    <input type="text" name="accused_user" placeholder="Təqsirləndirilən istifadəçi (Nik)" required style="flex:1; padding:10px; border-radius:10px; background:#09090b; border:1px solid rgba(255,255,255,0.2); color:#fff;">
                    <input type="text" name="reason" placeholder="Pozduğu qayda / Səbəb" required style="flex:2; padding:10px; border-radius:10px; background:#09090b; border:1px solid rgba(255,255,255,0.2); color:#fff;">
                    <button type="submit" style="background:#ef4444; color:#fff; border:none; padding:10px 18px; border-radius:10px; font-weight:700; cursor:pointer;">Məhkəməyə Ver ⚖️</button>
                </form>

                {% if cases %}
                    <div style="display:flex; flex-direction:column; gap:10px;">
                        {% for c in cases %}
                            <div style="background:rgba(9,9,11,0.7); padding:14px; border-radius:12px; border:1px solid rgba(255,255,255,0.08); display:flex; justify-content:space-between; align-items:center;">
                                <div>
                                    <b>Təqsirləndirilən:</b> <span style="color:#f97316;">@{{ c[1] }}</span> | <b>Səbəb:</b> {{ c[2] }}
                                    <div style="font-size:13px; color:#a1a1aa; margin-top:4px;"><b>Hakim:</b> {{ c[4] }} | <b>Qərar:</b> <span style="color:#eab308;">{{ c[3] }}</span></div>
                                </div>
                                {% if is_admin %}
                                    <form method="POST" action="/idare_merkezi/verdict/{{ c[0] }}" style="display:flex; gap:6px;">
                                        <input type="text" name="verdict" placeholder="Hökm yaz..." required style="padding:6px; border-radius:8px; background:#18181b; border:1px solid #555; color:#fff; font-size:12px;">
                                        <button type="submit" style="background:#22c55e; color:#fff; border:none; padding:6px 12px; border-radius:8px; font-weight:700; cursor:pointer; font-size:12px;">Hökm Ver (win_wid)</button>
                                    </form>
                                {% endif %}
                            </div>
                        {% endfor %}
                    </div>
                {% else %}
                    <p style="color:#a1a1aa; font-size:14px;">Hazırda məhkəmədə aktiv iş yoxdur.</p>
                {% endif %}
            </div>
        {% endif %}
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action')
        nickname = request.form.get('nickname').strip()
        password = request.form.get('password').strip()
        
        if not nickname or not password:
            return render_template_string(INDEX_TEMPLATE, error="Bütün xanaları doldurun!")
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if action == 'register':
            cursor.execute("SELECT * FROM users WHERE nickname = ?", (nickname,))
            if cursor.fetchone():
                conn.close()
                return render_template_string(INDEX_TEMPLATE, error="Bu nik artıq istifadə olunur!")
            
            cursor.execute("INSERT INTO users (nickname, password, points) VALUES (?, ?, ?)", (nickname, password, 20))
            conn.commit()
            conn.close()
            session['user'] = nickname
            return redirect(url_for('chat'))
            
        elif action == 'login':
            cursor.execute("SELECT * FROM users WHERE nickname = ? AND password = ?", (nickname, password))
            user = cursor.fetchone()
            conn.close()
            if user:
                session['user'] = nickname
                return redirect(url_for('chat'))
            else:
                return render_template_string(INDEX_TEMPLATE, error="Nik və ya şifrə yanlışdır!")
                
    return render_template_string(INDEX_TEMPLATE)

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
    
    cursor.execute("SELECT points FROM users WHERE nickname = ?", (current_user,))
    res = cursor.fetchone()
    user_points = res[0] if res else 0
    
    cursor.execute("SELECT id FROM notifications WHERE username = ? AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    
    cursor.execute('''
        SELECT m.id, m.sender, m.content, u.name_color, u.msg_color, u.profile_sticker 
        FROM messages m 
        LEFT JOIN users u ON m.sender = u.nickname 
        ORDER BY m.id ASC
    ''')
    messages = cursor.fetchall()
    
    # YALNIZ win_wid ADMINDIR (EMKA adminlikdən çıxarıldı)
    is_admin = (current_user.lower() == 'win_wid')
    
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(CHAT_TEMPLATE, messages=messages, current_user=current_user, is_admin=is_admin, user_points=user_points, header=header_html)

@app.route('/chat/send', methods=['POST'])
def chat_send():
    if 'user' not in session:
        return redirect(url_for('index'))
    content = request.form.get('content', '').strip()
    if content:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (sender, content) VALUES (?, ?)", (session['user'], content))
        conn.commit()
        conn.close()
    return redirect(url_for('chat'))

@app.route('/chat/delete/<int:msg_id>', methods=['POST'])
def chat_delete(msg_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Giriş edilməyib'})
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT sender FROM messages WHERE id = ?", (msg_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'error': 'Mesaj tapılmadı'})
    
    is_admin = (current_user.lower() == 'win_wid')
    
    # Yalnız mesajın sahibi və ya win_wid silə bilər
    if row[0] == current_user or is_admin:
        cursor.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    conn.close()
    return jsonify({'success': False, 'error': 'İcazəniz yoxdur'})

@app.route('/chat/edit/<int:msg_id>', methods=['POST'])
def chat_edit(msg_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Giriş edilməyib'})
    data = request.get_json()
    new_content = data.get('content', '').strip()
    if not new_content:
        return jsonify({'success': False, 'error': 'Mətn boş ola bilməz'})
        
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT sender FROM messages WHERE id = ?", (msg_id,))
    row = cursor.fetchone()
    if row and row[0] == current_user:
        cursor.execute("UPDATE messages SET content = ? WHERE id = ?", (new_content, msg_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'content': new_content})
    conn.close()
    return jsonify({'success': False, 'error': 'İcazəniz yoxdur'})

@app.route('/oyun', methods=['GET', 'POST'])
def oyun():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM notifications WHERE username = ? AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    
    questions_bank = {
        "tarix": [
            ("Azərbaycan Demokratik Respublikası neçənci ildə yaradılıb?", "1918", "XX əsrin əvvəlləri"),
            ("İkinci Dünya müharibəsi neçənci ildə bitmişdir?", "1945", "1940-cı illərin ortaları")
        ],
        "cografiya": [
            ("Azərbaycanın ən hündür zirvəsi hansıdır?", "Bazardüzü", "B hərfi ilə başlayır"),
            ("Dünyanın ən böyük okeanı hansıdır?", "Sakit okean", "Adı sakitliklə bağlıdır")
        ]
    }
    
    topic = request.form.get('topic') or request.args.get('topic')
    if topic:
        topic_lower = topic.strip().lower()
        q_list = questions_bank.get(topic_lower, [
            ("Azərbaycan Respublikasının paytaxtı haradır?", "Bakı", "Xəzər dənizi sahilindədir")
        ])
        q_data = random.choice(q_list)
        return render_template_string(OYUN_TEMPLATE, header=header_html, topic=topic, question=q_data[0], answer=q_data[1], hint=q_data[2])
        
    return render_template_string(OYUN_TEMPLATE, header=header_html)

@app.route('/oyun/cavabla', methods=['POST'])
def oyun_cavabla():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    current_user = session['user']
    user_answer = request.form.get('user_answer', '').strip().lower()
    correct_answer = request.form.get('correct_answer', '').strip().lower()
    topic = request.form.get('topic', '')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM notifications WHERE username = ? AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    
    success = (user_answer == correct_answer)
    message = "Təbriklər! Düzgün cavab (+5 bal)" if success else f"Səhvdir! Düzgün cavab: {correct_answer}"
    
    if success:
        cursor.execute("UPDATE users SET points = points + 5 WHERE nickname = ?", (current_user,))
        conn.commit()
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(OYUN_TEMPLATE, header=header_html, topic=topic, message=message, success=success)

@app.route('/istifadeciler')
def istifadeciler():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM notifications WHERE username = ? AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    
    is_admin = (current_user.lower() == 'win_wid')
    
    cursor.execute("SELECT nickname, profile_pic, name_color, profile_sticker FROM users")
    all_users = cursor.fetchall()
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(USERS_TEMPLATE, all_users=all_users, current_user=current_user, is_admin=is_admin, header=header_html)

@app.route('/ozel_mesaj/<receiver>', methods=['GET', 'POST'])
def ozel_mesaj(receiver):
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            cursor.execute("INSERT INTO private_messages (sender, receiver, content) VALUES (?, ?, ?)", (current_user, receiver, content))
            conn.commit()
            
    cursor.execute("SELECT id FROM notifications WHERE username = ? AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    
    cursor.execute('''
        SELECT id, sender, receiver, content FROM private_messages 
        WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?) 
        ORDER BY id ASC
    ''', (current_user, receiver, receiver, current_user))
    messages = cursor.fetchall()
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(PRIVATE_CHAT_TEMPLATE, messages=messages, receiver=receiver, current_user=current_user, header=header_html)

@app.route('/vidyo')
def vidyo():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM notifications WHERE username = ? AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    
    is_admin = (current_user.lower() == 'win_wid')
    
    cursor.execute('''
        SELECT v.id, v.uploader, v.video_data, u.name_color 
        FROM videos v 
        LEFT JOIN users u ON v.uploader = u.nickname 
        ORDER BY v.id DESC
    ''')
    raw_videos = cursor.fetchall()
    
    videos = []
    for v in raw_videos:
        v_id = v[0]
        cursor.execute("SELECT * FROM video_likes WHERE video_id = ? AND username = ?", (v_id, current_user))
        liked = cursor.fetchone() is not None
        
        cursor.execute("SELECT COUNT(*) FROM video_likes WHERE video_id = ?", (v_id,))
        like_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT id, username, comment FROM video_comments WHERE video_id = ? ORDER BY id ASC", (v_id,))
        comments = cursor.fetchall()
        
        videos.append((v[0], v[1], v[2], liked, like_count, comments, v[3]))
        
    conn.close()
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(VIDYO_TEMPLATE, videos=videos, current_user=current_user, is_admin=is_admin, header=header_html)

@app.route('/vidyo/upload', methods=['POST'])
def vidyo_upload():
    if 'user' not in session:
        return redirect(url_for('index'))
    file = request.files.get('video_file')
    if file:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp:
            file.save(temp.name)
            temp_path = temp.name
        
        try:
            size_mb = os.path.getsize(temp_path) / (1024 * 1024)
            if size_mb > 15:
                os.unlink(temp_path)
                return render_template_string(VIDYO_TEMPLATE, upload_error="Video həcmi çox böyükdür (Max 15MB)!", videos=[], current_user=session['user'])
        except Exception:
            pass
            
        with open(temp_path, 'rb') as f:
            vid_bytes = f.read()
        os.unlink(temp_path)
        
        b64_str = "data:video/mp4;base64," + base64.b64encode(vid_bytes).decode('utf-8')
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO videos (uploader, video_data) VALUES (?, ?)", (session['user'], b64_str))
        conn.commit()
        conn.close()
    return redirect(url_for('vidyo'))

@app.route('/vidyo/like/<int:video_id>', methods=['POST'])
def vidyo_like(video_id):
    if 'user' not in session:
        return jsonify({'success': False})
    user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM video_likes WHERE video_id = ? AND username = ?", (video_id, user))
    if cursor.fetchone():
        cursor.execute("DELETE FROM video_likes WHERE video_id = ? AND username = ?", (video_id, user))
        liked = False
    else:
        cursor.execute("INSERT INTO video_likes (video_id, username) VALUES (?, ?)", (video_id, user))
        liked = True
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM video_likes WHERE video_id = ?", (video_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return jsonify({'success': True, 'liked': liked, 'count': count})

@app.route('/vidyo/comment/<int:video_id>', methods=['POST'])
def vidyo_comment(video_id):
    if 'user' not in session:
        return jsonify({'success': False})
    data = request.get_json()
    comment = data.get('comment', '').strip()
    if not comment:
        return jsonify({'success': False})
    user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO video_comments (video_id, username, comment) VALUES (?, ?, ?)", (video_id, user, comment))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'user': user, 'comment': comment})

@app.route('/vidyo/share/<int:video_id>', methods=['POST'])
def vidyo_share(video_id):
    if 'user' not in session:
        return jsonify({'success': False})
    data = request.get_json()
    receiver = data.get('receiver', '').strip()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE nickname = ?", (receiver,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'error': 'İstifadəçi tapılmadı'})
    cursor.execute("INSERT INTO video_shares (video_id, sender, receiver) VALUES (?, ?, ?)", (video_id, session['user'], receiver))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/vidyo/delete/<int:video_id>', methods=['POST'])
def vidyo_delete(video_id):
    if 'user' not in session:
        return jsonify({'success': False})
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT uploader FROM videos WHERE id = ?", (video_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False})
    
    is_admin = (current_user.lower() == 'win_wid')
    if row[0] == current_user or is_admin:
        cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    conn.close()
    return jsonify({'success': False})

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
            new_name = request.form.get('new_nickname', '').strip()
            if not new_name or len(new_name) > 7:
                message = "Nik adı 7 hərfdən çox ola bilməz!"
                error = True
            else:
                cursor.execute("SELECT * FROM users WHERE nickname = ?", (new_name,))
                if cursor.fetchone():
                    message = "Bu nik artıq istifadə olunur!"
                    error = True
                else:
                    cursor.execute("UPDATE users SET nickname = ? WHERE nickname = ?", (new_name, current_user))
                    cursor.execute("UPDATE messages SET sender = ? WHERE sender = ?", (new_name, current_user))
                    cursor.execute("UPDATE videos SET uploader = ? WHERE uploader = ?", (new_name, current_user))
                    conn.commit()
                    session['user'] = new_name
                    current_user = new_name
                    message = "Adınız uğurla dəyişdirildi!"
        elif action == 'change_pic':
            file = request.files.get('pic_file')
            if file:
                img_bytes = file.read()
                b64_str = "data:image/jpeg;base64," + base64.b64encode(img_bytes).decode('utf-8')
                cursor.execute("UPDATE users SET profile_pic = ? WHERE nickname = ?", (b64_str, current_user))
                conn.commit()
                message = "Profil şəkli yeniləndi!"
        elif action == 'delete_account':
            cursor.execute("DELETE FROM users WHERE nickname = ?", (current_user,))
            conn.commit()
            conn.close()
            session.pop('user', None)
            return redirect(url_for('index'))

    cursor.execute("SELECT points, profile_pic, name_color, profile_sticker FROM users WHERE nickname = ?", (current_user,))
    user_data = cursor.fetchone()
    points = user_data[0] if user_data else 0
    pic = user_data[1] if user_data else None
    name_color = user_data[2] if user_data else 'inherit'
    profile_sticker = user_data[3] if user_data else ''
    
    cursor.execute("SELECT gift, sender FROM gifts WHERE receiver = ?", (current_user,))
    gifts = cursor.fetchall()
    
    cursor.execute("SELECT id FROM notifications WHERE username = ? AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    
    is_admin = (current_user.lower() == 'win_wid')
    
    conn.close()
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(PROFIL_TEMPLATE, user=current_user, points=points, pic=pic, name_color=name_color, profile_sticker=profile_sticker, gifts=gifts, is_admin=is_admin, message=message, error=error, header=header_html)

@app.route('/canli')
def canli():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM notifications WHERE username = ? AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    
    cursor.execute('''
        SELECT l.id, l.host, u.profile_pic 
        FROM lives l 
        LEFT JOIN users u ON l.host = u.nickname 
        WHERE l.is_active = 1
    ''')
    lives = cursor.fetchall()
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(CANLI_TEMPLATE, lives=lives, current_user=current_user, header=header_html)

@app.route('/canli/ac', methods=['POST'])
def canli_ac():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT points FROM users WHERE nickname = ?", (current_user,))
    res = cursor.fetchone()
    points = res[0] if res else 0
    
    if points < 60:
        cursor.execute('''
            SELECT l.id, l.host, u.profile_pic 
            FROM lives l 
            LEFT JOIN users u ON l.host = u.nickname 
            WHERE l.is_active = 1
        ''')
        lives = cursor.fetchall()
        conn.close()
        return render_template_string(CANLI_TEMPLATE, lives=lives, current_user=current_user, error="Canlı açmaq üçün balansınızda ən azı 60 bal olmalıdır!", header=get_header_template(False))
        
    cursor.execute("INSERT INTO lives (host, is_active) VALUES (?, 1)", (current_user,))
    live_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return redirect(url_for('canli_izle', live_id=live_id))

@app.route('/canli/izle/<int:live_id>')
def canli_izle(live_id):
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT host FROM lives WHERE id = ? AND is_active = 1", (live_id,))
    live = cursor.fetchone()
    if not live:
        conn.close()
        return redirect(url_for('canli'))
    host = live[0]
    
    cursor.execute("SELECT profile_pic FROM users WHERE nickname = ?", (host,))
    p_res = cursor.fetchone()
    host_pic = p_res[0] if p_res else None
    
    cursor.execute("SELECT id, sender, gift FROM live_gifts WHERE live_id = ?", (live_id,))
    gifts = cursor.fetchall()
    
    cursor.execute("SELECT id FROM notifications WHERE username = ? AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(CANLI_ROOM_TEMPLATE, live_id=live_id, host=host, host_pic=host_pic, gifts=gifts, current_user=current_user, header=header_html)

@app.route('/canli/like/<int:live_id>', methods=['POST'])
def canli_like(live_id):
    if 'user' not in session:
        return jsonify({'success': False})
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO live_likes (live_id, username) VALUES (?, ?)", (live_id, current_user))
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM live_likes WHERE live_id = ?", (live_id,))
    likes_count = cursor.fetchone()[0]
    conn.close()
    return jsonify({'success': True, 'likes_count': likes_count})

@app.route('/canli/mesaj/<int:live_id>', methods=['POST'])
def canli_mesaj(live_id):
    if 'user' not in session:
        return jsonify({'success': False})
    data = request.get_json()
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'success': False})
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO live_messages (live_id, sender, content) VALUES (?, ?, ?)", (live_id, session['user'], content))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/canli/yenile/<int:live_id>')
def canli_yenile(live_id):
    if 'user' not in session:
        return jsonify({'success': False})
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM live_likes WHERE live_id = ?", (live_id,))
    likes_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT sender, content FROM live_messages WHERE live_id = ? ORDER BY id ASC", (live_id,))
    messages = [{'sender': r[0], 'content': r[1]} for r in cursor.fetchall()]
    conn.close()
    
    return jsonify({'success': True, 'likes_count': likes_count, 'messages': messages})

@app.route('/canli/hediyye/<int:live_id>', methods=['POST'])
def canli_hediyye(live_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Giriş edilməyib'})
    current_user = session['user']
    data = request.get_json()
    gift = data.get('gift')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT points FROM users WHERE nickname = ?", (current_user,))
    res = cursor.fetchone()
    user_points = res[0] if res else 0
    
    if user_points < 10:
        conn.close()
        return jsonify({'success': False, 'error': 'Balınız kifayət etmir (Hədiyyə 10 baldır)'})
        
    cursor.execute("SELECT host FROM lives WHERE id = ?", (live_id,))
    live = cursor.fetchone()
    if not live:
        conn.close()
        return jsonify({'success': False, 'error': 'Canlı tapılmadı'})
    host = live[0]
    
    cursor.execute("UPDATE users SET points = points - 10 WHERE nickname = ?", (current_user,))
    cursor.execute("UPDATE users SET points = points + 10 WHERE nickname = ?", (host,))
    cursor.execute("INSERT INTO live_gifts (live_id, sender, gift) VALUES (?, ?, ?)", (live_id, current_user, gift))
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM live_gifts WHERE live_id = ?", (live_id,))
    gifts_count = cursor.fetchone()[0]
    conn.close()
    
    return jsonify({'success': True, 'gifts_count': gifts_count})

@app.route('/canli/bitir/<int:live_id>', methods=['POST'])
def canli_bitir(live_id):
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT host FROM lives WHERE id = ? AND is_active = 1", (live_id,))
    live = cursor.fetchone()
    if live and live[0] == current_user:
        cursor.execute("UPDATE lives SET is_active = 0 WHERE id = ?", (live_id,))
        
        cursor.execute("SELECT COUNT(*) FROM live_likes WHERE live_id = ?", (live_id,))
        likes_count = cursor.fetchone()[0]
        
        bonus_points = (likes_count // 50) * 10
        if bonus_points > 0:
            cursor.execute("UPDATE users SET points = points + ? WHERE nickname = ?", (bonus_points, current_user))
            
        conn.commit()
    conn.close()
    return redirect(url_for('canli'))

@app.route('/bildiris')
def bildiris():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE username = ?", (current_user,))
    cursor.execute("SELECT id, content FROM notifications WHERE username = ? ORDER BY id DESC", (current_user,))
    notifs = cursor.fetchall()
    conn.commit()
    conn.close()
    
    notifs_html = "".join([f"<div style='background:rgba(39,39,42,0.8); padding:16px; border-radius:14px; margin-bottom:12px; border:1px solid rgba(255,255,255,0.08); font-size:15px;'>{n[1]}</div>" for n in notifs]) or "<p style='text-align:center; color:#a1a1aa;'>Bildiriş yoxdur.</p>"
    
    page = f'''
    <!DOCTYPE html>
    <html lang="az">
    <head>
        <meta charset="UTF-8">
        <title>WİN_WİD - Bildirişlər</title>
        {COMMON_STYLE}
    </head>
    <body>
        {get_header_template(False)}
        <div style="background:rgba(24,24,27,0.85); flex:1; border-radius:22px; padding:24px; overflow-y:auto; border:1px solid rgba(255,255,255,0.1);">
            <h2 style="color:#f97316; margin-top:0; text-align:center;">🔔 BİLDİRİŞLƏR</h2>
            {notifs_html}
        </div>
    </body>
    </html>
    '''
    return render_template_string(page)

# 1. TƏLƏB: BÜTÜN ŞİKAYƏTLƏR BİLDİRİŞ BÖLMƏSİNDƏ win_wid HESABINA GÖRSƏNİR
@app.route('/sikayet', methods=['GET', 'POST'])
def sikayet():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    message = None
    if request.method == 'POST':
        category = request.form.get('category')
        content = request.form.get('content')
        if category and content:
            cursor.execute("INSERT INTO complaints (username, category, content) VALUES (?, ?, ?)", (current_user, category, content))
            
            # WIN_WID hesabının bildiriş bölməsinə göndərilir
            notif_text = f"📢 Yeni Şikayət! İstifadəçi: @{current_user} | Kateqoriya: {category} | Mətn: {content}"
            cursor.execute("INSERT INTO notifications (username, content) VALUES ('win_wid', ?)", (notif_text,))
            
            conn.commit()
            message = "Şikayətiniz uğurla göndərildi!"
            
    cursor.execute("SELECT id FROM notifications WHERE username = ? AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    conn.close()
    
    page = f'''
    <!DOCTYPE html>
    <html lang="az">
    <head>
        <meta charset="UTF-8">
        <title>WİN_WİD - Şikayət</title>
        {COMMON_STYLE}
    </head>
    <body>
        {get_header_template(has_unread_notifs)}
        <div style="background:rgba(24,24,27,0.85); flex:1; border-radius:22px; padding:28px; overflow-y:auto; border:1px solid rgba(255,255,255,0.1); max-width:600px; margin:0 auto; width:100%; box-sizing:border-box;">
            <h2 style="color:#f97316; margin-top:0; text-align:center;">📢 ŞİKAYƏT VƏ TƏKLİF</h2>
            {f"<p style='color:#4ade80; text-align:center; font-weight:700;'>{message}</p>" if message else ""}
            <form method="POST" style="display:flex; flex-direction:column; gap:16px;">
                <select name="category" required style="padding:14px; border-radius:12px; background:#111; color:#fff; border:1px solid #f97316; font-size:15px;">
                    <option value="" disabled selected>Kateqoriya seçin...</option>
                    <option value="Texniki problem">Texniki problem</option>
                    <option value="İstifadəçi şikayəti">İstifadəçi şikayəti</option>
                    <option value="Təklif">Təklif</option>
                </select>
                <textarea name="content" placeholder="Şikayət və ya təklifinizi ətraflı yazın..." rows="5" required style="padding:14px; border-radius:12px; background:#111; color:#fff; border:1px solid #f97316; font-size:15px; resize:none;"></textarea>
                <button type="submit" style="background:linear-gradient(135deg, #f97316, #ea580c); color:#fff; border:none; padding:15px; border-radius:12px; font-weight:700; font-size:16px; cursor:pointer;">Göndər</button>
            </form>
        </div>
    </body>
    </html>
    '''
    return render_template_string(page)

# İDARƏ MƏRKƏZİ ROUTE-LARI
@app.route('/idare_merkezi')
def idare_merkezi():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM notifications WHERE username = ? AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None

    is_police_logged = session.get('is_police_logged', False)
    active_regiment = session.get('active_regiment', '')

    cursor.execute("SELECT username, regiment, role FROM police_officers")
    officers = cursor.fetchall()

    cursor.execute("SELECT id, accused_user, reason, verdict, judge FROM court_cases ORDER BY id DESC")
    cases = cursor.fetchall()

    # YALNIZ win_wid ADMINDIR
    is_admin = (current_user.lower() == 'win_wid')

    conn.close()

    header_html = get_header_template(has_unread_notifs)
    return render_template_string(
        IDARE_MERKEZI_TEMPLATE,
        header=header_html,
        is_police_logged=is_police_logged,
        active_regiment=active_regiment,
        current_user=current_user,
        officers=officers,
        cases=cases,
        is_admin=is_admin,
        error=request.args.get('error')
    )

@app.route('/idare_merkezi/login', methods=['POST'])
def idare_merkezi_login():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    current_user = session['user']
    code = request.form.get('code', '').strip()
    regiment = request.form.get('regiment', '')

    if code.isdigit() and len(code) == 6 and code == '370811' and regiment:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO police_officers (username, regiment, role) 
            VALUES (?, ?, 'Police')
            ON CONFLICT(username) DO UPDATE SET regiment = excluded.regiment
        ''', (current_user, regiment))
        
        conn.commit()
        conn.close()

        session['is_police_logged'] = True
        session['active_regiment'] = regiment
        return redirect(url_for('idare_merkezi'))
    else:
        return redirect(url_for('idare_merkezi', error="Xüsusi 6 rəqəmli KOD və ya Alay yanlışdır!"))

@app.route('/idare_merkezi/logout')
def idare_merkezi_logout():
    session.pop('is_police_logged', None)
    session.pop('active_regiment', None)
    return redirect(url_for('idare_merkezi'))

# 3. TƏLƏB: POLİS ALAYLARININ RƏİSİNİ TƏYİN ETMƏK YALNIZ win_wid HESABINA MƏXSUSDUR
@app.route('/idare_merkezi/add_officer', methods=['POST'])
def idare_merkezi_add_officer():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    
    # Yalnız win_wid hesabı rəis təyin edə bilər
    if current_user.lower() == 'win_wid':
        officer_name = request.form.get('officer_name', '').strip()
        regiment = request.form.get('regiment')
        role = request.form.get('role', 'Police')
        
        if officer_name and regiment:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT OR REPLACE INTO police_officers (username, regiment, role) VALUES (?, ?, ?)", (officer_name, regiment, role))
                conn.commit()
            except sqlite3.Error:
                pass
            conn.close()
    return redirect(url_for('idare_merkezi'))

@app.route('/idare_merkezi/add_case', methods=['POST'])
def idare_merkezi_add_case():
    if 'user' not in session or not session.get('is_police_logged'):
        return redirect(url_for('idare_merkezi'))
    accused_user = request.form.get('accused_user', '').strip()
    reason = request.form.get('reason', '').strip()

    if accused_user and reason:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO court_cases (accused_user, reason) VALUES (?, ?)", (accused_user, reason))
        conn.commit()
        conn.close()
    return redirect(url_for('idare_merkezi'))

# 4. TƏLƏB: MƏHKƏMƏ HÖKMÜNÜ VERMƏK YALNIZ win_wid HESABINA MƏXSUSDUR
@app.route('/idare_merkezi/verdict/<int:case_id>', methods=['POST'])
def idare_merkezi_verdict(case_id):
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    
    # Yalnız win_wid hökm verə bilər
    if current_user.lower() == 'win_wid':
        verdict = request.form.get('verdict', '').strip()
        if verdict:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("UPDATE court_cases SET verdict = ?, judge = ? WHERE id = ?", (verdict, f"Sayt Rəhbərliyi (@{current_user})", case_id))
            conn.commit()
            conn.close()
    return redirect(url_for('idare_merkezi'))

@app.route('/admin/sikayetler')
def admin_sikayetler():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    
    if current_user.lower() != 'win_wid':
        return redirect(url_for('chat'))
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, category, content FROM complaints ORDER BY id DESC")
    comps = cursor.fetchall()
    conn.close()
    
    rows = "".join([f"<div style='background:rgba(39,39,42,0.8); padding:16px; border-radius:14px; margin-bottom:12px; border:1px solid rgba(255,255,255,0.08);'><b>@{c[1]}</b> ({c[2]}):<p style='margin:8px 0 0 0; color:#d4d4d8;'>{c[3]}</p></div>" for c in comps]) or "<p style='text-align:center; color:#a1a1aa;'>Şikayət yoxdur.</p>"
    
    page = f'''
    <!DOCTYPE html>
    <html lang="az">
    <head>
        <meta charset="UTF-8">
        <title>WİN_WİD - Admin Şikayətlər</title>
        {COMMON_STYLE}
    </head>
    <body>
        {get_header_template(False)}
        <div style="background:rgba(24,24,27,0.85); flex:1; border-radius:22px; padding:24px; overflow-y:auto; border:1px solid rgba(255,255,255,0.1);">
            <h2 style="color:#f97316; margin-top:0; text-align:center;">⚙ GƏLƏN ŞİKAYƏTLƏR (ADMİN)</h2>
            {rows}
        </div>
    </body>
    </html>
    '''
    return render_template_string(page)

# 2. TƏLƏB: İSTİFADƏÇİLƏRİN HESABINI VƏ MESAJLARINI SİLMƏK YALNIZ win_wid HESABINA MƏXSUSDUR
@app.route('/admin/delete_user/<username>', methods=['POST'])
def admin_delete_user(username):
    if 'user' not in session:
        return jsonify({'success': False})
    current_user = session['user']
    
    if current_user.lower() == 'win_wid' and username.lower() != 'win_wid':
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE nickname = ?", (username,))
        cursor.execute("DELETE FROM messages WHERE sender = ?", (username,))
        cursor.execute("DELETE FROM private_messages WHERE sender = ? OR receiver = ?", (username, username))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/magaza')
def magaza():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE nickname = ?", (current_user,))
    res = cursor.fetchone()
    user_points = res[0] if res else 0
    cursor.execute("SELECT id FROM notifications WHERE username = ? AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    conn.close()
    
    page = f'''
    <!DOCTYPE html>
    <html lang="az">
    <head>
        <meta charset="UTF-8">
        <title>WİN_WİD - Mağaza</title>
        {COMMON_STYLE}
    </head>
    <body>
        {get_header_template(has_unread_notifs)}
        <div style="background:rgba(24,24,27,0.85); flex:1; border-radius:22px; padding:28px; overflow-y:auto; border:1px solid rgba(255,255,255,0.1); text-align:center;">
            <h2 style="color:#f97316; margin-top:0;">🛍 MAQAZİN / HƏDİYYƏLƏR</h2>
            <p style="font-size:16px; color:#4ade80; font-weight:700;">Balansınız: {user_points} bal</p>
            <p style="color:#d4d4d8; font-size:15px;">TEZLİKLƏ MAĞAZA BÖLMƏSİ İŞLƏYƏCƏKDİR!! </p>
        </div>
    </body>
    </html>
    '''
    return render_template_string(page)

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('is_police_logged', None)
    session.pop('active_regiment', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
