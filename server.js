const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

// --- IN-MEMORY DATABASE STRUCTURES ---
let students = {};      // Replaces 'cybergame.db' table records dynamically
let activePlayers = {}; // Tracks real-time positions for multiplayer room overlays
let serverNeedsReset = false; 

// --- PURGE ENDPOINT ---
app.post('/api/admin/clear-all-students', (req, res) => {
    try {
        activePlayers = {};
        
        // Loop through the in-memory object and remove entries starting with STU_
        Object.keys(students).forEach(key => {
            if (key.startsWith('STU_')) {
                delete students[key];
            }
        });

        serverNeedsReset = true;
        setTimeout(() => { serverNeedsReset = false; }, 1200);

        console.log("\n[ADMIN PURGE] In-memory JavaScript database data wiped successfully.");
        res.json({ success: true, message: "All STU_ records and scores deleted successfully from memory." });
    } catch (err) {
        console.error("Delete Error:", err);
        res.status(500).json({ error: "Server error: " + err.message });
    }
});

// --- MULTIPLAYER CONNECTION LOGGING ---
app.get('/game.html', (req, res, next) => {
    const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
    console.log(`\n[MULTIPLAYER CONNECTION] game.html opened by a separate browser window!`);
    console.log(`[IP Address] ${ip}`);
    console.log(`[Timestamp]  ${new Date().toLocaleTimeString()}\n`);
    next(); 
});

app.use(express.static(__dirname));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'game.html'));
});

// Automated Garbage Collector Loop: Removes offline players after 5 seconds
setInterval(() => {
    const timeThreshold = Date.now();
    Object.keys(activePlayers).forEach(id => {
        if (timeThreshold - activePlayers[id].lastPing > 5000) {
            console.log(`[MULTIPLAYER LEAVE] Student #${id} timed out or closed the browser room.`);
            delete activePlayers[id];
        }
    });
}, 3000);

// --- IN-MEMORY AUTHENTICATION CHANNEL ---
app.post('/api/auth', (req, res) => {
    const { studentNumber } = req.body;
    if (!studentNumber) return res.status(400).json({ error: "Identification argument expected." });

    // Look up user inside the global object memory space
    if (students[studentNumber]) {
        res.json({ authenticated: true, data: students[studentNumber] });
    } else {
        // Create an initial student data profile frame directly in the JavaScript object structure
        students[studentNumber] = {
            student_number: studentNumber,
            safe_completed: 0, safe_score: 0,
            savvy_completed: 0, savvy_score: 0,
            social_completed: 0, social_score: 0,
            last_active: new Date().toISOString()
        };
        res.json({ authenticated: true, data: students[studentNumber] });
    }
});

app.post('/api/multiplayer/join-room', (req, res) => {
    const { studentNumber, roomCode } = req.body;
    if (!studentNumber || !roomCode) {
        return res.status(400).json({ error: "Missing identity or room sequence parameters." });
    }
    
    console.log(`[ROOM MATCH] Student #${studentNumber} has synchronized into Room Instance: [${roomCode.toUpperCase()}]`);
    res.json({ success: true, roomCode: roomCode.toUpperCase() });
});

app.post('/api/multiplayer/sync', (req, res) => {
    const { studentNumber, roomCode, currentRoomCode, x, y, angle, moving, animStep } = req.body;
    if (!studentNumber) return res.status(400).json({ error: "Missing identity sequence parameters." });

    const normalizedRoom = roomCode ? roomCode.trim().toUpperCase() : "DEFAULT";

    activePlayers[studentNumber] = {
        studentNumber,
        roomCode: normalizedRoom,
        currentRoomCode: currentRoomCode || 'room_background', 
        x, y, angle, moving, animStep,
        lastPing: Date.now()
    };

    const peerPlayers = {};
    Object.keys(activePlayers).forEach(id => {
        if (id !== studentNumber && activePlayers[id].roomCode === normalizedRoom) {
            peerPlayers[id] = activePlayers[id];
        }
    });

    res.json({ 
        players: peerPlayers,
        forceClear: serverNeedsReset 
    });
});

app.post('/api/change-room', (req, res) => {
    const { studentNumber, newRoom } = req.body;
    if (activePlayers[studentNumber]) {
        activePlayers[studentNumber].roomCode = newRoom;
    }
    res.json({ success: true });
});

// --- IN-MEMORY PROGRESS SAVE ---
app.post('/api/save-progress', (req, res) => {
    const { studentNumber, module, score, completed } = req.body;
    
    if (!students[studentNumber]) {
        return res.status(404).json({ error: "Student target context missing in memory loop." });
    }

    // Directly assign key values within runtime JavaScript variables
    students[studentNumber][`${module}_completed`] = completed ? 1 : 0;
    students[studentNumber][`${module}_score`] = score;
    students[studentNumber].last_active = new Date().toISOString();

    res.json({ success: true });
});

// Soft memory clear endpoint
app.post('/api/admin/global-reset', (req, res) => {
    activePlayers = {}; 
    serverNeedsReset = true; 
    setTimeout(() => { serverNeedsReset = false; }, 1000);
    
    console.log("[Admin]: Global soft memory reset triggered.");
    res.status(200).json({ status: "Success", message: "In-memory registry purged." });
});

// Hard Memory Clear Endpoint (Wipes both active logs and score cache instances)
app.post('/api/admin/hard-purge-database', (req, res) => {
    activePlayers = {};
    students = {}; // Clear global storage entirely
    serverNeedsReset = true;
    setTimeout(() => { serverNeedsReset = false; }, 1200);

    console.log("\n=======================================================");
    // Safe to delete cybergame.db files now via terminal without errors
    console.log("[IN-MEMORY RESET]: All score maps completely wiped!");
    console.log("=======================================================\n");

    res.status(200).json({ status: "Success", message: "All memory contexts rebuilt successfully." });
});

// Debug tool showing current structural object state inside engine
app.get('/api/admin/debug-players', (req, res) => {
    res.json({ activePlayers, students });
});

const HOST = '192.168.1.8'; 

app.listen(PORT, HOST, () => {
    console.log(`===================================================`);
    console.log(` SERVER RUNNING LOCAL: http://localhost:${PORT}`);
    console.log(` SERVER RUNNING NETWORK: http://192.168.1.8:${PORT}`);
    console.log(`===================================================`);
});