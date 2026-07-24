const express = require('express');
const cors = require('cors');
const path = require('path');
const sqlite3 = require('sqlite3').verbose(); 

const HOST = '192.168.1.23';
const PORT = 3000;

const app = express();

app.use(cors());
app.use(express.json());
app.use(express.text({ type: 'text/plain' }));

// Global in-memory real-time player tracking instance
const activePlayers = {};

// =========================================================================
// SQLITE LOCAL STORAGE ENGINE CONFIGURATION (cybergame.db)
// =========================================================================
const dbPath = path.join(__dirname, 'cybergame.db');
const localDb = new sqlite3.Database(dbPath, (err) => {
    if (err) {
        console.error("❌ Failed to connect to cybergame.db:", err.message);
    } else {
        console.log("💾 Connected successfully to cybergame.db");
        // Create local students table reproducing the exact schema fields
        localDb.run(`CREATE TABLE IF NOT EXISTS students (
            student_number TEXT PRIMARY KEY,
            safe_score INTEGER DEFAULT 0,
            savvy_score INTEGER DEFAULT 0,
            social_score INTEGER DEFAULT 0,
            safe_completed INTEGER DEFAULT 0,
            savvy_completed INTEGER DEFAULT 0,
            social_completed INTEGER DEFAULT 0,
            last_active TEXT
        )`);
    }
});

// =========================================================================
// ROOM CODE ALLOCATION MAPPING (STU_001 TO STU_060)
// =========================================================================
function getAssignedRoomCode(studentNumber) {
    const numericId = parseInt(studentNumber.replace(/\D/g, ""), 10);
    if (isNaN(numericId)) return null;

    if (numericId >= 1 && numericId <= 10) return 'ROOM1';
    if (numericId >= 11 && numericId <= 20) return 'ROOM2';
    if (numericId >= 21 && numericId <= 30) return 'ROOM3';
    if (numericId >= 31 && numericId <= 40) return 'ROOM4';
    if (numericId >= 41 && numericId <= 50) return 'ROOM5';
    if (numericId >= 51 && numericId <= 60) return 'ROOM6';
    
    return null; // Out of authorized range
}

app.get('/api/config', (req, res) => {
    res.json({ host: HOST });
});

// --- MULTIPLAYER CONNECTION LOGGING ---
app.get('/game.html', (req, res, next) => {
    const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
    console.log(`\n[ACCESS] game.html opened by a separate browser window!`);
    console.log(`[IP Address] ${ip}`);
    console.log(`[Timestamp]  ${new Date().toLocaleTimeString()}\n`);
    next();
});

app.use(express.static(__dirname));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'game.html'));
});

// =========================================================================
// LOCAL SQLITE AUTHENTICATION & SEEDING ROUTE (EXPLICIT 3-MODULE SCHEMA)
// =========================================================================
app.post('/api/auth', (req, res) => {
    const { studentNumber } = req.body;
    if (!studentNumber) return res.status(400).json({ error: "Identification argument expected." });

    const normalizedKey = studentNumber.trim().toUpperCase();
    const assignedRoom = getAssignedRoomCode(normalizedKey);

    if (!assignedRoom) {
        return res.status(403).json({
            authenticated: false,
            error: `Access Denied: ${normalizedKey} falls outside the authorized range (STU_001 to STU_060).`
        });
    }
    
    console.log(`[LOCAL AUTH] Local database authentication: ${normalizedKey} -> Assigned: ${assignedRoom}`);
    
    localDb.get(`SELECT * FROM students WHERE student_number = ?`, [normalizedKey], (err, row) => {
        if (err) {
            console.error(`[LOCAL DB ERROR]:`, err.message);
            return res.status(500).json({ error: "Local database tracking fault." });
        }

        if (row) {
            return res.json({ authenticated: true, assignedRoom, data: row });
        } else {
            const newRecord = {
                student_number: studentNumber,
                safe_score: 0,
                savvy_score: 0,
                social_score: 0,
                safe_completed: 0,
                savvy_completed: 0,
                social_completed: 0,
                last_active: new Date().toISOString()
            };

            localDb.run(`INSERT INTO students (student_number, safe_score, savvy_score, social_score, safe_completed, savvy_completed, social_completed, last_active) 
                VALUES (?, 0, 0, 0, 0, 0, 0, ?)`, 
                [normalizedKey, newRecord.last_active], 
                (insertErr) => {
                    if (insertErr) {
                        console.error(`[LOCAL DB INSERT ERROR]:`, insertErr.message);
                        return res.status(500).json({ error: "Local seeding process crashed." });
                    }
                    return res.json({ authenticated: true, assignedRoom, data: newRecord });
                }
            );
        }
    });
});

// =========================================================================
// TEACHER RECORDS FETCH ROUTE (SQLITE EXCLUSIVE READ)
// =========================================================================
app.get('/api/teacher/records', (req, res) => {
    localDb.all(`SELECT * FROM students ORDER BY student_number ASC`, [], (err, rows) => {
        if (err) {
            console.error(`[TEACHER FETCH ERROR]:`, err.message);
            return res.status(500).json({ error: "Failed to read student database." });
        }
        res.json({ success: true, players: rows });
    });
});

// =========================================================================
// AUTOMATIC LOCAL PROGRESSION ROUTING ON ROOM ENTRANCE
// =========================================================================
app.post('/api/multiplayer/join-room', (req, res) => {
    const { studentNumber, roomId } = req.body;
    if (!studentNumber) {
        return res.status(400).json({ error: "Missing identity parameters." });
    }

    const normalizedId = studentNumber.trim().toUpperCase();
    const assignedRoom = getAssignedRoomCode(normalizedId);

    if (!assignedRoom) {
        return res.status(403).json({
            success: false,
            error: `Access Denied: Student number ${normalizedId} is out of bounds.`
        });
    }
    
    let calculatedRoomId = roomId ? roomId.toLowerCase() : 'room1';

    localDb.get(`SELECT * FROM students WHERE student_number = ?`, [normalizedId], (err, row) => {
        if (!err && row) {
            // CASE-INSENSITIVE FALLBACK READS:
            const safe = row.safe_score || row.Safe_score || row.SAFE_SCORE || 0;
            const savvy = row.savvy_score || row.Savvy_score || row.SAVVY_SCORE || 0;
            const social = row.social_score || row.Social_score || row.SOCIAL_SCORE || 0;
            const totalScore = safe + savvy + social;

            // Score thresholds matched completely
            if (totalScore >= 60) {
                calculatedRoomId = 'room3';
            } else if (totalScore >= 30) {
                calculatedRoomId = 'room2';
            } else {
                calculatedRoomId = 'room1';
            }
            console.log(`[SPAWN ROUTER LOCAL] Recalled Student #${studentNumber} (Scores -> Safe: ${safe}, Savvy: ${savvy}, Social: ${social} | Total: ${totalScore}). Routed to Zone: ${calculatedRoomId}`);
        } else {
            console.log(`[SPAWN ROUTER LOCAL] No record found yet for ${studentNumber}. Defaulting spawn zone to room1.`);
            calculatedRoomId = 'room1';
        }
        completeJoinRoom();
    });

    function completeJoinRoom() {
        // --- OVERRIDE GHOST SESSIONS SAFELY ---
        if (activePlayers[normalizedId]) {
            if (activePlayers[normalizedId].isInactive || (Date.now() - activePlayers[normalizedId].lastPing > 15000)) {
                console.log(`[ROOM MANAGER] Evicting stale session ghost for Student #${normalizedId}.`);
                delete activePlayers[normalizedId];
            } else {
                console.log(`[CONCURRENCY REJECTION] Student #${normalizedId} is truly active.`);
                return res.status(409).json({ 
                    success: false, 
                    error: `Access Denied: Student number ${normalizedId} is already active in a running session.` 
                });
            }
        }

        // --- INITIALIZE MEMORY BLOCK WITH DYNAMIC COORDINATE PROTECTION ---
        activePlayers[normalizedId] = {
            studentNumber: studentNumber,
            roomCode: assignedRoom,
            roomId: calculatedRoomId,
            x: null,
            y: null, 
            angle: 0, 
            moving: false, 
            animStep: 0,
            lastPing: Date.now(),
            isInactive: false 
        };
        
        console.log(`[ROOM MATCH] Student #${studentNumber} initialized inside Room Group: ${assignedRoom} (Zone: ${calculatedRoomId})`);
        res.json({ success: true, roomCode: assignedRoom, roomId: calculatedRoomId });
    }
});

app.post('/api/multiplayer/sync', (req, res) => {
    const { studentNumber, roomId, x, y, angle, moving, animStep, isInactive } = req.body;
    
    if (!studentNumber) {
        return res.status(400).json({ error: "Missing required tracking session keys" });
    }

    const normalizedId = studentNumber.trim().toUpperCase();
    const assignedRoom = getAssignedRoomCode(normalizedId);
    const activeRoomId = roomId || 'room1';

    if (!assignedRoom) {
        return res.status(403).json({ error: "Invalid identity range for synchronization." });
    }

    if (activePlayers[normalizedId]) {
        activePlayers[normalizedId].x = x;
        activePlayers[normalizedId].y = y;
        activePlayers[normalizedId].angle = angle;
        activePlayers[normalizedId].moving = moving;
        activePlayers[normalizedId].animStep = animStep;
        activePlayers[normalizedId].roomId = activeRoomId;
        activePlayers[normalizedId].roomCode = assignedRoom;
        activePlayers[normalizedId].lastPing = Date.now();
        
        if (typeof isInactive !== 'undefined') {
            activePlayers[normalizedId].isInactive = isInactive;
        }
    } else {
        activePlayers[normalizedId] = {
            studentNumber: studentNumber,
            roomCode: assignedRoom,
            roomId: activeRoomId, 
            x, y, angle, moving, animStep,
            lastPing: Date.now(),
            isInactive: isInactive || false
        };
    }

    const peerPlayers = {};
    Object.keys(activePlayers).forEach(id => {
        if (
            activePlayers[id].studentNumber !== studentNumber && 
            activePlayers[id].roomCode === assignedRoom && 
            activePlayers[id].roomId === activeRoomId &&
            activePlayers[id].x !== null 
        ) {
            peerPlayers[id] = activePlayers[id];
        }
    });

    res.json({ players: peerPlayers });
});

// =========================================================================
// MULTIPLAYER CONNECTION TERMINATION (IMMEDIATE DEPARTURE)
// =========================================================================
app.post('/api/multiplayer/leave', (req, res) => {
    let payload = req.body;
    if (typeof payload === 'string') {
        try { 
            payload = JSON.parse(payload); 
        } catch (e) {
            // Fallback if formatting fails during fast teardown
        }
    }

    const { studentNumber } = payload || {};
    if (!studentNumber) return res.status(400).json({ error: "Missing identity sequence argument." });

    const normalizedId = studentNumber.trim().toUpperCase();

    if (activePlayers[normalizedId]) {
        console.log(`\n===================================================`);
        console.log(`[MULTIPLAYER DISCONNECT] 🚪 Student #${normalizedId} left the game!`);
        console.log(`[Timestamp]   ${new Date().toLocaleTimeString()}`);
        console.log(`===================================================\n`);
        
        delete activePlayers[normalizedId];
    }

    res.json({ success: true });
});

// =========================================================================
// LOCAL PROGRESS SAVING ROUTE (SQLITE EXCLUSIVE WRITE - ACCUMULATIVE INCREMENT)
// =========================================================================
app.post('/api/save-progress', (req, res) => {
    const { studentNumber, module, score, completed } = req.body;
    
    if (!studentNumber || !module) {
        return res.status(400).json({ error: "Missing progress tracking keys." });
    }

    const normalizedKey = studentNumber.trim().toUpperCase();
    const normalizedModule = module.trim().toLowerCase();

    localDb.get(`SELECT * FROM students WHERE student_number = ?`, [normalizedKey], (err, row) => {
        if (err || !row) return res.status(500).json({ error: "Failed to locate database identity." });

        const currentScore = row[`${normalizedModule}_score`] || 0;
        const updatedScore = currentScore + score;
        const completedVal = completed ? 1 : 0;
        const nowStr = new Date().toISOString();

        localDb.run(`UPDATE students SET 
            ${normalizedModule}_score = ?, 
            ${normalizedModule}_completed = ?, 
            last_active = ? 
            WHERE student_number = ?`,
            [updatedScore, completedVal, nowStr, normalizedKey],
            function(updateErr) {
                if (updateErr) {
                    console.error(`[LOCAL PROGRESS SAVE ERROR]:`, updateErr.message);
                    return res.status(500).json({ error: "Local state write failure." });
                }
                console.log(`[LOCAL PROGRESS RECORDED]: Added ${score} points to ${normalizedModule}_score for Student #${studentNumber}.`);
                res.json({ success: true, changes: this.changes });
            }
        );
    });
});

// --- Respect Background Tab State & Target True Window Drops ---
setInterval(() => {
    const now = Date.now();
    Object.keys(activePlayers).forEach(id => {
        if (activePlayers[id].isInactive) {
            return; 
        }
        if (now - activePlayers[id].lastPing > 45000) { 
            console.log(`[MULTIPLAYER TIMEOUT] Student #${id} dropped due to connection loss.`);
            delete activePlayers[id];
        }
    });
}, 10000);

app.listen(PORT, HOST, () => {
    console.log(`[GAME SERVER] Unified server running at http://${HOST}:${PORT} managing ROOM1 through ROOM6.`);
});