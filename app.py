<!DOCTYPE html>
<html lang="az">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WİN_WİD</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            background-color: #0f172a;
            color: #ffffff;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }

        .container {
            width: 100%;
            max-width: 450px;
            background-color: #1e293b;
            border-radius: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: 90vh;
        }

        /* AUTH SCREEN */
        #auth-screen {
            padding: 40px 30px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100%;
            text-align: center;
        }

        #auth-screen h1 {
            font-size: 24px;
            margin-bottom: 30px;
            color: #38bdf8;
            letter-spacing: 1px;
        }

        .input-group {
            width: 100%;
            margin-bottom: 20px;
            text-align: left;
        }

        .input-group label {
            display: block;
            font-size: 14px;
            margin-bottom: 8px;
            color: #94a3b8;
        }

        .input-group input {
            width: 100%;
            padding: 12px 15px;
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 10px;
            color: #fff;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }

        .input-group input:focus {
            border-color: #38bdf8;
        }

        .btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #0ea5e9, #2563eb);
            border: none;
            border-radius: 10px;
            color: white;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: opacity 0.3s;
            margin-top: 10px;
        }

        .btn:hover {
            opacity: 0.9;
        }

        .error-msg {
            color: #f43f5e;
            font-size: 13px;
            margin-top: 10px;
            min-height: 20px;
        }

        /* MAIN APP */
        #main-app {
            display: none;
            flex-direction: column;
            height: 100%;
        }

        /* NAVIGATION BAR (Şəkildəki dizayn) */
        .nav-bar {
            background-color: #111827;
            padding: 12px 10px;
            display: flex;
            justify-content: space-around;
            align-items: center;
            border-bottom: 1px solid #334155;
            overflow-x: auto;
            white-space: nowrap;
        }

        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            cursor: pointer;
            padding: 8px 10px;
            border-radius: 12px;
            transition: background 0.3s, color 0.3s;
            color: #94a3b8;
            font-size: 12px;
            text-decoration: none;
        }

        .nav-item span.icon {
            font-size: 20px;
            margin-bottom: 4px;
        }

        .nav-item.active {
            background-color: #0ea5e9;
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4);
        }

        .nav-item:hover:not(.active) {
            color: #ffffff;
            background-color: #1f2937;
        }

        /* CONTENT PAGES */
        .content-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background-color: #0f172a;
        }

        .page {
            display: none;
            height: 100%;
            flex-direction: column;
        }

        .page.active {
            display: flex;
        }

        /* CHAT PAGE STYLES */
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 15px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding-right: 5px;
        }

        .message-card {
            background-color: #1e293b;
            padding: 10px 14px;
            border-radius: 10px;
            max-width: 80%;
            word-break: break-word;
        }

        .message-card .msg-user {
            font-size: 11px;
            color: #38bdf8;
            margin-bottom: 3px;
            font-weight: bold;
        }

        .message-card .msg-text {
            font-size: 14px;
            color: #f8fafc;
        }

        .chat-input-area {
            display: flex;
            gap: 10px;
        }

        .chat-input-area input {
            flex: 1;
            padding: 10px 15px;
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            color: white;
            outline: none;
        }

        .chat-input-area button {
            padding: 0 20px;
            background-color: #0ea5e9;
            border: none;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }

        .placeholder-content {
            text-align: center;
            color: #64748b;
            margin-top: 50px;
            font-size: 16px;
        }
    </style>
</head>
<body>

<div class="container">
    
    <!-- QEYDİYAT HİSSƏSİ -->
    <div id="auth-screen">
        <h1>WİN_WİD'Ə XOŞ GƏLMİSİZ</h1>
        <div class="input-group">
            <label>Nik Name (Maksimum 7 hərf)</label>
            <input type="text" id="nickname" maxlength="7" placeholder="Nik yazın...">
        </div>
        <div class="input-group">
            <label>Kod (Maksimum 4 rəqəm)</label>
            <input type="password" id="password" maxlength="4" placeholder="Rəqəm yazın...">
        </div>
        <button class="btn" onclick="registerUser()">Daxil Ol</button>
        <div class="error-msg" id="error-msg"></div>
    </div>

    <!-- ƏSAS PANEL -->
    <div id="main-app">
        <!-- Şəkildəki ardıcıllığa uyğun Naviqasiya Paneli -->
        <div class="nav-bar">
            <div class="nav-item active" onclick="switchPage('chat', this)">
                <span class="icon">💬</span>
                Çat
            </div>
            <div class="nav-item" onclick="switchPage('photos', this)">
                <span class="icon">📸</span>
                Şəkillər
            </div>
            <div class="nav-item" onclick="switchPage('videos', this)">
                <span class="icon">📹</span>
                Videolar
            </div>
            <div class="nav-item" onclick="switchPage('games', this)">
                <span class="icon">🎮</span>
                Oyunlar
            </div>
            <div class="nav-item" onclick="switchPage('shop', this)">
                <span class="icon">🛍️</span>
                Mağaza
            </div>
            <div class="nav-item" onclick="switchPage('profile', this)">
                <span class="icon">👤</span>
                Profil
            </div>
        </div>

        <!-- Səhifələrin Məzmunu -->
        <div class="content-container">
            
            <!-- ÇAT SƏHİFƏSİ -->
            <div id="chat-page" class="page active">
                <div class="chat-messages" id="chat-messages">
                    <!-- Mesajlar bura gələcək -->
                </div>
                <div class="chat-input-area">
                    <input type="text" id="msg-input" placeholder="Mesaj yazın...">
                    <button onclick="sendMessage()">Göndər</button>
                </div>
            </div>

            <!-- ŞƏKİLLƏR SƏHİFƏSİ -->
            <div id="photos-page" class="page">
                <div class="placeholder-content">Şəkillər bölməsi tezliklə aktivləşəcək</div>
            </div>

            <!-- VİDEOLAR SƏHİFƏSİ -->
            <div id="videos-page" class="page">
                <div class="placeholder-content">Videolar bölməsi tezliklə aktivləşəcək</div>
            </div>

            <!-- OYUNLAR SƏHİFƏSİ -->
            <div id="games-page" class="page">
                <div class="placeholder-content">Oyunlar bölməsi tezliklə aktivləşəcək</div>
            </div>

            <!-- MAĞAZA SƏHİFƏSİ -->
            <div id="shop-page" class="page">
                <div class="placeholder-content">Mağaza bölməsi tezliklə aktivləşəcək</div>
            </div>

            <!-- PROFİL SƏHİFƏSİ -->
            <div id="profile-page" class="page">
                <div style="text-align: center; margin-top: 30px;">
                    <h3 id="profile-name" style="color: #38bdf8; font-size: 22px; margin-bottom: 10px;"></h3>
                    <p style="color: #94a3b8;">Status: Aktiv istifadəçi</p>
                    <button class="btn" style="margin-top: 30px; background-color: #f43f5e;" onclick="logout()">Çıxış Et</button>
                </div>
            </div>

        </div>
    </div>

</div>

<script>
    // İstifadəçi qeydiyyatı və yoxlanılması
    function registerUser() {
        const nickname = document.getElementById('nickname').value.trim();
        const password = document.getElementById('password').value.trim();
        const errorMsg = document.getElementById('error-msg');

        if (!nickname || !password) {
            errorMsg.textContent = "Zəhmət olmasa bütün xanaları doldurun!";
            return;
        }

        if (nickname.length > 7) {
            errorMsg.textContent = "Nik name maksimum 7 hərf ola bilər!";
            return;
        }

        if (password.length > 4 || isNaN(password)) {
            errorMsg.textContent = "Kod maksimum 4 rəqəm olmalıdır!";
            return;
        }

        // Mövcud istifadəçiləri yoxlayaq (localStorage vasitəsilə)
        let users = JSON.parse(localStorage.getItem('win_wid_users')) || [];
        
        let existingUser = users.find(u => u.nickname.toLowerCase() === nickname.toLowerCase());
        
        if (existingUser) {
            // Əgər istifadəçi əvvəlcədən varsa, kodu yoxlayıb daxil ola bilər və ya fərqli ad seçməlidir
            if (existingUser.password === password) {
                loginSuccess(nickname);
            } else {
                errorMsg.textContent = "Bu nik artıq istifadə olunur və ya şifrə yanlışdır!";
            }
            return;
        }

        // Yeni istifadəçi əlavə edirik
        users.push({ nickname, password });
        localStorage.setItem('win_wid_users', JSON.stringify(users));
        
        loginSuccess(nickname);
    }

    function loginSuccess(nickname) {
        localStorage.setItem('win_wid_current_user', nickname);
        document.getElementById('auth-screen').style.display = 'none';
        document.getElementById('main-app').style.display = 'flex';
        document.getElementById('profile-name').textContent = "@" + nickname;
        loadMessages();
    }

    // Səhifələr arası keçid
    function switchPage(pageId, element) {
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

        document.getElementById(pageId + '-page').classList.add('active');
        element.classList.add('active');
    }

    // Çat funksionallığı
    function sendMessage() {
        const input = document.getElementById('msg-input');
        const text = input.value.trim();
        const currentUser = localStorage.getItem('win_wid_current_user');

        if (!text) return;

        let messages = JSON.parse(localStorage.getItem('win_wid_messages')) || [];
        messages.push({ user: currentUser, text: text });
        localStorage.setItem('win_wid_messages', JSON.stringify(messages));

        input.value = '';
        loadMessages();
    }

    function loadMessages() {
        const container = document.getElementById('chat-messages');
        let messages = JSON.parse(localStorage.getItem('win_wid_messages')) || [];
        
        container.innerHTML = '';
        if(messages.length === 0) {
            container.innerHTML = '<div style="color: #64748b; text-align: center; margin-top: 20px;">Hələ ki mesaj yoxdur. İlk mesajı siz yazın!</div>';
            return;
        }

        messages.forEach(msg => {
            const card = document.createElement('div');
            card.className = 'message-card';
            card.innerHTML = `
                <div class="msg-user">@${msg.user}</div>
                <div class="msg-text">${msg.text}</div>
            `;
            container.appendChild(card);
        });
        container.scrollTop = container.scrollHeight;
    }

    function logout() {
        localStorage.removeItem('win_wid_current_user');
        location.reload();
    }

    // Avtomatik olaraq əvvəlki sessiyanı yoxla
    window.onload = function() {
        const currentUser = localStorage.getItem('win_wid_current_user');
        if (currentUser) {
            document.getElementById('auth-screen').style.display = 'none';
            document.getElementById('main-app').style.display = 'flex';
            document.getElementById('profile-name').textContent = "@" + currentUser;
            loadMessages();
        }
    }
</script>

</body>
</html>
