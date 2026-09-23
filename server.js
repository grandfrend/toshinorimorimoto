import express from 'express';
import cors from 'cors';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3000;
const HOST = '0.0.0.0';

// Middlewares
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// In-memory data storage (simulates Cloudflare D1 / SQLite database)
const db = {
  enrollments: [
    {
      id: 1,
      student_name: "Mateo Nguema Oyono",
      birth_date: "2022-04-15",
      tutor_name: "Elena Oyono Mba",
      tutor_phone: "+240 222 123 456",
      tutor_email: "elena.oyono@ejemplo.com",
      shift: "mañana",
      documents_submitted: 0,
      status: "pendiente",
      created_at: new Date(Date.now() - 3600000 * 24).toISOString()
    },
    {
      id: 2,
      student_name: "Aitana Mbengono Mangue",
      birth_date: "2021-11-20",
      tutor_name: "Vicente Mangue Nsue",
      tutor_phone: "+240 222 654 321",
      tutor_email: "vicente.mangue@ejemplo.com",
      shift: "completo",
      documents_submitted: 1,
      status: "confirmado",
      created_at: new Date(Date.now() - 3600000 * 12).toISOString()
    }
  ],
  contacts: [
    {
      id: 1,
      name: "Carlos Ondo Mikue",
      phone: "+240 222 987 654",
      email: "carlos.ondo@ejemplo.com",
      message: "Buenas tardes, quisiera consultar sobre los requisitos para el aula de 2 años en el turno de la tarde y las fechas límite de matriculación.",
      status: "nuevo",
      created_at: new Date(Date.now() - 3600000 * 6).toISOString()
    },
    {
      id: 2,
      name: "Esperanza Bindang",
      phone: "+240 222 456 789",
      email: "esperanza.bindang@ejemplo.com",
      message: "Hola, me gustaría saber si disponen de servicio de comedor escolar en el turno completo.",
      status: "nuevo",
      created_at: new Date(Date.now() - 3600000 * 2).toISOString()
    }
  ],
  parent_attendance: []
};

// API Routes
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'Centro Privado Toshinori Morimoto API',
    uptime: process.uptime()
  });
});

// 1. Pre-inscripción Escolar
app.post('/api/enroll', (req, res) => {
  try {
    const { student_name, birth_date, tutor_name, tutor_phone, tutor_email, shift } = req.body || {};

    if (!student_name || !birth_date || !tutor_name || !tutor_phone || !shift) {
      return res.status(400).json({ error: 'Faltan campos obligatorios' });
    }

    const record = {
      id: db.enrollments.length + 1,
      student_name,
      birth_date,
      tutor_name,
      tutor_phone,
      tutor_email: tutor_email || '',
      shift,
      documents_submitted: 0,
      status: 'pendiente',
      created_at: new Date().toISOString()
    };

    db.enrollments.push(record);

    res.status(201).json({
      success: true,
      message: 'Pre-inscripción registrada con éxito.',
      id: record.id
    });
  } catch (err) {
    res.status(500).json({ error: 'Error interno del servidor', details: err.message });
  }
});

app.get('/api/enroll', (req, res) => {
  res.json({
    success: true,
    total: db.enrollments.length,
    enrollments: db.enrollments
  });
});

// 2. Mensajes de Contacto
app.post('/api/contact', (req, res) => {
  try {
    const { name, phone, email, message } = req.body || {};

    if (!name || !phone || !message) {
      return res.status(400).json({ error: 'Faltan campos obligatorios' });
    }

    const record = {
      id: db.contacts.length + 1,
      name,
      phone,
      email: email || '',
      message,
      status: 'nuevo',
      created_at: new Date().toISOString()
    };

    db.contacts.push(record);

    res.status(201).json({
      success: true,
      message: 'Mensaje de contacto guardado.',
      id: record.id
    });
  } catch (err) {
    res.status(500).json({ error: 'Error interno del servidor', details: err.message });
  }
});

app.get('/api/contact', (req, res) => {
  res.json({
    success: true,
    total: db.contacts.length,
    contacts: db.contacts
  });
});

// 3. Control de Asistencias
app.post('/api/attendance', (req, res) => {
  try {
    const { meeting_type, date_checked, tutor_name, student_name } = req.body || {};

    if (!meeting_type || !date_checked || !tutor_name || !student_name) {
      return res.status(400).json({ error: 'Faltan campos obligatorios' });
    }

    const record = {
      id: db.parent_attendance.length + 1,
      meeting_type,
      date_checked,
      tutor_name,
      student_name,
      teacher_signature: 'firmado',
      tutor_signature: 'firmado',
      created_at: new Date().toISOString()
    };

    db.parent_attendance.push(record);

    res.status(201).json({
      success: true,
      message: 'Asistencia de tutor registrada.',
      id: record.id
    });
  } catch (err) {
    res.status(500).json({ error: 'Error interno del servidor', details: err.message });
  }
});

app.get('/api/attendance', (req, res) => {
  res.json({
    success: true,
    total: db.parent_attendance.length,
    attendance: db.parent_attendance
  });
});

// 4. Panel de Administración
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'admin123';
const adminTokens = new Map(); // token -> expires_at
let loginAttempts = [];

// POST /api/admin/login
app.post('/api/admin/login', (req, res) => {
  const ip = req.ip || req.connection?.remoteAddress || '127.0.0.1';
  const now = Date.now();

  // Limpiar intentos de más de 15 minutos
  loginAttempts = loginAttempts.filter(a => now - a.time < 15 * 60 * 1000);
  const recentFails = loginAttempts.filter(a => a.ip === ip && !a.success);

  if (recentFails.length >= 5) {
    return res.status(429).json({
      error: 'Demasiados intentos fallidos. Inténtalo de nuevo en 15 minutos.'
    });
  }

  const { password } = req.body || {};
  const valid = Boolean(password && (password === ADMIN_PASSWORD || (process.env.ADMIN_PASSWORD && password === process.env.ADMIN_PASSWORD)));

  loginAttempts.push({ ip, success: valid, time: now });

  if (!valid) {
    return res.status(401).json({ error: 'Contraseña incorrecta' });
  }

  const token = 'tok_' + Math.random().toString(36).substring(2) + Date.now().toString(36);
  const expires_at = now + 8 * 60 * 60 * 1000;
  adminTokens.set(token, expires_at);

  return res.json({
    success: true,
    token,
    expires_at
  });
});

function verifyAdminToken(req) {
  const auth = req.headers['authorization'] || '';
  const match = auth.match(/^Bearer (.+)$/);
  if (!match) return false;
  const token = match[1];
  const expiresAt = adminTokens.get(token);
  if (!expiresAt || expiresAt < Date.now()) {
    adminTokens.delete(token);
    return false;
  }
  return true;
}

// GET /api/admin/enrollments
app.get('/api/admin/enrollments', (req, res) => {
  if (!verifyAdminToken(req)) {
    return res.status(401).json({ error: 'No autorizado' });
  }
  return res.json({
    success: true,
    enrollments: [...db.enrollments].reverse()
  });
});

// GET /api/admin/contacts
app.get('/api/admin/contacts', (req, res) => {
  if (!verifyAdminToken(req)) {
    return res.status(401).json({ error: 'No autorizado' });
  }
  return res.json({
    success: true,
    contacts: [...db.contacts].reverse()
  });
});

// Determine static file directory
const staticDir = path.join(__dirname, 'public');

// Serve static assets
app.use(express.static(staticDir));

// Clean absolute routes fallback
app.get('*', (req, res, next) => {
  if (req.path.startsWith('/api/')) return next();

  // Normalize path without trailing slash
  const cleanPath = req.path.replace(/\/$/, '');
  const dirIndexPath = path.join(staticDir, cleanPath, 'index.html');
  const directFilePath = path.join(staticDir, req.path);
  const htmlFilePath = path.join(staticDir, `${cleanPath}.html`);

  if (fs.existsSync(dirIndexPath) && fs.statSync(dirIndexPath).isFile()) {
    return res.sendFile(dirIndexPath);
  }
  if (fs.existsSync(htmlFilePath) && fs.statSync(htmlFilePath).isFile()) {
    return res.sendFile(htmlFilePath);
  }
  if (fs.existsSync(directFilePath) && fs.statSync(directFilePath).isFile()) {
    return res.sendFile(directFilePath);
  }

  // Root fallback
  const indexPath = path.join(staticDir, 'index.html');
  if (fs.existsSync(indexPath)) {
    return res.sendFile(indexPath);
  }

  res.status(404).send('Página no encontrada');
});

app.listen(PORT, HOST, () => {
  console.log(`[Toshinori PWA] Server running on http://${HOST}:${PORT}`);
  console.log(`[Toshinori PWA] Serving static files from: ${staticDir}`);
});
