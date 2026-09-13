from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
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
            sender TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN sender TEXT")
    except sqlite3.OperationalError:
        pass
    
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
            width: 320px; 
            padding: 25px 20px; 
            background: #172554; 
            border-radius: 12px; 
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4); 
            text-align: center; 
            border: 1px solid #3b82f6; 
        }
        h1 { 
            font-size: 15px; 
            margin-bottom: 20px; 
            color: #ffffff; 
            letter-spacing: 0.5px;
        }
        input { 
            width: 100%; 
            padding: 10px 12px; 
            margin: 8px 0; 
            border: 1px solid #3b82f6; 
            border-radius: 6px; 
            background: #1e3a8a; 
            color: #ffffff; 
            box-sizing: border-box; 
            font-size: 13px;
        }
        input:focus {
            border-color: #60a5fa;
            outline: none;
        }
        input::placeholder { color: #93c5fd; }
        button { 
            width: 100%; 
            padding: 10px; 
            margin: 8px 0; 
            background: #2563eb; 
            color: white; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            font-weight: bold; 
            font-size: 13px;
        }
        button:hover { background: #1d4ed8; }
        .error { color: #f87171; font-size: 12px; margin-bottom: 10px; }
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

# Üst Menyu
def get_header_template(points=500):
    return f'''
    <div class="nav-bar">
        <a href="/chat" class="nav-item">
            <span class="icon">💬</span>
            <span>Çat</span>
        </a>
        <a href="/istifadeciler" class="nav-item">
            <span class="icon">👥</span>
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
        <a href="/bildiris" class="nav-item">
            <span class="icon">🔔</span>
            <span>Bildiriş</span>
        </a>
    </div>
'''

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
            border: 2px solid #f97316; 
            border-radius: 12px; 
            padding: 8px 6px; 
            display: flex; 
            justify-content: space-around; 
            align-items: center; 
            margin-bottom: 8px;
            gap: 4px;
            overflow-x: auto;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            flex-shrink: 0;
        }
        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-decoration: none;
            color: #cbd5e1;
            padding: 4px 6px;
            border-radius: 8px;
            font-size: 10px;
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
            background: rgba(59, 130, 246, 0.3);
            transform: translateY(-2px);
        }
    </style>
'''

CHAT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Çat</title>
    ''' + COMMON_STYLE + '''
    <style>
        .chat-outer-container {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding-top: 10px;
            box-sizing: border-box;
            overflow: hidden;
        }
        .chat-main-wrapper {
            width: 98%;
            max-width: 620px;
            height: 56vh;
            display: flex;
            flex-direction: column;
            background: #172554;
            border: 2px solid #f97316;
            border-radius: 12px;
            padding: 10px;
            box-sizing: border-box;
            overflow: hidden;
        }
        .chat-header-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
            font-weight: bold;
            color: #f97316;
            background: #1e3a8a;
            padding: 6px 10px;
            border-radius: 6px;
            border: 1px solid #3b82f6;
            margin-bottom: 6px;
            flex-shrink: 0;
        }
        .chat-box { 
            flex: 1; 
            overflow-y: auto; 
            color: #ffffff; 
            margin-bottom: 8px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            padding-right: 4px;
        }
        .message-card {
            background: #1e3a8a;
            padding: 6px 10px;
            border-radius: 6px;
            border-left: 3px solid #3b82f6;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
        }
        .message-content {
            word-break: break-all;
            flex: 1;
        }
        .message-actions {
            display: flex;
            gap: 4px;
            margin-left: 8px;
            flex-shrink: 0;
        }
        .action-btn {
            background: transparent;
            border: none;
            cursor: pointer;
            font-size: 13px;
            padding: 2px;
            border-radius: 4px;
        }
        .action-btn:hover {
            background: rgba(59, 130, 246, 0.4);
        }
        .message-form { 
            display: flex; 
            gap: 6px; 
            background: #1e3a8a;
            padding: 6px;
            border: 1px solid #3b82f6;
            border-radius: 8px;
            align-items: center;
            flex-shrink: 0;
        }
        input[type="text"] { 
            flex: 1; 
            padding: 7px 10px; 
            border: 1px solid #f97316; 
            border-radius: 6px; 
            background: #172554; 
            color: #ffffff; 
            font-size: 12px;
        }
        input[type="text"]::placeholder { color: #93c5fd; }
        button[type="submit"] { 
            padding: 7px 12px; 
            background: #22c55e; 
            color: white; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            font-weight: bold; 
            font-size: 12px;
        }
        button[type="submit"]:hover { background: #16a34a; }
    </style>
</head>
<body>
    {{ header|safe }}
    <div class="chat-outer-container">
        <div class="chat-main-wrapper">
            <div class="chat-header-info">
                <span>💬 Ümumi Çat</span>
                <span>BAL - <span id="userPointsDisplay">{{ points }}</span></span>
            </div>
            <div class="chat-box">
                {% if messages %}
                    {% for msg in messages %}
                        <div class="message-card" id="msg-{{ msg[0] }}">
                            <div class="message-content" id="content-{{ msg[0] }}"><b>{{ msg[1] }}</b>: {{ msg[2] }}</div>
                            {% if msg[1] == current_user %}
                                <div class="message-actions">
                                    <button class="action-btn" title="Redaktə et" onclick="editMessage('{{ msg[0] }}', '{{ msg[2] }}')">✏️</button>
                                    <button class="action-btn" title="Sil" onclick="deleteMessage('{{ msg[0] }}')">🗑️</button>
                                </div>
                            {% endif %}
                        </div>
                    {% endfor %}
                {% else %}
                    <p style="color: #93c5fd; text-align: center; border-left: none; background: transparent; font-size: 11px;">Hələ ki mesaj yoxdur. İlk mesajı sən yaz!</p>
                {% endif %}
            </div>
            <form method="POST" class="message-form">
                <input type="text" name="message" placeholder="Mesaj yaz..." autocomplete="off" required>
                <button type="submit">Göndər</button>
            </form>
        </div>
    </div>
    <script>
        function deleteMessage(msgId) {
            if(confirm("Bu mesajı silmək istədiyinizə əminsinizmi?")) {
                fetch('/delete_message/' + msgId, { method: 'POST' })
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

        function editMessage(msgId, oldText) {
            let newText = prompt("Mesajınızı redaktə edin:", oldText);
            if(newText !== null && newText.trim() !== "") {
                fetch('/edit_message/' + msgId, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content: newText.trim() })
                })
                .then(res => res.json())
                .then(data => {
                    if(data.success) {
                        location.reload();
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
            background: #172554;
            flex: 1;
            border: 2px solid #f97316;
            border-radius: 12px;
            padding: 12px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .users-title {
            font-size: 14px;
            font-weight: bold;
            color: #ffffff;
            border-bottom: 1px solid #3b82f6;
            padding-bottom: 6px;
            margin: 0 0 6px 0;
            text-align: center;
        }
        .user-card {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #1e3a8a;
            padding: 8px 12px;
            border-radius: 8px;
            border: 1px solid #3b82f6;
        }
        .user-left {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .user-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border: 1px solid #f97316;
            object-fit: cover;
            background: #111;
        }
        .user-name {
            font-size: 13px;
            font-weight: bold;
            color: #ffffff;
            margin: 0 0 2px 0;
        }
        .user-status {
            font-size: 11px;
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
            <p style="text-align: center; color: #93c5fd; font-size: 12px;">Hələ ki qeydiyyatdan keçmiş istifadəçi yoxdur.</p>
        {% endif %}
    </div>
</body>
</html>
'''

SEKIL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Şəkil</title>
    ''' + COMMON_STYLE + '''
    <style>
        .sekil-container {
            background: #172554;
            flex: 1;
            border: 2px solid #f97316;
            border-radius: 12px;
            padding: 12px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .sekil-title {
            font-size: 14px;
            font-weight: bold;
            color: #ffffff;
            border-bottom: 1px solid #3b82f6;
            padding-bottom: 6px;
            margin: 0;
            text-align: center;
        }
        .upload-box {
            background: #1e3a8a;
            border: 1px solid #3b82f6;
            border-radius: 8px;
            padding: 10px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        input[type="file"] {
            color: #93c5fd;
            font-size: 12px;
        }
        .btn-upload {
            background: #22c55e;
            color: white;
            border: none;
            padding: 8px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 12px;
            cursor: pointer;
            text-align: center;
        }
        .btn-upload:hover { background: #16a34a; }
        .gallery-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
            gap: 8px;
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
            height: 90px;
            object-fit: cover;
        }
        .gallery-user {
            font-size: 10px;
            color: #93c5fd;
            padding: 4px;
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
            <label style="font-size: 12px; color: #93c5fd; font-weight: bold;">Qalereyadan şəkil seç:</label>
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
                <p style="grid-column: 1 / -1; text-align: center; color: #93c5fd; font-size: 12px;">Hələ ki şəkil yüklənməyib.</p>
            {% endif %}
        </div>
    </div>
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
            padding: 10px;
            box-sizing: border-box;
        }
        .profile-container {
            background: #172554;
            border: 2px solid #f97316;
            border-radius: 14px;
            padding: 21px 27px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            width: 100%;
            max-width: 830px;
            box-sizing: border-box;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        .profile-title {
            font-size: 15px;
            font-weight: bold;
            color: #ffffff;
            border-bottom: 1px solid #3b82f6;
            padding-bottom: 6px;
            margin: 0;
            text-align: center;
        }
        .profile-header {
            display: flex;
            align-items: center;
            gap: 14px;
            background: #1e3a8a;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid #3b82f6;
        }
        .avatar-wrapper {
            position: relative;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            border: 2px solid #ef4444;
            box-shadow: 0 0 8px rgba(239, 68, 68, 0.7);
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
            font-size: 11px;
            background: #1e3a8a;
            border-radius: 50%;
            padding: 1px;
            border: 1px solid #f97316;
        }
        .profile-info h3 {
            margin: 0 0 2px 0;
            font-size: 15px;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .profile-info .status {
            color: #22c55e;
            font-size: 12px;
            font-weight: bold;
            margin: 0;
        }
        .gifts-box {
            background: #1e3a8a;
            border: 1px solid #3b82f6;
            border-radius: 6px;
            padding: 8px 12px;
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
            min-height: 36px;
            align-items: center;
        }
        .gift-item {
            font-size: 16px;
            background: #172554;
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid #f97316;
        }
        form {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin: 0;
        }
        input[type="text"] {
            width: 100%;
            padding: 9px 12px;
            border: 1px solid #3b82f6;
            border-radius: 6px;
            background: #1e3a8a;
            color: #ffffff;
            font-size: 13px;
            box-sizing: border-box;
            text-align: center;
        }
        input[type="text"]::placeholder { color: #93c5fd; }
        input[type="file"] {
            display: none;
        }
        .btn-blue {
            background: #0284c7;
            color: white;
            border: none;
            padding: 9px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 13px;
            cursor: pointer;
            text-align: center;
            width: 100%;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .btn-blue:hover { background: #0369a1; }
        .btn-gray {
            background: #334155;
            color: white;
            border: 1px solid #475569;
            padding: 9px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 13px;
            cursor: pointer;
            text-align: center;
            width: 100%;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .btn-gray:hover { background: #475569; }
        .btn-red {
            background: #dc2626;
            color: white;
            border: none;
            padding: 9px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 13px;
            cursor: pointer;
            text-align: center;
            width: 100%;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
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

    <div class="profile-wrapper">
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

            <div>
                <p style="font-size: 12px; margin: 0 0 3px 0; color: #93c5fd;">Hədiyyələr / Stikerlər:</p>
                <div class="gifts-box">
                    {% if gifts %}
                        {% for g in gifts %}
                            <span class="gift-item" title="Göndərən: {{ g[1] }}">{{ g[0] }}</span>
                        {% endfor %}
                    {% else %}
                        <span style="font-size: 12px; color: #93c5fd;">Hələ ki hədiyyə yoxdur.</span>
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
            padding: 10px;
            box-sizing: border-box;
        }
        .magaza-container {
            background: #172554;
            border: 2px solid #f97316;
            border-radius: 12px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            width: 100%;
            max-width: 680px;
            box-sizing: border-box;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        .magaza-title {
            font-size: 14px;
            font-weight: bold;
            color: #ffffff;
            border-bottom: 1px solid #3b82f6;
            padding-bottom: 6px;
            margin: 0;
            text-align: center;
        }
        .product-section {
            background: #1e3a8a;
            border: 1px solid #3b82f6;
            border-radius: 8px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .product-title {
            font-size: 13px;
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
        
        .emoji-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            max-height: 120px;
            overflow-y: auto;
            background: #172554;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #3b82f6;
        }
        .emoji-btn {
            font-size: 18px;
            cursor: pointer;
            padding: 4px 6px;
            background: #1e3a8a;
            border-radius: 6px;
            border: 1px solid transparent;
        }
        .emoji-btn:hover {
            transform: scale(1.1);
            border-color: #f97316;
            background: #2563eb;
        }
        select {
            width: 100%;
            padding: 9px 12px;
            background: #172554;
            color: #fff;
            border: 1px solid #3b82f6;
            border-radius: 6px;
            font-size: 12px;
            box-sizing: border-box;
        }
        .msg-alert {
            font-size: 12px;
            text-align: center;
            margin: 0;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="magaza-outer-wrapper">
        <div class="magaza-container">
            <p class="magaza-title">🛍️ MAQAZİN BÖLMƏSİ (BAL - <span id="userPointsDisplay">{{ points }}</span>)</p>

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
                    <div class="emoji-grid" style="margin-top: 6px;">
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
    </div>
</body>
</html>
'''

# Oyunlar Paneli
OYUN_PANEL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Oyunlar Paneli</title>
    ''' + COMMON_STYLE + '''
    <style>
        .panel-container {
            background: #172554;
            flex: 1;
            border: 2px solid #f97316;
            border-radius: 12px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 15px;
            text-align: center;
        }
        .panel-title {
            font-size: 16px;
            font-weight: bold;
            color: #ffffff;
            margin: 0;
        }
        .games-grid {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            justify-content: center;
        }
        .game-card {
            background: #1e3a8a;
            border: 2px solid #3b82f6;
            border-radius: 10px;
            padding: 20px;
            width: 180px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
            text-decoration: none;
            color: #fff;
            transition: 0.2s;
        }
        .game-card:hover {
            border-color: #f97316;
            transform: translateY(-3px);
            background: #1d4ed8;
        }
        .game-icon {
            font-size: 32px;
        }
        .game-name {
            font-size: 14px;
            font-weight: bold;
            margin: 0;
        }
        .game-desc {
            font-size: 11px;
            color: #93c5fd;
            margin: 0;
        }
    </style>
</head>
<body>
    {{ header|safe }}
    <div class="panel-container">
        <p class="panel-title">🎮 OYUNLAR PANELİ (BAL - <span id="userPointsDisplay">{{ points }}</span>)</p>
        <div class="games-grid">
            <a href="/oyun/wow" class="game-card">
                <span class="game-icon">🔠</span>
                <p class="game-name">WOW Oyunu</p>
                <p class="game-desc">Gizli hərfi tap, 5 bal qazan!</p>
            </a>
            <a href="/oyun/sual_cavab" class="game-card">
                <span class="game-icon">❓</span>
                <p class="game-name">Sual-Cavab</p>
                <p class="game-desc">1 dəqiqə ərzində cavabla, 8 bal qazan!</p>
            </a>
        </div>
    </div>
</body>
</html>
'''

WOW_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - WOW Oyunu</title>
    ''' + COMMON_STYLE + '''
    <style>
        .game-container {
            background: #172554;
            flex: 1;
            border: 2px solid #f97316;
            border-radius: 12px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 12px;
            text-align: center;
        }
        .game-box {
            background: #1e3a8a;
            border: 1px solid #3b82f6;
            border-radius: 8px;
            padding: 20px;
            width: 100%;
            max-width: 320px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            box-sizing: border-box;
        }
        .word-display {
            font-size: 24px;
            letter-spacing: 4px;
            font-weight: bold;
            color: #f97316;
            margin: 5px 0;
        }
        .btn-action {
            background: #22c55e;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
            font-size: 12px;
        }
        .btn-action:hover { background: #16a34a; }
        .back-link {
            font-size: 11px;
            color: #93c5fd;
            text-decoration: none;
            margin-top: 5px;
        }
        .back-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    {{ header|safe }}
    <div class="game-container">
        <div class="game-box">
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; font-weight: bold; color: #f97316;">
                <span>🔠 WOW SÖZ OYUNU</span>
                <span>BAL - <span id="userPointsDisplay">{{ points }}</span></span>
            </div>
            <p style="font-size: 11px; color: #93c5fd; margin: 0;">Sözdə 1 hərf əskikdir. Tap və 5 bal qazan!</p>
            <div class="word-display" id="maskedWord">---</div>
            <input type="text" id="userLetter" maxlength="1" placeholder="Bir hərf yaz" style="padding: 8px; border-radius: 6px; border: 1px solid #3b82f6; background: #172554; color: #fff; text-align: center; font-size: 14px; text-transform: uppercase;">
            <button class="btn-action" onclick="checkLetter()">Yoxla</button>
            <p id="wowResult" style="font-size: 12px; font-weight: bold; margin: 0;"></p>
            <a href="/oyun" class="back-link">⬅️ Oyunlar Panelinə Qayıt</a>
        </div>
    </div>
    <script>
        let words = [
            { full: "KITAB", hiddenIndex: 2, hiddenChar: "T" },
            { full: "QƏLƏM", hiddenIndex: 2, hiddenChar: "L" },
            { full: "MƏKTƏB", hiddenIndex: 3, hiddenChar: "T" },
            { full: "KOMPYUTER", hiddenIndex: 5, hiddenChar: "Y" },
            { full: "TELEFON", hiddenIndex: 4, hiddenChar: "F" },
            { full: "AZƏRBAYCAN", hiddenIndex: 3, hiddenChar: "R" },
            { full: "DOSKA", hiddenIndex: 2, hiddenChar: "S" }
        ];
        let currentWordObj = {};

        function nextWord() {
            let randomIndex = Math.floor(Math.random() * words.length);
            currentWordObj = words[randomIndex];
            
            let maskedArr = currentWordObj.full.split('');
            maskedArr[currentWordObj.hiddenIndex] = '_';
            document.getElementById('maskedWord').innerText = maskedArr.join(' ');
            document.getElementById('userLetter').value = '';
            document.getElementById('wowResult').innerText = '';
        }

        function checkLetter() {
            let userVal = document.getElementById('userLetter').value.toUpperCase();
            let res = document.getElementById('wowResult');
            if(!userVal) {
                res.style.color = "#f87171";
                res.innerText = "Zəhmət olmasa hərf daxil edin!";
                return;
            }
            if(userVal === currentWordObj.hiddenChar) {
                res.style.color = "#22c55e";
                res.innerText = "Təbriklər! Düzdür (+5 bal)";
                
                fetch('/add_points', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ points: 5 })
                }).then(res => res.json()).then(data => {
                    if(data.success) {
                        let elements = document.querySelectorAll('#userPointsDisplay');
                        elements.forEach(el => el.innerText = data.new_points);
                    }
                });

                setTimeout(nextWord, 1500);
            } else {
                res.style.color = "#f87171";
                res.innerText = "Səhvdir! Yenidən yoxla.";
            }
        }
        nextWord();
    </script>
</body>
</html>
'''

SUAL_CAVAB_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Sual-Cavab</title>
    ''' + COMMON_STYLE + '''
    <style>
        .game-container {
            background: #172554;
            flex: 1;
            border: 2px solid #f97316;
            border-radius: 12px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 12px;
            text-align: center;
        }
        .game-box {
            background: #1e3a8a;
            border: 1px solid #3b82f6;
            border-radius: 8px;
            padding: 20px;
            width: 100%;
            max-width: 340px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            box-sizing: border-box;
        }
        .timer-box {
            font-size: 13px;
            color: #f97316;
            font-weight: bold;
        }
        .question-text {
            font-size: 13px;
            color: #fff;
            margin: 5px 0;
            font-weight: bold;
        }
        .hint-text {
            font-size: 11px;
            color: #93c5fd;
            font-style: italic;
        }
        .btn-action {
            background: #22c55e;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 6px;
            font-weight: bold;
            cursor: pointer;
            font-size: 12px;
        }
        .btn-action:hover { background: #16a34a; }
        .back-link {
            font-size: 11px;
            color: #93c5fd;
            text-decoration: none;
            margin-top: 5px;
        }
        .back-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    {{ header|safe }}
    <div class="game-container">
        <div class="game-box">
            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; font-weight: bold; color: #f97316;">
                <span>❓ SUAL-CAVAB</span>
                <span>BAL - <span id="userPointsDisplay">{{ points }}</span></span>
            </div>
            <div class="timer-box">⏰ Qalan Vaxt: <span id="timeLeft">60</span> san</div>
            <div class="question-text" id="questionBox">Sual yüklənir...</div>
            <div class="hint-text" id="hintBox">İpucu: ...</div>
            <input type="text" id="userAnswer" placeholder="Cavabınızı yazın..." style="padding: 8px; border-radius: 6px; border: 1px solid #3b82f6; background: #172554; color: #fff; text-align: center; font-size: 12px;">
            <button class="btn-action" onclick="checkAnswer()">Cavab Ver</button>
            <p id="qaResult" style="font-size: 12px; font-weight: bold; margin: 0;"></p>
            <a href="/oyun" class="back-link">⬅️ Oyunlar Panelinə Qayıt</a>
        </div>
    </div>
    <script>
        let questions = [
            { q: "Azərbaycanın paytaxtı hansı şəhərdir?", hint: "B hərfi ilə başlayır", a: "BAKI" },
            { q: "Dünyanın ən böyük okeanı hansıdır?", hint: "Sakit okean da deyilir", a: "SAKIT OKEAN" },
            { q: "İşığın sürəti təxminən neçə km/san-dir?", hint: "300 min civarında", a: "300000" },
            { q: "Dəmirin kimyəvi işarəsi necədir?", hint: "Fe", a: "FE" },
            { q: "Günəş sistemində ən böyük planet hansıdır?", hint: "Yupiter", a: "YUPITER" }
        ];
        
        let currentQIndex = 0;
        let timer;
        let timeLeft = 60;

        function loadQuestion() {
            clearInterval(timer);
            timeLeft = 60;
            document.getElementById('timeLeft').innerText = timeLeft;
            
            if (currentQIndex >= questions.length) {
                currentQIndex = 0;
            }
            
            let qObj = questions[currentQIndex];
            document.getElementById('questionBox').innerText = qObj.q;
            document.getElementById('hintBox').innerText = "İpucu: " + qObj.hint;
            document.getElementById('userAnswer').value = '';
            document.getElementById('qaResult').innerText = '';

            timer = setInterval(() => {
                timeLeft--;
                document.getElementById('timeLeft').innerText = timeLeft;
                if (timeLeft <= 0) {
                    clearInterval(timer);
                    document.getElementById('qaResult').style.color = "#f87171";
                    document.getElementById('qaResult').innerText = "Vaxt bitdi! Növbəti suala keçilir...";
                    setTimeout(nextQuestion, 2000);
                }
            }, 1000);
        }

        function nextQuestion() {
            currentQIndex++;
            loadQuestion();
        }

        function checkAnswer() {
            let userVal = document.getElementById('userAnswer').value.trim().toUpperCase();
            let qObj = questions[currentQIndex];
            let res = document.getElementById('qaResult');

            if (!userVal) {
                res.style.color = "#f87171";
                res.innerText = "Zəhmət olmasa cavab yazın!";
                return;
            }

            if (userVal === qObj.a) {
                clearInterval(timer);
                res.style.color = "#22c55e";
                res.innerText = "Təbriklər! Düzgün cavab (+8 bal)";
                
                fetch('/add_points', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ points: 8 })
                }).then(res => res.json()).then(data => {
                    if(data.success) {
                        let elements = document.querySelectorAll('#userPointsDisplay');
                        elements.forEach(el => el.innerText = data.new_points);
                    }
                });

                setTimeout(nextQuestion, 2000);
            } else {
                res.style.color = "#f87171";
                res.innerText = "Səhv cavab! Yenidən cəhd et.";
            }
        }

        loadQuestion();
    </script>
</body>
</html>
'''

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
            padding: 15px; 
            text-align: center;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 14px;
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

@app.route('/add_points', methods=['POST'])
def add_points():
    if 'user' not in session:
        return {"success": False}, 401
    data = request.get_json()
    added_pts = data.get('points', 0)
    current_user = session['user']
    
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET points = points + ? WHERE nickname = ?", (added_pts, current_user))
    conn.commit()
    
    cursor.execute("SELECT points FROM users WHERE nickname = ?", (current_user,))
    new_pts = cursor.fetchone()[0]
    conn.close()
    
    return {"success": True, "new_points": new_pts}

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        msg = request.form.get('message').strip()
        if msg:
            cursor.execute("INSERT INTO messages (sender, content) VALUES (?, ?)", (session['user'], msg))
            conn.commit()
        conn.close()
        return redirect(url_for('chat'))
        
    cursor.execute("SELECT id, sender, content FROM messages")
    messages = cursor.fetchall()
    conn.close()
    
    points = get_user_points(session['user'])
    header = get_header_template(points)
        
    return render_template_string(CHAT_TEMPLATE, messages=messages, header=header, points=points, current_user=session['user'])

@app.route('/delete_message/<int:msg_id>', methods=['POST'])
def delete_message(msg_id):
    if 'user' not in session:
        return jsonify({"success": False, "error": "Giriş etməmisiniz"}), 401
        
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    cursor.execute("SELECT sender FROM messages WHERE id = ?", (msg_id,))
    row = cursor.fetchone()
    
    if row and row[0] == session['user']:
        cursor.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    
    conn.close()
    return jsonify({"success": False, "error": "Bu mesajı silməyə icazəniz yoxdur"})

@app.route('/edit_message/<int:msg_id>', methods=['POST'])
def edit_message(msg_id):
    if 'user' not in session:
        return jsonify({"success": False, "error": "Giriş etməmisiniz"}), 401
        
    data = request.get_json()
    new_content = data.get('content', '').strip()
    
    if not new_content:
        return jsonify({"success": False, "error": "Mesaj boş ola bilməz"})
        
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    cursor.execute("SELECT sender FROM messages WHERE id = ?", (msg_id,))
    row = cursor.fetchone()
    
    if row and row[0] == session['user']:
        cursor.execute("UPDATE messages SET content = ? WHERE id = ?", (new_content, msg_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
        
    conn.close()
    return jsonify({"success": False, "error": "Bu mesajı redaktə etməyə icazəniz yoxdur"})

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
                    cursor.execute("UPDATE messages SET sender = ? WHERE sender = ?", (new_name, current_user))
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
            cursor.execute("DELETE FROM messages WHERE sender = ?", (current_user,))
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
    return render_template_string(SUB_TEMPLATE, title="Vidyo", header=header)

@app.route('/oyun')
def oyun():
    if 'user' not in session:
        return redirect(url_for('index'))
    points = get_user_points(session['user'])
    header = get_header_template(points)
    return render_template_string(OYUN_PANEL_TEMPLATE, header=header, points=points)

@app.route('/oyun/wow')
def oyun_wow():
    if 'user' not in session:
        return redirect(url_for('index'))
    points = get_user_points(session['user'])
    header = get_header_template(points)
    return render_template_string(WOW_TEMPLATE, header=header, points=points)

@app.route('/oyun/sual_cavab')
def oyun_sual_cavab():
    if 'user' not in session:
        return redirect(url_for('index'))
    points = get_user_points(session['user'])
    header = get_header_template(points)
    return render_template_string(SUAL_CAVAB_TEMPLATE, header=header, points=points)

@app.route('/bildiris')
def bildiris():
    if 'user' not in session:
        return redirect(url_for('index'))
    points = get_user_points(session['user'])
    header = get_header_template(points)
    return render_template_string(SUB_TEMPLATE, title="Bildiriş", header=header)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
