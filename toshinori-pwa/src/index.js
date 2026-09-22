// ============================================================
// Utilidades generales
// ============================================================

function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function jsonResponse(obj, status, headers) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...headers, "Content-Type": "application/json" }
  });
}

// CORS público: usado por los endpoints que el formulario del sitio llama
// directamente (enroll, contact, attendance). Abierto porque no exponen
// datos de terceros, solo reciben envíos.
function publicCorsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

// CORS del panel de administración: restringido al dominio real del sitio,
// nunca "*", porque estos endpoints devuelven datos personales de familias.
function adminCorsHeaders(env) {
  return {
    "Access-Control-Allow-Origin": env.ADMIN_ALLOWED_ORIGIN || "https://toshinori-morimoto.grandfrend-media.workers.dev",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Vary": "Origin"
  };
}

// Comparación en tiempo constante (mitiga ataques de temporización).
function timingSafeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string") return false;
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return result === 0;
}

// ============================================================
// Correo (Resend)
// ============================================================

async function sendEmail(env, { to, subject, html, replyTo }) {
  if (!env.RESEND_API_KEY) {
    return { sent: false, reason: "RESEND_API_KEY no configurada" };
  }
  if (!to) {
    return { sent: false, reason: "Sin destinatario" };
  }

  const fromEmail = env.FROM_EMAIL || "Centro Toshinori Morimoto <notificaciones@toshinorimorimoto.org>";

  try {
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.RESEND_API_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        from: fromEmail,
        to: Array.isArray(to) ? to : [to],
        reply_to: replyTo || undefined,
        subject,
        html
      })
    });

    if (!res.ok) {
      const errText = await res.text();
      return { sent: false, reason: errText };
    }
    return { sent: true };
  } catch (err) {
    return { sent: false, reason: err.message };
  }
}

// ============================================================
// Autenticación del panel de administración (JWT minimalista con
// Web Crypto, sin dependencias externas: header.payload.firma HMAC-SHA256)
// ============================================================

function base64UrlEncode(bytes) {
  let binary = "";
  const arr = new Uint8Array(bytes);
  for (let i = 0; i < arr.length; i++) binary += String.fromCharCode(arr[i]);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function base64UrlEncodeStr(str) {
  return base64UrlEncode(new TextEncoder().encode(str));
}

function base64UrlDecodeToStr(b64url) {
  const pad = "===".slice((b64url.length + 3) % 4);
  const b64 = b64url.replace(/-/g, "+").replace(/_/g, "/") + pad;
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return new TextDecoder().decode(bytes);
}

async function hmacSign(data, secret) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(data));
  return base64UrlEncode(sig);
}

const SESSION_DURATION_SECONDS = 8 * 60 * 60; // 8 horas

async function createToken(env) {
  const header = base64UrlEncodeStr(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const now = Math.floor(Date.now() / 1000);
  const exp = now + SESSION_DURATION_SECONDS;
  const payload = base64UrlEncodeStr(JSON.stringify({ role: "admin", iat: now, exp }));
  const signature = await hmacSign(`${header}.${payload}`, env.JWT_SECRET);
  return { token: `${header}.${payload}.${signature}`, expires_at: exp * 1000 };
}

async function verifyToken(request, env) {
  if (!env.JWT_SECRET) return false;
  const auth = request.headers.get("Authorization") || "";
  const match = auth.match(/^Bearer (.+)$/);
  if (!match) return false;

  const parts = match[1].split(".");
  if (parts.length !== 3) return false;
  const [header, payload, signature] = parts;

  const expectedSignature = await hmacSign(`${header}.${payload}`, env.JWT_SECRET);
  if (!timingSafeEqual(expectedSignature, signature)) return false;

  try {
    const data = JSON.parse(base64UrlDecodeToStr(payload));
    if (!data.exp || data.exp < Math.floor(Date.now() / 1000)) return false;
    return true;
  } catch {
    return false;
  }
}

// Máximo de intentos fallidos de login por IP en 15 minutos.
const MAX_LOGIN_ATTEMPTS = 5;
const LOGIN_WINDOW_MINUTES = 15;

async function isRateLimited(env, ip) {
  // Limpieza oportunista de intentos con más de 24h (evita crecimiento indefinido).
  await env.DB.prepare("DELETE FROM login_attempts WHERE created_at < datetime('now', '-1 day')").run();

  const { results } = await env.DB.prepare(
    `SELECT COUNT(*) as count FROM login_attempts
     WHERE ip = ? AND success = 0 AND created_at > datetime('now', ?)`
  ).bind(ip, `-${LOGIN_WINDOW_MINUTES} minutes`).all();

  return (results?.[0]?.count ?? 0) >= MAX_LOGIN_ATTEMPTS;
}

async function recordLoginAttempt(env, ip, success) {
  await env.DB.prepare("INSERT INTO login_attempts (ip, success) VALUES (?, ?)")
    .bind(ip, success ? 1 : 0).run();
}

// ============================================================
// Worker principal
// ============================================================

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const isAdminRoute = url.pathname.startsWith("/api/admin/");
    const corsHeaders = isAdminRoute ? adminCorsHeaders(env) : publicCorsHeaders();

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // ------------------------------------------------------
      // 1. Pre-inscripción escolar (público)
      // ------------------------------------------------------
      if (url.pathname === "/api/enroll" && request.method === "POST") {
        const body = await request.json();
        const { student_name, birth_date, tutor_name, tutor_phone, tutor_email, shift } = body;

        if (!student_name || !birth_date || !tutor_name || !tutor_phone || !shift) {
          return jsonResponse({ error: "Faltan campos obligatorios" }, 400, corsHeaders);
        }

        await env.DB.prepare(
          "INSERT INTO enrollments (student_name, birth_date, tutor_name, tutor_phone, tutor_email, shift) VALUES (?, ?, ?, ?, ?, ?)"
        ).bind(student_name, birth_date, tutor_name, tutor_phone, tutor_email, shift).run();

        const shiftLabels = {
          "mañana": "Turno Mañana (08:00H - 13:00H)",
          "tarde": "Turno Tarde (13:00H - 18:00H)",
          "completo": "Turno Completo (08:00H - 18:00H)"
        };
        const shiftLabel = shiftLabels[shift] || shift;

        const adminEmail = env.ADMIN_EMAIL_ENROLL || "admisiones@toshinorimorimoto.org";
        const emailResult = await sendEmail(env, {
          to: adminEmail,
          subject: `Nueva pre-inscripción: ${student_name}`,
          replyTo: tutor_email || undefined,
          html: `
            <h2>Nueva solicitud de pre-inscripción</h2>
            <p><strong>Alumno/a:</strong> ${escapeHtml(student_name)}</p>
            <p><strong>Fecha de nacimiento:</strong> ${escapeHtml(birth_date)}</p>
            <p><strong>Tutor legal:</strong> ${escapeHtml(tutor_name)}</p>
            <p><strong>Teléfono:</strong> ${escapeHtml(tutor_phone)}</p>
            <p><strong>Correo del tutor:</strong> ${escapeHtml(tutor_email || "No proporcionado")}</p>
            <p><strong>Turno solicitado:</strong> ${escapeHtml(shiftLabel)}</p>
            <hr>
            <p style="font-size:12px;color:#888;">Este registro también quedó guardado en la base de datos del centro.</p>
          `
        });

        let confirmationResult = { sent: false, reason: "Tutor no proporcionó correo" };
        if (tutor_email) {
          confirmationResult = await sendEmail(env, {
            to: tutor_email,
            subject: "Hemos recibido tu solicitud de pre-inscripción — Centro Toshinori Morimoto",
            html: `
              <h2>¡Gracias, ${escapeHtml(tutor_name)}!</h2>
              <p>Hemos recibido correctamente tu solicitud de pre-inscripción para <strong>${escapeHtml(student_name)}</strong> en el Centro Privado Toshinori Morimoto (Baney).</p>
              <p><strong>Resumen de tu solicitud:</strong></p>
              <ul>
                <li><strong>Alumno/a:</strong> ${escapeHtml(student_name)}</li>
                <li><strong>Fecha de nacimiento:</strong> ${escapeHtml(birth_date)}</li>
                <li><strong>Turno solicitado:</strong> ${escapeHtml(shiftLabel)}</li>
              </ul>
              <p>Esta solicitud es una <strong>reserva de plaza</strong>. Para completar la matrícula, recuerda presentar en la secretaría del centro:</p>
              <ul>
                <li>Fotocopia completa del certificado de nacimiento del menor</li>
                <li>1 fotografía en color del alumno, tamaño carnet</li>
                <li>Fotocopia del Documento de Identidad del tutor legal</li>
                <li>Pago del 50% de la matrícula anual como depósito inicial</li>
              </ul>
              <p>Nuestro equipo de administración se pondrá en contacto contigo en breve al teléfono ${escapeHtml(tutor_phone)} para confirmar los siguientes pasos.</p>
              <hr>
              <p style="font-size:12px;color:#888;">Centro Privado Toshinori Morimoto — Av. de la Independencia, s/n, Baney, Guinea Ecuatorial.</p>
            `
          });
        }

        return jsonResponse({
          success: true,
          message: "Pre-inscripción registrada con éxito.",
          email_sent: emailResult.sent,
          confirmation_sent: confirmationResult.sent
        }, 201, corsHeaders);
      }

      // ------------------------------------------------------
      // 2. Mensajes de contacto (público)
      // ------------------------------------------------------
      if (url.pathname === "/api/contact" && request.method === "POST") {
        const body = await request.json();
        const { name, phone, email, message } = body;

        if (!name || !phone || !message) {
          return jsonResponse({ error: "Faltan campos obligatorios" }, 400, corsHeaders);
        }

        await env.DB.prepare(
          "INSERT INTO contacts (name, phone, email, message) VALUES (?, ?, ?, ?)"
        ).bind(name, phone, email, message).run();

        const adminEmail = env.ADMIN_EMAIL_CONTACT || "contacto@toshinorimorimoto.org";
        const emailResult = await sendEmail(env, {
          to: adminEmail,
          subject: `Nuevo mensaje de contacto: ${name}`,
          replyTo: email || undefined,
          html: `
            <h2>Nuevo mensaje desde el formulario de contacto</h2>
            <p><strong>Nombre:</strong> ${escapeHtml(name)}</p>
            <p><strong>Teléfono:</strong> ${escapeHtml(phone)}</p>
            <p><strong>Correo:</strong> ${escapeHtml(email || "No proporcionado")}</p>
            <p><strong>Mensaje:</strong></p>
            <p>${escapeHtml(message).replace(/\n/g, "<br>")}</p>
            <hr>
            <p style="font-size:12px;color:#888;">Este mensaje también quedó guardado en la base de datos del centro.</p>
          `
        });

        return jsonResponse({
          success: true,
          message: "Mensaje de contacto guardado.",
          email_sent: emailResult.sent
        }, 201, corsHeaders);
      }

      // ------------------------------------------------------
      // 3. Control de asistencias de tutores (público)
      // ------------------------------------------------------
      if (url.pathname === "/api/attendance" && request.method === "POST") {
        const body = await request.json();
        const { meeting_type, date_checked, tutor_name, student_name } = body;

        if (!meeting_type || !date_checked || !tutor_name || !student_name) {
          return jsonResponse({ error: "Faltan campos obligatorios" }, 400, corsHeaders);
        }

        await env.DB.prepare(
          "INSERT INTO parent_attendance (meeting_type, date_checked, tutor_name, student_name) VALUES (?, ?, ?, ?)"
        ).bind(meeting_type, date_checked, tutor_name, student_name).run();

        return jsonResponse({ success: true, message: "Asistencia de tutor registrada." }, 201, corsHeaders);
      }

      // ------------------------------------------------------
      // 4. Panel de administración — login
      // ------------------------------------------------------
      if (url.pathname === "/api/admin/login" && request.method === "POST") {
        const ip = request.headers.get("CF-Connecting-IP") || "unknown";

        if (await isRateLimited(env, ip)) {
          return jsonResponse({
            error: `Demasiados intentos fallidos. Inténtalo de nuevo en ${LOGIN_WINDOW_MINUTES} minutos.`
          }, 429, corsHeaders);
        }

        const body = await request.json().catch(() => ({}));
        const password = body.password;

        const valid = !!password && !!env.ADMIN_PASSWORD && timingSafeEqual(String(password), env.ADMIN_PASSWORD);
        await recordLoginAttempt(env, ip, valid);

        if (!valid) {
          return jsonResponse({ error: "Contraseña incorrecta" }, 401, corsHeaders);
        }

        const { token, expires_at } = await createToken(env);
        return jsonResponse({ success: true, token, expires_at }, 200, corsHeaders);
      }

      // ------------------------------------------------------
      // 5. Panel de administración — listado de inscripciones (protegido)
      // ------------------------------------------------------
      if (url.pathname === "/api/admin/enrollments" && request.method === "GET") {
        if (!(await verifyToken(request, env))) {
          return jsonResponse({ error: "No autorizado" }, 401, corsHeaders);
        }
        const { results } = await env.DB.prepare(
          "SELECT * FROM enrollments ORDER BY created_at DESC LIMIT 200"
        ).all();
        return jsonResponse({ success: true, enrollments: results }, 200, corsHeaders);
      }

      // ------------------------------------------------------
      // 6. Panel de administración — listado de mensajes de contacto (protegido)
      // ------------------------------------------------------
      if (url.pathname === "/api/admin/contacts" && request.method === "GET") {
        if (!(await verifyToken(request, env))) {
          return jsonResponse({ error: "No autorizado" }, 401, corsHeaders);
        }
        const { results } = await env.DB.prepare(
          "SELECT * FROM contacts ORDER BY created_at DESC LIMIT 200"
        ).all();
        return jsonResponse({ success: true, contacts: results }, 200, corsHeaders);
      }

      return jsonResponse({ error: "Ruta no encontrada" }, 404, corsHeaders);

    } catch (err) {
      return jsonResponse({ error: "Error interno del servidor", details: err.message }, 500, corsHeaders);
    }
  }
};
