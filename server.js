
const express = require('express');
const cors = require('cors');
const path = require('path');
const { initializeApp, cert } = require('firebase-admin/app');
const { getFirestore, FieldValue } = require('firebase-admin/firestore');

const HOST = '192.168.1.12';

// =========================================================================
// INTEGRATED CLOUD SERVICE STORAGE ENGINE (FIREBASE GLOBAL ACCESS)
// =========================================================================
// Ensure your 'firebase-service-account.json' file is in the same directory!
const serviceAccount = require('./firebase-service-account.json');

initializeApp({
    credential: cert(serviceAccount)
});

const firestore = getFirestore(); 
const studentsCollection = firestore.collection('students');

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
    app.get('/api/config', (req, res) => {
        res.json({ host: HOST });
    });
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
    // CLOUD-BASED AUTHENTICATION & SEEDING ROUTE (EXPLICIT 3-MODULE SCHEMA)
    // =========================================================================
    app.post('/api/auth', async (req, res) => {
        const { studentNumber } = req.body;
        if (!studentNumber) return res.status(400).json({ error: "Identification argument expected." });

        const normalizedKey = studentNumber.trim().toUpperCase();
        const studentDocRef = studentsCollection.doc(normalizedKey);

        try {
            const doc = await studentDocRef.get();

            if (doc.exists) {
                // Return data directly from Cloud Firestore
                res.json({ authenticated: true, data: doc.data() });
            } else {
                // Force-seed all three sub-modules (Safe, Savvy, Social) upon initial sign-in
                const newRecord = {
                    student_number: studentNumber,
                    
                    // Scores Divided Into 3 Modules
                    safe_score: 0,
                    savvy_score: 0,
                    social_score: 0,
                    
                    // Completion States
                    safe_completed: 0,
                    savvy_completed: 0,
                    social_completed: 0,
                    
                    last_active: FieldValue.serverTimestamp()
                };
                
                await studentDocRef.set(newRecord);
                res.json({ authenticated: true, data: newRecord });
            }
        } catch (err) {
            console.error(`[CLOUD AUTH ERROR - SHARD ${portNumber}]:`, err.message);
            res.status(500).json({ error: "Cloud database synchronization failed." });
        }
    });
    // =========================================================================
    // TEACHER RECORDS FETCH ROUTE (FIREBASE CLOUD READ)
    // =========================================================================
    app.get('/api/teacher/records', async (req, res) => {
        try {
            const snapshot = await studentsCollection.get();
            const players = [];
            
            snapshot.forEach(doc => {
                const data = doc.data();
                // Helper to convert Firestore Timestamp to standard string
                if (data.last_active && typeof data.last_active.toDate === 'function') {
                    data.last_active = data.last_active.toDate().toISOString();
                }
                players.push(data);
            });

            res.json({ success: true, players: players });
        } catch (err) {
            console.error(`[TEACHER FETCH ERROR - SHARD ${portNumber}]:`, err.message);
            res.status(500).json({ error: "Failed to retrieve student records from cloud." });
        }
    });
    // =========================================================================
    // AUTOMATIC CLOUD-BASED PROGRESSION ROUTING ON ROOM ENTRANCE
    // =========================================================================
    app.post('/api/multiplayer/join-room', async (req, res) => {
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
        
        // Fallback default
        let calculatedRoomId = roomId ? roomId.toLowerCase() : 'room1';

        try {
            // Retrieve latest progression scores directly from Cloud Firestore record to calculate spawn room
            const doc = await studentsCollection.doc(normalizedId).get();
            if (doc.exists) {
                const record = doc.data();
                
                // Aggregate score categories safely
                const safe = record.safe_score || 0;
                const savvy = record.savvy_score || 0;
                const social = record.social_score || 0;
                const totalScore = safe + savvy + social;

                if (totalScore >= 40) {
                    calculatedRoomId = 'room3';
                } else if (totalScore >= 20) {
                    calculatedRoomId = 'room2';
                } else {
                    calculatedRoomId = 'room1';
                }
                
                console.log(`[SPAWN ROUTER - SHARD ${portNumber}] Recalled Student #${studentNumber} (Scores -> Safe: ${safe}, Savvy: ${savvy}, Social: ${social} | Total: ${totalScore}). Routed to: ${calculatedRoomId}`);
            } else {
                console.log(`[SPAWN ROUTER - SHARD ${portNumber}] No cloud record found yet for ${studentNumber}. Defaulting spawn to room1.`);
                calculatedRoomId = 'room1';
            }
        } catch (err) {
            console.error(`[SHARD ${portNumber} CLOUD ROOM ROUTE ERROR]:`, err.message);
            calculatedRoomId = 'room1'; // Gracefully fallback to prevent player blockage on connection faults
        }

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
    // ATOMIC CLOUD PROGRESS SAVING ROUTE (FIREBASE CLOUD WRITE - MERGE FIXED)
    // =========================================================================
    app.post('/api/save-progress', async (req, res) => {
        const { studentNumber, module, score, completed } = req.body;
        
        if (!studentNumber || !module) {
            return res.status(400).json({ error: "Missing progress tracking keys." });
        }

        const normalizedKey = studentNumber.trim().toUpperCase();
        const studentDocRef = studentsCollection.doc(normalizedKey);

        try {
            // set with { merge: true } safely writes fields whether the record is fresh or pre-existing
            await studentDocRef.set({
                [`${module}_score`]: FieldValue.increment(score),
                [`${module}_completed`]: completed ? 1 : 0,
                last_active: FieldValue.serverTimestamp()
            }, { merge: true });

            console.log(`[CLOUD PROGRESS RECORDED]: Added ${score} points to ${module}_score for Student #${studentNumber}.`);
            res.json({ success: true, changes: 1 });
        } catch (err) {
            console.error(`[CLOUD PROGRESS SAVE ERROR - SHARD ${portNumber}]:`, err.message);
            res.status(500).json({ error: "Failed to persist score matrix to cloud buckets." });
        }
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
}

// =========================================================================
// INITIALIZE LOCAL PORTS CLUSTERS
// =========================================================================
createGameShard(3000, 1, 20);  // Server Shard 1: Tracks STU_001 through STU_020
createGameShard(3001, 21, 40); // Server Shard 2: Tracks STU_021 through STU_040
createGameShard(3002, 41, 60); // Server Shard 3: Tracks STU_041 through STU_060