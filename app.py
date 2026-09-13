from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import base64
import os

app = Flask(__name__)
app.secret_key = 'win_wid_gizli_kalit'

# Bazanın yaradılması və cədvəllərin qurulması (Məlumatların silinməməsi üçün qoruyucu yoxlamalar ilə)
def init_db():
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    
    # İstifadəçilər cədvəli
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
        
    # Mesajlar cədvəli
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
    
    # Hədiyyələr cədvəli
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            gift TEXT NOT NULL
        )
    ''')

    # ŞƏKİL BÖLMƏSİ ÜÇÜN CƏDVƏLLƏR
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

    # VİDEO BÖLMƏSİ ÜÇÜN CƏDVƏLLƏR
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

# ŞƏKİL BÖLMƏSİ (ŞƏKİLLƏR ÜÇÜN SHORTS/REELS FORMATI - SEKIL_TEMPLATE)
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
            border: 2px solid #f97316;
            border-radius: 12px;
            overflow-y: scroll;
            scroll-snap-type: y mandatory;
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
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
            background: #111;
        }
        .short-card img {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
        .upload-trigger-bar {
            position: absolute;
            top: 10px;
            right: 15px;
            z-index: 20;
            width: 110px;
            height: 32px;
        }
        .btn-open-upload {
            background: #22c55e;
            color: white;
            border: none;
            width: 100%;
            height: 100%;
            border-radius: 6px;
            font-weight: bold;
            font-size: 11px;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .btn-open-upload:hover { background: #16a34a; }

        .upload-modal {
            display: none;
            position: absolute;
            top: 50px;
            left: 50%;
            transform: translateX(-50%);
            background: #172554;
            border: 2px solid #f97316;
            padding: 15px;
            border-radius: 10px;
            z-index: 30;
            width: 80%;
            max-width: 300px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.7);
        }
        
        .shorts-actions {
            position: absolute;
            right: 15px;
            bottom: 140px; 
            width: 60px;
            height: 250px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-end;
            gap: 15px;
            z-index: 10;
            border: none;
            background: transparent;
        }
        .action-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            background: rgba(0, 0, 0, 0.5);
            padding: 10px;
            border-radius: 50%;
            cursor: pointer;
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #fff;
            width: 56px;  
            height: 56px; 
            justify-content: center;
            transition: 0.2s;
        }
        .action-item:hover {
            background: rgba(59, 130, 246, 0.6);
        }
        .action-item span {
            font-size: 26px; 
        }
        .action-count {
            font-size: 12px;
            font-weight: bold;
            margin-top: 4px;
            color: #fff;
            text-shadow: 0 1px 2px #000;
        }

        .shorts-info {
            position: absolute;
            left: 15px;
            bottom: 30px; 
            z-index: 10;
            color: #fff;
            text-shadow: 0 1px 3px #000;
        }
        .shorts-username {
            font-size: 15px;
            font-weight: bold;
            color: #fff;
            margin-bottom: 4px;
        }
        .delete-short-btn {
            background: #dc2626;
            border: none;
            color: white;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            cursor: pointer;
            margin-top: 5px;
        }

        .comments-drawer {
            position: absolute;
            bottom: -100%;
            left: 0;
            width: 100%;
            height: 50%;
            background: #172554;
            border-top: 2px solid #f97316;
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
            transition: 0.3s ease-in-out;
            z-index: 25;
            display: flex;
            flex-direction: column;
            padding: 10px;
            box-sizing: border-box;
        }
        .comments-drawer.active {
            bottom: 0;
        }
        .drawer-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            font-weight: bold;
            border-bottom: 1px solid #3b82f6;
            padding-bottom: 6px;
            color: #f97316;
        }
        .close-drawer {
            background: transparent;
            border: none;
            color: #fff;
            font-size: 16px;
            cursor: pointer;
        }
        .drawer-list {
            flex: 1;
            overflow-y: auto;
            margin: 8px 0;
            display: flex;
            flex-direction: column;
            gap: 6px;
            font-size: 11px;
        }
        .drawer-comment-item {
            background: #1e3a8a;
            padding: 5px 8px;
            border-radius: 6px;
            word-break: break-all;
        }
        .drawer-form {
            display: flex;
            gap: 6px;
        }
        .drawer-input {
            flex: 1;
            padding: 6px;
            background: #1e3a8a;
            border: 1px solid #3b82f6;
            border-radius: 6px;
            color: #fff;
            font-size: 11px;
        }
        .drawer-submit {
            background: #2563eb;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 11px;
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
            <form method="POST" enctype="multipart/form-data" action="/sekil/upload" style="display:flex; flex-direction:column; gap:8px;">
                <label style="font-size: 11px; color: #93c5fd; font-weight: bold;">Şəkil Seç:</label>
                <input type="file" name="sekil_file" accept="image/*" required style="font-size:10px; color:#fff;">
                <button type="submit" style="background:#22c55e; color:#fff; border:none; padding:6px; border-radius:4px; font-weight:bold; cursor:pointer; font-size:11px;">Yüklə</button>
                <button type="button" onclick="toggleUploadModal()" style="background:#dc2626; color:#fff; border:none; padding:4px; border-radius:4px; cursor:pointer; font-size:10px;">Bağla</button>
            </form>
        </div>

        {% if photos %}
            {% for p in photos %}
                <div class="short-card" id="photo-card-{{ p[0] }}">
                    <img src="{{ p[2] }}" alt="Şəkil">

                    <div class="shorts-info">
                        <div class="shorts-username">@{{ p[1] }}</div>
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
            <div style="display:flex; justify-content:center; align-items:center; height:100%; color:#93c5fd; font-size:13px; text-align:center; padding:20px;">
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

# VİDEO BÖLMƏSİ (VIDYO_TEMPLATE)
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
            border: 2px solid #f97316;
            border-radius: 12px;
            overflow-y: scroll;
            scroll-snap-type: y mandatory;
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
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
            background: #111;
        }
        .short-card video {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .upload-trigger-bar {
            position: absolute;
            top: 10px;
            right: 15px;
            z-index: 20;
            width: 110px;
            height: 32px;
        }
        .btn-open-upload {
            background: #22c55e;
            color: white;
            border: none;
            width: 100%;
            height: 100%;
            border-radius: 6px;
            font-weight: bold;
            font-size: 11px;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .btn-open-upload:hover { background: #16a34a; }

        .upload-modal {
            display: none;
            position: absolute;
            top: 50px;
            left: 50%;
            transform: translateX(-50%);
            background: #172554;
            border: 2px solid #f97316;
            padding: 15px;
            border-radius: 10px;
            z-index: 30;
            width: 80%;
            max-width: 300px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.7);
        }
        
        .shorts-actions {
            position: absolute;
            right: 15px;
            bottom: 140px; 
            width: 60px;
            height: 250px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-end;
            gap: 15px;
            z-index: 10;
            border: none;
            background: transparent;
        }
        .action-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            background: rgba(0, 0, 0, 0.5);
            padding: 10px;
            border-radius: 50%;
            cursor: pointer;
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #fff;
            width: 56px;  
            height: 56px; 
            justify-content: center;
            transition: 0.2s;
        }
        .action-item:hover {
            background: rgba(59, 130, 246, 0.6);
        }
        .action-item span {
            font-size: 26px; 
        }
        .action-count {
            font-size: 12px;
            font-weight: bold;
            margin-top: 4px;
            color: #fff;
            text-shadow: 0 1px 2px #000;
        }

        .shorts-info {
            position: absolute;
            left: 15px;
            bottom: 30px; 
            z-index: 10;
            color: #fff;
            text-shadow: 0 1px 3px #000;
        }
        .shorts-username {
            font-size: 15px;
            font-weight: bold;
            color: #fff;
            margin-bottom: 4px;
        }
        .delete-short-btn {
            background: #dc2626;
            border: none;
            color: white;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            cursor: pointer;
            margin-top: 5px;
        }

        .comments-drawer {
            position: absolute;
            bottom: -100%;
            left: 0;
            width: 100%;
            height: 50%;
            background: #172554;
            border-top: 2px solid #f97316;
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
            transition: 0.3s ease-in-out;
            z-index: 25;
            display: flex;
            flex-direction: column;
            padding: 10px;
            box-sizing: border-box;
        }
        .comments-drawer.active {
            bottom: 0;
        }
        .drawer-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            font-weight: bold;
            border-bottom: 1px solid #3b82f6;
            padding-bottom: 6px;
            color: #f97316;
        }
        .close-drawer {
            background: transparent;
            border: none;
            color: #fff;
            font-size: 16px;
            cursor: pointer;
        }
        .drawer-list {
            flex: 1;
            overflow-y: auto;
            margin: 8px 0;
            display: flex;
            flex-direction: column;
            gap: 6px;
            font-size: 11px;
        }
        .drawer-comment-item {
            background: #1e3a8a;
            padding: 5px 8px;
            border-radius: 6px;
            word-break: break-all;
        }
        .drawer-form {
            display: flex;
            gap: 6px;
        }
        .drawer-input {
            flex: 1;
            padding: 6px;
            background: #1e3a8a;
            border: 1px solid #3b82f6;
            border-radius: 6px;
            color: #fff;
            font-size: 11px;
        }
        .drawer-submit {
            background: #2563eb;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: bold;
            font-size: 11px;
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
            <form method="POST" enctype="multipart/form-data" action="/vidyo/upload" style="display:flex; flex-direction:column; gap:8px;">
                <label style="font-size: 11px; color: #93c5fd; font-weight: bold;">Shorts Videosu Seç:</label>
                <input type="file" name="video_file" accept="video/*" required style="font-size:10px; color:#fff;">
                <button type="submit" style="background:#22c55e; color:#fff; border:none; padding:6px; border-radius:4px; font-weight:bold; cursor:pointer; font-size:11px;">Yüklə</button>
                <button type="button" onclick="toggleUploadModal()" style="background:#dc2626; color:#fff; border:none; padding:4px; border-radius:4px; cursor:pointer; font-size:10px;">Bağla</button>
            </form>
        </div>

        {% if videos %}
            {% for v in videos %}
                <div class="short-card" id="video-card-{{ v[0] }}">
                    <video src="{{ v[2] }}" loop playsinline onclick="togglePlay(this)"></video>

                    <div class="shorts-info">
                        <div class="shorts-username">@{{ v[1] }}</div>
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
            <div style="display:flex; justify-content:center; align-items:center; height:100%; color:#93c5fd; font-size:13px; text-align:center; padding:20px;">
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
        <p>{{ title }} bölməsi tezliklə aktiv olacaqdır</p>
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

# Çat bölməsi "tezliklə aktiv olacaqdır" mesajı ilə yeniləndi
@app.route('/chat')
def chat():
    if 'user' not in session:
        return redirect(url_for('index'))
    points = get_user_points(session['user'])
    header = get_header_template(points)
    return render_template_string(SUB_TEMPLATE, title="Çat", header=header)

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

# ŞƏKİL BÖLMƏSİ ROUTELARI (SHORTS FORMATINA UYĞUN)
@app.route('/sekil')
def sekil():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    current_user = session['user']
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, uploader, image_data FROM photos ORDER BY id DESC")
    raw_photos = cursor.fetchall()
    
    photos = []
    for p in raw_photos:
        p_id = p[0]
        uploader = p[1]
        img_data = p[2]
        
        cursor.execute("SELECT COUNT(*) FROM photo_likes WHERE photo_id = ?", (p_id,))
        like_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM photo_likes WHERE photo_id = ? AND username = ?", (p_id, current_user))
        is_liked = cursor.fetchone()[0] > 0
        
        cursor.execute("SELECT id, username, comment FROM photo_comments WHERE photo_id = ?", (p_id,))
        comments = cursor.fetchall()
        
        photos.append((p_id, uploader, img_data, is_liked, like_count, comments))
        
    conn.close()
    points = get_user_points(current_user)
    header = get_header_template(points)
    return render_template_string(SEKIL_TEMPLATE, photos=photos, header=header, current_user=current_user)

@app.route('/sekil/upload', methods=['POST'])
def sekil_upload():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    file = request.files.get('sekil_file')
    if file and file.filename != '':
        file_bytes = file.read()
        encoded = base64.b64encode(file_bytes).decode('utf-8')
        mime_type = file.content_type or 'image/jpeg'
        img_data = f"data:{mime_type};base64,{encoded}"
        
        conn = sqlite3.connect('win_wid.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO photos (uploader, image_data) VALUES (?, ?)", (session['user'], img_data))
        conn.commit()
        conn.close()
        
    return redirect(url_for('sekil'))

@app.route('/sekil/like/<int:photo_id>', methods=['POST'])
def sekil_like(photo_id):
    if 'user' not in session:
        return jsonify({"success": False}), 401
    
    current_user = session['user']
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM photo_likes WHERE photo_id = ? AND username = ?", (photo_id, current_user))
    if cursor.fetchone():
        cursor.execute("DELETE FROM photo_likes WHERE photo_id = ? AND username = ?", (photo_id, current_user))
        liked = False
    else:
        cursor.execute("INSERT INTO photo_likes (photo_id, username) VALUES (?, ?)", (photo_id, current_user))
        liked = True
        
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM photo_likes WHERE photo_id = ?", (photo_id,))
    count = cursor.fetchone()[0]
    conn.close()
    
    return jsonify({"success": True, "liked": liked, "count": count})

@app.route('/sekil/comment/<int:photo_id>', methods=['POST'])
def sekil_comment(photo_id):
    if 'user' not in session:
        return jsonify({"success": False}), 401
        
    data = request.get_json()
    comment = data.get('comment', '').strip()
    if not comment:
        return jsonify({"success": False})
        
    current_user = session['user']
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO photo_comments (photo_id, username, comment) VALUES (?, ?, ?)", (photo_id, current_user, comment))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "user": current_user, "comment": comment})

@app.route('/sekil/share/<int:photo_id>', methods=['POST'])
def sekil_share(photo_id):
    if 'user' not in session:
        return jsonify({"success": False}), 401
        
    data = request.get_json()
    receiver = data.get('receiver', '').strip()
    current_user = session['user']
    
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE nickname = ?", (receiver,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "error": "İstifadəçi tapılmadı!"})
        
    cursor.execute("INSERT INTO photo_shares (photo_id, sender, receiver) VALUES (?, ?, ?)", (photo_id, current_user, receiver))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route('/sekil/delete/<int:photo_id>', methods=['POST'])
def sekil_delete(photo_id):
    if 'user' not in session:
        return jsonify({"success": False}), 401
        
    current_user = session['user']
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    cursor.execute("SELECT uploader FROM photos WHERE id = ?", (photo_id,))
    row = cursor.fetchone()
    
    if row and row[0] == current_user:
        cursor.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
        cursor.execute("DELETE FROM photo_likes WHERE photo_id = ?", (photo_id,))
        cursor.execute("DELETE FROM photo_comments WHERE photo_id = ?", (photo_id,))
        cursor.execute("DELETE FROM photo_shares WHERE photo_id = ?", (photo_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
        
    conn.close()
    return jsonify({"success": False, "error": "Bu şəkli silməyə icazəniz yoxdur"})

# VİDEO BÖLMƏSİ ROUTELARI
@app.route('/vidyo')
def vidyo():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    current_user = session['user']
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, uploader, video_data FROM videos ORDER BY id DESC")
    raw_videos = cursor.fetchall()
    
    videos = []
    for v in raw_videos:
        v_id = v[0]
        uploader = v[1]
        v_data = v[2]
        
        cursor.execute("SELECT COUNT(*) FROM video_likes WHERE video_id = ?", (v_id,))
        like_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM video_likes WHERE video_id = ? AND username = ?", (v_id, current_user))
        is_liked = cursor.fetchone()[0] > 0
        
        cursor.execute("SELECT id, username, comment FROM video_comments WHERE video_id = ?", (v_id,))
        comments = cursor.fetchall()
        
        videos.append((v_id, uploader, v_data, is_liked, like_count, comments))
        
    conn.close()
    points = get_user_points(current_user)
    header = get_header_template(points)
    return render_template_string(VIDYO_TEMPLATE, videos=videos, header=header, current_user=current_user)

@app.route('/vidyo/upload', methods=['POST'])
def vidyo_upload():
    if 'user' not in session:
        return redirect(url_for('index'))
    
    file = request.files.get('video_file')
    if file and file.filename != '':
        file_bytes = file.read()
        encoded = base64.b64encode(file_bytes).decode('utf-8')
        mime_type = file.content_type or 'video/mp4'
        video_data = f"data:{mime_type};base64,{encoded}"
        
        conn = sqlite3.connect('win_wid.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO videos (uploader, video_data) VALUES (?, ?)", (session['user'], video_data))
        conn.commit()
        conn.close()
        
    return redirect(url_for('vidyo'))

@app.route('/vidyo/like/<int:video_id>', methods=['POST'])
def vidyo_like(video_id):
    if 'user' not in session:
        return jsonify({"success": False}), 401
    
    current_user = session['user']
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM video_likes WHERE video_id = ? AND username = ?", (video_id, current_user))
    if cursor.fetchone():
        cursor.execute("DELETE FROM video_likes WHERE video_id = ? AND username = ?", (video_id, current_user))
        liked = False
    else:
        cursor.execute("INSERT INTO video_likes (video_id, username) VALUES (?, ?)", (video_id, current_user))
        liked = True
        
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM video_likes WHERE video_id = ?", (video_id,))
    count = cursor.fetchone()[0]
    conn.close()
    
    return jsonify({"success": True, "liked": liked, "count": count})

@app.route('/vidyo/comment/<int:video_id>', methods=['POST'])
def vidyo_comment(video_id):
    if 'user' not in session:
        return jsonify({"success": False}), 401
        
    data = request.get_json()
    comment = data.get('comment', '').strip()
    if not comment:
        return jsonify({"success": False})
        
    current_user = session['user']
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO video_comments (video_id, username, comment) VALUES (?, ?, ?)", (video_id, current_user, comment))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "user": current_user, "comment": comment})

@app.route('/vidyo/share/<int:video_id>', methods=['POST'])
def vidyo_share(video_id):
    if 'user' not in session:
        return jsonify({"success": False}), 401
        
    data = request.get_json()
    receiver = data.get('receiver', '').strip()
    current_user = session['user']
    
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE nickname = ?", (receiver,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "error": "İstifadəçi tapılmadı!"})
        
    cursor.execute("INSERT INTO video_shares (video_id, sender, receiver) VALUES (?, ?, ?)", (video_id, current_user, receiver))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route('/vidyo/delete/<int:video_id>', methods=['POST'])
def vidyo_delete(video_id):
    if 'user' not in session:
        return jsonify({"success": False}), 401
        
    current_user = session['user']
    conn = sqlite3.connect('win_wid.db')
    cursor = conn.cursor()
    cursor.execute("SELECT uploader FROM videos WHERE id = ?", (video_id,))
    row = cursor.fetchone()
    
    if row and row[0] == current_user:
        cursor.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        cursor.execute("DELETE FROM video_likes WHERE video_id = ?", (video_id,))
        cursor.execute("DELETE FROM video_comments WHERE video_id = ?", (video_id,))
        cursor.execute("DELETE FROM video_shares WHERE video_id = ?", (video_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
        
    conn.close()
    return jsonify({"success": False, "error": "Bu videonu silməyə icazəniz yoxdur"})

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
                    cursor.execute("UPDATE photo_likes SET username = ? WHERE username = ?", (new_name, current_user))
                    cursor.execute("UPDATE photo_comments SET username = ? WHERE username = ?", (new_name, current_user))
                    cursor.execute("UPDATE photo_shares SET sender = ? WHERE sender = ?", (new_name, current_user))
                    cursor.execute("UPDATE photo_shares SET receiver = ? WHERE receiver = ?", (new_name, current_user))
                    cursor.execute("UPDATE messages SET sender = ? WHERE sender = ?", (new_name, current_user))
                    cursor.execute("UPDATE videos SET uploader = ? WHERE uploader = ?", (new_name, current_user))
                    cursor.execute("UPDATE video_likes SET username = ? WHERE username = ?", (new_name, current_user))
                    cursor.execute("UPDATE video_comments SET username = ? WHERE username = ?", (new_name, current_user))
                    cursor.execute("UPDATE video_shares SET sender = ? WHERE sender = ?", (new_name, current_user))
                    cursor.execute("UPDATE video_shares SET receiver = ? WHERE receiver = ?", (new_name, current_user))
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
                message = "Profil şəkli dəyişdirildi!"
                
        elif action == 'delete_account':
            cursor.execute("DELETE FROM users WHERE nickname = ?", (current_user))
            conn.commit()
            conn.close()
            session.pop('user', None)
            return redirect(url_for('index'))
            
    cursor.execute("SELECT profile_pic, points FROM users WHERE nickname = ?", (current_user,))
    row = cursor.fetchone()
    pic = row[0] if row else ''
    points = row[1] if row and row[1] is not None else 500
    
    cursor.execute("SELECT gift, sender FROM gifts WHERE receiver = ?", (current_user,))
    gifts = cursor.fetchall()
    
    conn.close()
    header = get_header_template(points)
    return render_template_string(PROFIL_TEMPLATE, user=current_user, pic=pic, gifts=gifts, message=message, error=error, header=header)

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
            
            cursor.execute("SELECT points FROM users WHERE nickname = ?", (current_user,))
            pts = cursor.fetchone()[0]
            
            if pts < 20:
                message = "Balınız kifayət etmir (20 bal lazımdır)!"
                error = True
            else:
                cursor.execute("UPDATE users SET points = points - 20 WHERE nickname = ?", (current_user,))
                cursor.execute("INSERT INTO gifts (sender, receiver, gift) VALUES (?, ?, ?)", (current_user, receiver, gift))
                conn.commit()
                message = f"Hədiyyə @{receiver}-ə uğurla göndərildi!"
                
    cursor.execute("SELECT nickname FROM users")
    users = [row[0] for row in cursor.fetchall()]
    
    points = get_user_points(current_user)
    conn.close()
    
    header = get_header_template(points)
    return render_template_string(MAGAZA_TEMPLATE, users=users, current_user=current_user, points=points, message=message, error=error, header=header)

@app.route('/oyun')
def oyun_panel():
    if 'user' not in session:
        return redirect(url_for('index'))
    points = get_user_points(session['user'])
    header = get_header_template(points)
    return render_template_string(OYUN_PANEL_TEMPLATE, points=points, header=header)

@app.route('/oyun/wow')
def wow_oyunu():
    if 'user' not in session:
        return redirect(url_for('index'))
    points = get_user_points(session['user'])
    header = get_header_template(points)
    return render_template_string(WOW_TEMPLATE, points=points, header=header)

@app.route('/oyun/sual_cavab')
def sual_cavab():
    if 'user' not in session:
        return redirect(url_for('index'))
    points = get_user_points(session['user'])
    header = get_header_template(points)
    return render_template_string(SUAL_CAVAB_TEMPLATE, points=points, header=header)

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
    app.run(host='0.0.0.0', port=5000, debug=True)
