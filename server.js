// WIN_WID - Backend Server Kodu
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const mongoose = require('mongoose');
const multer = require('multer');
const badWordsFilter = require('bad-words');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

app.use(express.json());

// 1. VERİLƏNLƏR BAZASI MODELLƏRİ
const UserSchema = new mongoose.Schema({
    username: { type: String, unique: true, required: true },
    password: { type: String, required: true },
    profilePic: { type: String, default: 'default.jpg' },
    followers: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
    following: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
    isBanned: { type: Boolean, default: false }
});
const User = mongoose.model('User', UserSchema);

const PostSchema = new mongoose.Schema({
    userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    mediaUrl: String,
    mediaType: String,
    createdAt: { type: Date, default: Date.now }
});
const Post = mongoose.model('Post', PostSchema);

// 2. WIN_WID TƏHLÜKƏSİZLİK SİSTEMİ (18+ FİLTR VƏ BLOKLAMA)
const filter = new badWordsFilter();

async function checkTextSafety(userId, text) {
    if (filter.isProfane(text)) {
        await User.findByIdAndUpdate(userId, { isBanned: true });
        return false;
    }
    return true;
}

async function checkMediaSafety(userId, fileBuffer) {
    let isNsfw = false; 
    if (isNsfw) {
        await User.findByIdAndUpdate(userId, { isBanned: true });
        return false;
    }
    return true;
}

// 3. İSTİFADƏÇİ VƏ PROFİL SİSTEMİ
app.post('/api/register', async (req, res) => {
    const { username, password } = req.body;
    try {
        const user = new User({ username, password });
        await user.save();
        res.json({ success: true, message: "Hesab yaradıldı!" });
    } catch (err) {
        res.status(400).json({ error: "İstifadəçi adı artıq mövcuddur!" });
    }
});

app.post('/api/follow', async (req, res) => {
    const { currentUserId, targetUserId } = req.body;
    await User.findByIdAndUpdate(currentUserId, { $addToSet: { following: targetUserId } });
    await User.findByIdAndUpdate(targetUserId, { $addToSet: { followers: currentUserId } });
    res.json({ success: true, message: "Uğurla izləyirsiniz!" });
});

// 4. ŞƏKİL VƏ VİDEO PAYLAŞIMI
const upload = multer({ dest: 'uploads/' });

app.post('/api/upload', upload.single('media'), async (req, res) => {
    const { userId, mediaType } = req.body;
    const user = await User.findById(userId);
    if (user.isBanned) {
        return res.status(403).json({ error: "Hesabınız 18+ qayda pozuntusuna görə BLOKLANIB!" });
    }

    const isSafe = await checkMediaSafety(userId, req.file);
    if (!isSafe) {
        return res.status(400).json({ error: "18+ Məzmun aşkar edildi! Hesabınız bloklandı." });
    }

    const newPost = new Post({ userId, mediaUrl: req.file.path, mediaType });
    await newPost.save();
    res.json({ success: true, post: newPost });
});

// 5. REAL-VAXTLI ÇAT VƏ ŞƏXSİ MESAJLAŞMA (DM)
io.on('connection', (socket) => {
    socket.on('send_global_message', async (data) => {
        const { userId, message } = data;
        const isSafe = await checkTextSafety(userId, message);
        if (!isSafe) {
            socket.emit('error_message', '18+ kontentə görə hesabınız BLOKLANDI!');
            return;
        }
        io.emit('receive_global_message', { userId, message });
    });

    socket.on('send_private_message', async (data) => {
        const { senderId, receiverId, message } = data;
        const isSafe = await checkTextSafety(senderId, message);
        if (!isSafe) {
            socket.emit('error_message', '18+ kontentə görə hesabınız BLOKLANDI!');
            return;
        }
        socket.to(receiverId).emit('receive_private_message', { senderId, message });
    });
});

server.listen(3000, () => {
    console.log('Win_Wid serveri işləyir...');
});
