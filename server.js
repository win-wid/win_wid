import os
from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'win_wid_secret_key_2026'
socketio = SocketIO(app)

# Sadə yaddaş bazası (Dataclasses yerinə siyahılar)
users = {}          # {username: {"password": pass, "balance": 100, "color": "black", "avatar": "default.png", "blocked": False}}
messages = []       # [{"id": id, "user": user, "text": text, "color": "black"}]
photos = []         # [{"id": id, "user": user, "url": url, "likes": [], "comments": []}]
videos = []         # [{"id": id, "user": user, "url": url, "likes": [], "comments": []}]
private_chats = {}  # {(u1, u2): [messages]}

BAD_WORDS = ['18+', 'porno', 'seks', 'nsfw'] # Qadağan olunmuş sözlər sistemi

def check_content(text):
    for word in BAD_WORDS:
        if word in text.lower():
            return True
    return False

# --- HTML ŞABLONLARI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { font-family: Arial, sans-serif; background: #f0f2f5; margin: 0; padding: 0; }
        header { background: #2c3e50; color: white; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; }
        .container { max-width: 900px; margin: 20px auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        .nav-bar { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .nav-bar a { padding: 10px 15px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }
        .nav-bar a:hover { background: #2980b9; }
        input, button, select { padding: 8px; margin: 5px 0; }
        .error { color: red; }
    </style>
</head>
<body>
    <header>WİN_WİD"Ə XOŞ GƏLMİSİZ</header>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        nickname = request.form.get('nickname').strip()
        password = request.form.get('password').strip()
        
        # Məhdudiyyətlər yoxlaması
        if len(nickname) > 7:
            error = "Nik name maksimum 7 hərf olmalıdır!"
        elif len(password) > 4 or not password.isdigit():
            error = "Kod maksimum 4 rəqəm olmalıdır!"
        elif nickname in users:
            if users[nickname]['blocked']:
                error = "Bu hesab bloklanıb!"
            else:
                error = "Bu nik name artıq istifadə olunub!"
        else:
            users[nickname] = {
                "password": password, 
                "balance": 100, 
                "color": "black", 
                "avatar": "https://i.imgur.com/6VBx3io.png",
                "blocked": False,
                "status": "Aktiv"
            }
            session['username'] = nickname
            return redirect(url_for('dashboard'))
            
    return render_template_string(HTML_TEMPLATE + """
    {% block content %}
    <h2>Qeydiyyat və Giriş</h2>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    <form method="POST">
        <label>Nik name (Max 7 hərf):</label><br>
        <input type="text" name="nickname" maxlength="7" required><br>
        <label>Kod (Max 4 rəqəm):</label><br>
        <input type="password" name="password" maxlength="4" required><br>
        <button type="submit">Daxil Ol</button>
    </form>
    {% endblock %}
    """, error=error)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = session['username']
    return render_template_string(HTML_TEMPLATE + f"""
    {% block content %}
    <h3>Xoş gəldin, {user}! (Balans: {users[user]['balance']} Bal)</h3>
    <div class="nav-bar">
        <a href="/chat">Çat</a>
        <a href="/photos">Şəkil</a>
        <a href="/videos">Vidos</a>
        <a href="/magazin">Maqazin</a>
        <a href="/games">Oyun</a>
        <a href="/profile">Profil</a>
        <a href="/users_list">İstifadəçilər</a>
    </div>
    <p>Üst menyudan istədiyiniz bölməni seçin.</p>
    {% endblock %}
    """)

# --- 4. ÇAT BÖLMƏSİ ---
@app.route('/chat')
def chat():
    if 'username' not in session: return redirect(url_for('login'))
    return render_template_string(HTML_TEMPLATE + """
    {% block content %}
    <a href="/dashboard">← Geri</a>
    <h2>Ümumi Çat</h2>
    <div id="chat-box" style="height: 300px; border: 1px solid #ccc; overflow-y: scroll; padding: 10px; margin-bottom: 10px;"></div>
    <input type="text" id="message-input" placeholder="Mesaj yazın..." style="width: 75%;">
    <button onclick="sendMessage()">Göndər</button>

    <script>
        var socket = io();
        var currentUser = "{{ session['username'] }}";

        socket.on('update_chat', function(msgs) {
            let box = document.getElementById('chat-box');
            box.innerHTML = '';
            msgs.forEach(m => {
                let editDeleteHTML = '';
                if(m.user === currentUser) {
                    editDeleteHTML = ` <button onclick="deleteMsg(${m.id})">Sil</button> <button onclick="editMsg(${m.id})">Redaktə</button>`;
                }
                box.innerHTML += `<div style="color: ${m.color}"><b>${m.user}</b>: <span id="msg-${m.id}">${m.text}</span> ${editDeleteHTML}</div>`;
            });
            box.scrollTop = box.scrollHeight;
        });

        function sendMessage() {
            let text = document.getElementById('message-input').value;
            if(text.trim() !== '') {
                socket.emit('send_message', {user: currentUser, text: text});
                document.getElementById('message-input').value = '';
            }
        }

        function deleteMsg(id) { socket.emit('delete_message', {id: id, user: currentUser}); }
        function editMsg(id) {
            let newText = prompt("Yeni mesajı daxil edin:");
            if(newText) { socket.emit('edit_message', {id: id, user: currentUser, text: newText}); }
        }
    </script>
    {% endblock %}
    """)

@socketio.on('send_message')
def handle_message(data):
    if check_content(data['text']):
        users[data['user']]['blocked'] = True
        return
    msg_id = len(messages) + 1
    user_color = users[data['user']]['color']
    messages.append({"id": msg_id, "user": data['user'], "text": data['text'], "color": user_color})
    emit('update_chat', messages, broadcast=True)

@socketio.on('delete_message')
def delete_message(data):
    global messages
    messages = [m for m in messages if not (m['id'] == data['id'] and m['user'] == data['user'])]
    emit('update_chat', messages, broadcast=True)

@socketio.on('edit_message')
def edit_message(data):
    if check_content(data['text']): return
    for m in messages:
        if m['id'] == data['id'] and m['user'] == data['user']:
            m['text'] = data['text']
    emit('update_chat', messages, broadcast=True)

# --- 5 & 6. ŞƏKİL VƏ VİDEO BÖLMƏLƏRİ ---
@app.route('/photos', methods=['GET', 'POST'])
def photos_page():
    if 'username' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        url = request.form.get('url')
        if check_content(url):
            users[session['username']]['blocked'] = True
            return redirect(url_for('login'))
        photos.append({"id": len(photos)+1, "user": session['username'], "url": url, "likes": 0, "comments": []})
    return render_template_string(HTML_TEMPLATE + f"""
    {% block content %}
    <a href="/dashboard">← Geri</a>
    <h2>Şəkil Paylaşım Paneli</h2>
    <form method="POST">
        <input type="text" name="url" placeholder="Şəkil Linki (URL) daxil edin" style="width: 70%;" required>
        <button type="submit">Paylaş</button>
    </form>
    <hr>
    <h3>Paylaşılan Şəkillər:</h3>
    {{% for p in photos %}}
        <div style="border:1px solid #ddd; padding:10px; margin-bottom:10px;">
            <p><b>{p.user}</b> tərəfindən</p>
            <img src="{{p.url}}" width="250"><br>
            <a href="/like_photo/{{p.id}}">❤️ Bəyən ({p.likes})</a>
        </div>
    {{% endfor %}}
    {% endblock %}
    """, photos=photos)

@app.route('/like_photo/<int:pid>')
def like_photo(pid):
    for p in photos:
        if p['id'] == pid:
            p['likes'] += 1
    return redirect(url_for('photos_page'))

@app.route('/videos', methods=['GET', 'POST'])
def videos_page():
    if 'username' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        url = request.form.get('url')
        videos.append({"id": len(videos)+1, "user": session['username'], "url": url, "likes": 0})
    return render_template_string(HTML_TEMPLATE + f"""
    {% block content %}
    <a href="/dashboard">← Geri</a>
    <h2>Video Paylaşım Paneli</h2>
    <form method="POST">
        <input type="text" name="url" placeholder="Video Linki daxil edin" style="width: 70%;" required>
        <button type="submit">Paylaş</button>
    </form>
    <hr>
    <h3>Paylaşılan Videolar:</h3>
    {{% for v in videos %}}
        <div style="border:1px solid #ddd; padding:10px; margin-bottom:10px;">
            <p><b>{v.user}</b></p>
            <a href="{{v.url}}" target="_blank">Videonu İzlə (Link)</a>
        </div>
    {{% endfor %}}
    {% endblock %}
    """, videos=videos)

# --- 7. MAGAZİN BÖLMƏSİ ---
@app.route('/magazin')
def magazin():
    if 'username' not in session: return redirect(url_for('login'))
    return render_template_string(HTML_TEMPLATE + """
    {% block content %}
    <a href="/dashboard">← Geri</a>
    <h2>Maqazin (30 Bal)</h2>
    <h3>A) Rəngli Nik (Sarı, Qırmızı, Göy, Bənövşəyi, Yaşıl) - 30 Bal</h3>
    <a href="/buy/color/yellow"><button>Sarı Al</button></a>
    <a href="/buy/color/red"><button>Qırmızı Al</button></a>
    
    <h3>B) Hədiyyələr (😇, 🤣, 🤩, 🚀, 💰 və s.)</h3>
    <p>İstifadəçilərə profilindən hədiyyə göndərə bilərsiniz.</p>
    {% endblock %}
    """)

@app.route('/buy/color/<color>')
def buy_color(color):
    user = session['username']
    if users[user]['balance'] >= 30:
        users[user]['balance'] -= 30
        users[user]['color'] = color
    return redirect(url_for('magazin'))

# --- 8. OYUN BÖLMƏSİ ---
@app.route('/games')
def games():
    if 'username' not in session: return redirect(url_for('login'))
    return render_template_string(HTML_TEMPLATE + """
    {% block content %}
    <a href="/dashboard">← Geri</a>
    <h2>Oyunlar</h2>
    <ul>
        <li><a href="/game/wow">WOW Oyunu (Söz Tap və 3 Bal Qazan)</a></li>
        <li><a href="/game/trivia">Sual-Cavab (5 Bal Qazan)</a></li>
    </ul>
    {% endblock %}
    """)

@app.route('/game/wow', methods=['GET', 'POST'])
def game_wow():
    msg = ""
    if request.method == 'POST':
        ans = request.form.get('ans').strip().lower()
        if ans == "python": # Nümunə söz
            users[session['username']]['balance'] += 3
            msg = "Təbriklər! Düzgün tapdınız (+3 Bal)"
        else:
            msg = "Səhvdir, yenidən cəhd edin."
    return render_template_string(HTML_TEMPLATE + f"""
    {% block content %}
    <a href="/games">← Oyunlara Geri Qayıt</a>
    <h2>WOW Söz Oyunu</h2>
    <p>Tapmaca: P _ T H _ N (Hərf əskikliyini tamamlayın)</p>
    <p style="color: green;">{{msg}}</p>
    <form method="POST">
        <input type="text" name="ans" required placeholder="Cavabınızı yazın">
        <button type="submit">Yoxla</button>
    </form>
    {% endblock %}
    """, msg=msg)

@app.route('/game/trivia', methods=['GET', 'POST'])
def game_trivia():
    msg = ""
    if request.method == 'POST':
        ans = request.form.get('ans').strip().lower()
        if ans == "baki" or ans == "bakı":
            users[session['username']]['balance'] += 5
            msg = "Düzgündür! (+5 Bal)"
        else:
            msg = "Səhvdir!"
    return render_template_string(HTML_TEMPLATE + f"""
    {% block content %}
    <a href="/games">← Oyunlara Geri Qayıt</a>
    <h2>Sual-Cavab Oyunu (İpucu: Paytaxt şəhər)</h2>
    <p>Sual: Azərbaycanın paytaxtı haradır?</p>
    <p style="color: green;">{{msg}}</p>
    <form method="POST">
        <input type="text" name="ans" required>
        <button type="submit">Cavabla</button>
    </form>
    {% endblock %}
    """, msg=msg)

# --- 9 & 11. PROFİL VƏ İSTİFADƏÇİLƏR BÖLMƏSİ ---
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session: return redirect(url_for('login'))
    user = session['username']
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'delete':
            del users[user]
            session.pop('username', None)
            return redirect(url_for('login'))
        elif action == 'logout':
            session.pop('username', None)
            return redirect(url_for('login'))
    return render_template_string(HTML_TEMPLATE + f"""
    {% block content %}
    <a href="/dashboard">← Geri</a>
    <h2>Profilim: {user}</h2>
    <p>Balans: {users[user]['balance']} Bal</p>
    <form method="POST">
        <button name="action" value="logout">Hesabdan Çıx</button>
        <button name="action" value="delete" style="background:red; color:white;">Profili Sil</button>
    </form>
    {% endblock %}
    """)

@app.route('/users_list')
def users_list():
    if 'username' not in session: return redirect(url_for('login'))
    return render_template_string(HTML_TEMPLATE + f"""
    {% block content %}
    <a href="/dashboard">← Geri</a>
    <h2>Sayıtdakı İstifadəçilər</h2>
    <ul>
        {{% for uname, udata in users.items() %}}
            {% if not udata.blocked %}
                <li>
                    <img src="{{udata.avatar}}" width="30" style="border-radius:50%"> 
                    <a href="/private_chat/{{uname}}">{{uname}}</a> - <span style="color:green;">● Aktİv</span>
                </li>
            {% endif %}
        {{% endfor %}}
    </ul>
    {% endblock %}
    """)

# --- 10. ŞƏXSİ SMS PANELİ ---
@app.route('/private_chat/<target_user>', methods=['GET', 'POST'])
def private_chat(target_user):
    if 'username' not in session: return redirect(url_for('login'))
    current = session['username']
    chat_key = tuple(sorted([current, target_user]))
    
    if chat_key not in private_chats:
        private_chats[chat_key] = []
        
    if request.method == 'POST':
        text = request.form.get('text')
        if check_content(text):
            users[current]['blocked'] = True
            return redirect(url_for('login'))
        private_chats[chat_key].append(f"{current}: {text}")
        
    return render_template_string(HTML_TEMPLATE + f"""
    {% block content %}
    <a href="/users_list">← İstifadəçilərə Qayıt</a>
    <h2>Şəxsi Söhbət: {target_user}</h2>
    <div style="height: 250px; border:1px solid #ccc; overflow-y:scroll; padding:10px;">
        {{% for m in chat_messages %}}
            <p>{{m}}</p>
        {{% endfor %}}
    </div>
    <form method="POST">
        <input type="text" name="text" placeholder="Şəxsi mesaj yazın..." style="width:70%;" required>
        <button type="submit">Göndər</button>
    </form>
    {% endblock %}
    """, chat_messages=private_chats[chat_key])

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
