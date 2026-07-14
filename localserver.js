const express = require('express');
const cors = require('cors');
const path = require('path');
const sqlite3 = require('sqlite3').verbose(); 

const HOST = '10.32.96.71';

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
// FACTORY ENGINE: GENERATES INDEPENDENT SHARDS DYNAMICALLY
// =========================================================================
function createGameShard(portNumber, minStudentNum, maxStudentNum) {
    const app = express();

    app.use(cors());
    app.use(express.json());
    app.use(express.text({ type: 'text/plain' }));

    // Each individual port keeps its own unique in-memory real-time tracking instance
    const activePlayers = {};

    // --- MULTIPLAYER CONNECTION LOGGING ---
    app.get('/game.html', (req, res, next) => {
        const ip = req.headers['x-forwarded-for'] || req.socket.remoteAddress;
        console.log(`\n[SHARD ${portNumber} ACCESS] game.html opened by a separate browser window!`);
        console.log(`[IP Address] ${ip}`);
        console.log(`[Timestamp]  ${new Date().toLocaleTimeString()}\n`);
        next();
    });

    app.use(express.static(__dirname));

    app.get('/', (req, res) => {
        res.sendFile(path.join(__dirname, 'game.html'));
    });

    // =========================================================================
    // LOCAL SQLITE AUTHENTICATION & SEEDING ROUTE (3-MODULE SCHEMA)
    // =========================================================================
    app.post('/api/auth', (req, res) => {
        const { studentNumber } = req.body;
        if (!studentNumber) return res.status(400).json({ error: "Identification argument expected." });

        const normalizedKey = studentNumber.trim().toUpperCase();
        
        console.log(`[LOCAL AUTH - SHARD ${portNumber}] Local database authentication: ${normalizedKey}`);
        
        localDb.get(`SELECT * FROM students WHERE student_number = ?`, [normalizedKey], (err, row) => {
            if (err) {
                console.error("[LOCAL DB ERROR]:", err.message);
                return res.status(500).json({ error: "Local database tracking fault." });
            }

            if (row) {
                return res.json({ authenticated: true, data: row });
            } else {
                const newRecord = {
                    student_number: normalizedKey,
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
                            console.error("[LOCAL DB INSERT ERROR]:", insertErr.message);
                            return res.status(500).json({ error: "Local seeding process crashed." });
                        }
                        return res.json({ authenticated: true, data: newRecord });
                    }
                );
            }
        });
    });

    // =========================================================================
    // AUTOMATIC PROGRESSION ROUTING ON ROOM ENTRANCE
    // =========================================================================
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
        
        let calculatedRoomId = roomId ? roomId.toLowerCase() : 'room1';

        localDb.get(`SELECT * FROM students WHERE student_number = ?`, [normalizedId], (err, row) => {
            if (!err && row) {
                const safe = row.safe_score || 0;
                const savvy = row.savvy_score || 0;
                const social = row.social_score || 0;
                const totalScore = safe + savvy + social;

                if (totalScore >= 40) {
                    calculatedRoomId = 'room3';
                } else if (totalScore >= 20) {
                    calculatedRoomId = 'room2';
                } else {
                    calculatedRoomId = 'room1';
                }
                console.log(`[SPAWN ROUTER LOCAL - SHARD ${portNumber}] Student #${studentNumber} Score: ${totalScore}. Routed to: ${calculatedRoomId}`);
            }
            completeJoinRoom();
        });

        function completeJoinRoom() {
            // --- OVERRIDE GHOST SESSIONS SAFELY ---
            if (activePlayers[normalizedId]) {
                if (activePlayers[normalizedId].isInactive || (Date.now() - activePlayers[normalizedId].lastPing > 15000)) {
                    console.log(`[SHARD ${portNumber}] Evicting stale session ghost for Student #${normalizedId}.`);
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
                roomCode: normalizedRoom,
                roomId: calculatedRoomId,
                x: null,
                y: null, 
                angle: 0, 
                moving: false, 
                animStep: 0,
                lastPing: Date.now(),
                isInactive: false 
            };
            
            console.log(`[ROOM MATCH - SHARD ${portNumber}] Student #${studentNumber} initialized inside Screen Shard: ${calculatedRoomId}`);
            res.json({ success: true, roomCode: normalizedRoom, roomId: calculatedRoomId });
        }
    });

    app.post('/api/multiplayer/sync', (req, res) => {
        const { studentNumber, roomCode, roomId, x, y, angle, moving, animStep, isInactive } = req.body;
        
        if (!studentNumber || !roomCode) {
            return res.status(400).json({ error: "Missing required tracking session keys" });
        }

        const normalizedId = studentNumber.trim().toUpperCase();
        const normalizedRoom = roomCode.trim().toUpperCase();
        const activeRoomId = roomId || 'room1';

        if (activePlayers[normalizedId]) {
            activePlayers[normalizedId].x = x;
            activePlayers[normalizedId].y = y;
            activePlayers[normalizedId].angle = angle;
            activePlayers[normalizedId].moving = moving;
            activePlayers[normalizedId].animStep = animStep;
            activePlayers[normalizedId].roomId = activeRoomId;
            activePlayers[normalizedId].lastPing = Date.now();
            
            if (typeof isInactive !== 'undefined') {
                activePlayers[normalizedId].isInactive = isInactive;
            }
        } else {
            activePlayers[normalizedId] = {
                studentNumber: studentNumber,
                roomCode: normalizedRoom,
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
                activePlayers[id].roomCode === normalizedRoom && 
                activePlayers[id].roomId === activeRoomId &&
                activePlayers[id].x !== null 
            ) {
                peerPlayers[id] = activePlayers[id];
            }
        });

        res.json({ players: peerPlayers });
    });

    app.post('/api/multiplayer/leave', (req, res) => {
        let payload = req.body;
        if (typeof payload === 'string') {
            try { payload = JSON.parse(payload); } catch (e) {}
        }

        const { studentNumber } = payload;
        if (!studentNumber) return res.status(400).json({ error: "Missing identity sequence argument." });

        const normalizedId = studentNumber.trim().toUpperCase();

        if (activePlayers[normalizedId]) {
            console.log(`\n===================================================`);
            console.log(`[MULTIPLAYER DISCONNECT] 🚪 Student #${studentNumber} left the game!`);
            console.log(`[Shard Port]  ${portNumber}`);
            console.log(`[Timestamp]   ${new Date().toLocaleTimeString()}`);
            console.log(`===================================================\n`);
            
            delete activePlayers[normalizedId];
        }

        res.json({ success: true });
    });

    // =========================================================================
    // LOCAL PROGRESS SAVING ROUTE (SQLITE EXCLUSIVE WRITE)
    // =========================================================================
    app.post('/api/save-progress', (req, res) => {
        const { studentNumber, module, score, completed } = req.body;
        
        if (!studentNumber || !module) {
            return res.status(400).json({ error: "Missing progress tracking keys." });
        }

        const normalizedKey = studentNumber.trim().toUpperCase();

        console.log(`[LOCAL PROGRESS SAVE] Committing ${score} pts to ${module}_score inside cybergame.db`);
        
        // Query current score first to perform incremental updates safely
        localDb.get(`SELECT * FROM students WHERE student_number = ?`, [normalizedKey], (err, row) => {
            if (err || !row) {
                return res.status(500).json({ error: "Failed to locate local database identity row." });
            }

            const currentScore = row[`${module}_score`] || 0;
            const updatedScore = currentScore + score;
            const completedVal = completed ? 1 : 0;
            const nowStr = new Date().toISOString();

            localDb.run(`UPDATE students SET 
                ${module}_score = ?, 
                ${module}_completed = ?, 
                last_active = ? 
                WHERE student_number = ?`,
                [updatedScore, completedVal, nowStr, normalizedKey],
                function(updateErr) {
                    if (updateErr) {
                        console.error("[LOCAL UPDATE ERROR]:", updateErr.message);
                        return res.status(500).json({ error: "Local state write failure." });
                    }
                    res.json({ success: true, localDbChanges: this.changes });
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
                console.log(`[MULTIPLAYER TIMEOUT - SHARD ${portNumber}] Student #${id} dropped due to connection loss.`);
                delete activePlayers[id];
            }
        });
    }, 10000);

    app.listen(portNumber, HOST, () => {
        console.log(`[GAME SHARD] http://${HOST}:${portNumber} Active (STU_${String(minStudentNum).padStart(3, '0')} - STU_${String(maxStudentNum).padStart(3, '0')})`);
    });
    // =========================================================================
    // TEACHER RECORDS FETCH ROUTE (SQLITE EXCLUSIVE)
    // =========================================================================
    app.get('/api/teacher/records', (req, res) => {
        localDb.all(`SELECT * FROM students ORDER BY student_number ASC`, [], (err, rows) => {
            if (err) {
                console.error("[TEACHER FETCH ERROR]:", err.message);
                return res.status(500).json({ error: "Failed to read student database." });
            }
            res.json({ success: true, players: rows });
        });
    });
}

// =========================================================================
// INITIALIZE LOCAL PORTS CLUSTERS
// =========================================================================
createGameShard(3000, 1, 20);  // Server Shard 1: Tracks STU_001 through STU_020
createGameShard(3001, 21, 40); // Server Shard 2: Tracks STU_021 through STU_040
createGameShard(3002, 41, 60); // Server Sh0ard 3: Tracks STU_041 through STU_060