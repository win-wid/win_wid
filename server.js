import os
from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.secret_key = "win_wid_secret_key_security"
socketio = SocketIO(app)

# Sadə yaddaş bazası (Məlumatların itməməsi üçün real layihədə SQL istifadə olunmalıdır)
users = {}          # {username: {"password": pwd, "profile_pic": url, "blocked": False}}
posts = []          # [{"user": name, "type": "image/video", "url": link, "caption": text}]
messages = []       # [{"sender": u1, "receiver": u2, "text": msg}]
global_chat = []    # [{"user": name, "text": msg}]

# 5. TƏHLÜKƏSİZLİK SİSTEMİ (18+ və Qadağan olunmuş sözlər/məzmunlar)
BANNED_WORDS = ["18+", "porno", "sex", "nude", "erootik", "badword1", "badword2"]

def check_security(text):
    if not text:
        return False
    text_lower = text.lower()
    for word in BANNED_WORDS:
        if word in text_lower:
            return True
    return False

# HTML VƏ FRONTEND HİSSƏSİ (Tək faylda bütün səhifələr)
TEMPLATE = """
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Sosial Şəbəkə</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: auto; background: #1e293b; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h1, h2 { color: #38bdf8; text-align: center; }
        .nav { display: flex; justify-content: space-around; background: #334155; padding: 10px; border-radius: 8px; margin-bottom: 20px; }
        .nav a { color: #f8fafc; text-decoration: none; font-weight: bold; }
        .nav a:hover { color: #38bdf8; }
        input, button, select { padding: 10px; margin: 5px 0; width: 100%; border-radius: 5px; border: 1px solid #475569; background: #0f172a; color: #fff; }
        button { background: #0284c7; border: none; cursor: pointer; font-weight: bold; }
        button:hover { background: #0369a1; }
        .chat-box { height: 250px; background: #0f172a; border: 1px solid #475569; border-radius: 5px; overflow-y: scroll; padding: 10px; margin-bottom: 10px; }
        .post-card { background: #334155; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
        img, video { max-width: 100%; border-radius: 5px; margin-top: 10px; }
        .alert { background: #ef4444; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 10px; }
    </style>
</head>
<body>
<div class="container">
    <h1>WİN_WİD SOSİAL ŞƏBƏKƏSİ</h1>
    
    {% if 'user' not in session %}
        <!-- 2. PROFİL QEYDİYYƏT VƏ GİRİŞ -->
        <h2>Giriş və ya Qeydiyyat</h2>
        {% if error %}<div class="alert">{{ error }}</div>{% endif %}
        <form method="POST" action="/auth">
            <input type="text" name="username" placeholder="İstifadəçi Adı" required>
            <input type="password" name="password" placeholder="Şifrə" required>
            <input type="text" name="profile_pic" placeholder="Profil Şəkli Linki (URL)" required>
            <button type="submit" name="action" value="register">Qeydiyyat ol</button>
            <button type="submit" name="action" value="login">Daxil ol</button>
        </form>
    {% else %}
        <!-- NAVİQASİYA -->
        <div class="nav">
            <a href="/">Ümumi Çat</a>
            <a href="/feed">Paylaşımlar (Şəkil/Video)</a>
            <a href="/dm">Şəxsi Mesajlar (DM)</a>
            <a href="/profile">Profilim</a>
            <a href="/logout">Çıxış</a>
        </div>

        {% if page == 'chat' %}
            <!-- 1. ÜMUMİ ÇAT -->
            <h2>Ümumi Çat</h2>
            <div class="chat-box" id="chat-messages">
                {% for m in chat_history %}
                    <div><b>{{ m.user }}:</b> {{ m.text }}</div>
                {% endfor %}
            </div>
            <input type="text" id="chat-input" placeholder="Mesaj yazın...">
            <button onclick="sendChatMessage()">Göndər</button>

            <script>
                const socket = io();
                const chatBox = document.getElementById('chat-messages');
                
                function sendChatMessage() {
                    const text = document.getElementById('chat-input').value;
                    if(text.trim() !== "") {
                        socket.emit('new_chat_message', {text: text});
                        document.getElementById('chat-input').value = '';
                    }
                }

                socket.on('update_chat', function(data) {
                    if (data.blocked) {
                        alert("Təhlükəsizlik Sistemi: 18+ və ya qadağan olunmuş məzmun aşkarlandı! Hesabınız bloklandı.");
                        window.location.href = "/logout";
                        return;
                    }
                    chatBox.innerHTML += `<div><b>${data.user}:</b> ${data.text}</div>`;
                    chatBox.scrollTop = chatBox.scrollHeight;
                });
            </script>

        {% elif page == 'feed' %}
            <!-- 3 & 4. ŞƏKİL VƏ VİDYO PAYLAŞIMI -->
            <h2>Paylaşım Et</h2>
            <form method="POST" action="/add_post">
                <select name="type">
                    <option value="image">Şəkil Paylaş</option>
                    <option value="video">Video Paylaş</option>
                </select>
                <input type="text" name="url" placeholder="Şəkil və ya Video Linki (URL)" required>
                <input type="text" name="caption" placeholder="Açıqlama (Caption)" required>
                <button type="submit">Paylaş</button>
            </form>

            <h2>Bütün Paylaşımlar</h2>
            {% for post in posts %}
                <div class="post-card">
                    <b>@{{ post.user }}</b>
                    <p>{{ post.caption }}</p>
                    {% if post.type == 'image' %}
                        <img src="{{ post.url }}" alt="Şəkil">
                    {% else %}
                        <video controls src="{{ post.url }}"></video>
                    {% endif %}
                </div>
            {% endfor %}

        {% elif page == 'dm' %}
            <!-- 6. ŞƏXSİ MESAJLAŞMA (DM) -->
            <h2>Şəxsi Mesajlaşma (DM)</h2>
            <form method="GET" action="/dm">
                <select name="receiver" onchange="this.form.submit()">
                    <option value="">Söhbət seçin...</option>
                    {% for u in users %}
                        {% if u != session['user'] %}
                            <option value="{{ u }}" {% if receiver == u %}selected{% endif %}>{{ u }}</option>
                        {% endif %}
                    {% endfor %}
                </select>
            </form>

            {% if receiver %}
                <h3>{{ receiver }} ilə söhbət</h3>
                <div class="chat-box">
                    {% for msg in dm_messages %}
                        {% if (msg.sender == session['user'] and msg.receiver == receiver) or (msg.sender == receiver and msg.receiver == session['user']) %}
                            <div><b>{{ msg.sender }}:</b> {{ msg.text }}</div>
                        {% endif %}
                    {% endfor %}
                </div>
                <form method="POST" action="/send_dm">
                    <input type="hidden" name="receiver" value="{{ receiver }}">
                    <input type="text" name="text" placeholder="Şəxsi mesaj yaz..." required>
                    <button type="submit">Göndər</button>
                </form>
            {% endif %}

        {% elif page == 'profile' %}
            <!-- PROFİL HİSSƏSİ -->
            <h2>Profil Məlumatlarım</h2>
            <div style="text-align: center;">
                <img src="{{ current_user_data.profile_pic }}" style="width: 150px; height: 150px; border-radius: 50%; object-fit: cover;" alt="Profil Şəkli">
                <h3>İstifadəçi Adı: {{ session['user'] }}</h3>
                <p style="color: #22c55e;">Status: Aktiv / Təhlükəsizlikdən Keçib</p>
            </div>
        {% endif %}
    {% endif %}
</div>
</body>
</html>
"""

@app.route('/')
def index():
    if 'user' not in session:
        return render_template_string(TEMPLATE)
    if users[session['user']]['blocked']:
        session.clear()
        return render_template_string(TEMPLATE, error="Hesabınız 18+ təhlükəsizlik qaydalarını pozduğuna görə bloklanıb!")
    return render_template_string(TEMPLATE, page='chat', chat_history=global_chat)

@app.route('/auth', methods=['POST'])
def auth():
    action = request.form.get('action')
    username = request.form.get('username')
    password = request.form.get('password')
    profile_pic = request.form.get('profile_pic', '')

    if action == 'register':
        if username in users:
            return render_template_string(TEMPLATE, error="Bu istifadəçi adı artıq mövcuddur!")
        users[username] = {"password": password, "profile_pic": profile_pic, "blocked": False}
        session['user'] = username
    elif action == 'login':
        if username in users and users[username]['password'] == password:
            if users[username]['blocked']:
                return render_template_string(TEMPLATE, error="Bu hesab bloklanıb!")
            session['user'] = username
        else:
            return render_template_string(TEMPLATE, error="İstifadəçi adı və ya şifrə yanlışdır!")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/feed')
def feed():
    if 'user' not in session: return redirect(url_for('index'))
    return render_template_string(TEMPLATE, page='feed', posts=posts)

@app.route('/add_post', methods=['POST'])
def add_post():
    if 'user' not in session: return redirect(url_for('index'))
    
    post_type = request.form.get('type')
    url = request.form.get('url')
    caption = request.form.get('caption')
    
    # 5. Təhlükəsizlik Yoxlaması (18+ məzmun aşkarlandıqda)
    if check_security(caption) or check_security(url):
        users[session['user']]['blocked'] = True
        session.clear()
        return render_template_string(TEMPLATE, error="Təhlükəsizlik Sistemi: Paylaşımda 18+ məzmun aşkarlandı. Hesabınız bloklandı!")

    posts.insert(0, {"user": session['user'], "type": post_type, "url": url, "caption": caption})
    return redirect(url_for('feed'))

@app.route('/dm')
def dm():
    if 'user' not in session: return redirect(url_for('index'))
    receiver = request.args.get('receiver')
    return render_template_string(TEMPLATE, page='dm', users=users, receiver=receiver, dm_messages=messages)

@app.route('/send_dm', methods=['POST'])
def send_dm():
    if 'user' not in session: return redirect(url_for('index'))
    receiver = request.form.get('receiver')
    text = request.form.get('text')

    # 5. Təhlükəsizlik Yoxlaması (DM-də 18+)
    if check_security(text):
        users[session['user']]['blocked'] = True
        session.clear()
        return render_template_string(TEMPLATE, error="Təhlükəsizlik Sistemi: Şəxsi mesajda 18+ söz aşkarlandı. Hesabınız bloklandı!")

    messages.append({"sender": session['user'], "receiver": receiver, "text": text})
    return redirect(url_for('dm', receiver=receiver))

@app.route('/profile')
def profile():
    if 'user' not in session: return redirect(url_for('index'))
    return render_template_string(TEMPLATE, page='profile', current_user_data=users[session['user']])

# WebSocket vasitəsilə Ümumi Çat İdarəetməsi
@socketio.on('new_chat_message')
def handle_chat_message(data):
    user = session.get('user')
    if not user: return
    
    text = data.get('text')
    
    # 5. Təhlükəsizlik Yoxlaması (Ümumi çatda 18+)
    if check_security(text):
        users[user]['blocked'] = True
        emit('update_chat', {'blocked': True})
        return

    msg_obj = {"user": user, "text": text}
    global_chat.append(msg_obj)
    emit('update_chat', msg_obj, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
