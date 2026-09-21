# -*- coding: utf-8 -*-
import os
import base64

# Este script genera automáticamente toda la estructura de archivos para la PWA del Centro Toshinori Morimoto.
# Para usarlo:
# 1. Guarda este código como 'generar_proyecto.py' en tu ordenador.
# 2. Ejecuta: python generar_proyecto.py
# 3. Se creará una carpeta llamada 'toshinori-pwa' con todos los archivos listos para desplegar.

print("Iniciando la generación del proyecto PWA...")

# Crear directorios
os.makedirs("toshinori-pwa/src", exist_ok=True)
os.makedirs("toshinori-pwa/public", exist_ok=True)

# 1. wrangler.toml
with open("toshinori-pwa/wrangler.toml", "w", encoding="utf-8") as f:
    f.write('''name = "toshinori-morimoto-api"
main = "src/index.js"
compatibility_date = "2024-03-01"

[vars]
ENVIRONMENT = "production"

[[d1_databases]]
binding = "DB"
database_name = "toshinori_db"
database_id = "TU_DATABASE_ID" # Reemplazar con el ID obtenido al crear la base de datos D1
''')

# 2. schema.sql
with open("toshinori-pwa/schema.sql", "w", encoding="utf-8") as f:
    f.write('''-- Tabla de Solicitudes de Pre-inscripción Escolar
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
''')

# 3. src/index.js (Worker)
with open("toshinori-pwa/src/index.js", "w", encoding="utf-8") as f:
    f.write('''export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      if (url.pathname === "/api/enroll" && request.method === "POST") {
        const body = await request.json();
        const { student_name, birth_date, tutor_name, tutor_phone, tutor_email, shift } = body;

        if (!student_name || !birth_date || !tutor_name || !tutor_phone || !shift) {
          return new Response(JSON.stringify({ error: "Faltan campos obligatorios" }), {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" }
          });
        }

        await env.DB.prepare(
          "INSERT INTO enrollments (student_name, birth_date, tutor_name, tutor_phone, tutor_email, shift) VALUES (?, ?, ?, ?, ?, ?)"
        ).bind(student_name, birth_date, tutor_name, tutor_phone, tutor_email, shift).run();

        return new Response(JSON.stringify({ success: true, message: "Pre-inscripción registrada con éxito." }), {
          status: 201,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }

      if (url.pathname === "/api/contact" && request.method === "POST") {
        const body = await request.json();
        const { name, phone, email, message } = body;

        if (!name || !phone || !message) {
          return new Response(JSON.stringify({ error: "Faltan campos obligatorios" }), {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" }
          });
        }

        await env.DB.prepare(
          "INSERT INTO contacts (name, phone, email, message) VALUES (?, ?, ?, ?)"
        ).bind(name, phone, email, message).run();

        return new Response(JSON.stringify({ success: true, message: "Mensaje de contacto guardado." }), {
          status: 201,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }

      if (url.pathname === "/api/attendance" && request.method === "POST") {
        const body = await request.json();
        const { meeting_type, date_checked, tutor_name, student_name } = body;

        if (!meeting_type || !date_checked || !tutor_name || !student_name) {
          return new Response(JSON.stringify({ error: "Faltan campos obligatorios" }), {
            status: 400,
            headers: { ...corsHeaders, "Content-Type": "application/json" }
          });
        }

        await env.DB.prepare(
          "INSERT INTO parent_attendance (meeting_type, date_checked, tutor_name, student_name) VALUES (?, ?, ?, ?)"
        ).bind(meeting_type, date_checked, tutor_name, student_name).run();

        return new Response(JSON.stringify({ success: true, message: "Asistencia de tutor registrada." }), {
          status: 201,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }

      return new Response(JSON.stringify({ error: "Ruta no encontrada" }), {
        status: 404,
        headers: { ...corsHeaders, "Content-Type": "application/json" }
      });

    } catch (err) {
      return new Response(JSON.stringify({ error: "Error interno del servidor", details: err.message }), {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" }
      });
    }
  }
};
''')

# 4. public/manifest.json
with open("toshinori-pwa/public/manifest.json", "w", encoding="utf-8") as f:
    f.write('''{
  "name": "Centro Privado Toshinori Morimoto",
  "short_name": "Toshinori Morimoto",
  "description": "PWA para el Centro de Educación Infantil Toshinori Morimoto de Baney",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#e11d48",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "/icon-192.png",
      "type": "image/png",
      "sizes": "192x192"
    },
    {
      "src": "/icon-512.png",
      "type": "image/png",
      "sizes": "512x512"
    }
  ]
}
''')

# 5. public/sw.js
with open("toshinori-pwa/public/sw.js", "w", encoding="utf-8") as f:
    f.write('''const CACHE_NAME = 'toshinori-cache-v1';
const ASSETS = [
  '/',
  '/index.html',
  '/app.js',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
  'https://cdn.jsdelivr.net/npm/lucide@0.344.0/dist/umd/lucide.min.js'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (url.pathname.startsWith('/api/')) {
    e.respondWith(
      fetch(e.request).catch(() => {
        return new Response(JSON.stringify({ 
          offline: true, 
          message: 'Estás sin conexión. Los datos se guardarán y sincronizarán luego.' 
        }), { headers: { 'Content-Type': 'application/json' } });
      })
    );
  } else {
    e.respondWith(
      caches.match(e.request).then((cachedResponse) => {
        if (cachedResponse) {
          fetch(e.request).then((networkResponse) => {
            if (networkResponse.status === 200) {
              caches.open(CACHE_NAME).then((cache) => cache.put(e.request, networkResponse));
            }
          }).catch(() => {});
          return cachedResponse;
        }
        return fetch(e.request);
      })
    );
  }
});
''')

# 6. public/app.js
with open("toshinori-pwa/public/app.js", "w", encoding="utf-8") as f:
    f.write('''document.addEventListener("DOMContentLoaded", () => {
  // Inicializar iconos Lucide
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
  
  // URL de la API de producción en Cloudflare Workers
  // NOTA: Reemplazar esta URL con la tuya después de ejecutar 'npx wrangler deploy'
  const API_URL = "https://toshinori-morimoto-api.tu-subdominio.workers.dev";

  // Control de menú móvil
  const mobileMenuBtn = document.getElementById("mobile-menu-btn");
  const mobileMenu = document.getElementById("mobile-menu");
  const menuIcon = document.getElementById("menu-icon");

  if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener("click", () => {
      mobileMenu.classList.toggle("hidden");
      const isOpen = !mobileMenu.classList.contains("hidden");
      if (menuIcon) {
        menuIcon.setAttribute("data-lucide", isOpen ? "x" : "menu");
        if (typeof lucide !== 'undefined') {
          lucide.createIcons();
        }
      }
    });
  }

  // Detección de red y barra de estado offline
  const connectionStatus = document.getElementById("connection-status");
  const syncStatus = document.getElementById("sync-status");

  function updateOnlineStatus() {
    if (navigator.onLine) {
      if (connectionStatus) connectionStatus.classList.add("hidden");
      syncOfflineQueue();
    } else {
      if (connectionStatus) connectionStatus.classList.remove("hidden");
    }
  }

  window.addEventListener(\'online\', updateOnlineStatus);
  window.addEventListener(\'offline\', updateOnlineStatus);
  updateOnlineStatus();

  // Claves del localStorage para colas de sincronización local
  const OFFLINE_QUEUES = {
    enrollments: "toshinori_offline_enrollments",
    contacts: "toshinori_offline_contacts",
    attendance: "toshinori_offline_attendance"
  };

  function saveOffline(queueKey, data) {
    const queue = JSON.parse(localStorage.getItem(queueKey) || "[]");
    queue.push({ ...data, offline_timestamp: Date.now() });
    localStorage.setItem(queueKey, JSON.stringify(queue));
    showToast("Guardado sin conexión", "Los datos se enviarán cuando haya internet.", "info");
  }

  // Sincronización automática al recuperar la señal
  async function syncOfflineQueue() {
    if (!navigator.onLine) return;

    const enrollments = JSON.parse(localStorage.getItem(OFFLINE_QUEUES.enrollments) || "[]");
    const contacts = JSON.parse(localStorage.getItem(OFFLINE_QUEUES.contacts) || "[]");
    const attendance = JSON.parse(localStorage.getItem(OFFLINE_QUEUES.attendance) || "[]");

    const totalPending = enrollments.length + contacts.length + attendance.length;
    if (totalPending === 0) return;

    if (syncStatus) syncStatus.classList.remove("hidden");

    // Sincronizar pre-inscripciones
    if (enrollments.length > 0) {
      for (const item of enrollments) {
        try {
          await fetch(`${API_URL}/api/enroll`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(item)
          });
        } catch (e) {
          console.error("Error sincronizando inscripción:", e);
        }
      }
      localStorage.removeItem(OFFLINE_QUEUES.enrollments);
    }

    // Sincronizar contactos
    if (contacts.length > 0) {
      for (const item of contacts) {
        try {
          await fetch(`${API_URL}/api/contact`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(item)
          });
        } catch (e) {
          console.error("Error sincronizando contacto:", e);
        }
      }
      localStorage.removeItem(OFFLINE_QUEUES.contacts);
    }

    // Sincronizar asistencias
    if (attendance.length > 0) {
      for (const item of attendance) {
        try {
          await fetch(`${API_URL}/api/attendance`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(item)
          });
        } catch (e) {
          console.error("Error sincronizando asistencia:", e);
        }
      }
      localStorage.removeItem(OFFLINE_QUEUES.attendance);
      renderLocalAttendance();
    }

    showToast("Sincronización completada", `Se han subido ${totalPending} registros pendientes.`, "success");
    if (syncStatus) {
      setTimeout(() => syncStatus.classList.add("hidden"), 1500);
    }
  }

  // Gestión de Formularios
  // 1. Formulario de Pre-inscripción
  const enrollForm = document.getElementById("enroll-form");
  if (enrollForm) {
    enrollForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = {
        student_name: document.getElementById("student_name").value,
        birth_date: document.getElementById("birth_date").value,
        tutor_name: document.getElementById("tutor_name").value,
        tutor_phone: document.getElementById("tutor_phone").value,
        tutor_email: document.getElementById("tutor_email").value || "",
        shift: document.getElementById("shift").value
      };

      if (!navigator.onLine) {
        saveOffline(OFFLINE_QUEUES.enrollments, formData);
        enrollForm.reset();
        return;
      }

      try {
        const res = await fetch(`${API_URL}/api/enroll`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(formData)
        });
        const data = await res.json();
        if (res.ok) {
          showToast("¡Éxito!", "La pre-inscripción ha sido enviada con éxito.", "success");
          enrollForm.reset();
        } else {
          showToast("Error", data.error || "No se pudo procesar la solicitud.", "error");
        }
      } catch (err) {
        saveOffline(OFFLINE_QUEUES.enrollments, formData);
        enrollForm.reset();
      }
    });
  }

  // 2. Formulario de Contacto
  const contactForm = document.getElementById("contact-form");
  if (contactForm) {
    contactForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = {
        name: document.getElementById("contact_name").value,
        phone: document.getElementById("contact_phone").value,
        email: document.getElementById("contact_email").value || "",
        message: document.getElementById("contact_message").value
      };

      if (!navigator.onLine) {
        saveOffline(OFFLINE_QUEUES.contacts, formData);
        contactForm.reset();
        return;
      }

      try {
        const res = await fetch(`${API_URL}/api/contact`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(formData)
        });
        const data = await res.json();
        if (res.ok) {
          showToast("Mensaje enviado", "Nos pondremos en contacto contigo pronto.", "success");
          contactForm.reset();
        } else {
          showToast("Error", data.error || "No se pudo enviar el mensaje.", "error");
        }
      } catch (err) {
        saveOffline(OFFLINE_QUEUES.contacts, formData);
        contactForm.reset();
      }
    });
  }

  // 3. Formulario de Control de Asistencias (Docentes)
  const attendanceForm = document.getElementById("attendance-form");
  if (attendanceForm) {
    attendanceForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = {
        meeting_type: document.getElementById("meeting_type").value,
        date_checked: document.getElementById("date_checked").value,
        tutor_name: document.getElementById("tutor_name_att").value,
        student_name: document.getElementById("student_name_att").value
      };

      // Guardar localmente para renderizarlo en la tabla
      saveLocalAttendance(formData);

      if (!navigator.onLine) {
        saveOffline(OFFLINE_QUEUES.attendance, formData);
        attendanceForm.reset();
        renderLocalAttendance();
        return;
      }

      try {
        const res = await fetch(`${API_URL}/api/attendance`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(formData)
        });
        const data = await res.json();
        if (res.ok) {
          showToast("Asistencia guardada", "Se ha registrado la asistencia en el servidor.", "success");
          attendanceForm.reset();
        } else {
          showToast("Error", data.error || "No se pudo registrar en la base de datos.", "error");
        }
      } catch (err) {
        saveOffline(OFFLINE_QUEUES.attendance, formData);
        attendanceForm.reset();
      }
      renderLocalAttendance();
    });
  }

  // Guardar asistencias localmente para visualización en el dispositivo
  function saveLocalAttendance(data) {
    const list = JSON.parse(localStorage.getItem("toshinori_local_attendance_list") || "[]");
    list.unshift({ ...data, id: Date.now(), synced: navigator.onLine });
    localStorage.setItem("toshinori_local_attendance_list", JSON.stringify(list));
  }

  function renderLocalAttendance() {
    const list = JSON.parse(localStorage.getItem("toshinori_local_attendance_list") || "[]");
    const tbody = document.getElementById("attendance-tbody");
    if (!tbody) return;

    if (list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="px-6 py-4 text-center text-gray-500 text-sm">No hay asistencias registradas localmente en esta sesión.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(item => `
      <tr class="hover:bg-gray-50 border-b border-gray-200">
        <td class="px-6 py-4 text-sm font-medium text-gray-900">${escapeHtml(item.meeting_type)}</td>
        <td class="px-6 py-4 text-sm text-gray-500">${escapeHtml(item.date_checked)}</td>
        <td class="px-6 py-4 text-sm text-gray-900 font-semibold">${escapeHtml(item.tutor_name)}</td>
        <td class="px-6 py-4 text-sm text-gray-500">${escapeHtml(item.student_name)}</td>
        <td class="px-6 py-4 text-sm text-center">
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${item.synced ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}">
            ${item.synced ? 'Sincronizado' : 'Pendiente (Offline)'}
          </span>
        </td>
      </tr>
    `).join('');
  }

  renderLocalAttendance();

  // Función auxiliar de escape HTML para seguridad contra XSS
  function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  // Sistema de Toasts (Notificaciones flotantes)
  function showToast(title, message, type = "success") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `p-4 mb-3 rounded-lg shadow-lg border-l-4 transition-all duration-300 transform translate-y-2 opacity-0 flex items-start gap-3 w-80 md:w-96 ${
      type === "success" ? "bg-white border-green-500 text-gray-800" :
      type === "error" ? "bg-white border-red-500 text-gray-800" :
      "bg-white border-amber-500 text-gray-800"
    }`;

    const icon = type === "success" ? "check-circle" : type === "error" ? "alert-triangle" : "info";
    const iconColor = type === "success" ? "text-green-500" : type === "error" ? "text-red-500" : "text-amber-500";

    toast.innerHTML = `
      <div class="${iconColor} mt-0.5"><i data-lucide="${icon}"></i></div>
      <div class="flex-1">
        <h4 class="text-sm font-bold text-gray-900">${title}</h4>
        <p class="text-xs text-gray-500 mt-1">${message}</p>
      </div>
    `;

    container.appendChild(toast);
    if (typeof lucide !== 'undefined') {
      lucide.createIcons({ attrs: { class: 'w-5 h-5' } });
    }

    // Animación de entrada
    setTimeout(() => {
      toast.classList.remove("opacity-0", "translate-y-2");
    }, 10);

    // Salida automática
    setTimeout(() => {
      toast.classList.add("opacity-0", "translate-y-2");
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
});
''')

# 7. public/index.html
with open("toshinori-pwa/public/index.html", "w", encoding="utf-8") as f:
    f.write('''<!DOCTYPE html>
<html lang="es" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Centro Privado Toshinori Morimoto - Baney</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#e11d48">
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
        }
        h1, h2, h3, h4, .font-display {
            font-family: 'Nunito', sans-serif;
        }
    </style>
</head>
<body class="bg-gray-50 text-gray-800 overflow-x-hidden">

    <!-- Toast Container para notificaciones -->
    <div id="toast-container" class="fixed bottom-5 right-5 z-50 flex flex-col items-end"></div>

    <!-- Barra de Estado Offline -->
    <div id="connection-status" class="hidden bg-amber-500 text-white text-xs font-semibold py-2 px-4 text-center sticky top-0 z-50 flex items-center justify-center gap-2">
        <i data-lucide="wifi-off" class="w-4 h-4"></i>
        <span>Estás navegando sin conexión. Los datos del formulario se guardarán localmente y se sincronizarán al recuperar internet.</span>
    </div>

    <!-- Barra de Sincronización activa -->
    <div id="sync-status" class="hidden bg-emerald-600 text-white text-xs font-semibold py-2 px-4 text-center sticky top-0 z-50 flex items-center justify-center gap-2">
        <i data-lucide="refresh-cw" class="w-4 h-4 animate-spin"></i>
        <span>Sincronizando registros guardados con el servidor de Cloudflare...</span>
    </div>

    <!-- HEADER & NAVEGACIÓN -->
    <header class="bg-white shadow-md sticky top-0 z-40">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-20">
                <!-- Logotipo -->
                <div class="flex items-center gap-3">
                    <div class="bg-rose-600 text-white p-2.5 rounded-xl shadow-md">
                        <i data-lucide="graduation-cap" class="w-8 h-8"></i>
                    </div>
                    <div>
                        <span class="text-xl md:text-2xl font-extrabold text-rose-600 block leading-tight tracking-tight">TOSHINORI MORIMOTO</span>
                        <span class="text-xs text-gray-500 font-medium tracking-widest block uppercase">Centro Privado - Baney</span>
                    </div>
                </div>

                <!-- Menú Escritorio -->
                <nav class="hidden lg:flex items-center gap-6">
                    <a href="#inicio" class="text-gray-600 hover:text-rose-600 font-semibold text-sm transition-colors">Inicio</a>
                    <a href="#quienes-somos" class="text-gray-600 hover:text-rose-600 font-semibold text-sm transition-colors">Quiénes Somos</a>
                    <a href="#pedagogia" class="text-gray-600 hover:text-rose-600 font-semibold text-sm transition-colors">Pedagogía</a>
                    <a href="#admisiones" class="text-gray-600 hover:text-rose-600 font-semibold text-sm transition-colors">Admisiones y Costos</a>
                    <a href="#asistencias" class="text-gray-600 hover:text-rose-600 font-semibold text-sm transition-colors">Control de Firmas</a>
                    <a href="#sala-ordenadores" class="text-gray-600 hover:text-rose-600 font-semibold text-sm transition-colors">Sala de Ordenadores</a>
                    <a href="#contacto" class="text-gray-600 hover:text-rose-600 font-semibold text-sm transition-colors">Contacto</a>
                    <a href="#admisiones" class="bg-rose-600 text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-md hover:bg-rose-700 transition-colors">Matrículas 2025-2026</a>
                </nav>

                <!-- Botón Menú Móvil -->
                <button id="mobile-menu-btn" class="lg:hidden p-2 text-gray-600 hover:text-rose-600 focus:outline-none">
                    <i id="menu-icon" data-lucide="menu" class="w-7 h-7"></i>
                </button>
            </div>
        </div>

        <!-- Menú Móvil Desplegable -->
        <div id="mobile-menu" class="hidden lg:hidden bg-white border-t border-gray-100 px-4 pt-2 pb-6 space-y-3 shadow-inner">
            <a href="#inicio" class="block text-gray-700 hover:text-rose-600 font-bold py-2">Inicio</a>
            <a href="#quienes-somos" class="block text-gray-700 hover:text-rose-600 font-bold py-2">Quiénes Somos</a>
            <a href="#pedagogia" class="block text-gray-700 hover:text-rose-600 font-bold py-2">Propuesta Pedagógica</a>
            <a href="#admisiones" class="block text-gray-700 hover:text-rose-600 font-bold py-2">Inscripción y Costos</a>
            <a href="#asistencias" class="block text-gray-700 hover:text-rose-600 font-bold py-2">Control de Firmas Docente</a>
            <a href="#sala-ordenadores" class="block text-gray-700 hover:text-rose-600 font-bold py-2">Sala de Ordenadores</a>
            <a href="#contacto" class="block text-gray-700 hover:text-rose-600 font-bold py-2">Contacto</a>
            <a href="#admisiones" class="block bg-rose-600 text-white text-center px-4 py-3 rounded-xl font-bold shadow-md hover:bg-rose-700">Matrículas 2025-2026</a>
        </div>
    </header>

    <!-- SECCIÓN HÉROE (Inicio) -->
    <section id="inicio" class="relative bg-gradient-to-br from-rose-50 to-white py-16 md:py-24 overflow-hidden border-b border-gray-100">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
            <div class="grid lg:grid-cols-12 gap-12 items-center">
                <div class="lg:col-span-7 space-y-6 text-center lg:text-left">
                    <div class="inline-flex items-center gap-2 bg-rose-100 text-rose-700 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider">
                        <i data-lucide="sparkles" class="w-4 h-4"></i>
                        <span>Admisiones Abiertas para Guardería y Preescolar</span>
                    </div>
                    <h1 class="text-4xl md:text-5xl lg:text-6xl font-extrabold text-gray-900 leading-tight">
                        Educación Integral y de Calidad desde la <span class="text-rose-600">Primera Infancia</span>
                    </h1>
                    <p class="text-lg text-gray-600 max-w-2xl mx-auto lg:mx-0">
                        Fundado en el año 2011 en Baney, nuestro propósito principal es garantizar un desarrollo físico, motor, cognitivo, afectivo y social en un ambiente seguro, estructurado y basado en valores sólidos.
                    </p>
                    <div class="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                        <a href="#admisiones" class="bg-rose-600 text-white px-8 py-4 rounded-xl font-bold shadow-lg hover:bg-rose-700 transition-transform hover:-translate-y-0.5 flex items-center justify-center gap-2">
                            <span>Pre-inscribir a mi Hijo</span>
                            <i data-lucide="chevron-right" class="w-5 h-5"></i>
                        </a>
                        <a href="#quienes-somos" class="bg-white border-2 border-rose-200 text-rose-700 px-8 py-4 rounded-xl font-bold hover:bg-rose-50 transition-colors flex items-center justify-center gap-2">
                            <span>Conocer el Centro</span>
                            <i data-lucide="info" class="w-5 h-5"></i>
                        </a>
                    </div>
                </div>
                <div class="lg:col-span-5 relative flex justify-center">
                    <!-- Decoración e Ilustración del Centro -->
                    <div class="relative w-full max-w-md bg-white p-6 rounded-3xl shadow-2xl border border-gray-100">
                        <div class="absolute -top-4 -right-4 bg-amber-400 text-gray-900 p-4 rounded-2xl shadow-lg transform rotate-12">
                            <i data-lucide="heart" class="w-8 h-8 fill-gray-900"></i>
                        </div>
                        <div class="space-y-4">
                            <div class="bg-rose-50 p-4 rounded-2xl flex items-center gap-4">
                                <div class="bg-rose-600 text-white p-2 rounded-xl"><i data-lucide="shield-check" class="w-6 h-6"></i></div>
                                <div>
                                    <h4 class="font-bold text-gray-900 text-sm">Ambiente Confortable y Seguro</h4>
                                    <p class="text-xs text-gray-500">Espacios controlados para niños de 3 meses a 5 años</p>
                                </div>
                            </div>
                            <div class="bg-blue-50 p-4 rounded-2xl flex items-center gap-4">
                                <div class="bg-blue-600 text-white p-2 rounded-xl"><i data-lucide="book-open" class="w-6 h-6"></i></div>
                                <div>
                                    <h4 class="font-bold text-gray-900 text-sm">Metodologías Activas</h4>
                                    <p class="text-xs text-gray-500">Estimulación, juego e inteligencias múltiples</p>
                                </div>
                            </div>
                            <div class="bg-amber-50 p-4 rounded-2xl flex items-center gap-4">
                                <div class="bg-amber-500 text-white p-2 rounded-xl"><i data-lucide="users" class="w-6 h-6"></i></div>
                                <div>
                                    <h4 class="font-bold text-gray-900 text-sm">Comunidad de Padres</h4>
                                    <p class="text-xs text-gray-500">Canales de comunicación directos por WhatsApp</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- SECCIÓN QUIÉNES SOMOS -->
    <section id="quienes-somos" class="py-20 bg-white">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center max-w-3xl mx-auto mb-16 space-y-4">
                <span class="text-rose-600 font-bold uppercase tracking-wider text-xs">Nuestra Identidad</span>
                <h2 class="text-3xl md:text-4xl font-extrabold text-gray-900">Un Centro Referente en Baney</h2>
                <div class="w-24 h-1.5 bg-rose-600 mx-auto rounded-full"></div>
                <p class="text-gray-600">Fundado en el año 2011, contamos con autorización oficial del Ministerio de Educación (Despacho nº 016-017-146) para impartir clases y velar por el desarrollo armónico integral de la infancia.</p>
            </div>

            <!-- Misión y Visión -->
            <div class="grid md:grid-cols-2 gap-8 mb-16">
                <div class="bg-rose-50 p-8 rounded-3xl border border-rose-100 shadow-sm relative overflow-hidden">
                    <div class="absolute -top-10 -right-10 text-rose-100 opacity-50"><i data-lucide="target" class="w-40 h-40"></i></div>
                    <h3 class="text-2xl font-bold text-rose-700 mb-4 flex items-center gap-3">
                        <i data-lucide="target" class="w-7 h-7"></i> Misión Institucional
                    </h3>
                    <p class="text-gray-700 leading-relaxed relative z-10">
                        Brindar una educación integral y de calidad a niños desde la guardería hasta el preescolar, promoviendo el desarrollo armónico de sus capacidades intelectuales, afectivas, físicas y sociales en un ambiente seguro, lúdico y estimulante.
                    </p>
                </div>
                <div class="bg-blue-50 p-8 rounded-3xl border border-blue-100 shadow-sm relative overflow-hidden">
                    <div class="absolute -top-10 -right-10 text-blue-100 opacity-50"><i data-lucide="eye" class="w-40 h-40"></i></div>
                    <h3 class="text-2xl font-bold text-blue-700 mb-4 flex items-center gap-3">
                        <i data-lucide="eye" class="w-7 h-7"></i> Visión Institucional
                    </h3>
                    <p class="text-gray-700 leading-relaxed relative z-10">
                        Ser el centro educativo infantil referente en el Distrito de Baney y en el país, reconocido por su excelencia pedagógica, su enfoque humanista, el respeto a los ritmos individuales de aprendizaje y un fuerte compromiso con los valores éticos y el bienestar de las familias.
                    </p>
                </div>
            </div>

            <!-- 10 Valores Fundacionales -->
            <div class="mb-16">
                <h3 class="text-2xl font-bold text-gray-900 text-center mb-8">Nuestros 10 Valores Institucionales</h3>
                <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
                    <div class="bg-gray-50 p-4 rounded-xl text-center hover:bg-rose-50 hover:border-rose-200 border border-transparent transition-all">
                        <span class="text-rose-600 block text-2xl mb-2">❤️</span>
                        <h4 class="font-bold text-sm text-gray-900">Amor</h4>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-xl text-center hover:bg-rose-50 hover:border-rose-200 border border-transparent transition-all">
                        <span class="text-rose-600 block text-2xl mb-2">🤝</span>
                        <h4 class="font-bold text-sm text-gray-900">Respeto</h4>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-xl text-center hover:bg-rose-50 hover:border-rose-200 border border-transparent transition-all">
                        <span class="text-rose-600 block text-2xl mb-2">⏰</span>
                        <h4 class="font-bold text-sm text-gray-900">Responsabilidad</h4>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-xl text-center hover:bg-rose-50 hover:border-rose-200 border border-transparent transition-all">
                        <span class="text-rose-600 block text-2xl mb-2">🤗</span>
                        <h4 class="font-bold text-sm text-gray-900">Empatía</h4>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-xl text-center hover:bg-rose-50 hover:border-rose-200 border border-transparent transition-all">
                        <span class="text-rose-600 block text-2xl mb-2">✊</span>
                        <h4 class="font-bold text-sm text-gray-900">Perseverancia</h4>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-xl text-center hover:bg-rose-50 hover:border-rose-200 border border-transparent transition-all">
                        <span class="text-rose-600 block text-2xl mb-2">🎗️</span>
                        <h4 class="font-bold text-sm text-gray-900">Solidaridad</h4>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-xl text-center hover:bg-rose-50 hover:border-rose-200 border border-transparent transition-all">
                        <span class="text-rose-600 block text-2xl mb-2">👥</span>
                        <h4 class="font-bold text-sm text-gray-900">Cooperación</h4>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-xl text-center hover:bg-rose-50 hover:border-rose-200 border border-transparent transition-all">
                        <span class="text-rose-600 block text-2xl mb-2">🌱</span>
                        <h4 class="font-bold text-sm text-gray-900">Humildad</h4>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-xl text-center hover:bg-rose-50 hover:border-rose-200 border border-transparent transition-all">
                        <span class="text-rose-600 block text-2xl mb-2">⚖️</span>
                        <h4 class="font-bold text-sm text-gray-900">Disciplina</h4>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-xl text-center hover:bg-rose-50 hover:border-rose-200 border border-transparent transition-all">
                        <span class="text-rose-600 block text-2xl mb-2">🙏</span>
                        <h4 class="font-bold text-sm text-gray-900">Gratitud</h4>
                    </div>
                </div>
            </div>

            <!-- Infraestructura del Centro -->
            <div class="bg-gray-50 rounded-3xl p-8 border border-gray-200">
                <h3 class="text-2xl font-bold text-gray-900 text-center mb-8">Nuestra Infraestructura Segura y Confortable</h3>
                <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    <div class="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 flex items-start gap-4">
                        <div class="bg-rose-100 text-rose-600 p-2.5 rounded-xl"><i data-lucide="door-open" class="w-6 h-6"></i></div>
                        <div>
                            <h4 class="font-bold text-gray-900 text-sm">3 Aulas Amplias</h4>
                            <p class="text-xs text-gray-500 mt-1">Confortables y climatizadas para cada grupo de edad.</p>
                        </div>
                    </div>
                    <div class="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 flex items-start gap-4">
                        <div class="bg-rose-100 text-rose-600 p-2.5 rounded-xl"><i data-lucide="layout" class="w-6 h-6"></i></div>
                        <div>
                            <h4 class="font-bold text-gray-900 text-sm">Salón Multiuso</h4>
                            <p class="text-xs text-gray-500 mt-1">Para psicomotricidad, asambleas y talleres creativos.</p>
                        </div>
                    </div>
                    <div class="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 flex items-start gap-4">
                        <div class="bg-rose-100 text-rose-600 p-2.5 rounded-xl"><i data-lucide="book-open" class="w-6 h-6"></i></div>
                        <div>
                            <h4 class="font-bold text-gray-900 text-sm">Biblioteca y Sala</h4>
                            <p class="text-xs text-gray-500 mt-1">Espacio de lectura guiada y actividades didácticas.</p>
                        </div>
                    </div>
                    <div class="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 flex items-start gap-4">
                        <div class="bg-rose-100 text-rose-600 p-2.5 rounded-xl"><i data-lucide="building-2" class="w-6 h-6"></i></div>
                        <div>
                            <h4 class="font-bold text-gray-900 text-sm">513 m² Totales</h4>
                            <p class="text-xs text-gray-500 mt-1">Incluye oficina de dirección, cantina y planta sótano.</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Estructura Organizativa -->
            <div class="mt-16 text-center">
                <h3 class="text-2xl font-bold text-gray-900 mb-8">Órganos de Gestión y Dirección</h3>
                <div class="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
                    <div class="bg-white p-6 rounded-2xl border border-gray-200 hover:shadow-md transition-shadow">
                        <div class="bg-rose-100 text-rose-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
                            <i data-lucide="user-check" class="w-6 h-6"></i>
                        </div>
                        <h4 class="font-bold text-gray-900">D. Guillermo Noha Boreku</h4>
                        <p class="text-xs text-rose-600 font-semibold tracking-wider uppercase mt-1">Representante Legal / Director</p>
                    </div>
                    <div class="bg-white p-6 rounded-2xl border border-gray-200 hover:shadow-md transition-shadow">
                        <div class="bg-rose-100 text-rose-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
                            <i data-lucide="user" class="w-6 h-6"></i>
                        </div>
                        <h4 class="font-bold text-gray-900">Ruth Boko Bolekia</h4>
                        <p class="text-xs text-rose-600 font-semibold tracking-wider uppercase mt-1">Jefa de Estudios</p>
                    </div>
                    <div class="bg-white p-6 rounded-2xl border border-gray-200 hover:shadow-md transition-shadow">
                        <div class="bg-rose-100 text-rose-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
                            <i data-lucide="file-text" class="w-6 h-6"></i>
                        </div>
                        <h4 class="font-bold text-gray-900">Esperanza Boko Barila</h4>
                        <p class="text-xs text-rose-600 font-semibold tracking-wider uppercase mt-1">Secretaria del Centro</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- SECCIÓN PROPUESTA PEDAGÓGICA -->
    <section id="pedagogia" class="py-20 bg-gray-50 border-t border-b border-gray-100">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center max-w-3xl mx-auto mb-16 space-y-4">
                <span class="text-rose-600 font-bold uppercase tracking-wider text-xs">Aprender Jugando</span>
                <h2 class="text-3xl md:text-4xl font-extrabold text-gray-900">Nuestra Metodología Pedagógica</h2>
                <div class="w-24 h-1.5 bg-rose-600 mx-auto rounded-full"></div>
                <p class="text-gray-600">Consideramos el nivel inicial como el punto de partida del proceso formativo, sustentado en principios de aprendizaje activo y seguridad afectiva.</p>
            </div>

            <!-- Principios Pedagógicos -->
            <div class="grid md:grid-cols-3 lg:grid-cols-5 gap-6">
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-200 space-y-3">
                    <span class="text-3xl">🧸</span>
                    <h4 class="font-bold text-gray-900 text-sm">Método Lúdico</h4>
                    <p class="text-xs text-gray-500 leading-relaxed">El juego como la herramienta central y natural de aprendizaje.</p>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-200 space-y-3">
                    <span class="text-3xl">⏳</span>
                    <h4 class="font-bold text-gray-900 text-sm">Respeto al Ritmo</h4>
                    <p class="text-xs text-gray-500 leading-relaxed">Cada niño tiene un proceso de desarrollo único que el centro adapta.</p>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-200 space-y-3">
                    <span class="text-3xl">❤️</span>
                    <h4 class="font-bold text-gray-900 text-sm">Educación Emocional</h4>
                    <p class="text-xs text-gray-500 leading-relaxed">Fomento de habilidades sociales: cooperar, empatizar y resolver conflictos.</p>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-200 space-y-3">
                    <span class="text-3xl">🛡️</span>
                    <h4 class="font-bold text-gray-900 text-sm">Seguridad y Bienestar</h4>
                    <p class="text-xs text-gray-500 leading-relaxed">Entorno seguro que garantiza protección física, afecto y estabilidad.</p>
                </div>
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-200 space-y-3">
                    <span class="text-3xl">👪</span>
                    <h4 class="font-bold text-gray-900 text-sm">Colaboración Familiar</h4>
                    <p class="text-xs text-gray-500 leading-relaxed">Comunicación y participación constante con las familias.</p>
                </div>
            </div>

            <!-- Áreas de Desarrollo y Objetivos -->
            <div class="grid lg:grid-cols-2 gap-12 mt-16 items-center">
                <div class="space-y-6">
                    <h3 class="text-2xl font-bold text-gray-900">Seis Áreas Principales de Desarrollo</h3>
                    <p class="text-sm text-gray-600">Organizamos nuestra acción educativa diaria para estimular de manera equilibrada todas las capacidades:</p>
                    <ul class="space-y-3 text-sm text-gray-700">
                        <li class="flex items-center gap-3">
                            <span class="w-2.5 h-2.5 bg-rose-600 rounded-full"></span>
                            <span><strong>Desarrollo Personal y Social:</strong> Autonomía, hábitos de higiene y convivencia diaria.</span>
                        </li>
                        <li class="flex items-center gap-3">
                            <span class="w-2.5 h-2.5 bg-rose-600 rounded-full"></span>
                            <span><strong>Lenguaje y Comunicación:</strong> Cuentos, expresión verbal e identificación de imágenes.</span>
                        </li>
                        <li class="flex items-center gap-3">
                            <span class="w-2.5 h-2.5 bg-rose-600 rounded-full"></span>
                            <span><strong>Psicomotricidad:</strong> Motricidad gruesa (saltar, correr) y fina (ensartar, plastilina).</span>
                        </li>
                        <li class="flex items-center gap-3">
                            <span class="w-2.5 h-2.5 bg-rose-600 rounded-full"></span>
                            <span><strong>Expresión Artística:</strong> Pintura, recortes, dramatización y teatro infantil.</span>
                        </li>
                        <li class="flex items-center gap-3">
                            <span class="w-2.5 h-2.5 bg-rose-600 rounded-full"></span>
                            <span><strong>Exploración del Entorno:</strong> Observación de la naturaleza, climas y colores.</span>
                        </li>
                        <li class="flex items-center gap-3">
                            <span class="w-2.5 h-2.5 bg-rose-600 rounded-full"></span>
                            <span><strong>Pensamiento Lógico Inicial:</strong> Clasificación, seriación, formas y tamaños.</span>
                        </li>
                    </ul>
                </div>
                <div class="bg-white p-8 rounded-3xl border border-gray-200">
                    <h3 class="text-xl font-bold text-gray-900 mb-6 text-center">Calendario Escolar Clave 2025–2026</h3>
                    <div class="space-y-4 text-xs md:text-sm">
                        <div class="flex justify-between border-b border-gray-100 pb-2">
                            <span class="font-semibold text-gray-800">1 de Septiembre</span>
                            <span class="text-rose-600 font-bold">Comienzo oficial del curso</span>
                        </div>
                        <div class="flex justify-between border-b border-gray-100 pb-2">
                            <span class="font-semibold text-gray-800">15 de Septiembre</span>
                            <span class="text-rose-600 font-bold">Inicio de clases presenciales</span>
                        </div>
                        <div class="flex justify-between border-b border-gray-100 pb-2">
                            <span class="font-semibold text-gray-800">21 de Noviembre</span>
                            <span class="text-rose-600 font-bold">1ª Reunión con Padres y Tutores</span>
                        </div>
                        <div class="flex justify-between border-b border-gray-100 pb-2">
                            <span class="font-semibold text-gray-800">19 de Diciembre</span>
                            <span class="text-rose-600 font-bold">Entrega de Boletines de Progreso</span>
                        </div>
                        <div class="flex justify-between border-b border-gray-100 pb-2">
                            <span class="font-semibold text-gray-800">8 de Enero</span>
                            <span class="text-rose-600 font-bold">Inicio del Segundo Trimestre</span>
                        </div>
                        <div class="flex justify-between border-b border-gray-100 pb-2">
                            <span class="font-semibold text-gray-800">6 de Marzo</span>
                            <span class="text-rose-600 font-bold">2ª Reunión con Padres y Tutores</span>
                        </div>
                        <div class="flex justify-between pb-2">
                            <span class="font-semibold text-gray-800">30 de Junio</span>
                            <span class="text-rose-600 font-bold">Entrega final y Clausura del Curso</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- SECCIÓN ADMISIONES, COSTOS Y NORMAS -->
    <section id="admisiones" class="py-20 bg-white">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center max-w-3xl mx-auto mb-16 space-y-4">
                <span class="text-rose-600 font-bold uppercase tracking-wider text-xs">Transparencia</span>
                <h2 class="text-3xl md:text-4xl font-extrabold text-gray-900">Admisiones, Tarifas y Normativa</h2>
                <div class="w-24 h-1.5 bg-rose-600 mx-auto rounded-full"></div>
            </div>

            <div class="grid lg:grid-cols-3 gap-8 mb-16">
                <!-- Requisitos de Inscripción -->
                <div class="bg-gray-50 p-6 rounded-3xl border border-gray-200">
                    <h3 class="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                        <i data-lucide="file-check-2" class="text-rose-600 w-6 h-6"></i> Requisitos
                    </h3>
                    <ul class="space-y-4 text-sm text-gray-700">
                        <li class="flex items-start gap-3">
                            <span class="text-rose-600 font-bold mt-0.5">✓</span>
                            <span>Fotocopia completa del certificado de nacimiento del menor.</span>
                        </li>
                        <li class="flex items-start gap-3">
                            <span class="text-rose-600 font-bold mt-0.5">✓</span>
                            <span>1 fotografía en color del alumno, tamaño carnet.</span>
                        </li>
                        <li class="flex items-start gap-3">
                            <span class="text-rose-600 font-bold mt-0.5">✓</span>
                            <span>Fotocopia del Documento de Identidad del tutor legal.</span>
                        </li>
                        <li class="flex items-start gap-3">
                            <span class="text-rose-600 font-bold mt-0.5">✓</span>
                            <span>Pago del 50% de la matrícula anual como depósito inicial.</span>
                        </li>
                    </ul>
                    <div class="mt-8 bg-white p-4 rounded-2xl border border-rose-100 text-xs text-rose-700">
                        <strong>Nota importante:</strong> La inscripción formal del estudiante solo se considera efectiva al completar estos requisitos ante la secretaría.
                    </div>
                </div>

                <!-- Tarifas y Turnos -->
                <div class="bg-rose-50/50 p-6 rounded-3xl border border-rose-100">
                    <h3 class="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                        <i data-lucide="wallet" class="text-rose-600 w-6 h-6"></i> Tarifas Oficiales
                    </h3>
                    <div class="space-y-4">
                        <div class="bg-white p-4 rounded-xl flex justify-between items-center shadow-sm">
                            <span class="font-semibold text-gray-700 text-sm">Matrícula Anual</span>
                            <span class="text-rose-600 font-extrabold text-lg">30.000 FCFA</span>
                        </div>
                        <div class="bg-white p-4 rounded-xl flex justify-between items-center shadow-sm">
                            <span class="font-semibold text-gray-700 text-sm">Uniforme Escolar</span>
                            <span class="text-rose-600 font-extrabold text-lg">8.000 FCFA</span>
                        </div>
                    </div>
                    <h4 class="font-bold text-gray-900 text-sm mt-6 mb-3">Turnos y Mensualidades:</h4>
                    <div class="space-y-2 text-xs md:text-sm">
                        <div class="flex justify-between border-b border-rose-100/50 pb-2">
                            <span>Turno Mañana (08:00H - 13:00H)</span>
                            <span class="font-bold text-gray-900">30.000 XAF/mes</span>
                        </div>
                        <div class="flex justify-between border-b border-rose-100/50 pb-2">
                            <span>Turno Tarde (13:00H - 18:00H)</span>
                            <span class="font-bold text-gray-900">30.000 XAF/mes</span>
                        </div>
                        <div class="flex justify-between pb-2">
                            <span>Turno Completo (08:00H - 18:00H)</span>
                            <span class="font-bold text-gray-900">60.000 XAF/mes</span>
                        </div>
                    </div>
                </div>

                <!-- Horarios y Normativas -->
                <div class="bg-gray-50 p-6 rounded-3xl border border-gray-200 space-y-4 text-sm text-gray-700">
                    <h3 class="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
                        <i data-lucide="clock" class="text-rose-600 w-6 h-6"></i> Horarios y Normas
                    </h3>
                    <p><strong>Puntualidad:</strong> Apertura de puertas a las 07:45H. Formación a las 08:00H e inicio formal de clases a las 08:15H.</p>
                    <p><strong>Recogida de niños:</strong> De 13:00H a 17:00H. Para garantizar el bienestar y la seguridad, se aplicará una <strong>multa de 1.000 FCFA</strong> por recogida tardía.</p>
                    <p><strong>Alimentación:</strong> Promovemos meriendas saludables. Queda estrictamente <strong>prohibida la comida chatarra, dulces, refrescos o golosinas</strong> en las instalaciones.</p>
                    <p><strong>Uniforme:</strong> De lunes a jueves, uniforme oficial completo. Los viernes se asiste con el uniforme deportivo color rojo.</p>
                </div>
            </div>

            <!-- Formulario de Inscripción Virtual -->
            <div id="formulario-registro" class="bg-white rounded-3xl p-8 border border-gray-200 shadow-xl max-w-3xl mx-auto">
                <div class="text-center mb-8">
                    <h3 class="text-2xl font-bold text-gray-900">Formulario de Pre-inscripción en Línea</h3>
                    <p class="text-xs text-gray-500 mt-1">Completa los datos del menor y del tutor legal para reservar tu vacante en el centro.</p>
                </div>
                <form id="enroll-form" class="space-y-6">
                    <div class="grid md:grid-cols-2 gap-6">
                        <div>
                            <label class="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Nombre Completo del Niño/a *</label>
                            <input type="text" id="student_name" required placeholder="Ej. Guillermo Noha" class="w-full px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-rose-500 text-sm">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Fecha de Nacimiento *</label>
                            <input type="date" id="birth_date" required class="w-full px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-rose-500 text-sm">
                        </div>
                    </div>
                    <div class="grid md:grid-cols-2 gap-6">
                        <div>
                            <label class="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Nombre del Tutor Legal *</label>
                            <input type="text" id="tutor_name" required placeholder="Nombre y Apellidos" class="w-full px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-rose-500 text-sm">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Teléfono de Contacto *</label>
                            <input type="tel" id="tutor_phone" required placeholder="Ej. 222 298 863" class="w-full px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-rose-500 text-sm">
                        </div>
                    </div>
                    <div class="grid md:grid-cols-2 gap-6">
                        <div>
                            <label class="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Correo Electrónico (Opcional)</label>
                            <input type="email" id="tutor_email" placeholder="ejemplo@gmail.com" class="w-full px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-rose-500 text-sm">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Turno Escolar Solicitado *</label>
                            <select id="shift" required class="w-full px-4 py-3 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-rose-500 text-sm">
                                <option value="mañana">Turno Mañana (30.000 FCFA/mes)</option>
                                <option value="tarde">Turno Tarde (30.000 FCFA/mes)</option>
                                <option value="completo">Turno Completo (60.000 FCFA/mes)</option>
                            </select>
                        </div>
                    </div>
                    <div class="text-center">
                        <button type="submit" class="w-full md:w-auto bg-rose-600 text-white px-10 py-4 rounded-xl font-bold shadow-lg hover:bg-rose-700 transition-colors flex items-center justify-center gap-2 mx-auto">
                            <i data-lucide="send" class="w-5 h-5"></i>
                            <span>Enviar Pre-inscripción</span>
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </section>

    <!-- SECCIÓN CONTROL DE FIRMAS Y ASISTENCIAS -->
    <section id="asistencias" class="py-20 bg-gray-50 border-t border-b border-gray-100">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="text-center max-w-3xl mx-auto mb-16 space-y-4">
                <span class="text-rose-600 font-bold uppercase tracking-wider text-xs">Gestión Interna</span>
                <h2 class="text-3xl md:text-4xl font-extrabold text-gray-900">Control de Firmas y Reuniones</h2>
                <div class="w-24 h-1.5 bg-rose-600 mx-auto rounded-full"></div>
                <p class="text-gray-600">Portal digitalizado para el control de asistencia de tutores a las reuniones informativas trimestrales y entregas de boletines escolares.</p>
            </div>

            <div class="grid lg:grid-cols-12 gap-8 items-start">
                <!-- Formulario Docente -->
                <div class="lg:col-span-4 bg-white p-6 rounded-3xl border border-gray-200 shadow-sm space-y-6">
                    <h3 class="text-lg font-bold text-gray-900">Registrar Nueva Firma</h3>
                    <form id="attendance-form" class="space-y-4">
                        <div>
                            <label class="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Evento / Reunión *</label>
                            <select id="meeting_type" required class="w-full px-4 py-2.5 rounded-xl border border-gray-300 text-xs">
                                <option value="1a Reunión">1ª Reunión General (Padres)</option>
                                <option value="1a Evaluación">1ª Evaluación (Entrega Boletines)</option>
                                <option value="2a Reunión">2ª Reunión General (Padres)</option>
                                <option value="2a Evaluación">2ª Evaluación (Entrega Boletines)</option>
                                <option value="3a Reunión">3ª Reunión General (Padres)</option>
                                <option value="Evaluación Final">Evaluación Final (Clausura)</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Fecha del Evento *</label>
                            <input type="date" id="date_checked" required class="w-full px-4 py-2.5 rounded-xl border border-gray-300 text-xs">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Nombre del Tutor *</label>
                            <input type="text" id="tutor_name_att" required placeholder="Firma de Tutor" class="w-full px-4 py-2.5 rounded-xl border border-gray-300 text-xs">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">Nombre del Estudiante *</label>
                            <input type="text" id="student_name_att" required placeholder="Nombre del Menor" class="w-full px-4 py-2.5 rounded-xl border border-gray-300 text-xs">
                        </div>
                        <button type="submit" class="w-full bg-rose-600 text-white py-3 rounded-xl font-bold text-xs shadow-md hover:bg-rose-700 flex items-center justify-center gap-2">
                            <i data-lucide="edit-3" class="w-4 h-4"></i>
                            <span>Firmar y Registrar</span>
                        </button>
                    </form>
                </div>

                <!-- Tabla de Registros -->
                <div class="lg:col-span-8 bg-white rounded-3xl border border-gray-200 shadow-sm overflow-hidden">
                    <div class="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                        <h3 class="text-lg font-bold text-gray-900">Historial Local de Asistencia</h3>
                        <span class="text-xs text-gray-500 font-medium">Registrado en este dispositivo</span>
                    </div>
                    <div class="overflow-x-auto">
                        <table class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Reunión</th>
                                    <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Fecha</th>
                                    <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Tutor</th>
                                    <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Alumno</th>
                                    <th class="px-6 py-3 text-center text-xs font-bold text-gray-500 uppercase tracking-wider">Estado</th>
                                </tr>
                            </thead>
                            <tbody id="attendance-tbody" class="bg-white divide-y divide-gray-200">
                                <!-- Renderizado dinámico desde app.js -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- SECCIÓN SADA DE ORDENADORES -->
    <section id="sala-ordenadores" class="py-20 bg-white">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="grid lg:grid-cols-2 gap-12 items-center">
                <div class="space-y-6">
                    <div class="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider">
                        <i data-lucide="monitor" class="w-4 h-4"></i>
                        <span>Proyecto de Expansión Tecnológica</span>
                    </div>
                    <h2 class="text-3xl md:text-4xl font-extrabold text-gray-900">Próximamente: Sala de Ordenadores en Baney</h2>
                    <p class="text-gray-600">
                        Con el objetivo de promover la educación tecnológica y reducir la brecha digital en nuestra comunidad, el Centro Privado Toshinori Morimoto está diseñando una sala de informática de última generación.
                    </p>
                    <p class="text-gray-600">
                        Este espacio ofrecerá cursos, talleres y seminarios adaptados para un amplio grupo de edad (desde los 12 hasta los 65 años), facilitando la transferencia de habilidades en el manejo de equipos y softwares indispensables para el desarrollo laboral actual.
                    </p>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-gray-50 p-4 rounded-xl border border-gray-100">
                            <span class="text-rose-600 font-extrabold text-xl">12 - 65 años</span>
                            <span class="text-xs text-gray-500 block mt-1">Rango de edad beneficiaria</span>
                        </div>
                        <div class="bg-gray-50 p-4 rounded-xl border border-gray-100">
                            <span class="text-rose-600 font-extrabold text-xl">100% Práctico</span>
                            <span class="text-xs text-gray-500 block mt-1">Orientación profesional</span>
                        </div>
                    </div>
                </div>
                <!-- Pre-registro de Interés -->
                <div class="bg-gradient-to-br from-gray-900 to-rose-950 text-white p-8 rounded-3xl shadow-2xl space-y-6 relative overflow-hidden">
                    <div class="absolute -bottom-10 -right-10 text-white opacity-5"><i data-lucide="monitor" class="w-60 h-60"></i></div>
                    <div class="text-center relative z-10">
                        <h3 class="text-2xl font-bold">Reserva tu Plaza</h3>
                        <p class="text-xs text-rose-200 mt-1">Regístrate de forma preferencial para recibir notificaciones sobre el inicio de los cursos tecnológicos.</p>
                    </div>
                    <!-- Formulario Simplificado -->
                    <form id="tech-interest-form" class="space-y-4 relative z-10">
                        <div class="grid sm:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-[10px] font-bold text-rose-200 uppercase tracking-wider mb-1.5">Nombre Completo *</label>
                                <input type="text" required placeholder="Ej. Antonio Nsue" class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-2.5 text-xs text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-rose-500">
                            </div>
                            <div>
                                <label class="block text-[10px] font-bold text-rose-200 uppercase tracking-wider mb-1.5">Edad *</label>
                                <input type="number" required min="12" max="65" placeholder="Ej. 25" class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-2.5 text-xs text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-rose-500">
                            </div>
                        </div>
                        <div class="grid sm:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-[10px] font-bold text-rose-200 uppercase tracking-wider mb-1.5">Teléfono *</label>
                                <input type="tel" required placeholder="Ej. 222 197 328" class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-2.5 text-xs text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-rose-500">
                            </div>
                            <div>
                                <label class="block text-[10px] font-bold text-rose-200 uppercase tracking-wider mb-1.5">Nivel de Informática *</label>
                                <select class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:ring-2 focus:ring-rose-500">
                                    <option value="basico" class="text-gray-900">Principiante (Desde Cero)</option>
                                    <option value="medio" class="text-gray-900">Intermedio (Uso Básico)</option>
                                    <option value="avanzado" class="text-gray-900">Avanzado (Ofimática / Redes)</option>
                                </select>
                            </div>
                        </div>
                        <button type="submit" class="w-full bg-rose-600 text-white font-bold text-xs py-3 rounded-xl shadow-lg hover:bg-rose-700 transition-colors">Solicitar Información Preferente</button>
                    </form>
                </div>
            </div>
        </div>
    </section>

    <!-- SECCIÓN CONTACTO Y UBICACIÓN -->
    <section id="contacto" class="py-20 bg-gray-50 border-t border-gray-200">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="grid lg:grid-cols-12 gap-12 items-start">
                <!-- Información de Contacto -->
                <div class="lg:col-span-5 space-y-8">
                    <div class="space-y-3">
                        <span class="text-rose-600 font-bold uppercase tracking-wider text-xs">Comunicación Directa</span>
                        <h2 class="text-3xl font-extrabold text-gray-900">Estemos en Contacto</h2>
                        <p class="text-sm text-gray-600">Para consultas administrativas, visitas escolares o admisiones de alumnos, puedes comunicarte directamente con nosotros.</p>
                    </div>

                    <div class="space-y-4">
                        <div class="flex items-start gap-4">
                            <div class="bg-rose-100 text-rose-600 p-2.5 rounded-xl"><i data-lucide="map-pin" class="w-5 h-5"></i></div>
                            <div>
                                <h4 class="font-bold text-gray-900 text-sm">Ubicación Física</h4>
                                <p class="text-xs text-gray-500 mt-1">Av. de la Independencia, s/n, Distrito de Baney, Guinea Ecuatorial (Zona Baja C-1, en las inmediaciones de la comisaría policial municipal).</p>
                            </div>
                        </div>
                        <div class="flex items-start gap-4">
                            <div class="bg-rose-100 text-rose-600 p-2.5 rounded-xl"><i data-lucide="phone" class="w-5 h-5"></i></div>
                            <div>
                                <h4 class="font-bold text-gray-900 text-sm">Teléfonos de Atención</h4>
                                <p class="text-xs text-gray-500 mt-1">222 298 863 / 222 197 328</p>
                            </div>
                        </div>
                        <div class="flex items-start gap-4">
                            <div class="bg-rose-100 text-rose-600 p-2.5 rounded-xl"><i data-lucide="mail" class="w-5 h-5"></i></div>
                            <div>
                                <h4 class="font-bold text-gray-900 text-sm">Correo de Contacto</h4>
                                <p class="text-xs text-gray-500 mt-1">guillermonohanikobara@gmail.com</p>
                            </div>
                        </div>
                        <div class="flex items-start gap-4">
                            <div class="bg-rose-100 text-rose-600 p-2.5 rounded-xl"><i data-lucide="bell" class="w-5 h-5"></i></div>
                            <div>
                                <h4 class="font-bold text-gray-900 text-sm">Canal de Avisos</h4>
                                <p class="text-xs text-gray-500 mt-1">Grupo Informativo Automatizado por WhatsApp para padres de familia registrados.</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Formulario de Mensajes -->
                <div class="lg:col-span-7 bg-white p-8 rounded-3xl border border-gray-200 shadow-lg">
                    <h3 class="text-xl font-bold text-gray-900 mb-6">Escríbenos un Mensaje</h3>
                    <form id="contact-form" class="space-y-4">
                        <div class="grid sm:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1.5">Nombre Completo *</label>
                                <input type="text" id="contact_name" required placeholder="Tu Nombre" class="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-rose-500 text-xs">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1.5">Teléfono *</label>
                                <input type="tel" id="contact_phone" required placeholder="Tu Teléfono" class="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-rose-500 text-xs">
                            </div>
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1.5">Correo Electrónico (Opcional)</label>
                            <input type="email" id="contact_email" placeholder="correo@ejemplo.com" class="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-rose-500 text-xs">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1.5">Tu Mensaje *</label>
                            <textarea id="contact_message" required rows="4" placeholder="Escribe aquí tu consulta o sugerencia..." class="w-full px-4 py-2.5 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-rose-500 text-xs"></textarea>
                        </div>
                        <button type="submit" class="w-full bg-rose-600 text-white font-bold text-xs py-3 rounded-xl shadow-md hover:bg-rose-700 transition-colors">Enviar Mensaje</button>
                    </form>
                </div>
            </div>
        </div>
    </section>

    <!-- FOOTER -->
    <footer class="bg-gray-900 text-white py-12">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center md:text-left flex flex-col md:flex-row justify-between items-center gap-6">
            <div class="flex items-center gap-3">
                <div class="bg-rose-600 p-2 rounded-xl text-white">
                    <i data-lucide="graduation-cap" class="w-6 h-6"></i>
                </div>
                <div>
                    <span class="text-sm font-extrabold text-rose-500 block leading-tight uppercase tracking-wide">Toshinori Morimoto</span>
                    <span class="text-[10px] text-gray-400 font-medium block">Centro Privado de Educación Infantil</span>
                </div>
            </div>
            <div class="text-center md:text-right text-xs text-gray-400 space-y-2">
                <p>Ubicación: Av. de la Independencia, s/n, Baney, Guinea Ecuatorial</p>
                <p>Registro Ministerial: Despacho nº 016-017-146 (Dirección General de Planificación Educativa)</p>
                <p>Derechos Reservados © 2026 Centro Privado Toshinori Morimoto.</p>
            </div>
        </div>
    </footer>

    <!-- Lucide Icons CDN -->
    <script src="https://cdn.jsdelivr.net/npm/lucide@0.344.0/dist/umd/lucide.min.js"></script>
    <script src="/app.js"></script>
</body>
</html>
''')

# Ejecutar generación
print("Archivos generados exitosamente en la carpeta 'toshinori-pwa'.")
