from flask import Flask, render_template_string, request, jsonify
import json
import os

app = Flask(__name__)
DATA_FILE = 'data.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": [], "messages": []}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Sizin istədiyiniz bütün dizayn və funksionallıq birbaşa burada birləşdirilib
HTML_PAGE = """
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WİN_WİD</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: #0f172a; color: #ffffff; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .container { width: 100%; max-width: 450px; background-color: #1e293b; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); overflow: hidden; display: flex; flex-direction: column; height: 90vh; }
        
        #auth-screen { padding: 40px 30px; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; text-align: center; }
        #auth-screen h1 { font-size: 22px; margin-bottom: 30px; color: #38bdf8; letter-spacing: 1px; }
        .input-group { width: 100%; margin-bottom: 20px; text-align: left; }
        .input-group label { display: block; font-size: 14px; margin-bottom: 8px; color: #94a3b8; }
        .input-group input { width: 100%; padding: 12px 15px; background-color: #0f172a; border: 1px solid #334155; border-radius: 10px; color: #fff; font-size: 16px; outline: none; }
        .btn { width: 100%; padding: 12px; background: linear-gradient(135deg, #0ea5e9, #2563eb); border: none; border-radius: 10px; color: white; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 10px; }
        .error-msg { color: #f43f5e; font-size: 13px; margin-top: 10px; min-height: 20px; }

        #main-app { display: none; flex-direction: column; height: 100%; }
        
        /* Şəkildəki naviqasiya dizaynı */
        .nav-bar { background-color: #111827; padding: 12px 10px; display: flex; justify-content: space-around; align-items: center; border-bottom: 1px solid #334155; overflow-x: auto; }
        .nav-item { display: flex; flex-direction: column; align-items: center; cursor: pointer; padding: 8px 10px; border-radius: 12px; color: #94a3b8; font-size: 12px; transition: 0.3s; }
        .nav-item span.icon { font-size: 18px; margin-bottom: 3px; }
        .nav-item.active { background-color: #0ea5e9; color: #ffffff; box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4); }

        .content-container { flex: 1; overflow-y: auto; padding: 20px; background-color: #0f172a; }
        .page { display: none; height: 100%; flex-direction: column; }
        .page.active { display: flex; }

        .chat-messages { flex: 1; overflow-y: auto; margin-bottom: 15px; display: flex; flex-direction: column; gap: 10px; }
        .message-card { background-color: #1e293b; padding: 10px 14px; border-radius: 10px; max-width: 80%; word-break: break-word; border: 1px solid #334155; }
        .msg-user { font-size: 11px; color: #38bdf8; margin-bottom: 3px; font-weight: bold; }
        .msg-text { font-size: 14px; color: #f8fafc; }
        
        .chat-input-area { display: flex; gap: 10px; }
        .chat-input-area input { flex: 1; padding: 10px 15px; background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; color: white; outline: none; }
        .chat-input-area button { padding: 0 20px; background-color: #0ea5e9; border: none; border-radius: 8px; color: white; font-weight: bold; cursor: pointer; }
        .placeholder-content { text-align: center; color: #64748b; margin-top: 50px; font-size: 15px; }
    </style>
</head>
<body>

<div class="container">
    <!-- QEYDİYAT HİSSƏSİ -->
    <div id="auth-screen">
        <h1>WİN_WİD'Ə XOŞ GƏLMİSİZ</h1>
        <div class="input-group">
            <label>Nik Name (Max 7 hərf)</label>
            <input type="text" id="nickname" maxlength="7" placeholder="Nik yazın...">
        </div>
        <div class="input-group">
            <label>Kod (Max 4 rəqəm)</label>
            <input type="password" id="password" maxlength="4" placeholder="Rəqəm yazın...">
        </div>
        <button class="btn" onclick="registerUser()">Daxil Ol</button>
        <div class="error-msg" id="error-msg"></div>
    </div>

    <!-- ƏSAS PANEL -->
    <div id="main-app">
        <div class="nav-bar">
            <div class="nav-item active" onclick="switchPage('chat', this)"><span class="icon">💬</span>Çat</div>
            <div class="nav-item" onclick="switchPage('photos', this)"><span class="icon">📸</span>Şəkillər</div>
            <div class="nav-item" onclick="switchPage('videos', this)"><span class="icon">📹</span>Videolar</div>
            <div class="nav-item" onclick="switchPage('games', this)"><span class="icon">🎮</span>Oyunlar</div>
            <div class="nav-item" onclick="switchPage('shop', this)"><span class="icon">🛍️</span>Mağaza</div>
            <div class="nav-item" onclick="switchPage('profile', this)"><span class="icon">👤</span>Profil</div>
        </div>

        <div class="content-container">
            <div id="chat-page" class="page active">
                <div class="chat-messages" id="chat-messages"></div>
                <div class="chat-input-area">
                    <input type="text" id="msg-input" placeholder="Mesaj yazın...">
                    <button onclick="sendMessage()">Göndər</button>
                </div>
            </div>
            <div id="photos-page" class="page"><div class="placeholder-content">Şəkillər bölməsi</div></div>
            <div id="videos-page" class="page"><div class="placeholder-content">Videolar bölməsi</div></div>
            <div id="games-page" class="page"><div class="placeholder-content">Oyunlar bölməsi</div></div>
            <div id="shop-page" class="page"><div class="placeholder-content">Mağaza bölməsi</div></div>
            <div id="profile-page" class="page">
                <div style="text-align: center; margin-top: 30px;">
                    <h3 id="profile-name" style="color: #38bdf8; font-size: 20px; margin-bottom: 10px;"></h3>
                    <p style="color: #94a3b8; font-size: 14px;">Status: Aktiv</p>
                    <button class="btn" style="margin-top: 30px; background-color: #f43f5e;" onclick="logout()">Çıxış Et</button>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    function registerUser() {
        const nickname = document.getElementById('nickname').value.trim();
        const password = document.getElementById('password').value.trim();
        const errorMsg = document.getElementById('error-msg');

        if (!nickname || !password) { errorMsg.textContent = "Bütün xanaları doldurun!"; return; }
        if (nickname.length > 7) { errorMsg.textContent = "Nik max 7 hərf olmalıdır!"; return; }
        if (password.length > 4 || isNaN(password)) { errorMsg.textContent = "Kod max 4 rəqəm olmalıdır!"; return; }

        fetch('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nickname, password})
        })
        .then(res => res.json())
        .then(data => {
            if(data.status === 'success') {
                loginSuccess(nickname);
            } else {
                errorMsg.textContent = data.message;
            }
        });
    }

    function loginSuccess(nickname) {
        localStorage.setItem('win_wid_current_user', nickname);
        document.getElementById('auth-screen').style.display = 'none';
        document.getElementById('main-app').style.display = 'flex';
        document.getElementById('profile-name').textContent = "@" + nickname;
        loadMessages();
    }

    function switchPage(pageId, element) {
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.getElementById(pageId + '-page').classList.add('active');
        element.classList.add('active');
    }

    function sendMessage() {
        const input = document.getElementById('msg-input');
        const text = input.value.trim();
        const currentUser = localStorage.getItem('win_wid_current_user');
        if (!text) return;

        fetch('/api/messages', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user: currentUser, text: text})
        }).then(() => {
            input.value = '';
            loadMessages();
        });
    }

    function loadMessages() {
        fetch('/api/messages')
        .then(res => res.json())
        .then(messages => {
            const container = document.getElementById('chat-messages');
            container.innerHTML = '';
            if(messages.length === 0) {
                container.innerHTML = '<div style="color: #64748b; text-align: center; margin-top: 20px;">Hələ ki mesaj yoxdur.</div>';
                return;
            }
            messages.forEach(msg => {
                const card = document.createElement('div');
                card.className = 'message-card';
                card.innerHTML = `<div class="msg-user">@${msg.user}</div><div class="msg-text">${msg.text}</div>`;
                container.appendChild(card);
            });
            container.scrollTop = container.scrollHeight;
        });
    }

    function logout() {
        localStorage.removeItem('win_wid_current_user');
        location.reload();
    }

    window.onload = function() {
        const currentUser = localStorage.getItem('win_wid_current_user');
        if (currentUser) {
            document.getElementById('auth-screen').style.display = 'none';
            document.getElementById('main-app').style.display = 'flex';
            document.getElementById('profile-name').textContent = "@" + currentUser;
            loadMessages();
            setInterval(loadMessages, 3000);
        }
    }
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    nickname = data.get('nickname', '').strip()
    password = data.get('password', '').strip()
    db = load_data()
    
    user = next((u for u in db['users'] if u['nickname'].lower() == nickname.lower()), None)
    if user:
        if user['password'] == password:
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Şifrə yanlışdır və ya nik məşğuldur!"}), 400
    
    db['users'].append({"nickname": nickname, "password": password})
    save_data(db)
    return jsonify({"status": "success"})

@app.route('/api/messages', methods=['GET', 'POST'])
def handle_messages():
    db = load_data()
    if request.method == 'POST':
        db['messages'].append(request.json)
        save_data(db)
        return jsonify({"status": "success"})
    return jsonify(db['messages'])

if __name__ == '__main__':
    app.run(debug=True)
