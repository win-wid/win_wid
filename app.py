from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_from_directory
import psycopg2
import psycopg2.extras
import base64
import os
import random
import tempfile
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'win_wid_gizli_kalit'

# Neon PostgreSQL Connection String
DATABASE_URL = 'postgresql://neondb_owner:npg_6bXlKpZOS3cP@ep-blue-sea-b4jbcx92-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require'

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                nickname TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                profile_pic TEXT,
                points INTEGER DEFAULT 0,
                name_color TEXT DEFAULT 'inherit',
                msg_color TEXT DEFAULT '#f8fafc',
                profile_sticker TEXT DEFAULT '',
                has_entry_effect INTEGER DEFAULT 0
            )
        ''')
        
        columns_users = [
            ("profile_pic", "TEXT"),
            ("points", "INTEGER DEFAULT 0"),
            ("name_color", "TEXT DEFAULT 'inherit'"),
            ("msg_color", "TEXT DEFAULT '#f8fafc'"),
            ("profile_sticker", "TEXT DEFAULT ''"),
            ("has_entry_effect", "INTEGER DEFAULT 0")
        ]
        for col_name, col_type in columns_users:
            try:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                conn.commit()
            except Exception:
                conn.rollback()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                reply_to_id INTEGER DEFAULT NULL,
                reply_to_user TEXT DEFAULT NULL,
                reply_to_content TEXT DEFAULT NULL
            )
        ''')

        columns_messages = [
            ("reply_to_id", "INTEGER DEFAULT NULL"),
            ("reply_to_user", "TEXT DEFAULT NULL"),
            ("reply_to_content", "TEXT DEFAULT NULL")
        ]
        for col_name, col_type in columns_messages:
            try:
                cursor.execute(f"ALTER TABLE messages ADD COLUMN {col_name} {col_type}")
                conn.commit()
            except Exception:
                conn.rollback()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_reactions (
                id SERIAL PRIMARY KEY,
                message_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                reaction TEXT NOT NULL,
                UNIQUE(message_id, username)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS typing_status (
                username TEXT PRIMARY KEY,
                is_typing INTEGER DEFAULT 0,
                updated_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS private_messages (
                id SERIAL PRIMARY KEY,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                content TEXT NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gifts (
                id SERIAL PRIMARY KEY,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                gift TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id SERIAL PRIMARY KEY,
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
                id SERIAL PRIMARY KEY,
                video_id INTEGER,
                username TEXT,
                comment TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_shares (
                id SERIAL PRIMARY KEY,
                video_id INTEGER,
                sender TEXT,
                receiver TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                username TEXT NOT NULL,
                content TEXT NOT NULL,
                is_read INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lives (
                id SERIAL PRIMARY KEY,
                host TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_gifts (
                id SERIAL PRIMARY KEY,
                live_id INTEGER,
                sender TEXT,
                gift TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_messages (
                id SERIAL PRIMARY KEY,
                live_id INTEGER,
                sender TEXT,
                content TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_likes (
                id SERIAL PRIMARY KEY,
                live_id INTEGER,
                username TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS police_officers (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                regiment TEXT NOT NULL,
                role TEXT DEFAULT 'Police'
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS court_cases (
                id SERIAL PRIMARY KEY,
                accused_user TEXT NOT NULL,
                reason TEXT NOT NULL,
                verdict TEXT DEFAULT 'Araşdırılır',
                judge TEXT DEFAULT 'Sayt Rəhbərliyi'
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS archived_logs (
                id SERIAL PRIMARY KEY,
                log_type TEXT NOT NULL,
                target_info TEXT NOT NULL,
                police_name TEXT NOT NULL,
                regiment TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS police_chat_messages (
                id SERIAL PRIMARY KEY,
                sender TEXT NOT NULL,
                regiment TEXT NOT NULL,
                content TEXT,
                image_data TEXT,
                created_at TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_stream_chunks (
                live_id INTEGER PRIMARY KEY,
                frame_data TEXT,
                audio_data TEXT,
                is_video_off INTEGER DEFAULT 0,
                is_audio_off INTEGER DEFAULT 0,
                is_paused INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_blocks (
                id SERIAL PRIMARY KEY,
                live_id INTEGER NOT NULL,
                blocked_user TEXT NOT NULL,
                UNIQUE(live_id, blocked_user)
            )
        ''')

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB Init Error: {e}")

init_db()

INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Giriş</title>
    <link rel="manifest" href="/manifest.json">
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
    <!-- Sağ yuxarı küncdəki əsas düymə -->
<div style="position: fixed; top: 15px; right: 15px; z-index: 99999;">
    <button onclick="document.getElementById('pwaModal').style.setProperty('display', 'flex', 'important');"" style="background-color: #ff7316; color: #fff; padding: 8px 14px; border-radius: 8px; font-weight: 700; font-size: 12px; border: none; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.5);">
        📲 Proqramı Yüklə
    </button>
</div>

<!-- Kiçik açılan pəncərə (Modal) -->
<div id="pwaModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 999999; justify-content: center; align-items: center;">
    <div style="background: #18181b; padding: 25px; border-radius: 16px; width: 300px; text-align: center; border: 2px solid #ff7316; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
        <h3 style="color: #fff; margin-bottom: 20px; font-size: 18px;">Tətbiqi yükləyək?</h3>
        
        <!-- Proqramı Yüklə düyməsi -->
        <button onclick="triggerInstall()" style="width: 100%; background-color: #ff7316; color: #fff; padding: 12px; border-radius: 10px; font-weight: 700; border: none; cursor: pointer; margin-bottom: 10px; font-size: 14px;">
            Proqramı Yüklə
        </button>
        
        <!-- Proqramı Yükləmə (Geri qayıt) düyməsi -->
        <button onclick="closeInstallModal()">Yükləmə</button>
    </div>
</div>
    <div class="modal-overlay" id="warningModal">
        <div class="warning-box">
            <div class="warning-text">
                WİN_WİD'Ə XOŞ GƏLMİSİNİZ..🤗<br><br>
                İSDİFADƏÇİ ŞƏRTLƏRİNİ OXUYUB SONRA SAYITA DAXİL OLUN...
            </div>
            <div class="warning-buttons">
                <a href="/istifade_sertleri" class="warning-btn btn-read" target="_blank">OXU</a>
                <button type="button" class="warning-btn btn-unread" onclick="this.closest('#warningModal').style.display='none'; document.querySelector('.modal-overlay').style.display='none';">OXUMA</button>
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
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
});

function openInstallModal() {
    let modal = document.getElementById('pwaModal');
    if (modal) {
        modal.style.setProperty('display', 'flex', 'important');
    }
}

function closeInstallModal() {
    let modal = document.getElementById('pwaModal');
    if (modal) {
        modal.style.setProperty('display', 'none', 'important');
    }
}

function triggerInstall() {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('İstifadəçi proqramı quraşdırdı');
            }
            deferredPrompt = null;
            closeInstallModal();
        });
    } else {
        alert('Bu səhifə artıq quraşdırılıb və ya brauzer hələ sorğunu aktivləşdirməyib. Brauzerin menyusundan (3 nöqtə) "Ana ekrana əlavə et" seçə bilərsiniz.');
    }
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
    <link rel="manifest" href="/manifest.json">
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
    <link rel="manifest" href="/manifest.json?v=2">
</head>
<body>
    <div class="terms-box">
        <h2>WİN_WİD – QAYDALAR VƏ ŞƏRTLƏR</h2>
        <p>Saytımızdan istifadə etməzdən əvvəl bu qaydalarla tanış olmağınızı xahiş edirik. Sayta girməklə və ya qeydiyyatdan keçməklə bu şərtlərlə razılaşmış olursunuz.</p>
        
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

        <h3>4. Polis Nəzarəti və Səlahiyyətləri</h3>
        <p>Saytdakı asayişi və qayda-qanunu qorumaq üçün WİN_WİD rəhbərliyinin təyin etmiş Polis əməkdaşları platformada birbaşa nəzarət hüququna malikdir.</p>

        <h3>5. Mesajların Silinməsi və Arxiv</h3>
        <p>Qaydaları pozulduqda, təhqiramiz, söyüşlü və ya spam xarakterli mesajlar yazıldıqda... Polislər tərəfindən xəbərdarlıq edilmədən mesajlar silinə bilər. Silinən bütün mesajlar, silən polisin məlumatı ilə birlikdə təhlükəsizlik üçün İdarə Mərkəzində arxiv otaqına düşür.</p>

        <h3>6. Keçici Bloklama</h3>
        <p>Sayt qaydalarını pozan istifadəçilər Polis əməkdaşları tərəfindən 24 saatlıq müvəqqəti bloklana bilər. Bloklanan istifadəçi müddət bitənədək platformadan istifadə edə bilməz.</p>

        <h3>7. Məhkəmə Sistemi</h3>
        <p>Bloklanan və ya qaydaları kobud şəkildə pozan istifadəçilərin işləri avtomatik olaraq Məhkəmə Bölməsinə yönləndirilir. Yekun qərar və hökm Sayt Rəhbərliyi tərəfindən çıxarılır.</p>

        <h3>8. Mülkiyyət Hüququ</h3>
        <ul>
            <li>WİN_WİD-də olan bütün yazılar, şəkillər, loqolar və dizayn bizə məxsusdur.</li>
            <li>Bizim icazəmiz olmadan saytdakı məlumatları kopyalayıb başqa yerlərdə istifadə etmək olmaz.</li>
        </ul>

        <h3>9. Məsuliyyət və Təhlükəsizlik</h3>
        <ul>
            <li>Biz çalışırıq ki, sayt həmişə əla işləsin, lakin texniki nasazlıqlar ola bilər.</li>
            <li>Hər hansı kənar müdaxilə (haker hücumu) nəticəsində sayta məxsus məlumatlar oğurlanarsa və ya yayılarsa, tərəflər qanunvericiliyə uyğun olaraq məsuliyyət daşıyır və pozuntularla bağlı məhkəmə müstəvisində hüquqi addımlar atıla bilər.</li>
            <li>Qaydaları pozduğunuz təqdirdə hesabınızı bloklaya və ya silə bilərik.</li>
        </ul>
        
    </div>
</body>
</html>
'''

def get_header_template(has_unread_notifs=False):
    dot_html = '<span style="position: absolute; top: 8px; right: 24px; width: 10px; height: 10px; background: #ef4444; border-radius: 50%;"></span>' if has_unread_notifs else ''
    return f'''
    <div class="nav-bar"> 
    </a>
        <a href="/vidyo" class="nav-item">
            <span class="icon">📹</span>
            <span>Vidyolar</span>
         </a>
        <a href="/istifadeciler" class="nav-item">
            <span class="icon">👥</span>
            <span>İstifadəçilər</span>
        </a> 
        <a href="/oyun" class="nav-item">
            <span class="icon">🎮</span>
            <span>Oyun</span>
        </a>
        <a href="/magaza" class="nav-item">
            <span class="icon">🛍</span>
            <span>Market</span>
        </a>
        <a href="/canli" class="nav-item">
            <span class="icon">🔴</span>
            <span>Canlı</span>
        </a>
        <a href="/bildiris" class="nav-item" style="position: relative;">
            <span class="icon">🔔</span>
            <span>Bildiriş</span>
        </a>
            <a href="/profil" class="nav-item">
            <span class="icon">👤</span>
            <span>Profil</span>
            {dot_html}
        </a>
             <a href="/kukuli" class="nav-item">
            <span class="icon">🐻</span>
            <span>KUKULİ</span>
        </a>
    </div>
'''

COMMON_STYLE = '''
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { 
            font-family: 'Plus Jakarta Sans', sans-serif; 
            margin: 0; 
            padding: 15px; 
            padding-bottom: 90px; 
            background: #09090b; 
            color: #f8fafc; 
            display: flex; 
            flex-direction: column; 
            min-height: 100vh; 
            box-sizing: border-box; 
        }
        .nav-bar {
    position: fixed;
    bottom: 12px;
    left: 12px;
    width: calc(100% - 24px);
    background: #f97316;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 18px;
    padding: 10px 5px;
    display: flex;
    justify-content: space-around;
    align-items: center;
    gap: 5px;
    overflow-x: auto;
    box-shadow: 0 5px 20px rgba(0,0,0,0.4);
    z-index: 99999;
    box-sizing: border-box;
}
        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-decoration: none;
            color: #a1a1aa;
            padding: 6px 8px;
            border-radius: 10px;
            font-size: 11px;
            font-weight: 600;
            transition: all 0.2s ease;
            white-space: nowrap;
        }
        .nav-item .icon {
            font-size: 22px;
            margin-bottom: 2px;
        }
        .nav-item:hover, .nav-item:active {
            color: #f97316;
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
            position: relative;
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
        .reactions-container {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 8px;
        }
        .reaction-pill {
            background: rgba(0,0,0,0.4);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 12px;
            padding: 2px 8px;
            font-size: 13px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            color: #fff;
            transition: transform 0.1s;
        }
        .reaction-pill:hover { transform: scale(1.1); }
        .add-reaction-btn {
            background: rgba(255,255,255,0.1);
            border: 1px dashed rgba(255,255,255,0.3);
            border-radius: 50%;
            width: 24px;
            height: 24px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            cursor: pointer;
            color: #fff;
            margin-top: 8px;
        }
        .reaction-picker {
            display: none;
            position: absolute;
            background: rgba(15,15,18,0.95);
            border: 1px solid #f97316;
            border-radius: 14px;
            padding: 6px 10px;
            gap: 6px;
            z-index: 50;
            box-shadow: 0 10px 20px rgba(0,0,0,0.8);
        }
        .reaction-picker span {
            font-size: 18px;
            cursor: pointer;
            transition: transform 0.1s;
        }
        .reaction-picker span:hover { transform: scale(1.3); }

        .reply-preview-box {
            display: none;
            background: rgba(9,9,11,0.85);
            padding: 10px 16px;
            border-left: 4px solid #f97316;
            font-size: 13px;
            color: #d4d4d8;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid rgba(255,255,255,0.08);
        }
        .quoted-box {
            background: rgba(0,0,0,0.3);
            border-left: 3px solid #f97316;
            padding: 6px 10px;
            margin-bottom: 8px;
            border-radius: 6px;
            font-size: 13px;
            color: #cbd5e1;
        }

        .typing-indicator-bar {
            padding: 6px 20px;
            font-size: 13px;
            color: #a1a1aa;
            font-style: italic;
            background: rgba(9,9,11,0.5);
            min-height: 22px;
        }

        .chat-form {
            display: flex;
            padding: 18px;
            background: rgba(9, 9, 11, 0.7);
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            gap: 14px;
            align-items: center;
            flex-direction: column;
        }
        .chat-form-row {
            display: flex;
            width: 100%;
            gap: 14px;
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
            <div class="points-box-orange">TOPLANMIŞ WON: <span id="userPointsDisplay" style="color: #000000;">{{ user_points }}</span></div>
            <div class="real-time-clock" id="realTimeClock">00:00:00</div>
            <span>💬 ÜMUMİ ÇAT BÖLMƏSİ</span>
        </div>
        
        <div class="messages-box" id="messagesBox">
            {% if messages %}
                {% for m in messages %}
                    <div class="message-bubble {% if m[1] == current_user %}my-message{% endif %}" id="msg-{{ m[0] }}">
                        {% if m[6] %}
                            <div class="quoted-box">
                                <b>@{{ m[7] }}</b>: {{ m[8] }}
                            </div>
                        {% endif %}

                        <div class="msg-user" style="color: {{ m[3] if m[3] and m[3] != 'inherit' else ('#fed7aa' if m[1] == current_user else '#f97316') }};">@{{ m[1] }} {{ m[5] }}</div>
                        <p class="msg-text" id="msg-text-{{ m[0] }}" style="color: {{ m[4] if m[4] and m[4] != '#eab308' else '#f8fafc' }};">{{ m[2] }}</p>
                        
                        <div class="reactions-container" id="reactions-list-{{ m[0] }}">
                            {% if m[9] %}
                                {% for emoji, count in m[9].items() %}
                                    <span class="reaction-pill" onclick="toggleReaction('{{ m[0] }}', '{{ emoji }}')">{{ emoji }} {{ count }}</span>
                                {% endfor %}
                            {% endif %}
                        </div>

                        <div class="msg-actions">
                            <button onclick="prepareReply('{{ m[0] }}', '{{ m[1] }}', '{{ m[2]|e }}')">Cavab ver</button>
                            <button class="add-reaction-btn" onclick="togglePicker('picker-{{ m[0] }}')">😊</button>
                            
                            <div class="reaction-picker" id="picker-{{ m[0] }}">
                                <span onclick="addReaction('{{ m[0] }}', '👍')">👍</span>
                                <span onclick="addReaction('{{ m[0] }}', '❤️')">❤️</span>
                                <span onclick="addReaction('{{ m[0] }}', '😂')">😂</span>
                                <span onclick="addReaction('{{ m[0] }}', '🔥')">🔥</span>
                                <span onclick="addReaction('{{ m[0] }}', '🗿')">🗿</span>
                                <span onclick="addReaction('{{ m[0] }}', '😎')">😎</span>
                                <span onclick="addReaction('{{ m[0] }}', '😱')">😱</span>
                                <span onclick="addReaction('{{ m[0] }}', '🤘')">🤘</span>
                                <span onclick="addReaction('{{ m[0] }}', '🤔')">🤔</span>
                                <span onclick="addReaction('{{ m[0] }}', '🤯')">🤯</span>
                                <span onclick="addReaction('{{ m[0] }}', '🤠')">🤠</span>
                                <span onclick="addReaction('{{ m[0] }}', '🤬')">🤬</span>
                                <span onclick="addReaction('{{ m[0] }}', '🥹')">🥹</span>
                            </div>

                            {% if m[1] == current_user or is_admin or is_police %}
                                {% if m[1] == current_user %}
                                    <button onclick="editMessage('{{ m[0] }}')">Redaktə et</button>
                                {% endif %}
                                <button onclick="deleteMessage('{{ m[0] }}')" style="color: #fca5a5;">Sil</button>
                            {% endif %}
                        </div>
                    </div>
                {% endfor %}
            {% else %}
                <p style="text-align: center; color: #a1a1aa; font-size: 15px; margin: auto;">Hələ ki mesaj yoxdur. İlk mesajı sən yaz!</p>
            {% endif %}
        </div>

        <div class="typing-indicator-bar" id="typingIndicator"></div>

        <form class="chat-form" method="POST" action="/chat/send" id="chatForm">
            <div class="reply-preview-box" id="replyPreviewBox">
                <div><span id="replyUserText" style="font-weight: bold; color: #f97316;"></span> istifadəçisinə cavab yazılır: <span id="replyContentText"></span></div>
                <button type="button" onclick="cancelReply()" style="background:none; border:none; color:#ef4444; font-weight:bold; cursor:pointer;">✕</button>
            </div>
            <input type="hidden" name="reply_to_id" id="replyToIdInput" value="">
            <div class="chat-form-row">
                <input type="text" name="content" id="chatInput" class="chat-input" placeholder="Mesajınızı yazın..." required autocomplete="off" oninput="notifyTyping()">
                <button type="submit" class="chat-submit">Göndər</button>
            </div>
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

        function togglePicker(pickerId) {
            let picker = document.getElementById(pickerId);
            picker.style.display = picker.style.display === 'flex' ? 'none' : 'flex';
        }

        function addReaction(msgId, emoji) {
            fetch('/chat/reaction/' + msgId, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ emoji: emoji })
            })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    document.getElementById('picker-' + msgId).style.display = 'none';
                    updateReactionsUI(msgId, data.reactions);
                }
            });
        }

        function toggleReaction(msgId, emoji) {
            addReaction(msgId, emoji);
        }

        function updateReactionsUI(msgId, reactionsObj) {
            let container = document.getElementById('reactions-list-' + msgId);
            container.innerHTML = '';
            for (let [emoji, count] of Object.entries(reactionsObj)) {
                container.innerHTML += `<span class="reaction-pill" onclick="toggleReaction('${msgId}', '${emoji}')">${emoji} ${count}</span>`;
            }
        }

        function prepareReply(msgId, username, content) {
            document.getElementById('replyToIdInput').value = msgId;
            document.getElementById('replyUserText').innerText = '@' + username;
            document.getElementById('replyContentText').innerText = content;
            document.getElementById('replyPreviewBox').style.display = 'flex';
            document.getElementById('chatInput').focus();
        }

        function cancelReply() {
            document.getElementById('replyToIdInput').value = '';
            document.getElementById('replyPreviewBox').style.display = 'none';
        }

        let typingTimeout;
        function notifyTyping() {
            fetch('/chat/typing', { method: 'POST' });
            clearTimeout(typingTimeout);
            typingTimeout = setTimeout(() => {
                fetch('/chat/stop_typing', { method: 'POST' });
            }, 2000);
        }

        function checkTypingStatus() {
            fetch('/chat/get_typing')
            .then(res => res.json())
            .then(data => {
                let indicator = document.getElementById('typingIndicator');
                if(data.typing_users && data.typing_users.length > 0) {
                    indicator.innerText = "@" + data.typing_users.join(', ') + " YAZIYOR....";
                } else {
                    indicator.innerText = "";
                }
            });
        }
        setInterval(checkTypingStatus, 2500);

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

OYUN_MENU_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Oyunlar Bölməsi</title>
    ''' + COMMON_STYLE + '''
    <style>
        .games-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
            box-sizing: border-box;
        }
        .games-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            width: 100%;
            max-width: 700px;
        }
        .game-card {
            background: rgba(24, 24, 27, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 24px;
            padding: 35px;
            text-align: center;
            box-shadow: 0 20px 45px rgba(0,0,0,0.6);
            transition: transform 0.2s, border-color 0.2s;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            gap: 20px;
        }
        .game-card:hover {
            transform: translateY(-5px);
            border-color: #f97316;
        }
        .game-icon {
            font-size: 50px;
        }
        .game-title {
            font-size: 20px;
            font-weight: 700;
            color: #f97316;
            margin: 0;
        }
        .game-desc {
            font-size: 14px;
            color: #d4d4d8;
            margin: 0;
            line-height: 1.5;
        }
        .play-btn {
            background: linear-gradient(135deg, #f97316, #ea580c);
            color: white;
            border: none;
            padding: 14px;
            border-radius: 14px;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            text-decoration: none;
            box-shadow: 0 4px 15px rgba(249, 115, 22, 0.35);
            display: inline-block;
            transition: transform 0.2s;
        }
        .play-btn:hover { transform: translateY(-2px); }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="games-container">
           <!-- Reklam lenti -->
    <div class="ad-banner-container" style="width: 100%; max-width: 700px; margin-bottom: 20px; overflow: hidden; background: rgba(24, 24, 27, 0.9); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 12px; padding: 12px; text-align: center;">
        <div class="ad-banner-track" style="position: relative; height: 24px; overflow: hidden;">
            <a href="#" class="ad-slide active" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; text-decoration: none; color: #f8fafc; font-size: 13px; font-weight: 600; opacity: 1; transition: all 0.6s ease-in-out;">🚀 Tərəfdaş Sayt: WİN_WİD Dostları</a>
            <a href="#" class="ad-slide" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; text-decoration: none; color: #f8fafc; font-size: 13px; font-weight: 600; opacity: 0; transition: all 0.6s ease-in-out;">🔥 Yeni Elanlar və Xidmətlər Burada!</a>
            <a href="#" class="ad-slide" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; text-decoration: none; color: #f8fafc; font-size: 13px; font-weight: 600; opacity: 0; transition: all 0.6s ease-in-out;">📢 Reklam yerləşdirmək üçün bizə yazın!</a>
            <a href="#" class="ad-slide" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; text-decoration: none; color: #f8fafc; font-size: 13px; font-weight: 600; opacity: 0; transition: all 0.6s ease-in-out;">💎 Reklam: 1 Ay 2 AZN | 2 Ay 4 AZN | 3 Ay 6 AZN</a>
            <a href="#" class="ad-slide" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; text-decoration: none; color: #f8fafc; font-size: 13px; font-weight: 600; opacity: 0; transition: all 0.6s ease-in-out;"> REKLAM - TIK_TOK"DAN AVZ_370 ADLI SƏYFƏMİ İZLƏ!</a>
            
        </div>
    </div>
        <h2 style="color: #f97316; margin-bottom: 30px; font-size: 26px; text-align: center;">🎮 OYUNLAR MƏRKƏZİ</h2>
        
        <div class="games-grid">
            <div class="game-card">
                <div class="game-icon">🔤</div>
                <h3 class="game-title">1. WOW OYUNU</h3>
                <p class="game-desc">Sözlərdə əskik olan 1 hərfi tapın, hər düzgün cavaba 5 bal qazanın və növbəti sözə keçin!</p>
                <a href="/oyun/wow" class="play-btn">Oyna 🚀</a>
            </div>

            <div class="game-card">
                <div class="game-icon">❓</div>
                <h3 class="game-title">2. SUAL CAVAB OYUNU</h3>
                <p class="game-desc">İstədiyiniz mövzudan 40 dinamik sual. 30 saniyə vaxtınız var, düzgün cavab +5 bal!</p>
                <a href="/oyun/sual" class="play-btn">Oyna 🚀</a>
            </div>
        </div>
    </div>
    <script>
    // Reklam lentinin fırlanma mexanizmi
    const slides = document.querySelectorAll('.ad-slide');
    let currentSlide = 0;

    function nextSlide() {
        if (slides.length === 0) return;
        slides[currentSlide].classList.remove('active');
        slides[currentSlide].style.opacity = '0';
        
        currentSlide = (currentSlide + 1) % slides.length;
        
        slides[currentSlide].classList.add('active');
        slides[currentSlide].style.opacity = '1';
    }

    if (slides.length > 0) {
        setInterval(nextSlide, 3500); // Hər 3.5 saniyədən bir dəyişir
    }
</script>
</body>
</html>
'''

WOW_OYUNU_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - WOW Oyunu</title>
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
            max-width: 500px;
            box-shadow: 0 20px 45px rgba(0,0,0,0.7);
            text-align: center;
            box-sizing: border-box;
        }
        .masked-word {
            font-size: 32px;
            font-weight: 800;
            letter-spacing: 6px;
            color: #f97316;
            margin: 20px 0;
            background: rgba(9, 9, 11, 0.6);
            padding: 15px;
            border-radius: 14px;
            border: 1px solid rgba(249, 115, 22, 0.3);
        }
        input[type="text"] {
            width: 100%;
            padding: 15px;
            background: rgba(9, 9, 11, 0.8);
            border: 1px solid #f97316;
            border-radius: 14px;
            color: #fff;
            font-size: 18px;
            box-sizing: border-box;
            margin-bottom: 15px;
            text-align: center;
            text-transform: uppercase;
        }
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
        }
        .back-link {
            display: inline-block;
            margin-top: 20px;
            color: #a1a1aa;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
        }
        .back-link:hover { color: #fff; }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="game-wrapper">
        <div class="game-card">
            <h2 style="color: #f97316; margin-top: 0; font-size: 22px;">🔤 WOW OYUNU (HƏRFİ TAP)</h2>
            <p style="color: #d4d4d8; font-size: 15px;">Aşağıdakı sözdə əskik olan 1 hərfi tapın (+5 bal):</p>
            
            <div class="masked-word">{{ masked_word }}</div>

            <form method="POST" action="/oyun/wow/cavabla">
                <input type="hidden" name="hidden_letter" value="{{ hidden_letter }}">
                <input type="hidden" name="full_word" value="{{ full_word }}">
                <input type="text" name="user_letter" placeholder="Əskik hərf..." maxlength="1" required autocomplete="off" autofocus>
                <button type="submit" class="game-btn">Hərfi Yoxla 🎯</button>
            </form>

            {% if message %}
                <p style="margin-top: 15px; font-weight: 700; color: {% if success %}#4ade80{% else %}#f87171{% endif %};">{{ message }}</p>
            {% endif %}

            <a href="/oyun" class="back-link">← Oyunlar Menyusuna Qayıt</a>
        </div>
    </div>
</body>
</html>
'''

SUAL_CAVAB_TEMPLATE = '''
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
        }
        .score-badge {
            margin-top: 15px;
            font-size: 15px;
            font-weight: 600;
            color: #4ade80;
        }
        .back-link {
            display: inline-block;
            margin-top: 20px;
            color: #a1a1aa;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
        }
        .back-link:hover { color: #fff; }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="game-wrapper">
        <div class="game-card">
            <h2 style="color: #f97316; margin-top: 0; font-size: 22px;">❓ SUAL-CAVAB OYUNU</h2>
            
            <div class="timer-box" id="timer">30</div>
            <p class="question-text">❓ {{ question }}</p>

            <form method="POST" action="/oyun/sual/cavabla" id="answerForm">
                <input type="hidden" name="correct_answer" value="{{ answer }}">
                <input type="text" name="user_answer" placeholder="Cavabınızı yazın..." required autocomplete="off" autofocus>
                <button type="submit" class="game-btn">Cavabı Göndər (+5 bal)</button>
            </form>

            <p class="score-badge">Mövzu: {{ topic }} (Sual saylı bank: 40 Dinamik)</p>

            {% if message %}
                <p style="margin-top: 15px; font-weight: 700; color: {% if success %}#4ade80{% else %}#f87171{% endif %};">{{ message }}</p>
            {% endif %}

            <a href="/oyun" class="back-link">← Oyunlar Menyusuna Qayıt</a>

            <script>
                let timeLeft = 30;
                let timerElement = document.getElementById('timer');
                let countdown = setInterval(function() {
                    timeLeft--;
                    timerElement.innerText = timeLeft;
                    if(timeLeft <= 0) {
                        clearInterval(countdown);
                        alert("Vaxt bitdi! Növbəti suala keçilir.");
                        window.location.href = "/oyun/sual";
                    }
                }, 1000);
            </script>
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
        .profile-btn {
            background: linear-gradient(135deg, #0284c7, #0369a1);
            color: white;
            border: none;
            padding: 10px 18px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 14px;
            cursor: pointer;
            text-decoration: none;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
            transition: transform 0.2s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }
        .profile-btn:hover {
            transform: translateY(-2px);
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
        <p class="users-title">👥 SAYIT İSTİFADƏÇİLƏRİ</p>
        
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
                            <a href="/istifadeci_profil/{{ u[0] }}" class="profile-btn">👤 PROFİL BAX</a>
                            <a href="/ozel_mesaj/{{ u[0] }}" class="msg-btn">💬 MESAJ YAZ</a>
                            {% if is_admin or is_police %}
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

PUBLIC_PROFILE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - @{{ target_user }} Profili</title>
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
            border: 2px solid #f97316;
            overflow: hidden;
            background: #111;
            flex-shrink: 0;
        }
        .avatar-wrapper img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 50%;
        }
        .profile-info h3 {
            margin: 0 0 6px 0;
            font-size: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 700;
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
        .action-btn-row {
            display: flex;
            gap: 10px;
        }
        .back-btn {
            background: rgba(39, 39, 42, 0.9);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.12);
            padding: 14px;
            border-radius: 14px;
            font-weight: 600;
            font-size: 15px;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
            display: block;
        }
        .back-btn:hover { background: rgba(39, 39, 42, 1); }
        .btn-block {
            background: linear-gradient(135deg, #dc2626, #991b1b);
            color: #fff;
            border: none;
            flex: 1;
            padding: 14px;
            border-radius: 14px;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
            transition: transform 0.2s;
        }
        .btn-report {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: #fff;
            border: none;
            flex: 1;
            padding: 14px;
            border-radius: 14px;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
            transition: transform 0.2s;
        }
        .btn-block:hover, .btn-report:hover { transform: translateY(-1px); }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="profile-wrapper">
        <div class="profile-container">
            <p class="profile-title">@{{ target_user }} - İstifadəçi Profili</p>
            
            {% if message %}
                <p style="text-align:center; font-weight:700; color:#4ade80; margin:0;">{{ message }}</p>
            {% endif %}

            <div class="profile-header">
                <div class="avatar-wrapper">
                    <img src="{{ pic if pic else 'https://i.imgur.com/6VBx3io.png' }}" alt="Profil Şəkli">
                </div>
                <div class="profile-info">
                    <h3 style="color: {{ name_color if name_color and name_color != 'inherit' and name_color != '#eab308' else '#f8fafc' }};">@{{ target_user }} {{ profile_sticker }} 👑</h3>
                    <p style="color: #4ade80; font-size: 14px; font-weight: 600; margin: 0;">● Aktivdir</p>
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

            <a href="/ozel_mesaj/{{ target_user }}" class="back-btn" style="background: linear-gradient(135deg, #f97316, #ea580c); color: #fff; font-weight: 700; text-align: center;">💬 Mesaj Göndər</a>
            
            <div class="action-btn-row">
                <form action="/blok_et/{{ target_user }}" method="POST" style="flex:1; margin:0;" onsubmit="return confirm('@{{ target_user }} istifadəçisini bloklamaq istədiyinizə əminsinizmi?');">
                    <button type="submit" class="btn-block">⛔ BLOKLA</button>
                </form>
                <form action="/sikayet_et_profil/{{ target_user }}" method="POST" style="flex:1; margin:0;" onsubmit="return confirm('@{{ target_user }} istifadəçisini şikayət etmək istədiyinizə əminsinizmi?');">
                    <button type="submit" class="btn-report">⚠️ ŞİKAYƏT ET</button>
                </form>
            </div>

            <a href="/istifadeciler" class="back-btn">← İstifadəçilərə Qayıt</a>
        </div>
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
            overflow: hidden;
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
            pointer-events: none;
        }
        .comments-drawer.active {
            bottom: 0;
            pointer-events: auto;
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
                        {% if v[1] == current_user or is_admin or is_police %}
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
                        
                        <div style="display:flex; flex-direction:column; align-items:center;">
                            <button class="action-item" onclick="toggleBookmark('{{ v[0] }}')">
                                <span id="bookmark-icon-{{ v[0] }}" style="color: {{ '#f97316' if v[7] else '#fff' }};">📥</span>
                            </button>
                            <span class="action-count">Yaddaş</span>                       
                        </div>
                    </div>

                    <div class="comments-drawer" id="drawer-{{ v[0] }}">
                        <div class="drawer-header">
                            <span>Şərhlər</span>
                            <button class="close-drawer" type="button" onclick="closeComments('{{ v[0] }}'); event.stopPropagation();">✕</button>
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

                function toggleBookmark(videoId) {
            fetch('/vidyo/bookmark/' + videoId, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if(data.success) {
                    let icon = document.getElementById('bookmark-icon-' + videoId);
                    icon.style.color = data.bookmarked ? '#f97316' : '#fff';
                }
            });
        }

                function openComments(videoId) {
            // Eyni anda yalnız bir şərh panelinin açıq olması üçün digərlərini bağlayırıq
            document.querySelectorAll('.comments-drawer').forEach(drawer => {
                drawer.classList.remove('active');
            });
            
            let drawer = document.getElementById('drawer-' + videoId);
            if (drawer) {
                drawer.classList.add('active');
            }
        }

        function closeComments(videoId) {
            let drawer = document.getElementById('drawer-' + videoId);
            if (drawer) {
                drawer.classList.remove('active');
            }
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
                    let drawer = entry.target.querySelector('.comments-drawer');
                    if (entry.isIntersecting) {
                        vid.play().catch(e => {});
                    } else {
                        vid.pause();
                        vid.currentTime = 0;
                        if (drawer) {
                            drawer.classList.remove('active');
                        }
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
            align-items: flex-start;
            overflow-y: auto;
            padding: 20px;
            box-sizing: border-box;
            position: relative;
        }
        .profile-container {
            background: rgba(24, 24, 27, 0.92);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 18px;
            width: 100%;
            max-width: 580px;
            box-sizing: border-box;
            box-shadow: 0 20px 45px rgba(0,0,0,0.6);
            position: relative;
        }
        .menu-toggle-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            width: 40px;
            height: 40px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            gap: 5px;
            cursor: pointer;
            z-index: 20;
        }
        .menu-toggle-btn span {
            display: block;
            width: 20px;
            height: 2px;
            background: #fff;
            border-radius: 2px;
        }
        .side-dropdown-menu {
            display: none;
            position: absolute;
            top: 70px;
            right: 20px;
            background: rgba(18, 18, 22, 0.98);
            border: 1px solid rgba(249, 115, 22, 0.4);
            border-radius: 16px;
            padding: 10px;
            width: 200px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.8);
            z-index: 50;
            flex-direction: column;
            gap: 6px;
        }
        .side-dropdown-menu.active {
            display: flex;
        }
        .dropdown-item {
            background: transparent;
            border: none;
            color: #f8fafc;
            padding: 12px 14px;
            text-align: left;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            text-decoration: none;
        }
        .dropdown-item:hover {
            background: rgba(249, 115, 22, 0.15);
            color: #f97316;
        }
        .dropdown-item.danger:hover {
            background: rgba(239, 68, 68, 0.15);
            color: #f87171;
        }
        .profile-header-tk {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            margin-top: 10px;
        }
        .avatar-wrapper-tk {
            width: 96px;
            height: 96px;
            border-radius: 50%;
            border: 2px solid #f97316;
            overflow: hidden;
            background: #111;
            margin-bottom: 12px;
            box-shadow: 0 0 15px rgba(249, 115, 22, 0.3);
        }
        .avatar-wrapper-tk img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .username-tk {
            font-size: 20px;
            font-weight: 800;
            color: #f8fafc;
        }
        .handle-tk {
            color: #a1a1aa;
            font-size: 13px;
            margin-top: 2px;
            margin-bottom: 10px;
        }
        .bio-tk {
            font-size: 14px;
            color: #d4d4d8;
            margin-bottom: 20px;
            max-width: 420px;
            word-break: break-word;
            line-height: 1.4;
        }
        .tabs-tk {
            display: flex;
            justify-content: space-around;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 15px;
        }
        .tab-btn-tk {
            background: none;
            border: none;
            color: #71717a;
            font-size: 15px;
            padding: 10px 15px;
            cursor: pointer;
            font-weight: 700;
            position: relative;
        }
        .tab-btn-tk.active {
            color: #fff;
        }
        .tab-btn-tk.active::after {
            content: '';
            position: absolute;
            bottom: -1px;
            left: 0;
            width: 100%;
            height: 2px;
            background: #f97316;
        }
        .tab-content-tk {
            display: none;
        }
        .tab-content-tk.active {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 6px;
        }
        .video-card-tk {
            background-color: #27272a;
            aspect-ratio: 9/16;
            position: relative;
            overflow: hidden;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .video-card-tk video {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .video-placeholder-text {
            font-size: 13px;
            color: #a1a1aa;
            text-align: center;
            padding: 20px;
            grid-column: span 3;
        }
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(8px);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .modal-panel {
            background: #18181b;
            border: 2px solid #f97316;
            border-radius: 20px;
            padding: 24px;
            width: 90%;
            max-width: 400px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.8);
            display: flex;
            flex-direction: column;
            gap: 14px;
        }
        .modal-panel h3 { margin: 0; color: #f97316; font-size: 18px; text-align: center; }
        .modal-input {
            width: 100%;
            padding: 12px 16px;
            border-radius: 12px;
            background: #09090b;
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.2);
            font-size: 14px;
            box-sizing: border-box;
        }
        .btn-modal-save {
            background: linear-gradient(135deg, #f97316, #ea580c);
            color: #fff;
            border: none;
            padding: 12px;
            border-radius: 12px;
            font-weight: 700;
            cursor: pointer;
            font-size: 15px;
            width: 100%;
        }
        .btn-modal-close {
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            border: none;
            padding: 10px;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            width: 100%;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="profile-wrapper">
        <div class="profile-container">
            <div class="menu-toggle-btn" onclick="toggleSideMenu(event)">
                <span></span>
                <span></span>
                <span></span>
            </div>

            <div class="side-dropdown-menu" id="sideDropdownMenu">
                <button class="dropdown-item" onclick="openEditModal()">✏️ Hesabı Redaktə Et</button>
                <a href="/logout" class="dropdown-item">🚪 Hesabdan Çıx</a>
                <form method="POST" onsubmit="return confirm('DİQQƏT: Hesabınızı silmək istədiyinizə əminsinizmi?');" style="margin:0;">
                    <input type="hidden" name="action" value="delete_account">
                    <button type="submit" class="dropdown-item danger" style="width:100%;">🗑️ Hesabı Sil</button>
                </form>
            </div>

            {% if message %}
                <p style="font-size: 13px; text-align: center; margin: 0; font-weight: 700; color: {% if error %}#f87171{% else %}#4ade80{% endif %};">{{ message }}</p>
            {% endif %}

            <div class="profile-header-tk">
                <div class="avatar-wrapper-tk">
                    <img src="{{ pic if pic else 'https://i.imgur.com/6VBx3io.png' }}" alt="Profil Şəkli">
                </div>
                <div class="username-tk" style="color: {{ name_color if name_color and name_color != 'inherit' else '#f8fafc' }};">
                    @{{ user }} {{ profile_sticker }}
                </div>
                <div class="handle-tk">Bal: {{ points }} 💰</div>
                <div class="bio-tk">{{ bio if bio else 'Bioqrafiya daxil edilməyib...' }}</div>
            </div>

            <div class="tabs-tk">
                <button class="tab-btn-tk active" onclick="switchTab(event, 'my-videos')">🎬 Videolar</button>
                <button class="tab-btn-tk" onclick="switchTab(event, 'liked-videos')">❤️ Bəyənilən</button>
                <button class="tab-btn-tk" onclick="switchTab(event, 'saved-videos')">📌 Yaddaşda</button>
            </div>

            <div id="my-videos" class="tab-content-tk active">
                {% if user_videos %}
                    {% for v in user_videos %}
                        <div class="video-card-tk">
                            <video src="{{ v[2] }}" muted playsinline></video>
                        </div>
                    {% endfor %}
                {% else %}
                    <p class="video-placeholder-text">Hələ ki şəxsi video paylaşılmayıb.</p>
                {% endif %}
            </div>

            <div id="liked-videos" class="tab-content-tk">
                {% if liked_videos %}
                    {% for v in liked_videos %}
                        <div class="video-card-tk">
                            <video src="{{ v[2] }}" muted playsinline></video>
                        </div>
                    {% endfor %}
                {% else %}
                    <p class="video-placeholder-text">Bəyənilən video yoxdur.</p>
                {% endif %}
            </div>

            <div id="saved-videos" class="tab-content-tk">
                {% if saved_videos %}
                    {% for v in saved_videos %}
                        <div class="video-card-tk">
                            <video src="{{ v[2] }}" muted playsinline></video>
                        </div>
                    {% endfor %}
                {% else %}
                    <p class="video-placeholder-text">Yadda saxlanılan video yoxdur.</p>
                {% endif %}
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="editModal">
        <div class="modal-panel">
            <h3>✏️ Hesabı Redaktə Et</h3>
            <form method="POST" enctype="multipart/form-data" style="display:flex; flex-direction:column; gap:12px;">
                <input type="hidden" name="action" value="edit_profile">
                
                <label style="font-size:13px; color:#d4d4d8;">Nik Adı (Max 7 hərf):</label>
                <input type="text" name="new_nickname" value="{{ user }}" class="modal-input" maxlength="7" required>

                <label style="font-size:13px; color:#d4d4d8;">Öz Haqqında (Bioqrafiya):</label>
                <input type="text" name="new_bio" value="{{ bio }}" class="modal-input" maxlength="120">

                <label style="font-size:13px; color:#d4d4d8;">Profil Şəkli Seç:</label>
                <input type="file" name="pic_file" accept="image/*" class="modal-input" style="padding:8px;">

                <button type="submit" class="btn-modal-save">Yadda Saxla</button>
            </form>
            <button type="button" class="btn-modal-close" onclick="closeEditModal()">Bağla</button>
        </div>
    </div>

    <script>
        function toggleSideMenu(e) {
            e.stopPropagation();
            let menu = document.getElementById('sideDropdownMenu');
            menu.classList.toggle('active');
        }
        window.addEventListener('click', function() {
            let menu = document.getElementById('sideDropdownMenu');
            if (menu) menu.classList.remove('active');
        });
        function openEditModal() { document.getElementById('editModal').style.display = 'flex'; }
        function closeEditModal() { document.getElementById('editModal').style.display = 'none'; }
        function switchTab(evt, tabId) {
            document.querySelectorAll('.tab-content-tk').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn-tk').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            evt.currentTarget.classList.add('active');
        }
    </script>
</body>
</html>
'''

CANLI_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WİN_WİD - Canlı Yayımlar</title>
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
            flex-direction: column;
            align-items: center;
            text-align: center;
            gap: 14px;
            background: rgba(24, 24, 27, 0.9);
            padding: 24px 20px;
            border-radius: 20px;
            border: 1px solid rgba(249, 115, 22, 0.3);
        }
        .btn-start-live {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            border: none;
            width: 100%;
            max-width: 320px;
            padding: 16px 28px;
            border-radius: 16px;
            font-weight: 800;
            font-size: 17px;
            cursor: pointer;
            box-shadow: 0 6px 20px rgba(239, 68, 68, 0.45);
            transition: transform 0.2s;
            letter-spacing: 0.5px;
        }
        .btn-start-live:hover { transform: translateY(-2px); }
        
        .active-lives-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
            gap: 16px;
        }
        .live-card {
            background: rgba(24, 24, 27, 0.9);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 18px;
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
            font-size: 11px;
            font-weight: 800;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.4; }
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
            <h2 style="margin: 0; color: #f97316; font-size: 22px;">🔴 CANLI YAYIM MƏRKƏZİ</h2>
            <form method="POST" action="/canli/ac" style="width:100%; display:flex; justify-content:center; margin:0;">
                <button type="submit" class="btn-start-live">🎥 CANLI AÇ</button>
            </form>
            <p style="margin: 0; color: #a1a1aa; font-size: 13px;">Canlı açmaq üçün balansınızda ən azı 60 Won olmalıdır (Balansınız: <b style="color:#4ade80;">{{ user_points }} Won</b>)</p>
        </div>

        {% if error %}
            <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); color: #f87171; padding: 14px 20px; border-radius: 14px; font-weight: 700; text-align: center;">
                {{ error }}
            </div>
        {% endif %}

        <h3 style="margin: 5px 0 0 5px; color: #f8fafc; font-size: 16px;">📺 Aktiv Canlı Yayımlar</h3>

        <div class="active-lives-grid">
            {% if lives %}
                {% for l in lives %}
                    <div class="live-card">
                        <span class="live-badge">● CANLI</span>
                        <div style="display: flex; align-items: center; gap: 14px;">
                            <img src="{{ l[2] if l[2] else 'https://i.imgur.com/6VBx3io.png' }}" style="width: 54px; height: 54px; border-radius: 50%; border: 2px solid #f97316; object-fit: cover;">
                            <div>
                                <h3 style="margin: 0; font-size: 18px; color: #f8fafc;">@{{ l[1] }}</h3>
                                <p style="margin: 4px 0 0 0; color: #4ade80; font-size: 13px; font-weight: 600;">Yayım gedir...</p>
                            </div>
                        </div>
                        <a href="/canli/izle/{{ l[0] }}" class="btn-join-live">Canlıya Gir və Bax 👁️</a>
                    </div>
                {% endfor %}
            {% else %}
                <div style="grid-column: 1 / -1; text-align: center; color: #a1a1aa; padding: 40px 20px; background: rgba(24, 24, 27, 0.6); border-radius: 18px; font-size: 15px;">
                    Hazırda aktiv canlı yayım yoxdur. İlk canlıyı sən aç!
                </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

CANLI_ROOM_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WİN_WİD - @{{ host }} Canlı Yayımı</title>
    ''' + COMMON_STYLE + '''
    <style>
        body { padding: 10px; padding-bottom: 85px; }
        .room-container {
            flex: 1;
            background: #000;
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 22px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
            box-shadow: 0 15px 35px rgba(0,0,0,0.8);
        }
        .room-top-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            padding: 14px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(to bottom, rgba(0,0,0,0.8), transparent);
            z-index: 20;
            box-sizing: border-box;
        }
        .host-badge {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(0, 0, 0, 0.65);
            backdrop-filter: blur(8px);
            padding: 6px 12px;
            border-radius: 30px;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }
        .stats-pills {
            display: flex;
            gap: 8px;
            margin-top: 6px;
        }
        .stat-pill {
            background: rgba(0, 0, 0, 0.65);
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 800;
            color: #fff;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .three-lines-btn {
            width: 42px;
            height: 42px;
            background: rgba(15, 15, 18, 0.85);
            border: 1px solid rgba(249, 115, 22, 0.6);
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            gap: 5px;
            cursor: pointer;
            z-index: 30;
        }
        .three-lines-btn span {
            display: block;
            width: 22px;
            height: 2.5px;
            background: #fff;
            border-radius: 2px;
        }
        .right-control-drawer {
            position: absolute;
            top: 65px;
            right: -280px;
            width: 230px;
            background: rgba(18, 18, 22, 0.96);
            backdrop-filter: blur(16px);
            border: 1px solid #f97316;
            border-radius: 18px;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            z-index: 40;
            transition: right 0.25s ease;
            box-shadow: -10px 15px 30px rgba(0,0,0,0.9);
        }
        .right-control-drawer.open {
            right: 14px;
        }
        .drawer-ctrl-btn {
            background: rgba(39, 39, 42, 0.9);
            color: #f8fafc;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 11px 14px;
            border-radius: 12px;
            font-size: 13px;
            font-weight: 700;
            text-align: left;
            cursor: pointer;
            width: 100%;
            transition: background 0.2s;
        }
        .drawer-ctrl-btn:hover { background: rgba(249, 115, 22, 0.25); }
        .drawer-ctrl-btn.danger { background: #dc2626; color: #fff; border: none; text-align: center; }
        .drawer-ctrl-btn.active-state { background: #f97316; color: #000; }

        .stream-viewport {
            flex: 1;
            position: relative;
            background: #09090b;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }
        #webcamVideo, #viewerStreamImg {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        #webcamVideo { transform: scaleX(-1); }
        
        .status-overlay-box {
            display: none;
            position: absolute;
            inset: 0;
            background: rgba(9, 9, 11, 0.92);
            z-index: 15;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 20px;
            color: #f97316;
            font-size: 18px;
            font-weight: 800;
        }

        .live-chat-overlay {
            position: absolute;
            bottom: 14px;
            left: 14px;
            right: 85px;
            max-height: 230px;
            display: flex;
            flex-direction: column;
            justify-content: flex-end;
            z-index: 20;
        }
        .live-messages-list {
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 6px;
            max-height: 175px;
            padding-right: 6px;
            margin-bottom: 8px;
        }
        .live-msg-bubble {
            background: rgba(0, 0, 0, 0.65);
            backdrop-filter: blur(6px);
            padding: 7px 12px;
            border-radius: 12px;
            font-size: 13px;
            color: #fff;
            word-break: break-word;
            border: 1px solid rgba(255, 255, 255, 0.12);
            user-select: none;
            cursor: pointer;
            align-self: flex-start;
            max-width: 95%;
        }
        .live-msg-bubble:active {
            background: rgba(249, 115, 22, 0.4);
        }
        .live-chat-form {
            display: flex;
            gap: 6px;
        }
        .live-chat-input {
            flex: 1;
            padding: 10px 12px;
            background: rgba(0, 0, 0, 0.75);
            border: 1px solid rgba(249, 115, 22, 0.6);
            border-radius: 12px;
            color: #fff;
            font-size: 13px;
        }
        .live-chat-submit {
            background: #f97316;
            color: #fff;
            border: none;
            padding: 0 14px;
            border-radius: 12px;
            font-weight: 700;
            cursor: pointer;
            font-size: 13px;
        }

        .floating-like-btn {
            position: absolute;
            bottom: 16px;
            right: 16px;
            background: linear-gradient(135deg, #ef4444, #dc2626);
            border: 2px solid #fff;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 26px;
            cursor: pointer;
            z-index: 25;
            box-shadow: 0 6px 20px rgba(239, 68, 68, 0.6);
            transition: transform 0.1s;
        }
        .floating-like-btn:active { transform: scale(0.85); }

        .gifts-bar {
            background: rgba(15, 15, 18, 0.96);
            padding: 10px 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            overflow-x: auto;
            z-index: 25;
        }
        .gift-btn {
            background: rgba(39, 39, 42, 0.9);
            border: 1px solid rgba(249, 115, 22, 0.45);
            border-radius: 12px;
            padding: 6px 10px;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-width: 52px;
            flex-shrink: 0;
        }
        .gift-btn span.emoji { font-size: 22px; }
        .gift-btn span.price { font-size: 10px; color: #f97316; font-weight: 800; margin-top: 2px; }

        .bottom-action-sheet-overlay {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.75);
            z-index: 100000;
            justify-content: center;
            align-items: flex-end;
        }
        .bottom-action-sheet {
            background: #18181b;
            border-top: 2px solid #f97316;
            border-top-left-radius: 22px;
            border-top-right-radius: 22px;
            width: 100%;
            max-width: 500px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            box-sizing: border-box;
        }
        .sheet-btn {
            padding: 14px;
            border-radius: 14px;
            border: none;
            font-size: 15px;
            font-weight: 800;
            cursor: pointer;
            text-align: center;
            width: 100%;
        }
        .sheet-block { background: #dc2626; color: #fff; }
        .sheet-report { background: #f59e0b; color: #000; }
        .sheet-copy { background: #27272a; color: #fff; border: 1px solid rgba(255,255,255,0.15); }
        .sheet-cancel { background: transparent; color: #a1a1aa; margin-top: 4px; }

        .sticker-toast {
            position: absolute;
            top: 40%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0,0,0,0.85);
            border: 2px solid #f97316;
            padding: 16px 24px;
            border-radius: 20px;
            text-align: center;
            z-index: 50;
            display: none;
            animation: popIn 0.3s ease;
        }
        @keyframes popIn {
            0% { transform: translate(-50%, -50%) scale(0.5); opacity: 0; }
            100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="room-container">
        <div class="room-top-overlay">
            <div>
                <div class="host-badge">
                    <img src="{{ host_pic if host_pic else 'https://i.imgur.com/6VBx3io.png' }}" style="width: 36px; height: 36px; border-radius: 50%; border: 2px solid #ef4444; object-fit: cover;">
                    <div>
                        <div style="font-size: 14px; font-weight: 800; color: #fff;">@{{ host }}</div>
                        <div style="font-size: 11px; color: #4ade80; font-weight: 700;">● CANLI YAYIM</div>
                    </div>
                </div>
                <div class="stats-pills">
                    <div class="stat-pill">❤️ <span id="likeCountDisplay">{{ likes_count }}</span></div>
                    <div class="stat-pill">🎁 <span id="giftCount">{{ gifts|length }}</span></div>
                </div>
            </div>

            {% if current_user == host %}
                <button type="button" class="three-lines-btn" onclick="toggleRightMenu()">
                    <span></span>
                    <span></span>
                    <span></span>
                </button>
            {% else %}
                <a href="/canli" style="background: rgba(0,0,0,0.7); color: #fff; text-decoration: none; padding: 8px 14px; border-radius: 12px; font-weight: 700; font-size: 13px; border: 1px solid rgba(255,255,255,0.2);">Çıxış ✕</a>
            {% endif %}
        </div>

        {% if current_user == host %}
        <div class="right-control-drawer" id="rightControlDrawer">
            <form method="POST" action="/canli/bitir/{{ live_id }}" style="margin:0;">
                <button type="submit" class="drawer-ctrl-btn danger">🛑 Canlını bağla</button>
            </form>
            <button type="button" class="drawer-ctrl-btn" id="btnToggleVideo" onclick="toggleVideoState()">📷 Görüntünü bağla</button>
            <button type="button" class="drawer-ctrl-btn" id="btnToggleAudio" onclick="toggleAudioState()">🔇 SƏSİ bağla</button>
            <button type="button" class="drawer-ctrl-btn" id="btnToggleChat" onclick="toggleChatArea()">💬 MESAJ YERİN bağla</button>
            <button type="button" class="drawer-ctrl-btn" id="btnTogglePause" onclick="togglePauseState()">⏸️ Canlını MÜVƏQQƏTİ dondur</button>
            <button type="button" class="drawer-ctrl-btn" onclick="flipCamera()">🔄 KAMERANI ÇEVİR</button>
        </div>
        {% endif %}

        <div class="sticker-toast" id="stickerToast"></div>

        <div class="stream-viewport">
            <div class="status-overlay-box" id="statusOverlayBox">
                <span id="statusOverlayText">📷 Görüntü bağlıdır</span>
            </div>

            {% if current_user == host %}
                <video id="webcamVideo" autoplay playsinline muted></video>
                <canvas id="captureCanvas" style="display:none;"></canvas>
            {% else %}
                <img id="viewerStreamImg" src="" alt="Canlı Yayım Yüklənir...">
                <audio id="viewerAudioPlayer" autoplay></audio>
            {% endif %}

            <div class="live-chat-overlay" id="liveChatOverlay">
                <div class="live-messages-list" id="liveMessagesList"></div>
                <form class="live-chat-form" id="liveChatForm" onsubmit="sendLiveMessage(event)">
                    <input type="text" id="liveMsgInput" class="live-chat-input" placeholder="Mesaj yaz..." required autocomplete="off">
                    <button type="submit" class="live-chat-submit">Yaz</button>
                </form>
            </div>

            <button type="button" class="floating-like-btn" onclick="sendLike()">❤️</button>
        </div>

        <div class="gifts-bar">
            {% set gift_list = ['👑', '🤯', '❤️‍🔥', '🤠', '💋', '🫶', '🔥', '🧨', '🎀', '🌹', '🚀', '💎'] %}
            {% for gift in gift_list %}
                <button type="button" class="gift-btn" onclick="sendGift('{{ gift }}')">
                    <span class="emoji">{{ gift }}</span>
                    <span class="price">10 Won</span>
                </button>
            {% endfor %}
        </div>
    </div>

    <div class="bottom-action-sheet-overlay" id="msgActionOverlay" onclick="closeMsgActionSheet()">
        <div class="bottom-action-sheet" onclick="event.stopPropagation()">
            <div style="text-align:center; color:#f97316; font-weight:800; font-size:15px; margin-bottom:4px;" id="selectedMsgUserTitle">@istifadəçi</div>
            <button type="button" class="sheet-btn sheet-block" onclick="blockLiveUser()">🚫 İSDİFADƏÇİNİ BLOKLA</button>
            <button type="button" class="sheet-btn sheet-report" onclick="reportLiveUser()">⚠️ İSDİFADƏÇİNİ ŞİKAYƏT ET</button>
            <button type="button" class="sheet-btn sheet-copy" onclick="copyLiveMessage()">📋 +1 MESAJI KOPYALA</button>
            <button type="button" class="sheet-btn sheet-cancel" onclick="closeMsgActionSheet()">Ləğv et</button>
        </div>
    </div>

    <script>
        const isHost = {{ 'true' if current_user == host else 'false' }};
        const liveId = '{{ live_id }}';
        const currentUser = '{{ current_user }}';

        let currentFacingMode = 'user';
        let currentStream = null;
        let isVideoOff = false;
        let isAudioOff = false;
        let isPaused = false;
        let isChatHidden = false;

        function toggleRightMenu() {
            document.getElementById('rightControlDrawer').classList.toggle('open');
        }

        function toggleVideoState() {
            isVideoOff = !isVideoOff;
            let btn = document.getElementById('btnToggleVideo');
            if (currentStream) {
                currentStream.getVideoTracks().forEach(t => t.enabled = !isVideoOff);
            }
            btn.innerText = isVideoOff ? '📷 Görüntünü aç' : '📷 Görüntünü bağla';
            btn.classList.toggle('active-state', isVideoOff);
            updateLocalOverlay();
            sendHostControls();
        }

        function toggleAudioState() {
            isAudioOff = !isAudioOff;
            let btn = document.getElementById('btnToggleAudio');
            if (currentStream) {
                currentStream.getAudioTracks().forEach(t => t.enabled = !isAudioOff);
            }
            btn.innerText = isAudioOff ? '🔊 SƏSİ aç' : '🔇 SƏSİ bağla';
            btn.classList.toggle('active-state', isAudioOff);
            sendHostControls();
        }

        function toggleChatArea() {
            isChatHidden = !isChatHidden;
            let chatBox = document.getElementById('liveChatOverlay');
            let btn = document.getElementById('btnToggleChat');
            chatBox.style.display = isChatHidden ? 'none' : 'flex';
            btn.innerText = isChatHidden ? '💬 MESAJ YERİN aç' : '💬 MESAJ YERİN bağla';
            btn.classList.toggle('active-state', isChatHidden);
        }

        function togglePauseState() {
            isPaused = !isPaused;
            let btn = document.getElementById('btnTogglePause');
            let videoEl = document.getElementById('webcamVideo');
            if (videoEl) {
                if (isPaused) videoEl.pause();
                else videoEl.play();
            }
            btn.innerText = isPaused ? '▶️ Canlını DAVAM ET' : '⏸️ Canlını MÜVƏQQƏTİ dondur';
            btn.classList.toggle('active-state', isPaused);
            updateLocalOverlay();
            sendHostControls();
        }

        function updateLocalOverlay() {
            let box = document.getElementById('statusOverlayBox');
            let txt = document.getElementById('statusOverlayText');
            if (isPaused) {
                box.style.display = 'flex';
                txt.innerText = '⏸️ Canlı yayım müvəqqəti dondurulub';
            } else if (isVideoOff) {
                box.style.display = 'flex';
                txt.innerText = '📷 Kamera görüntüsü bağlıdır';
            } else {
                box.style.display = 'none';
            }
        }

        function sendHostControls() {
            fetch('/canli/kontrol/' + liveId, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    is_video_off: isVideoOff ? 1 : 0,
                    is_audio_off: isAudioOff ? 1 : 0,
                    is_paused: isPaused ? 1 : 0
                })
            });
        }

        function startCamera(facingMode) {
            if (currentStream) {
                currentStream.getTracks().forEach(track => track.stop());
            }
            navigator.mediaDevices.getUserMedia({ video: { facingMode: facingMode, width: 480, height: 640 }, audio: true })
                .then(stream => {
                    currentStream = stream;
                    stream.getVideoTracks().forEach(t => t.enabled = !isVideoOff);
                    stream.getAudioTracks().forEach(t => t.enabled = !isAudioOff);

                    const videoEl = document.getElementById('webcamVideo');
                    if (videoEl) {
                        videoEl.srcObject = stream;
                        videoEl.style.transform = (facingMode === 'user') ? 'scaleX(-1)' : 'scaleX(1)';
                    }
                    startBroadcastingLoops(stream);
                })
                .catch(err => {
                    alert("Kamera və ya mikrofona icazə verilmədi!");
                });
        }

        function flipCamera() {
            currentFacingMode = (currentFacingMode === 'user') ? 'environment' : 'user';
            startCamera(currentFacingMode);
        }

        let broadcastInterval = null;

        function startBroadcastingLoops(stream) {
            if (broadcastInterval) clearInterval(broadcastInterval);

            const videoEl = document.getElementById('webcamVideo');
            const canvas = document.getElementById('captureCanvas');
            const ctx = canvas.getContext('2d');

            broadcastInterval = setInterval(() => {
                if (isPaused || isVideoOff || !videoEl.videoWidth) return;
                canvas.width = 360;
                canvas.height = 480;
                ctx.save();
                if (currentFacingMode === 'user') {
                    ctx.scale(-1, 1);
                    ctx.drawImage(videoEl, -canvas.width, 0, canvas.width, canvas.height);
                } else {
                    ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);
                }
                ctx.restore();
                const frameData = canvas.toDataURL('image/jpeg', 0.55);

                fetch('/canli/yayim_gonder/' + liveId, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ frame_data: frameData })
                });
            }, 600);

            function recordAudioChunk() {
                if (isPaused || isAudioOff) {
                    setTimeout(recordAudioChunk, 1000);
                    return;
                }
                try {
                    const audioStream = new MediaStream(stream.getAudioTracks());
                    const recorder = new MediaRecorder(audioStream);
                    let chunks = [];
                    recorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data); };
                    recorder.onstop = () => {
                        const blob = new Blob(chunks, { type: 'audio/webm' });
                        const reader = new FileReader();
                        reader.onloadend = () => {
                            fetch('/canli/ses_gonder/' + liveId, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ audio_data: reader.result })
                            });
                        };
                        reader.readAsDataURL(blob);
                        recordAudioChunk();
                    };
                    recorder.start();
                    setTimeout(() => { if (recorder.state !== 'inactive') recorder.stop(); }, 1500);
                } catch (e) {}
            }
            recordAudioChunk();
        }

        if (isHost) {
            startCamera(currentFacingMode);
        }

        function sendLike() {
            fetch('/canli/like/' + liveId, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('likeCountDisplay').innerText = data.likes_count;
                }
            });
        }

        function sendLiveMessage(e) {
            e.preventDefault();
            let input = document.getElementById('liveMsgInput');
            let text = input.value.trim();
            if (!text) return;

            fetch('/canli/mesaj/' + liveId, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: text })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    input.value = '';
                    fetchLiveUpdates();
                } else if (data.error) {
                    alert(data.error);
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
                if (data.success) {
                    document.getElementById('giftCount').innerText = data.gifts_count;
                    showStickerToast(currentUser, giftSymbol);
                } else {
                    alert(data.error || "Xəta baş verdi!");
                }
            });
        }

        function showStickerToast(sender, gift) {
            let toast = document.getElementById('stickerToast');
            toast.innerHTML = `<div style="font-size:44px;">${gift}</div><div style="color:#fff; font-weight:800; font-size:14px; margin-top:6px;">@${sender} stiker göndərdi! (10 Won)</div>`;
            toast.style.display = 'block';
            setTimeout(() => { toast.style.display = 'none'; }, 2500);
        }

        let pressTimer = null;
        let selectedTargetUser = '';
        let selectedTargetMsg = '';

        function handlePressStart(sender, content) {
            pressTimer = setTimeout(() => {
                selectedTargetUser = sender;
                selectedTargetMsg = content;
                document.getElementById('selectedMsgUserTitle').innerText = '@' + sender;
                document.getElementById('msgActionOverlay').style.display = 'flex';
            }, 550);
        }

        function handlePressEnd() {
            clearTimeout(pressTimer);
        }

        function closeMsgActionSheet() {
            document.getElementById('msgActionOverlay').style.display = 'none';
        }

        function blockLiveUser() {
            if (!selectedTargetUser) return;
            fetch('/canli/blokla/' + liveId, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_user: selectedTargetUser })
            })
            .then(res => res.json())
            .then(data => {
                closeMsgActionSheet();
                alert(data.message || data.error);
            });
        }

        function reportLiveUser() {
            if (!selectedTargetUser) return;
            fetch('/canli/sikayet/' + liveId, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_user: selectedTargetUser, msg_content: selectedTargetMsg })
            })
            .then(res => res.json())
            .then(data => {
                closeMsgActionSheet();
                alert(data.message || "Şikayət göndərildi!");
            });
        }

        function copyLiveMessage() {
            if (selectedTargetMsg) {
                navigator.clipboard.writeText(selectedTargetMsg).then(() => {
                    closeMsgActionSheet();
                    alert("Mesaj kopyalandı: " + selectedTargetMsg);
                });
            }
        }

        let lastAudioHash = '';

        function fetchLiveUpdates() {
            fetch('/canli/yenile/' + liveId)
            .then(res => res.json())
            .then(data => {
                if (!data.is_active) {
                    alert("Canlı yayım başa çatdı!");
                    window.location.href = '/canli';
                    return;
                }
                if (data.is_blocked) {
                    alert("Yayım sahibi tərəfindən bu canlıdan bloklandınız!");
                    window.location.href = '/canli';
                    return;
                }

                document.getElementById('likeCountDisplay').innerText = data.likes_count;
                document.getElementById('giftCount').innerText = data.gifts_count;

                if (!isHost) {
                    let overlay = document.getElementById('statusOverlayBox');
                    let overlayTxt = document.getElementById('statusOverlayText');
                    let imgEl = document.getElementById('viewerStreamImg');

                    if (data.is_paused == 1) {
                        overlay.style.display = 'flex';
                        overlayTxt.innerText = '⏸️ Yayımçı canlını müvəqqəti dondurdu';
                    } else if (data.is_video_off == 1) {
                        overlay.style.display = 'flex';
                        overlayTxt.innerText = '📷 Yayımçı görüntünü bağladı';
                    } else {
                        overlay.style.display = 'none';
                        if (data.frame_data) {
                            imgEl.src = data.frame_data;
                        }
                    }

                    if (data.is_audio_off == 0 && data.audio_data && data.audio_data !== lastAudioHash) {
                        lastAudioHash = data.audio_data;
                        let audioEl = document.getElementById('viewerAudioPlayer');
                        audioEl.src = data.audio_data;
                        audioEl.play().catch(() => {});
                    }
                }

                let list = document.getElementById('liveMessagesList');
                let shouldScroll = (list.scrollTop + list.clientHeight >= list.scrollHeight - 40);
                list.innerHTML = '';
                data.messages.forEach(m => {
                    let div = document.createElement('div');
                    div.className = 'live-msg-bubble';
                    div.innerHTML = `<b style="color:#fb923c;">@${m.sender}</b>: ${m.content}`;
                    
                    div.addEventListener('touchstart', () => handlePressStart(m.sender, m.content));
                    div.addEventListener('touchend', handlePressEnd);
                    div.addEventListener('mousedown', () => handlePressStart(m.sender, m.content));
                    div.addEventListener('mouseup', handlePressEnd);
                    div.addEventListener('mouseleave', handlePressEnd);
                    
                    list.appendChild(div);
                });
                if (shouldScroll) {
                    list.scrollTop = list.scrollHeight;
                }
            });
        }

        setInterval(fetchLiveUpdates, 900);
        fetchLiveUpdates();
    </script>
</body>
</html>
'''

MAGAZA_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Mağaza</title>
    ''' + COMMON_STYLE + '''
    <style>
        .shop-container {
            background: rgba(24, 24, 27, 0.85);
            flex: 1;
            border-radius: 22px;
            padding: 28px;
            overflow-y: auto;
            border: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            flex-direction: column;
            gap: 25px;
        }
        .shop-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 16px;
        }
        .shop-header h2 { margin: 0; color: #f97316; font-size: 22px; }
        .balance-box {
            background: rgba(34, 197, 94, 0.15);
            border: 1px solid rgba(34, 197, 94, 0.3);
            color: #4ade80;
            padding: 8px 16px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 800;
        }
        .shop-section {
            background: rgba(39, 39, 42, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 18px;
            padding: 20px;
        }
        .shop-section-title {
            font-size: 18px;
            font-weight: 700;
            color: #fb923c;
            margin: 0 0 16px 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .shop-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 16px;
        }
        .shop-item-btn {
            background: rgba(9, 9, 11, 0.7);
            border: 1px solid rgba(249, 115, 22, 0.3);
            border-radius: 14px;
            padding: 16px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }
        .shop-item-btn:hover {
            transform: translateY(-3px);
            border-color: #f97316;
            background: rgba(249, 115, 22, 0.15);
        }
        .shop-item-price {
            font-size: 13px;
            font-weight: 800;
            color: #f97316;
            background: rgba(249, 115, 22, 0.1);
            padding: 4px 10px;
            border-radius: 8px;
        }
        
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.85);
            backdrop-filter: blur(8px);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        .modal-panel {
            background: rgba(24, 24, 27, 0.95);
            border: 2px solid #f97316;
            border-radius: 20px;
            padding: 28px;
            width: 90%;
            max-width: 450px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.8);
            display: flex;
            flex-direction: column;
            gap: 18px;
        }
        .modal-panel h3 { margin: 0; color: #f97316; font-size: 20px; text-align: center; }
        .color-options {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }
        .color-btn {
            padding: 12px;
            border-radius: 12px;
            border: none;
            font-weight: 700;
            cursor: pointer;
            color: #fff;
            text-align: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        }
        .gifts-grid-scroll {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 10px;
            max-height: 220px;
            overflow-y: auto;
            padding: 10px;
            background: rgba(9, 9, 11, 0.6);
            border-radius: 12px;
        }
        .gift-select-btn {
            font-size: 26px;
            background: rgba(39, 39, 42, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 8px;
            cursor: pointer;
            transition: transform 0.1s;
        }
        .gift-select-btn:hover { transform: scale(1.2); border-color: #f97316; }
        select.modal-input {
            width: 100%;
            padding: 12px;
            border-radius: 12px;
            background: #09090b;
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.2);
            font-size: 15px;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="shop-container">
        <div class="shop-header">
            <h2>🛍 WİN_WİD MAĞAZASI</h2>
            <div class="balance-box">💰 Balansınız: {{ user_points }} Bal</div>
        </div>

        {% if message %}
            <div style="background: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.3); color: #4ade80; padding: 12px 18px; border-radius: 12px; font-weight: 700; text-align: center;">
                {{ message }}
            </div>
        {% endif %}
        {% if error %}
            <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); color: #f87171; padding: 12px 18px; border-radius: 12px; font-weight: 700; text-align: center;">
                {{ error }}
            </div>
        {% endif %}

        <div class="shop-section">
            <div class="shop-section-title">⚡ GİRİŞ EFEKTİ (ÇATA DAXİLDƏ XÜSUSİ BİLDİRİŞ)</div>
            <div class="shop-grid">
                <div class="shop-item-btn" onclick="openEntryEffectModal()">
                    <span style="font-size:32px;">⚡</span>
                    <span style="font-weight:700;">GİRİŞ EFEKTİ AL</span>
                    <span class="shop-item-price"400 Won</span>
                </div>
            </div>
        </div>

        <div class="shop-section">
            <div class="shop-section-title">🎨  RƏNGLİ NİK (SİZİN ADINIZIN RƏNGİ)</div>
            <div class="shop-grid">
                <div class="shop-item-btn" onclick="openNickModal()">
                    <span style="font-size:32px;">🏷️</span>
                    <span style="font-weight:700;">RƏNGLİ NİK AL</span>
                    <span class="shop-item-price">25 Won</span>
                </div>
            </div>
        </div>

        <div class="shop-section">
            <div class="shop-section-title">💬  RƏNGLİ MESAJ (ÇAT MESAJLARINIZIN RƏNGİ)</div>
            <div class="shop-grid">
                <div class="shop-item-btn" onclick="openMsgModal()">
                    <span style="font-size:32px;">✉️</span>
                    <span style="font-weight:700;">RƏNGLİ MESAJ AL</span>
                    <span class="shop-item-price">25 Won</span>
                </div>
            </div>
        </div>

        <div class="shop-section">
            <div class="shop-section-title">🎁  İSTİFADƏÇİLƏRƏ HƏDİYYƏ ATMAQ</div>
            <div class="shop-grid">
                <div class="shop-item-btn" onclick="openGiftModal()" style="grid-column: 1 / -1;">
                    <span style="font-size:36px;">🎁</span>
                    <span style="font-weight:700; font-size:16px;">HƏDİYYƏ PANELSİNİ AÇ VƏ GÖNDƏR</span>
                    <span class="shop-item-price">HƏDİYYƏ DƏYƏRİ: BALANSINIZDAN</span>
                </div>
            </div>
        </div>
    </div>

    <div class="modal-overlay" id="entryEffectModal">
        <div class="modal-panel" style="text-align: center;">
            <h3>⚡ GİRİŞ EFEKTİ (400 Won)</h3>
            <p style="color: #d4d4d8; font-size: 15px; line-height: 1.5;">
                Hər dəfə çata daxil olduğunuzda bütün istifadəçilərə xüsusi bildiriş mesajı görünəcək:<br>
                <code style="color: #f97316; font-weight: bold;">⚡ @nik sayıta daxil oldu!</code>
            </p>
            <form method="POST" action="/magaza/al_entry_effect">
                <button type="submit" style="background: linear-gradient(135deg, #f97316, #ea580c); color: #fff; border: none; padding: 14px; border-radius: 12px; font-weight: 700; width: 100%; cursor: pointer; font-size: 16px;">Giriş Effektivini Al (500 Bal)</button>
            </form>
            <button type="button" onclick="closeModals()" style="background: rgba(255,255,255,0.1); color: #fff; border: none; padding: 10px; border-radius: 10px; cursor: pointer; margin-top: 10px;">Bağla</button>
        </div>
    </div>

    <div class="modal-overlay" id="nickModal">
        <div class="modal-panel">
            <h3>🏷️ NİK RƏNGİNİ SEÇİN (25 Won)</h3>
            <form method="POST" action="/magaza/al_nik">
                <div class="color-options">
                    <button type="submit" name="color" value="#eab308" class="color-btn" style="background:#eab308;">SARI</button>
                    <button type="submit" name="color" value="#ef4444" class="color-btn" style="background:#ef4444;">QIRMIZI</button>
                    <button type="submit" name="color" value="#3b82f6" class="color-btn" style="background:#3b82f6;">GÖY</button>
                    <button type="submit" name="color" value="#a855f7" class="color-btn" style="background:#a855f7;">BƏNÖVŞƏYİ</button>
                    <button type="submit" name="color" value="#22c55e" class="color-btn" style="background:#22c55e;">YAŞIL</button>
                </div>
            </form>
            <button type="button" onclick="closeModals()" style="background:rgba(255,255,255,0.1); color:#fff; border:none; padding:10px; border-radius:10px; cursor:pointer;">Bağla</button>
        </div>
    </div>

    <div class="modal-overlay" id="msgModal">
        <div class="modal-panel">
            <h3>💬 MESAJ RƏNGİNİ SEÇİN (25 Won)</h3>
            <form method="POST" action="/magaza/al_mesaj">
                <div class="color-options">
                    <button type="submit" name="color" value="#eab308" class="color-btn" style="background:#eab308;">SARI</button>
                    <button type="submit" name="color" value="#ef4444" class="color-btn" style="background:#ef4444;">QIRMIZI</button>
                    <button type="submit" name="color" value="#3b82f6" class="color-btn" style="background:#3b82f6;">GÖY</button>
                    <button type="submit" name="color" value="#a855f7" class="color-btn" style="background:#a855f7;">BƏNÖVŞƏYİ</button>
                    <button type="submit" name="color" value="#22c55e" class="color-btn" style="background:#22c55e;">YAŞIL</button>
                </div>
            </form>
            <button type="button" onclick="closeModals()" style="background:rgba(255,255,255,0.1); color:#fff; border:none; padding:10px; border-radius:10px; cursor:pointer;">Bağla</button>
        </div>
    </div>

    <div class="modal-overlay" id="giftModal">
        <div class="modal-panel">
            <h3>🎁 İSTİFADƏÇİYƏ HƏDİYYƏ GÖNDƏR</h3>
            <form method="POST" action="/magaza/gonder_hediyye" style="display:flex; flex-direction:column; gap:14px;">
                <label style="font-size:14px; color:#d4d4d8;">Göndəriləcək İstifadəçi:</label>
                <select name="receiver" class="modal-input" required>
                    <option value="" disabled selected>İstifadəçi seçin...</option>
                    {% for u in all_users %}
                        {% if u != current_user %}
                            <option value="{{ u }}">@{{ u }}</option>
                        {% endif %}
                    {% endfor %}
                </select>

                <label style="font-size:14px; color:#d4d4d8;">Hədiyyə Seçin:</label>
                <input type="hidden" name="selected_gift" id="selectedGiftInput" required>
                <div class="gifts-grid-scroll">
                    {% set gift_list = ['😇','🤣','🫠','🤩','🤗','🤭','😜','🤔','🤤','🤠','🤒','🤕','😎','😱','🥺','🥳','🫪','☠️','👻','😸','😹','🙀','🙊','🙈','💌','❤️‍🔥','💬','👋','🤘','🫶','🙏','🫰','🐻','🐹','🐼','🐸','🌹','🍻','🗽','✈️','✨','🧨','🎉','🎖️','💰'] %}
                    {% for g in gift_list %}
                        <button type="button" class="gift-select-btn" onclick="selectGift('{{ g }}', this)">{{ g }}</button>
                    {% endfor %}
                </div>
                <div id="selectedGiftPreview" style="text-align:center; font-weight:700; color:#f97316;">Seçilmiş Hədiyyə: Yoxdur</div>

                <button type="submit" style="background:linear-gradient(135deg, #f97316, #ea580c); color:#fff; border:none; padding:12px; border-radius:12px; font-weight:700; cursor:pointer;">Hədiyyəni Göndər (10 Bal)</button>
            </form>
            <button type="button" onclick="closeModals()" style="background:rgba(255,255,255,0.1); color:#fff; border:none; padding:10px; border-radius:10px; cursor:pointer;">Bağla</button>
        </div>
    </div>

    <script>
        function openEntryEffectModal() { document.getElementById('entryEffectModal').style.display = 'flex'; }
        function openNickModal() { document.getElementById('nickModal').style.display = 'flex'; }
        function openMsgModal() { document.getElementById('msgModal').style.display = 'flex'; }
        function openGiftModal() { document.getElementById('giftModal').style.display = 'flex'; }
        function closeModals() {
            document.getElementById('nickModal').style.display = 'none';
            document.getElementById('msgModal').style.display = 'none';
            document.getElementById('giftModal').style.display = 'none';
            document.getElementById('entryEffectModal').style.display = 'none';
        }

        function selectGift(gift, btn) {
            document.getElementById('selectedGiftInput').value = gift;
            document.getElementById('selectedGiftPreview').innerText = 'Seçilmiş Hədiyyə: ' + gift;
            let btns = document.querySelectorAll('.gift-select-btn');
            btns.forEach(b => b.style.borderColor = 'rgba(255,255,255,0.1)');
            btn.style.borderColor = '#f97316';
        }
    </script>
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
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if action == 'register':
            cursor.execute("SELECT * FROM users WHERE nickname = %s", (nickname,))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return render_template_string(INDEX_TEMPLATE, error="Bu nik artıq istifadə olunur!")
            
            cursor.execute("INSERT INTO users (nickname, password, points) VALUES (%s, %s, %s)", (nickname, password, 20))
            conn.commit()
            cursor.close()
            conn.close()
            session['user'] = nickname
            return redirect(url_for('chat'))
            
        elif action == 'login':
            cursor.execute("SELECT * FROM users WHERE nickname = %s AND password = %s", (nickname, password))
            user = cursor.fetchone()
            cursor.close()
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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT points, has_entry_effect FROM users WHERE nickname = %s", (current_user,))
    res = cursor.fetchone()
    user_points = res[0] if res else 0
    has_entry_effect = res[1] if res else 0
    
    if has_entry_effect == 1:
        session_key = f'entry_notified_{current_user}'
        if not session.get(session_key):
            entry_msg = f"⚡ @{current_user} çat otağına daxil oldu!"
            cursor.execute("INSERT INTO messages (sender, content) VALUES (%s, %s)", (current_user, entry_msg))
            conn.commit()
            session[session_key] = True

    cursor.execute("SELECT id FROM notifications WHERE username = %s AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    
    cursor.execute('''
        SELECT m.id, m.sender, m.content, u.name_color, u.msg_color, u.profile_sticker,
               m.reply_to_id, m.reply_to_user, m.reply_to_content
        FROM messages m 
        LEFT JOIN users u ON m.sender = u.nickname 
        ORDER BY m.id ASC
    ''')
    raw_messages = cursor.fetchall()
    
    messages = []
    for m in raw_messages:
        msg_id = m[0]
        cursor.execute("SELECT reaction, COUNT(*) FROM message_reactions WHERE message_id = %s GROUP BY reaction", (msg_id,))
        reactions_data = {row[0]: row[1] for row in cursor.fetchall()}
        messages.append((m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], reactions_data))
    
    is_admin = (current_user.lower() == 'win_wid')
    is_police = session.get('is_police_logged', False)
    
    cursor.close()
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(CHAT_TEMPLATE, messages=messages, current_user=current_user, is_admin=is_admin, is_police=is_police, user_points=user_points, header=header_html)

@app.route('/chat/send', methods=['POST'])
def chat_send():
    if 'user' not in session:
        return redirect(url_for('index'))
    content = request.form.get('content', '').strip()
    reply_to_id = request.form.get('reply_to_id')
    
    if content:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        reply_user = None
        reply_content = None
        if reply_to_id and reply_to_id.isdigit():
            cursor.execute("SELECT sender, content FROM messages WHERE id = %s", (int(reply_to_id),))
            r_msg = cursor.fetchone()
            if r_msg:
                reply_user = r_msg[0]
                reply_content = r_msg[1]
        
        cursor.execute('''
            INSERT INTO messages (sender, content, reply_to_id, reply_to_user, reply_to_content) 
            VALUES (%s, %s, %s, %s, %s)
        ''', (session['user'], content, reply_to_id if reply_to_id else None, reply_user, reply_content))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('chat'))

@app.route('/chat/reaction/<int:msg_id>', methods=['POST'])
def chat_reaction(msg_id):
    if 'user' not in session:
        return jsonify({'success': False})
    current_user = session['user']
    data = request.get_json()
    emoji = data.get('emoji')
    if not emoji:
        return jsonify({'success': False})

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, reaction FROM message_reactions WHERE message_id = %s AND username = %s", (msg_id, current_user))
    existing = cursor.fetchone()

    if existing:
        if existing[1] == emoji:
            cursor.execute("DELETE FROM message_reactions WHERE id = %s", (existing[0],))
        else:
            cursor.execute("UPDATE message_reactions SET reaction = %s WHERE id = %s", (emoji, existing[0]))
    else:
        cursor.execute("INSERT INTO message_reactions (message_id, username, reaction) VALUES (%s, %s, %s)", (msg_id, current_user, emoji))
    
    conn.commit()

    cursor.execute("SELECT reaction, COUNT(*) FROM message_reactions WHERE message_id = %s GROUP BY reaction", (msg_id,))
    reactions_data = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()
    conn.close()

    return jsonify({'success': True, 'reactions': reactions_data})

@app.route('/chat/typing', methods=['POST'])
def chat_typing():
    if 'user' not in session:
        return jsonify({'success': False})
    current_user = session['user']
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO typing_status (username, is_typing, updated_at) VALUES (%s, 1, %s)
        ON CONFLICT(username) DO UPDATE SET is_typing = 1, updated_at = %s
    ''', (current_user, now_str, now_str))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})

@app.route('/chat/stop_typing', methods=['POST'])
def chat_stop_typing():
    if 'user' not in session:
        return jsonify({'success': False})
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE typing_status SET is_typing = 0 WHERE username = %s", (current_user,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})

@app.route('/chat/get_typing')
def chat_get_typing():
    if 'user' not in session:
        return jsonify({'typing_users': []})
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM typing_status WHERE is_typing = 1 AND username != %s", (current_user,))
    typing_users = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return jsonify({'typing_users': typing_users})

@app.route('/chat/delete/<int:msg_id>', methods=['POST'])
def chat_delete(msg_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Giriş edilməyib'})
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT sender, content FROM messages WHERE id = %s", (msg_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': 'Mesaj tapılmadı'})
    
    is_admin = (current_user.lower() == 'win_wid')
    is_police = session.get('is_police_logged', False)
    police_regiment = session.get('active_regiment', 'POLİS İDARƏSİ')
    
    if row[0] == current_user or is_admin or is_police:
        cursor.execute("DELETE FROM messages WHERE id = %s", (msg_id,))
        cursor.execute("DELETE FROM message_reactions WHERE message_id = %s", (msg_id,))
        
        if is_police or is_admin:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_text = f"Silinən mesaj: '@{row[0]}: {row[1]}'"
            cursor.execute('''
                INSERT INTO archived_logs (log_type, target_info, police_name, regiment, created_at)
                VALUES (%s, %s, %s, %s, %s)
            ''', ('MESAJ_SILINDI', log_text, current_user, police_regiment, now_str))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    cursor.close()
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT sender FROM messages WHERE id = %s", (msg_id,))
    row = cursor.fetchone()
    if row and row[0] == current_user:
        cursor.execute("UPDATE messages SET content = %s WHERE id = %s", (new_content, msg_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'content': new_content})
    cursor.close()
    conn.close()
    return jsonify({'success': False, 'error': 'İcazəniz yoxdur'})

@app.route('/oyun')
def oyun():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM notifications WHERE username = %s AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(OYUN_MENU_TEMPLATE, header=header_html)

@app.route('/oyun/wow')
def oyun_wow():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM notifications WHERE username = %s AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    
    words_list = ["AZƏRBAYCAN", "KOMPÜTER", "PROQRAM", "İNFORMASİYA", "TƏHSİL", "QƏLƏBƏ", "KODLAŞMA", "DOSYA", "İDMAN", "TARİX"]
    full_word = random.choice(words_list)
    
    idx = random.randint(0, len(full_word) - 1)
    hidden_letter = full_word[idx]
    masked_word = full_word[:idx] + "_" + full_word[idx+1:]
    
    return render_template_string(WOW_OYUNU_TEMPLATE, header=header_html, masked_word=masked_word, full_word=full_word, hidden_letter=hidden_letter)

@app.route('/oyun/wow/cavabla', methods=['POST'])
def oyun_wow_cavabla():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    user_letter = request.form.get('user_letter', '').strip().upper()
    hidden_letter = request.form.get('hidden_letter', '').strip().upper()
    full_word = request.form.get('full_word', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM notifications WHERE username = %s AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    
    success = (user_letter == hidden_letter)
    message = "Təbriklər! Hərfi düz tapdınız (+5 WON) 🎉" if success else f"Səhvdir! Gizli hərf '{hidden_letter}' idi."
    
    if success:
        cursor.execute("UPDATE users SET points = points + 5 WHERE nickname = %s", (current_user,))
        conn.commit()
    cursor.close()
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    
    words_list = ["AZƏRBAYCAN", "KOMPÜTER", "PROQRAM", "İNFORMASİYA", "TƏHSİL", "QƏLƏBƏ", "KODLAŞMA", "DOSYA", "İDMAN", "TARİX"]
    next_word = random.choice(words_list)
    idx = random.randint(0, len(next_word) - 1)
    next_hidden = next_word[idx]
    next_masked = next_word[:idx] + "_" + next_word[idx+1:]
    
    return render_template_string(WOW_OYUNU_TEMPLATE, header=header_html, masked_word=next_masked, full_word=next_word, hidden_letter=next_hidden, message=message, success=success)

@app.route('/oyun/sual')
def oyun_sual():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM notifications WHERE username = %s AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    
    q_bank = [
        ("Azərbaycanın paytaxtı haradır?", "Bakı", "Coğrafiya"),
        ("Dünyanın ən böyük okeanı hansıdır?", "Sakit okean", "Coğrafiya"),
        ("Azərbaycan Demokratik Respublikası neçənci ildə yaradılıb?", "1918", "Tarix"),
        ("İkinci Dünya müharibəsi neçənci ildə bitmişdir?", "1945", "Tarix"),
        ("İnsanda neçə əsas qrup qan var?", "4", "Elm"),
        ("Günəş sisteminin ən böyük planet hansıdır?", "Yupiter", "Elm"),
        ("DNT-nin açılımı neçə hərflidir və ya forması necədir?", "Spiral", "Elm"),
        ("Azərbaycanın bayrağındakı rənglərin sayı neçədir?", "3", "Mədəniyyət"),
        ("Dünyanın ən uzun çayı hansıdır?", "Nil", "Coğrafiya"),
        ("Su kimyəvi olaraq necə işarələnir?", "H2O", "Elm"),
        ("Azərbaycanın dövlət himninin musiqisini kim bəstələyib?", "Üzeyir Hacıbəyov", "Mədəniyyət"),
        ("Kompüterin əsas beyini nə adlanır?", "Prosessor", "Texnologiya"),
        ("İşıq sürəti təqribən saniyədə neçə kilometrdir?", "300000", "Elm"),
        ("Dünyanın ən hündür dağı hansıdır?", "Everest", "Coğrafiya"),
        ("Azərbaycanın milli valyutası necə adlanır?", "Manat", "İqtisadiyyat"),
        ("Qız qalası hansı şəhərdə yerləşir?", "Bakı", "Mədəniyyət"),
        ("Dünyanın ən kiçik ölkəsi hansıdır?", "Vatikan", "Coğrafiya"),
        ("Futbol oyununda bir komandada meydanda neçə oyunçu olur?", "11", "İdman"),
        ("Basketbol səbətinin hündürlüyü neçə metrdir?", "3", "İdman"),
        ("Yer kürəsinin neçə faizi sudan ibarətdir?", "71", "Coğrafiya"),
        ("Kitabi-Dədə Qorqud dastanının neçə boyu var?", "12", "Ədəbiyyat"),
        ("Nizami Gəncəvinin məşhur əsəri 'Xəmsə' neçə poemadan ibarətdir?", "5", "Ədəbiyyat"),
        ("Azərbaycanın ilk dəmir yolu xətti hansı şəhərlər arasında çəkilib?", "Bakı Sabunçu", "Tarix"),
        ("Periodik cədvəlin banisi kimdir?", "Mendeleyev", "Elm"),
        ("İnsan bədənində ən güclü əzələ hansıdır?", "Çənə əzələsi", "Elm"),
        ("Dünyanın ən dərin gölü hansıdır?", "Baykal", "Coğrafiya"),
        ("Azərbaycan nefti ilk dəfə sənaye üsulu ilə harada çıxarılıb?", "Bibiheybət", "Tarix"),
        ("Dünyanın ən qədim şəhərlərindən biri olan Naxçıvanın yaşı təxminən neçə illikdir?", "5000", "Tarix"),
        ("Şahmat oyununda ümumi xana sayı neçədir?", "64", "İdman"),
        ("Kompüter klaviaturasında əsas hərflərin yazıldığı rejim necə adlanır?", "Qwerty", "Texnologiya"),
        ("Atatürk neçənci ildə anadan olub?", "1881", "Tarix"),
        ("Azərbaycanın ilk peyki necə adlanır?", "Azerspace", "Texnologiya"),
        ("Dünyanın ən böyük səhrası hansıdır?", "Saxara", "Coğrafiya"),
        ("İnsan skeletində təxminən neçə sümük var?", "206", "Elm"),
        ("Fransanın paytaxtı haradır?", "Paris", "Coğrafiya"),
        ("İtaliyanın paytaxtı hansı şəhərdir?", "Roma", "Coğrafiya"),
        ("Azərbaycanın ərazisi neçə kvadrat kilometrdir?", "86600", "Coğrafiya"),
        ("Dünyanın ən böyük materiki hansıdır?", "Asiya", "Coğrafiya"),
        ("Almaniyanın paytaxtı hansıdır?", "Berlin", "Coğrafiya"),
        ("İlk dəfə internet neçənci ildə yaradılıb?", "1969", "Texnologiya")
    ]
    
    q_item = random.choice(q_bank)
    return render_template_string(SUAL_CAVAB_TEMPLATE, header=header_html, question=q_item[0], answer=q_item[1], topic=q_item[2])

@app.route('/oyun/sual/cavabla', methods=['POST'])
def oyun_sual_cavabla():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    current_user = session['user']
    user_answer = request.form.get('user_answer', '').strip().lower()
    correct_answer = request.form.get('correct_answer', '').strip().lower()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM notifications WHERE username = %s AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    
    success = (user_answer == correct_answer)
    message = "Təbriklər! Düzgün cavab (+5 WON) 🎉" if success else f"Səhvdir! Düzgün cavab: {correct_answer}"
    
    if success:
        cursor.execute("UPDATE users SET points = points + 5 WHERE nickname = %s", (current_user,))
        conn.commit()
    cursor.close()
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(SUAL_CAVAB_TEMPLATE, header=header_html, question="Növbəti sual üçün aşağıdan davam edin və ya yeniləyin.", answer="", topic="Dinamik Sual", message=message, success=success)

@app.route('/istifadeciler')
def istifadeciler():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM notifications WHERE username = %s AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    
    is_admin = (current_user.lower() == 'win_wid')
    is_police = session.get('is_police_logged', False)
    
    cursor.execute("SELECT nickname, profile_pic, name_color, profile_sticker FROM users")
    all_users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(USERS_TEMPLATE, all_users=all_users, current_user=current_user, is_admin=is_admin, is_police=is_police, header=header_html)

@app.route('/istifadeci_profil/<username>')
def istifadeci_profil(username):
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT profile_pic, name_color, profile_sticker FROM users WHERE nickname = %s", (username,))
    user_res = cursor.fetchone()
    if not user_res:
        cursor.close()
        conn.close()
        return redirect(url_for('istifadeciler'))
        
    pic = user_res[0]
    name_color = user_res[1]
    profile_sticker = user_res[2]
    
    cursor.execute("SELECT gift, sender FROM gifts WHERE receiver = %s", (username,))
    gifts = cursor.fetchall()
    
    cursor.execute("SELECT id FROM notifications WHERE username = %s AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(PUBLIC_PROFILE_TEMPLATE, target_user=username, pic=pic, name_color=name_color, profile_sticker=profile_sticker, gifts=gifts, header=header_html, message=request.args.get('message'))

@app.route('/blok_et/<username>', methods=['POST'])
def blok_et(username):
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    notif_text = f"⚠️ Diqqət: @{current_user} tərəfindən bloklandınız!"
    cursor.execute("INSERT INTO notifications (username, content) VALUES (%s, %s)", (username, notif_text))
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for('istifadeci_profil', username=username, message=f"@{username} uğurla bloklandı!"))

@app.route('/sikayet_et_profil/<username>', methods=['POST'])
def sikayet_et_profil(username):
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    complaint_text = f"Profil şikayəti: @{current_user} tərəfindən @{username} şikayət olundu."
    cursor.execute("INSERT INTO complaints (username, category, content) VALUES (%s, %s, %s)", (current_user, "İstifadəçi profili şikayəti", complaint_text))
    cursor.execute("INSERT INTO notifications (username, content) VALUES ('win_wid', %s)", (f"📢 Profil Şikayəti: {complaint_text}",))
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for('istifadeci_profil', username=username, message=f"@{username} haqqında şikayət rəhbərliyə göndərildi!"))

@app.route('/ozel_mesaj/<receiver>', methods=['GET', 'POST'])
def ozel_mesaj(receiver):
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if content:
            cursor.execute("INSERT INTO private_messages (sender, receiver, content) VALUES (%s, %s, %s)", (current_user, receiver, content))
            conn.commit()
            
    cursor.execute("SELECT id FROM notifications WHERE username = %s AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    
    cursor.execute('''
        SELECT id, sender, receiver, content FROM private_messages 
        WHERE (sender = %s AND receiver = %s) OR (sender = %s AND receiver = %s) 
        ORDER BY id ASC
    ''', (current_user, receiver, receiver, current_user))
    messages = cursor.fetchall()
    cursor.close()
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(PRIVATE_CHAT_TEMPLATE, messages=messages, receiver=receiver, current_user=current_user, header=header_html)

@app.route('/vidyo')
def vidyo():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM notifications WHERE username = %s AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    
    is_admin = (current_user.lower() == 'win_wid')
    is_police = session.get('is_police_logged', False)
    
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
        cursor.execute("SELECT * FROM video_likes WHERE video_id = %s AND username = %s", (v_id, current_user))
        liked = cursor.fetchone() is not None
        
        cursor.execute("SELECT COUNT(*) FROM video_likes WHERE video_id = %s", (v_id,))
        like_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT id, username, comment FROM video_comments WHERE video_id = %s ORDER BY id ASC", (v_id,))
        comments = cursor.fetchall()
        
        videos.append((v[0], v[1], v[2], liked, like_count, comments, v[3]))
        
    cursor.close()
    conn.close()
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(VIDYO_TEMPLATE, videos=videos, current_user=current_user, is_admin=is_admin, is_police=is_police, header=header_html)

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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO videos (uploader, video_data) VALUES (%s, %s)", (session['user'], b64_str))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('vidyo'))

@app.route('/vidyo/like/<int:video_id>', methods=['POST'])
def vidyo_like(video_id):
    if 'user' not in session:
        return jsonify({'success': False})
    user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM video_likes WHERE video_id = %s AND username = %s", (video_id, user))
    if cursor.fetchone():
        cursor.execute("DELETE FROM video_likes WHERE video_id = %s AND username = %s", (video_id, user))
        liked = False
    else:
        cursor.execute("INSERT INTO video_likes (video_id, username) VALUES (%s, %s)", (video_id, user))
        liked = True
    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM video_likes WHERE video_id = %s", (video_id,))
    count = cursor.fetchone()[0]
    cursor.close()
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO video_comments (video_id, username, comment) VALUES (%s, %s, %s)", (video_id, user, comment))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True, 'user': user, 'comment': comment})

@app.route('/vidyo/share/<int:video_id>', methods=['POST'])
def vidyo_share(video_id):
    if 'user' not in session:
        return jsonify({'success': False})
    data = request.get_json()
    receiver = data.get('receiver', '').strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE nickname = %s", (receiver,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': 'İstifadəçi tapılmadı'})
    cursor.execute("INSERT INTO video_shares (video_id, sender, receiver) VALUES (%s, %s, %s)", (video_id, session['user'], receiver))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})

@app.route('/vidyo/delete/<int:video_id>', methods=['POST'])
def vidyo_delete(video_id):
    if 'user' not in session:
        return jsonify({'success': False})
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT uploader FROM videos WHERE id = %s", (video_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return jsonify({'success': False})
    
    is_admin = (current_user.lower() == 'win_wid')
    is_police = session.get('is_police_logged', False)
    if row[0] == current_user or is_admin or is_police:
        cursor.execute("DELETE FROM videos WHERE id = %s", (video_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    cursor.close()
    conn.close()
    return jsonify({'success': False})

@app.route('/vidyo/bookmark/<int:video_id>', methods=['POST'])
def toggle_bookmark(video_id):
    if 'user' not in session:
        return jsonify({'success': False})
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Əvvəlcədən yadda saxlanılıbmı yoxlayırıq
    cursor.execute("SELECT id FROM video_bookmarks WHERE video_id = %s AND username = %s", (video_id, current_user))
    existing = cursor.fetchone()
    
    if existing:
        # Varsa silirik (yaddaşdan çıxarırıq)
        cursor.execute("DELETE FROM video_bookmarks WHERE video_id = %s AND username = %s", (video_id, current_user))
        bookmarked = False
    else:
        # Yoxdursa əlavə edirik
        cursor.execute("INSERT INTO video_bookmarks (video_id, username) VALUES (%s, %s)", (video_id, current_user))
        bookmarked = True
        
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True, 'bookmarked': bookmarked})

@app.route('/profil', methods=['GET', 'POST'])
def profil():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Lazımi sütun və cədvəllərin mövcudluğunu təmin edirik
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        conn.rollback()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_bookmarks (
                id SERIAL PRIMARY KEY,
                video_id INTEGER,
                username TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS video_likes (
                id SERIAL PRIMARY KEY,
                video_id INTEGER,
                username TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gifts (
                id SERIAL PRIMARY KEY,
                receiver TEXT,
                sender TEXT,
                gift TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                username TEXT,
                is_read INTEGER DEFAULT 0
            )
        """)
        conn.commit()
    except Exception:
        conn.rollback()

    message = None
    error = False
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'edit_profile':
            new_name = request.form.get('new_nickname', '').strip()
            new_bio = request.form.get('new_bio', '').strip()
            
            if not new_name or len(new_name) > 7:
                message = "Nik adı 7 hərfdən çox ola bilməz!"
                error = True
            else:
                if new_name != current_user:
                    cursor.execute("SELECT * FROM users WHERE nickname = %s", (new_name,))
                    if cursor.fetchone():
                        message = "Bu nik artıq istifadə olunur!"
                        error = True
                    else:
                        cursor.execute("UPDATE users SET nickname = %s WHERE nickname = %s", (new_name, current_user))
                        cursor.execute("UPDATE messages SET sender = %s WHERE sender = %s", (new_name, current_user))
                        cursor.execute("UPDATE videos SET uploader = %s WHERE uploader = %s", (new_name, current_user))
                        session['user'] = new_name
                        current_user = new_name
                
                cursor.execute("UPDATE users SET bio = %s WHERE nickname = %s", (new_bio, current_user))
                
                file = request.files.get('pic_file')
                if file and file.filename != '':
                    img_bytes = file.read()
                    b64_str = "data:image/jpeg;base64," + base64.b64encode(img_bytes).decode('utf-8')
                    cursor.execute("UPDATE users SET profile_pic = %s WHERE nickname = %s", (b64_str, current_user))
                    
                conn.commit()
                message = "Profil uğurla yeniləndi!"
        elif action == 'delete_account':
            cursor.execute("DELETE FROM users WHERE nickname = %s", (current_user,))
            conn.commit()
            cursor.close()
            conn.close()
            session.pop('user', None)
            return redirect(url_for('index'))

    try:
        cursor.execute("SELECT points, profile_pic, name_color, profile_sticker, bio FROM users WHERE nickname = %s", (current_user,))
        user_data = cursor.fetchone()
    except Exception:
        user_data = None
        conn.rollback()

    points = user_data[0] if user_data else 0
    pic = user_data[1] if user_data else None
    name_color = user_data[2] if user_data else 'inherit'
    profile_sticker = user_data[3] if user_data else ''
    bio = user_data[4] if user_data and len(user_data) > 4 else ''
    
    try:
        cursor.execute("SELECT gift, sender FROM gifts WHERE receiver = %s", (current_user,))
        gifts = cursor.fetchall()
    except Exception:
        gifts = []
        conn.rollback()
    
    try:
        cursor.execute("SELECT id, uploader, video_data FROM videos WHERE uploader = %s ORDER BY id DESC", (current_user,))
        user_videos = cursor.fetchall()
    except Exception:
        user_videos = []
        conn.rollback()
    
    try:
        cursor.execute('''
            SELECT v.id, v.uploader, v.video_data 
            FROM videos v 
            JOIN video_likes l ON v.id = l.video_id 
            WHERE l.username = %s 
            ORDER BY v.id DESC
        ''', (current_user,))
        liked_videos = cursor.fetchall()
    except Exception:
        liked_videos = []
        conn.rollback()
    
    try:
        cursor.execute('''
            SELECT v.id, v.uploader, v.video_data 
            FROM videos v 
            JOIN video_bookmarks b ON v.id = b.video_id 
            WHERE b.username = %s 
            ORDER BY v.id DESC
        ''', (current_user,))
        saved_videos = cursor.fetchall()
    except Exception:
        saved_videos = []
        conn.rollback()
    
    try:
        cursor.execute("SELECT id FROM notifications WHERE username = %s AND is_read = 0", (current_user,))
        has_unread_notifs = cursor.fetchone() is not None
    except Exception:
        has_unread_notifs = False
        conn.rollback()
    
    is_admin = (current_user.lower() == 'win_wid')
    
    cursor.close()
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(
        PROFIL_TEMPLATE, 
        user=current_user, 
        points=points, 
        pic=pic, 
        name_color=name_color, 
        profile_sticker=profile_sticker, 
        bio=bio,
        gifts=gifts, 
        user_videos=user_videos,
        liked_videos=liked_videos,
        saved_videos=saved_videos,
        is_admin=is_admin, 
        message=message, 
        error=error, 
        header=header_html
    )

@app.route('/canli')
def canli():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT points FROM users WHERE nickname = %s", (current_user,))
    p_row = cursor.fetchone()
    user_points = p_row[0] if p_row else 0

    cursor.execute("SELECT id FROM notifications WHERE username = %s AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    
    cursor.execute('''
        SELECT l.id, l.host, u.profile_pic 
        FROM lives l 
        LEFT JOIN users u ON l.host = u.nickname 
        WHERE l.is_active = 1
        ORDER BY l.id DESC
    ''')
    lives = cursor.fetchall()
    cursor.close()
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(CANLI_TEMPLATE, lives=lives, current_user=current_user, user_points=user_points, header=header_html)

@app.route('/canli/ac', methods=['POST'])
def canli_ac():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT points FROM users WHERE nickname = %s", (current_user,))
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
        cursor.close()
        conn.close()
        return render_template_string(CANLI_TEMPLATE, lives=lives, current_user=current_user, user_points=points, error="Canlı açmaq üçün balansınızda ən azı 60 Won olmalıdır!", header=get_header_template(False))
        
    cursor.execute("UPDATE lives SET is_active = 0 WHERE host = %s", (current_user,))
    cursor.execute("INSERT INTO lives (host, is_active) VALUES (%s, 1) RETURNING id", (current_user,))
    live_id = cursor.fetchone()[0]
    cursor.execute("INSERT INTO live_stream_chunks (live_id) VALUES (%s) ON CONFLICT (live_id) DO NOTHING", (live_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('canli_izle', live_id=live_id))

@app.route('/canli/izle/<int:live_id>')
def canli_izle(live_id):
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM live_blocks WHERE live_id = %s AND blocked_user = %s", (live_id, current_user))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return redirect(url_for('canli'))

    cursor.execute("SELECT host FROM lives WHERE id = %s AND is_active = 1", (live_id,))
    live = cursor.fetchone()
    if not live:
        cursor.close()
        conn.close()
        return redirect(url_for('canli'))
    host = live[0]
    
    cursor.execute("SELECT profile_pic FROM users WHERE nickname = %s", (host,))
    p_res = cursor.fetchone()
    host_pic = p_res[0] if p_res else None
    
    cursor.execute("SELECT id, sender, gift FROM live_gifts WHERE live_id = %s", (live_id,))
    gifts = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM live_likes WHERE live_id = %s", (live_id,))
    likes_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT id FROM notifications WHERE username = %s AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(CANLI_ROOM_TEMPLATE, live_id=live_id, host=host, host_pic=host_pic, gifts=gifts, likes_count=likes_count, current_user=current_user, header=header_html)

@app.route('/canli/yayim_gonder/<int:live_id>', methods=['POST'])
def canli_yayim_gonder(live_id):
    if 'user' not in session:
        return jsonify({'success': False})
    data = request.get_json(silent=True) or {}
    frame_data = data.get('frame_data')
    if frame_data:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO live_stream_chunks (live_id, frame_data, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (live_id) DO UPDATE SET frame_data = EXCLUDED.frame_data, updated_at = NOW()
        ''', (live_id, frame_data))
        conn.commit()
        cursor.close()
        conn.close()
    return jsonify({'success': True})

@app.route('/canli/ses_gonder/<int:live_id>', methods=['POST'])
def canli_ses_gonder(live_id):
    if 'user' not in session:
        return jsonify({'success': False})
    data = request.get_json(silent=True) or {}
    audio_data = data.get('audio_data')
    if audio_data:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO live_stream_chunks (live_id, audio_data, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (live_id) DO UPDATE SET audio_data = EXCLUDED.audio_data, updated_at = NOW()
        ''', (live_id, audio_data))
        conn.commit()
        cursor.close()
        conn.close()
    return jsonify({'success': True})

@app.route('/canli/kontrol/<int:live_id>', methods=['POST'])
def canli_kontrol(live_id):
    if 'user' not in session:
        return jsonify({'success': False})
    data = request.get_json(silent=True) or {}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE live_stream_chunks 
        SET is_video_off = %s, is_audio_off = %s, is_paused = %s 
        WHERE live_id = %s
    ''', (data.get('is_video_off', 0), data.get('is_audio_off', 0), data.get('is_paused', 0), live_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})

@app.route('/canli/like/<int:live_id>', methods=['POST'])
def canli_like(live_id):
    if 'user' not in session:
        return jsonify({'success': False})
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO live_likes (live_id, username) VALUES (%s, %s)", (live_id, current_user))
    cursor.execute("SELECT COUNT(*) FROM live_likes WHERE live_id = %s", (live_id,))
    likes_count = cursor.fetchone()[0]

    if likes_count > 0 and likes_count % 50 == 0:
        cursor.execute("SELECT host FROM lives WHERE id = %s", (live_id,))
        live_row = cursor.fetchone()
        if live_row:
            cursor.execute("UPDATE users SET points = points + 10 WHERE nickname = %s", (live_row[0],))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True, 'likes_count': likes_count})

@app.route('/canli/mesaj/<int:live_id>', methods=['POST'])
def canli_mesaj(live_id):
    if 'user' not in session:
        return jsonify({'success': False})
    current_user = session['user']
    data = request.get_json(silent=True) or {}
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'success': False})
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM live_blocks WHERE live_id = %s AND blocked_user = %s", (live_id, current_user))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': 'Bloklandığınız üçün mesaj yaza bilməzsiniz!'})

    cursor.execute("INSERT INTO live_messages (live_id, sender, content) VALUES (%s, %s, %s)", (live_id, current_user, content))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})

@app.route('/canli/hediyye/<int:live_id>', methods=['POST'])
def canli_hediyye(live_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Giriş edilməyib'})
    current_user = session['user']
    data = request.get_json(silent=True) or {}
    gift = data.get('gift')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT points FROM users WHERE nickname = %s", (current_user,))
    res = cursor.fetchone()
    user_points = res[0] if res else 0
    
    if user_points < 10:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': 'Balansınızda kifayət qədər Won yoxdur (10 Won lazımdır)'})
        
    cursor.execute("SELECT host FROM lives WHERE id = %s", (live_id,))
    live = cursor.fetchone()
    if not live:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': 'Canlı yayım tapılmadı'})
    host = live[0]
    
    cursor.execute("UPDATE users SET points = points - 10 WHERE nickname = %s", (current_user,))
    cursor.execute("UPDATE users SET points = points + 10 WHERE nickname = %s", (host,))
    cursor.execute("INSERT INTO live_gifts (live_id, sender, gift) VALUES (%s, %s, %s)", (live_id, current_user, gift))
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM live_gifts WHERE live_id = %s", (live_id,))
    gifts_count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'gifts_count': gifts_count})

@app.route('/canli/blokla/<int:live_id>', methods=['POST'])
def canli_blokla(live_id):
    if 'user' not in session:
        return jsonify({'success': False})
    current_user = session['user']
    data = request.get_json(silent=True) or {}
    target_user = data.get('target_user', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT host FROM lives WHERE id = %s", (live_id,))
    live = cursor.fetchone()

    if not live or live[0] != current_user:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': 'Yalnız canlı sahibi istifadəçini bloklaya bilər!'})

    if target_user == current_user:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': 'Özünüzü bloklaya bilməzsiniz!'})

    cursor.execute("INSERT INTO live_blocks (live_id, blocked_user) VALUES (%s, %s) ON CONFLICT DO NOTHING", (live_id, target_user))
    cursor.execute("DELETE FROM live_messages WHERE live_id = %s AND sender = %s", (live_id, target_user))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True, 'message': f'@{target_user} canlı yayımdan bloklandı!'})

@app.route('/canli/sikayet/<int:live_id>', methods=['POST'])
def canli_sikayet(live_id):
    if 'user' not in session:
        return jsonify({'success': False})
    current_user = session['user']
    data = request.get_json(silent=True) or {}
    target_user = data.get('target_user', '').strip()
    msg_content = data.get('msg_content', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    notif_text = f"⚠️ Canlı Yayım Şikayəti: @{current_user} istifadəçisi @{target_user} haqqında şikayət etdi. Mesaj: '{msg_content}'"
    cursor.execute("INSERT INTO notifications (username, content) VALUES ('win_wid', %s)", (notif_text,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True, 'message': f'@{target_user} haqqında şikayət rəhbərliyə göndərildi!'})

@app.route('/canli/yenile/<int:live_id>')
def canli_yenile(live_id):
    if 'user' not in session:
        return jsonify({'success': False})
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT is_active FROM lives WHERE id = %s", (live_id,))
    l_row = cursor.fetchone()
    if not l_row or l_row[0] == 0:
        cursor.close()
        conn.close()
        return jsonify({'is_active': False})

    cursor.execute("SELECT id FROM live_blocks WHERE live_id = %s AND blocked_user = %s", (live_id, current_user))
    is_blocked = cursor.fetchone() is not None
    
    cursor.execute("SELECT COUNT(*) FROM live_likes WHERE live_id = %s", (live_id,))
    likes_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM live_gifts WHERE live_id = %s", (live_id,))
    gifts_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT sender, content FROM live_messages WHERE live_id = %s ORDER BY id ASC LIMIT 50", (live_id,))
    messages = [{'sender': r[0], 'content': r[1]} for r in cursor.fetchall()]

    cursor.execute('''
        SELECT frame_data, audio_data, is_video_off, is_audio_off, is_paused 
        FROM live_stream_chunks WHERE live_id = %s
    ''', (live_id,))
    stream_row = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return jsonify({
        'is_active': True,
        'is_blocked': is_blocked,
        'likes_count': likes_count,
        'gifts_count': gifts_count,
        'messages': messages,
        'frame_data': stream_row[0] if stream_row else None,
        'audio_data': stream_row[1] if stream_row else None,
        'is_video_off': stream_row[2] if stream_row else 0,
        'is_audio_off': stream_row[3] if stream_row else 0,
        'is_paused': stream_row[4] if stream_row else 0
    })

@app.route('/canli/bitir/<int:live_id>', methods=['POST'])
def canli_bitir(live_id):
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT host FROM lives WHERE id = %s AND is_active = 1", (live_id,))
    live = cursor.fetchone()
    if live and live[0] == current_user:
        cursor.execute("UPDATE lives SET is_active = 0 WHERE id = %s", (live_id,))
        cursor.execute("DELETE FROM live_stream_chunks WHERE live_id = %s", (live_id,))
        conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('canli'))

@app.route('/bildiris')
def bildiris():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE username = %s", (current_user,))
    cursor.execute("SELECT id, content FROM notifications WHERE username = %s ORDER BY id DESC", (current_user,))
    notifs = cursor.fetchall()
    conn.commit()
    cursor.close()
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

@app.route('/sikayet', methods=['GET', 'POST'])
def sikayet():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    message = None
    if request.method == 'POST':
        category = request.form.get('category')
        content = request.form.get('content')
        if category and content:
            cursor.execute("INSERT INTO complaints (username, category, content) VALUES (%s, %s, %s)", (current_user, category, content))
            
            notif_text = f"📢 Yeni Şikayət! İstifadəçi: @{current_user} | Kateqoriya: {category} | Mətn: {content}"
            cursor.execute("INSERT INTO notifications (username, content) VALUES ('win_wid', %s)", (notif_text,))
            
            conn.commit()
            message = "Şikayətiniz uğurla göndərildi!"
            
    cursor.execute("SELECT id FROM notifications WHERE username = %s AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    cursor.close()
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

@app.route('/admin/sikayetler')
def admin_sikayetler():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    
    if current_user.lower() != 'win_wid':
        return redirect(url_for('chat'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, category, content FROM complaints ORDER BY id DESC")
    comps = cursor.fetchall()
    cursor.close()
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

@app.route('/admin/delete_user/<username>', methods=['POST'])
def admin_delete_user(username):
    if 'user' not in session:
        return jsonify({'success': False})
    current_user = session['user']
    is_admin = (current_user.lower() == 'win_wid')
    is_police = session.get('is_police_logged', False)
    police_regiment = session.get('active_regiment', 'POLİS İDARƏSİ')
    
    if (is_admin or is_police) and username.lower() != 'win_wid':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE nickname = %s", (username,))
        cursor.execute("DELETE FROM messages WHERE sender = %s", (username,))
        cursor.execute("DELETE FROM private_messages WHERE sender = %s OR receiver = %s", (username, username))
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_text = f"Bloklanan / Silinən istifadəçi: '@{username}'"
        cursor.execute('''
            INSERT INTO archived_logs (log_type, target_info, police_name, regiment, created_at)
            VALUES (%s, %s, %s, %s, %s)
        ''', ('ISTIFADECI_BLOKLANDI', log_text, current_user, police_regiment, now_str))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/magaza')
def magaza():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE nickname = %s", (current_user,))
    res = cursor.fetchone()
    user_points = res[0] if res else 0
    cursor.execute("SELECT id FROM notifications WHERE username = %s AND is_read = 0", (current_user,))
    has_unread_notifs = cursor.fetchone() is not None
    
    cursor.execute("SELECT nickname FROM users")
    all_users = [u[0] for u in cursor.fetchall()]
    cursor.close()
    conn.close()
    
    header_html = get_header_template(has_unread_notifs)
    return render_template_string(
        MAGAZA_TEMPLATE,
        user_points=user_points,
        all_users=all_users,
        current_user=current_user,
        message=request.args.get('message'),
        error=request.args.get('error'),
        header=header_html
    )

@app.route('/magaza/al_entry_effect', methods=['POST'])
def magaza_al_entry_effect():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT points, has_entry_effect FROM users WHERE nickname = %s", (current_user,))
    res = cursor.fetchone()
    if not res:
        cursor.close()
        conn.close()
        return redirect(url_for('magaza', error="İstifadəçi tapılmadı!"))
        
    points, has_effect = res[0], res[1]
    
    if has_effect:
        cursor.close()
        conn.close()
        return redirect(url_for('magaza', error="Sizdə artıq Giriş Effekti mövcuddur!"))
        
    if points < 500:
        cursor.close()
        conn.close()
        return redirect(url_for('magaza', error="Balansınızda kifayət qədər bal yoxdur (400 Won lazımdır)!"))
        
    cursor.execute("UPDATE users SET points = points - 400, has_entry_effect = 1 WHERE nickname = %s", (current_user,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('magaza', message="Giriş Effekti uğurla alındı! Artıq çata daxil olanda hər kəsə bildiriş gedəcək."))

@app.route('/magaza/al_nik', methods=['POST'])
def magaza_al_nik():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    color = request.form.get('color')
    
    if not color:
        return redirect(url_for('magaza', error="Rəng seçilmədi!"))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE nickname = %s", (current_user,))
    points = cursor.fetchone()[0]
    
    if points < 25:
        cursor.close()
        conn.close()
        return redirect(url_for('magaza', error="Balansınızda kifayət qədər Won yoxdur (25 won lazımdır)!"))
        
    cursor.execute("UPDATE users SET points = points - 25, name_color = %s WHERE nickname = %s", (color, current_user))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('magaza', message="Rəngli Nik uğurla alındı! Çatda nikinizin rəngi yeniləndi."))

@app.route('/magaza/al_mesaj', methods=['POST'])
def magaza_al_mesaj():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    color = request.form.get('color')
    
    if not color:
        return redirect(url_for('magaza', error="Rəng seçilmədi!"))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE nickname = %s", (current_user,))
    points = cursor.fetchone()[0]
    
    if points < 25:
        cursor.close()
        conn.close()
        return redirect(url_for('magaza', error="Balansınızda kifayət qədər Won yoxdur (25 Won lazımdır)!"))
        
    cursor.execute("UPDATE users SET points = points - 25, msg_color = %s WHERE nickname = %s", (color, current_user))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('magaza', message="Rəngli Mesaj uğurla alındı! Çatdakı mesajlarınızın rəngi yeniləndi."))

@app.route('/magaza/gonder_hediyye', methods=['POST'])
def magaza_gonder_hediyye():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    receiver = request.form.get('receiver')
    selected_gift = request.form.get('selected_gift')
    
    if not receiver or not selected_gift:
        return redirect(url_for('magaza', error="Məlumatlar tam seçilmədi!"))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM users WHERE nickname = %s", (current_user,))
    points = cursor.fetchone()[0]
    
    if points < 10:
        cursor.close()
        conn.close()
        return redirect(url_for('magaza', error="Hədiyyə göndərmək üçün ən azı 10 Wonunuz olmalıdır!"))
        
    cursor.execute("UPDATE users SET points = points - 10 WHERE nickname = %s", (current_user,))
    cursor.execute("INSERT INTO gifts (sender, receiver, gift) VALUES (%s, %s, %s)", (current_user, receiver, selected_gift))
    
    notif_text = f"🎁 @{current_user} sizə mağazadan hədiyyə göndərdi: {selected_gift}"
    cursor.execute("INSERT INTO notifications (username, content) VALUES (%s, %s)", (receiver, notif_text))
    
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('magaza', message=f"{selected_gift} hədiyyəsi @{receiver} istifadəçisinə uğurla göndərildi!"))

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('is_police_logged', None)
    session.pop('active_regiment', None)
    return redirect(url_for('index'))
@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('.', 'manifest.json')

@app.route('/logo.jpg')
def serve_logo():
    return send_from_directory('.', 'logo.jpg')
    
    KUKULI_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - KUKULİ 🐻 Köməkçi</title>
    ''' + COMMON_STYLE + '''
    <style>
        .ai-container {
            background: rgba(24, 24, 27, 0.88);
            backdrop-filter: blur(16px);
            flex: 1;
            border: 1px solid rgba(249, 115, 22, 0.35);
            border-radius: 22px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 15px 35px rgba(0,0,0,0.6);
        }
        .ai-header {
            background: linear-gradient(135deg, rgba(249, 115, 22, 0.2), rgba(9, 9, 11, 0.9));
            padding: 16px 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        .ai-avatar {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: linear-gradient(135deg, #f97316, #ea580c);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 0 15px rgba(249, 115, 22, 0.5);
        }
        .ai-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }
        .ai-bubble {
            padding: 14px 18px;
            border-radius: 18px;
            max-width: 82%;
            font-size: 15px;
            line-height: 1.5;
            word-wrap: break-word;
        }
        .bot-msg {
            background: rgba(39, 39, 42, 0.85);
            border: 1px solid rgba(249, 115, 22, 0.3);
            color: #f8fafc;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
        }
        .user-msg {
            background: linear-gradient(135deg, #f97316, #ea580c);
            color: #fff;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        .quick-questions {
            display: flex;
            gap: 8px;
            padding: 10px 16px;
            overflow-x: auto;
            background: rgba(9, 9, 11, 0.5);
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }
        .quick-btn {
            background: rgba(249, 115, 22, 0.15);
            border: 1px solid rgba(249, 115, 22, 0.4);
            color: #fb923c;
            padding: 6px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            white-space: nowrap;
            cursor: pointer;
        }
        .ai-form {
            display: flex;
            padding: 14px;
            background: rgba(9, 9, 11, 0.8);
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            gap: 10px;
        }
        .ai-input {
            flex: 1;
            height: 48px;
            padding: 0 16px;
            background: rgba(24, 24, 27, 0.9);
            border: 1px solid #f97316;
            border-radius: 14px;
            color: #fff;
            font-size: 15px;
        }
        .ai-input:focus { outline: none; }
        .ai-send {
            background: linear-gradient(135deg, #f97316, #ea580c);
            color: white;
            border: none;
            padding: 0 22px;
            border-radius: 14px;
            font-weight: 700;
            cursor: pointer;
        }
    </style>
</head>
<body>
    {{ header|safe }}

    <div class="ai-container">
        <div class="ai-header">
            <div class="ai-avatar">🐻</div>
            <div>
                <h3 style="margin:0; font-size:17px; color:#f97316;">KUKULİ 🐻</h3>
                <span style="font-size:12px; color:#4ade80; font-weight:600;">● Saytın Rəsmi Süni İntellekti</span>
            </div>
        </div>

        <div class="ai-messages" id="aiMessages">
            <div class="ai-bubble bot-msg">
                Salam, <b>@{{ current_user }}</b>! 👋 Mən <b>KUKULİ 🐻</b>.<br>
                WİN_WİD saytının təhlükəsizlik sistemi, bal qazanmaq, canlı yayım, market və bütün bölmələri haqqında mənə istənilən sualı yaza bilərsən.
            </div>
        </div>

        <div class="quick-questions">
            <button class="quick-btn" onclick="askQuick('Təhlükəsizlik və polis sistemi necə işləyir?')">🛡️ Təhlükəsizlik</button>
            <button class="quick-btn" onclick="askQuick('Necə bal (WON) qazana bilərəm?')">💰 Bal Qazanmaq</button>
            <button class="quick-btn" onclick="askQuick('Canlı yayım necə açılır?')">🔴 Canlı Yayım</button>
            <button class="quick-btn" onclick="askQuick('Marketdə nələr var?')">🛍️ Market</button>
            <button class="quick-btn" onclick="askQuick('Shorts video necə yüklənir?')">📹 Vidyolar</button>
        </div>

        <form class="ai-form" onsubmit="sendToAI(event)">
            <input type="text" id="aiInput" class="ai-input" placeholder="KUKULİ 🐻-yə sualını yaz..." required autocomplete="off">
            <button type="submit" class="ai-send">Soruş</button>
        </form>
    </div>

    <script>
        function askQuick(text) {
            document.getElementById('aiInput').value = text;
            sendToAI(new Event('submit'));
        }

        function sendToAI(e) {
            e.preventDefault();
            let input = document.getElementById('aiInput');
            let msg = input.value.trim();
            if (!msg) return;

            let box = document.getElementById('aiMessages');
            box.innerHTML += `<div class="ai-bubble user-msg">${msg}</div>`;
            input.value = '';
            box.scrollTop = box.scrollHeight;

            fetch('/kukuli/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: msg })
            })
            .then(res => res.json())
            .then(data => {
                box.innerHTML += `<div class="ai-bubble bot-msg">${data.answer}</div>`;
                box.scrollTop = box.scrollHeight;
            });
        }
    </script>
</body>
</html>
'''

@app.route('/kukuli')
def kukuli():
    if 'user' not in session:
        return redirect(url_for('index'))
    current_user = session['user']
    has_unread_notifs = False
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM notifications WHERE username = %s AND is_read = 0", (current_user,))
        has_unread_notifs = cursor.fetchone() is not None
        cursor.close()
        conn.close()
    except Exception:
        pass
    
    header_html = get_header_template(has_unread_notifs)
    
    html = f'''
    <!DOCTYPE html>
    <html lang="az">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WİN_WİD - KUKULİ 🐻</title>
        {COMMON_STYLE}
        <style>
            .ai-container {{
                background: rgba(24, 24, 27, 0.92);
                flex: 1;
                border: 1px solid rgba(249, 115, 22, 0.4);
                border-radius: 22px;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }}
            .ai-header {{
                background: rgba(9, 9, 11, 0.9);
                padding: 15px 20px;
                display: flex;
                align-items: center;
                gap: 12px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }}
            .ai-messages {{
                flex: 1;
                padding: 18px;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }}
            .ai-bubble {{
                padding: 12px 16px;
                border-radius: 16px;
                max-width: 82%;
                font-size: 15px;
                line-height: 1.5;
                color: #f8fafc;
            }}
            .bot-msg {{
                background: rgba(39, 39, 42, 0.9);
                border: 1px solid rgba(249, 115, 22, 0.35);
                align-self: flex-start;
            }}
            .user-msg {{
                background: #f97316;
                color: #fff;
                align-self: flex-end;
            }}
            .quick-questions {{
                display: flex;
                gap: 8px;
                padding: 10px 14px;
                overflow-x: auto;
                background: rgba(9, 9, 11, 0.6);
            }}
            .quick-btn {{
                background: rgba(249, 115, 22, 0.2);
                border: 1px solid #f97316;
                color: #fb923c;
                padding: 6px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 700;
                white-space: nowrap;
                cursor: pointer;
            }}
            .ai-form {{
                display: flex;
                padding: 12px;
                background: rgba(9, 9, 11, 0.9);
                gap: 10px;
            }}
            .ai-input {{
                flex: 1;
                height: 46px;
                padding: 0 15px;
                background: #18181b;
                border: 1px solid #f97316;
                border-radius: 12px;
                color: #fff;
                font-size: 15px;
            }}
            .ai-send {{
                background: #f97316;
                color: white;
                border: none;
                padding: 0 20px;
                border-radius: 12px;
                font-weight: 700;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        {header_html}
        <div class="ai-container">
            <div class="ai-header">
                <span style="font-size:28px;">🐻</span>
                <div>
                    <h3 style="margin:0; font-size:17px; color:#f97316;">KUKULİ 🐻</h3>
                    <span style="font-size:12px; color:#4ade80;">● Aktivdir</span>
                </div>
            </div>

            <div class="ai-messages" id="aiMessages">
                <div class="ai-bubble bot-msg">
                    Salam, <b>@{current_user}</b>! 👋 Mən <b>KUKULİ 🐻</b>.<br>
                    WİN_WİD saytının təhlükəsizlik sistemi, bal qazanmaq, canlı yayım və bütün bölmələri haqqında mənə sual verə bilərsən.
                </div>
            </div>

            <div class="quick-questions">
                <button class="quick-btn" onclick="askQuick('Təhlükəsizlik və polis sistemi necə işləyir?')">🛡️ Təhlükəsizlik</button>
                <button class="quick-btn" onclick="askQuick('Necə bal qazana bilərəm?')">💰 Bal (WON)</button>
                <button class="quick-btn" onclick="askQuick('Canlı yayım necə açılır?')">🔴 Canlı</button>
                <button class="quick-btn" onclick="askQuick('Marketdə nələr var?')">🛍️ Market</button>
            </div>

            <form class="ai-form" onsubmit="sendToAI(event)">
                <input type="text" id="aiInput" class="ai-input" placeholder="KUKULİ 🐻-yə sualını yaz..." required autocomplete="off">
                <button type="submit" class="ai-send">Soruş</button>
            </form>
        </div>

        <script>
            function askQuick(text) {{
                document.getElementById('aiInput').value = text;
                sendToAI(new Event('submit'));
            }}

            function sendToAI(e) {{
                e.preventDefault();
                let input = document.getElementById('aiInput');
                let msg = input.value.trim();
                if (!msg) return;

                let box = document.getElementById('aiMessages');
                box.innerHTML += '<div class="ai-bubble user-msg">' + msg + '</div>';
                input.value = '';
                box.scrollTop = box.scrollHeight;

                fetch('/kukuli/ask', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ question: msg }})
                }})
                .then(res => res.json())
                .then(data => {{
                    box.innerHTML += '<div class="ai-bubble bot-msg">' + data.answer + '</div>';
                    box.scrollTop = box.scrollHeight;
                }});
            }}
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/kukuli/ask', methods=['POST'])
def kukuli_ask():
    if 'user' not in session:
        return jsonify({'answer': 'Zəhmət olmasa əvvəlcə hesaba daxil olun.'})
        
    current_user = session['user']
    data = request.get_json(silent=True) or {}
    q = str(data.get('question', '')).lower().strip()
    
    user_points = 0
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT points FROM users WHERE nickname = %s", (current_user,))
        res = cursor.fetchone()
        user_points = res[0] if res else 0
        cursor.close()
        conn.close()
    except Exception:
        pass

    if any(w in q for w in ['salam', 'necəsən', 'kim', 'nəsən', 'adın', 'kukuli']):
        ans = f"Salam @{current_user}! Mən <b>KUKULİ 🐻</b> — WİN_WİD platformasının süni intellekt köməkçisiyəm."
    elif any(w in q for w in ['təhlükəsizlik', 'polis', 'məhkəmə', 'arxiv', 'blok', 'qayda', 'haker']):
        ans = "🛡️ <b>Təhlükəsizlik Sistemi:</b> Saytda polis nəzarəti var. Qayda pozanların mesajları silinib <i>Arxiv Otağına</i> düşür, özləri 24 saat bloklanır və işləri <i>Məhkəmə Bölməsinə</i> göndərilir. Yekun qərarı <b>WİN_WİD</b> verir."
    elif any(w in q for w in ['bal', 'won', 'pul', 'oyun', 'wow', 'sual']):
        ans = f"💰 <b>Bal Sistemi (Balansın: {user_points} Bal):</b> Qeydiyyatda 20 bal verilir. Oyunlar bölməsindəki <i>WOW</i> və <i>Sual-Cavab</i> oyunlarında hər düzgün cavaba <b>+5 Bal</b>, canlı yayımda isə hər 50 bəyəniyə <b>+10 Bal</b> qazanırsan."
    elif any(w in q for w in ['canlı', 'yayım', 'kamera']):
        ans = "🔴 <b>Canlı Yayım:</b> Canlı açmaq üçün ən azı <b>60 Bal</b> lazımdır. Yayım zamanı kameranı çevirə, hədiyyə qəbul edə və bəyənilərdən bal qazana bilərsən."
    elif any(w in q for w in ['market', 'mağaza', 'rəng', 'nik', 'effekt', 'hədiyyə']):
        ans = "🛍️ <b>Market:</b> Giriş effekti (400-500 bal), Rəngli nik (25 bal), Rəngli mesaj (25 bal) ala və digər istifadəçilərə 10 bala hədiyyə göndərə bilərsən."
    else:
        ans = "Mən <b>KUKULİ 🐻</b>! Sənə <b>Təhlükəsizlik/Polis</b>, <b>Bal (WON) qazanmaq</b>, <b>Canlı yayım</b> və <b>Market</b> haqqında məlumat verə bilərəm. Bunlardan birini soruş!"

    return jsonify({'answer': ans})
