-- Tabla de Solicitudes de Pre-inscripción Escolar
CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    birth_date TEXT NOT NULL,
    tutor_name TEXT NOT NULL,
    tutor_phone TEXT NOT NULL,
    tutor_email TEXT,
    shift TEXT NOT NULL, -- 'mañana', 'tarde', 'completo'
    documents_submitted INTEGER DEFAULT 0, -- 1 = Sí, 0 = No (pendiente)
    status TEXT DEFAULT 'pendiente', -- 'pendiente', 'aprobado', 'cancelado'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Mensajes de Contacto y Sugerencias
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    message TEXT NOT NULL,
    status TEXT DEFAULT 'nuevo', -- 'nuevo', 'leído', 'respondido'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Registro de Asistencias de Tutores
CREATE TABLE IF NOT EXISTS parent_attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_type TEXT NOT NULL, -- '1a Reunión', '1a Evaluación', '2a Reunión', etc.
    date_checked TEXT NOT NULL,
    tutor_name TEXT NOT NULL,
    student_name TEXT NOT NULL,
    teacher_signature TEXT DEFAULT 'firmado',
    tutor_signature TEXT DEFAULT 'firmado',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
