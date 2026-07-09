const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
// --- Global Multiplayer Environment Config ---
const API_BASE = "http://192.168.1.7:3000"; 

let currentRoomCode = ""; 
var remotePlayers = {};
// --- MULTIPLAYER CONNECTION LOGGING ---
// Intercepts direct loads of game.html to trace when secondary browser instances enter the scope
app.get('/game.html', (req, res, next) => {
    const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
    console.log(`\n[MULTIPLAYER CONNECTION] game.html opened by a separate browser window!`);
    console.log(`[IP Address] ${ip}`);
    console.log(`[Timestamp]  ${new Date().toLocaleTimeString()}\n`);
    next(); // Pass control down to handle the file delivery
});

// ROUTE STATIC ROOT PATHS: Forces express to recognize game.html as a direct landing page file context
app.use(express.static(__dirname));

// Custom default point to load game.html automatically on navigating root path URLs
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'game.html'));
});

// Setup structural fallback Local Data SQLite table systems
const db = new sqlite3.Database(path.join(__dirname, 'cybergame.db'));
db.serialize(() => {
    db.run(`
        CREATE TABLE IF NOT EXISTS students (
            student_number TEXT PRIMARY KEY,
            safe_completed INTEGER DEFAULT 0, safe_score INTEGER DEFAULT 0,
            savvy_completed INTEGER DEFAULT 0, savvy_score INTEGER DEFAULT 0,
            social_completed INTEGER DEFAULT 0, social_score INTEGER DEFAULT 0,
            last_active DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `);
});

// Shared in-memory active tracking multiplayer register dictionary
const activePlayers = {};

// Automated Garbage Collector Loop: Erases players who disconnected/closed tab after 5 seconds
setInterval(() => {
    const timeThreshold = Date.now();
    Object.keys(activePlayers).forEach(id => {
        if (timeThreshold - activePlayers[id].lastPing > 5000) {
            console.log(`[MULTIPLAYER LEAVE] Student #${id} timed out or closed the browser room.`);
            delete activePlayers[id];
        }
    });
}, 3000);

// --- TELEMETRY / DATA API CHANNELS ---

app.post('/api/auth', (req, res) => {
    const { studentNumber } = req.body;
    if (!studentNumber) return res.status(400).json({ error: "Identification argument expected." });

    db.get('SELECT * FROM students WHERE student_number = ?', [studentNumber], (err, row) => {
        if (err) return res.status(500).json({ error: err.message });
        if (row) {
            res.json({ authenticated: true, data: row });
        } else {
            db.run('INSERT INTO students (student_number, safe_score) VALUES (?, 0)', [studentNumber], function(err) {
                if (err) return res.status(500).json({ error: err.message });
                res.json({ authenticated: true, data: { student_number: studentNumber, safe_score: 0 } });
            });
        }
    });
});

// --- FIX: Updated join-room endpoint that seeds player properties into the active memory channel ---
app.post('/api/multiplayer/join-room', (req, res) => {
    const { studentNumber, roomCode, roomId } = req.body;
    if (!studentNumber || !roomCode) {
        return res.status(400).json({ error: "Missing identity or room sequence parameters." });
    }
    
    const normalizedRoom = roomCode.toUpperCase();
    const activeRoomId = roomId || 'room1';

    // Seed/register initial structure to prevent out-of-sync initialization flags
    activePlayers[studentNumber] = {
        studentNumber,
        roomCode: normalizedRoom,
        roomId: activeRoomId,
        x: 400, // Safe default initial canvas x-coordinate
        y: 300, // Safe default initial canvas y-coordinate
        angle: 0,
        moving: false,
        animStep: 0,
        lastPing: Date.now()
    };
    
    console.log(`[ROOM MATCH] Student #${studentNumber} has synchronized into Room Instance: [${normalizedRoom}] Screen: ${activeRoomId}`);
    res.json({ success: true, roomCode: normalizedRoom, roomId: activeRoomId });
});
app.post('/api/multiplayer/sync', (req, res) => {
    const { studentNumber, roomCode, roomId, x, y, angle, moving, animStep } = req.body;
    
    if (!studentNumber || !roomCode) {
        return res.status(400).json({ error: "Missing required tracking session keys" });
    }

    const normalizedRoom = roomCode.trim().toUpperCase();
    const activeRoomId = roomId || 'room1';

    // Store tracking data
    activePlayers[studentNumber] = {
        studentNumber,
        roomCode: normalizedRoom,
        roomId: activeRoomId, 
        x, y, angle, moving, animStep,
        lastPing: Date.now()
    };

    // Filter output: Include peers who share BOTH the room code and specific room ID
    const peerPlayers = {};
    Object.keys(activePlayers).forEach(id => {
        if (id !== studentNumber && 
            activePlayers[id].roomCode === normalizedRoom && 
            activePlayers[id].roomId === activeRoomId) {
            peerPlayers[id] = activePlayers[id];
        }
    });

    res.json({ players: peerPlayers });
});
app.post('/api/save-progress', (req, res) => {
    const { studentNumber, module, score, completed } = req.body;
    const sqlUpdate = `UPDATE students SET ${module}_completed = ?, ${module}_score = ?, last_active = CURRENT_TIMESTAMP WHERE student_number = ?`;
    
    db.run(sqlUpdate, [completed ? 1 : 0, score, studentNumber], function(err) {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ success: true });
    });
});

const HOST = '192.168.1.7'; // Listens on all local network interfaces

app.listen(PORT, HOST, () => {
    console.log(`===================================================`);
    console.log(` SERVER RUNNING LOCAL: http://localhost:${PORT}`);
    console.log(` SERVER RUNNING NETWORK: http://192.168.1.7:${PORT}`);
    console.log(`===================================================`);
});