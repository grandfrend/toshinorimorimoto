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
  enrollments: [],
  contacts: [],
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
