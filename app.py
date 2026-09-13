from flask import Flask, render_template_string, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'win_wid_gizli_kalit'  # Sessiyanı idarə etmək üçün

# Sadə yaddaş (müvəqqəti olaraq siyahıda saxlanılır)
messages = []
users = {}  # {nickname: password}

# Giriş və Qeydiyyat Səhifəsi (Qara fon və mərkəzləşdirilmiş kvadrat panel)
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Giriş</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            background-color: #000000; 
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
            background: #121212; 
            border-radius: 12px; 
            box-shadow: 0 4px 20px rgba(255, 255, 255, 0.1); 
            text-align: center; 
            border: 1px solid #333333; 
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
            border: 1px solid #444444; 
            border-radius: 6px; 
            background: #1e1e1e; 
            color: #ffffff; 
            box-sizing: border-box; 
        }
        input::placeholder { color: #888888; }
        button { 
            width: 100%; 
            padding: 12px; 
            margin: 8px 0; 
            background: #007BFF; 
            color: white; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            font-weight: bold; 
        }
        button:hover { background: #0056b3; }
        .error { color: #ff4d4d; font-size: 14px; margin-bottom: 10px; }
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

# Mesajlaşma Paneli (Qara fon uyumlu)
CHAT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <title>WİN_WİD - Çat Paneli</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #000000; 
            color: #ffffff; 
            display: flex; 
            flex-direction: column; 
            height: 100vh; 
            box-sizing: border-box; 
        }
        .header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            background: #121212; 
            color: white; 
            padding: 15px 20px; 
            border-radius: 8px; 
            border: 1px solid #333333; 
        }
        .chat-box { 
            background: #121212; 
            flex: 1; 
            border: 1px solid #333333; 
            border-radius: 8px; 
            margin-top: 20px; 
            padding: 15px; 
            overflow-y: scroll; 
            color: #ffffff; 
        }
        .message-form { 
            margin-top: 20px; 
            display: flex; 
            gap: 10px; 
        }
        input[type="text"] { 
            flex: 1; 
            padding: 12px; 
            border: 1px solid #444444; 
            border-radius: 6px; 
            background: #1e1e1e; 
            color: #ffffff; 
        }
        button { 
            padding: 12px 20px; 
            background: #28a745; 
            color: white; 
            border: none; 
            border-radius: 6px; 
            cursor: pointer; 
            font-weight: bold; 
        }
        a.logout { 
            color: white; 
            text-decoration: none; 
            background: #dc3545; 
            padding: 8px 15px; 
            border-radius: 6px; 
            font-size: 14px; 
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>WİN_WİD'Ə XOŞ GƏLMİSİZ, {{ user }}!</h2>
        <a href="/logout" class="logout">Çıxış</a>
    </div>

    <div class="chat-box">
        {% for msg in messages %}
            <p>{{ msg }}</p>
        {% endfor %}
    </div>

    <form method="POST" class="message-form">
        <input type="text" name="message" placeholder="Mesajınızı yazın..." autocomplete="off" required>
        <button type="submit">Göndər</button>
    </form>
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
        elif action == 'register':
            if nickname in users:
                error = "Bu nikname artıq istifadədədir!"
            else:
                users[nickname] = password
                session['user'] = nickname
                return redirect(url_for('chat'))
        elif action == 'login':
            if nickname in users and users[nickname] == password:
                session['user'] = nickname
                return redirect(url_for('chat'))
            else:
                error = "Yanlış nikname və ya kod!"
                
    return render_template_string(INDEX_TEMPLATE, error=error)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user' not in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        msg = request.form.get('message').strip()
        if msg:
            full_msg = f"{session['user']}: {msg}"
            messages.append(full_msg)
        return redirect(url_for('chat'))
        
    return render_template_string(CHAT_TEMPLATE, user=session['user'], messages=messages)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
