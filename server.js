const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const HOST = '192.168.1.8';

// Initialize the shared fallback SQLite Database configuration
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

// =========================================================================
// FACTORY ENGINE: GENERATES INDEPENDENT SHARDS DYNAMICALLY
// =========================================================================
function createGameShard(portNumber, minStudentNum, maxStudentNum) {
    const app = express();

    app.use(cors());
    app.use(express.json());
    
    // Support parsing raw text/plain strings that navigator.sendBeacon often sends
    app.use(express.text({ type: 'text/plain' }));

    // Each individual port keeps its own unique tracking structure instance
    const activePlayers = {};

    // --- MULTIPLAYER CONNECTION LOGGING ---
    app.get('/game.html', (req, res, next) => {
        const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
        console.log(`\n[SHARD ${portNumber} ACCESS] game.html opened by a separate browser window!`);
        console.log(`[IP Address] ${ip}`);
        console.log(`[Timestamp]  ${new Date().toLocaleTimeString()}\n`);
        next();
    });

    // ROUTE STATIC ROOT PATHS: Expose folder static assets directly on this port
    app.use(express.static(__dirname));

    app.get('/', (req, res) => {
        res.sendFile(path.join(__dirname, 'game.html'));
    });

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

    app.post('/api/multiplayer/join-room', (req, res) => {
        const { studentNumber, roomCode, roomId } = req.body;
        if (!studentNumber || !roomCode) {
            return res.status(400).json({ error: "Missing identity or room sequence parameters." });
        }

        const studentNumericId = parseInt(studentNumber.replace(/\D/g, ""), 10);

        if (studentNumericId < minStudentNum || studentNumericId > maxStudentNum) {
            return res.status(403).json({
                success: false,
                error: `Access Denied: Shard Port ${portNumber} exclusively registers STU_${String(minStudentNum).padStart(3, '0')} to STU_${String(maxStudentNum).padStart(3, '0')}.`
            });
        }
        
        const normalizedId = studentNumber.trim().toUpperCase();
        const normalizedRoom = roomCode.toUpperCase();
        const activeRoomId = roomId || 'room1';

        // --- FIX: OVERRIDE STALE/INACTIVE SESSION GHOSTS ---
        if (activePlayers[normalizedId]) {
            if (activePlayers[normalizedId].isInactive || (Date.now() - activePlayers[normalizedId].lastPing > 15000)) {
                console.log(`[SHARD ${portNumber}] Evicting stale/inactive session ghost for Student #${normalizedId}.`);
                delete activePlayers[normalizedId];
            } else {
                console.log(`[CONCURRENCY REJECTION - SHARD ${portNumber}] Student #${normalizedId} is truly active.`);
                return res.status(409).json({ 
                    success: false, 
                    error: `Access Denied: Student number ${normalizedId} is already active in a running session.` 
                });
            }
        }

        activePlayers[normalizedId] = {
            studentNumber: normalizedId,
            roomCode: normalizedRoom,
            roomId: activeRoomId,
            x: 400, y: 300, angle: 0, moving: false, animStep: 0,
            lastPing: Date.now(),
            isInactive: false 
        };
        
        console.log(`[ROOM MATCH - SHARD ${portNumber}] Student #${normalizedId} joined [${normalizedRoom}] Screen: ${activeRoomId}`);
        res.json({ success: true, roomCode: normalizedRoom, roomId: activeRoomId });
    });

    app.post('/api/multiplayer/sync', (req, res) => {
        const { studentNumber, roomCode, roomId, x, y, angle, moving, animStep, isInactive } = req.body;
        
        if (!studentNumber || !roomCode) {
            return res.status(400).json({ error: "Missing required tracking session keys" });
        }

        const normalizedId = studentNumber.trim().toUpperCase();
        const normalizedRoom = roomCode.trim().toUpperCase();
        const activeRoomId = roomId || 'room1';

        // Store active matrix positions
        if (activePlayers[normalizedId]) {
            activePlayers[normalizedId].x = x;
            activePlayers[normalizedId].y = y;
            activePlayers[normalizedId].angle = angle;
            activePlayers[normalizedId].moving = moving;
            activePlayers[normalizedId].animStep = animStep;
            activePlayers[normalizedId].lastPing = Date.now(); // Refreshes heartbeat status counter
            
            // --- FIX: Retain dynamic inactive visibility tracking payload state ---
            if (typeof isInactive !== 'undefined') {
                activePlayers[normalizedId].isInactive = isInactive;
            }
        } else {
            // Fallback generation safety block if structural sync hits before join verification finishes
            activePlayers[normalizedId] = {
                studentNumber: normalizedId,
                roomCode: normalizedRoom,
                roomId: activeRoomId, 
                x, y, angle, moving, animStep,
                lastPing: Date.now(),
                isInactive: isInactive || false
            };
        }

        // Output Filter: Only match peers within the SAME shard server context, Room Code, and Map Room ID
        const peerPlayers = {};
        Object.keys(activePlayers).forEach(id => {
            if (id !== normalizedId && 
                activePlayers[id].roomCode === normalizedRoom && 
                activePlayers[id].roomId === activeRoomId) {
                peerPlayers[id] = activePlayers[id];
            }
        });

        res.json({ players: peerPlayers });
    });
// --- INTENTIONAL LEAVE / EXIT GAME BUTTON PURGE CHANNEL ---
    app.post('/api/multiplayer/leave', (req, res) => {
        let payload = req.body;
        
        // Safely parse body if sendBeacon delivered it wrapped as a raw text string context
        if (typeof payload === 'string') {
            try { payload = JSON.parse(payload); } catch (e) {}
        }

        const { studentNumber } = payload;
        if (!studentNumber) return res.status(400).json({ error: "Missing identity sequence argument." });

        const normalizedId = studentNumber.trim().toUpperCase();

        if (activePlayers[normalizedId]) {
            // --- TARGET TERMINAL NOTIFICATION ---
            console.log(`\n===================================================`);
            console.log(`[MULTIPLAYER DISCONNECT] 🚪 Student #${normalizedId} left the game!`);
            console.log(`[Shard Port]  ${portNumber}`);
            console.log(`[Timestamp]   ${new Date().toLocaleTimeString()}`);
            console.log(`===================================================\n`);
            
            // Remove the player instance from server tracking memory
            delete activePlayers[normalizedId];
        }

        res.json({ success: true });
    });

    app.post('/api/save-progress', (req, res) => {
        const { studentNumber, module, score, completed } = req.body;
        const sqlUpdate = `UPDATE students SET ${module}_completed = ?, ${module}_score = ?, last_active = CURRENT_TIMESTAMP WHERE student_number = ?`;
        
        db.run(sqlUpdate, [completed ? 1 : 0, score, studentNumber], function(err) {
            if (err) return res.status(500).json({ error: err.message });
            res.json({ success: true });
        });
    });

    // --- FIX: Respect Background Tab State & Target True Window Drops ---
    setInterval(() => {
        const now = Date.now();
        Object.keys(activePlayers).forEach(id => {
            // Bypasses evaluation entirely if student flag is backgrounded but running
            if (activePlayers[id].isInactive) {
                return; 
            }

            // Only remove if they completely lost power/crashed without fire beacon (45 seconds safety window)
            if (now - activePlayers[id].lastPing > 45000) { 
                console.log(`[MULTIPLAYER TIMEOUT - SHARD ${portNumber}] Student #${id} dropped due to connection loss.`);
                delete activePlayers[id];
            }
        });
    }, 10000);

    app.listen(portNumber, HOST, () => {
        console.log(`[GAME SHARD] http://${HOST}:${portNumber} Active (STU_${String(minStudentNum).padStart(3, '0')} - STU_${String(maxStudentNum).padStart(3, '0')})`);
    });
}

// =========================================================================
// INITIALIZE LOCAL PORTS CLUSTERS
// =========================================================================
createGameShard(3000, 1, 20);  // Server Shard 1: Tracks STU_001 through STU_020
createGameShard(3001, 21, 40); // Server Shard 2: Tracks STU_021 through STU_040
createGameShard(3002, 41, 60); // Server Shard 3: Tracks STU_041 through STU_060