// Escapa texto antes de insertarlo en el cuerpo HTML del correo, para evitar inyección.
function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Envía un correo usando la API de Resend (https://resend.com).
// Es "best effort": si falla o no hay RESEND_API_KEY configurada, no interrumpe
// el guardado en la base de datos, solo se informa en la respuesta.
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

export default {
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
      // 1. Pre-inscripción escolar
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

        const shiftLabels = {
          "mañana": "Turno Mañana (08:00H - 13:00H)",
          "tarde": "Turno Tarde (13:00H - 18:00H)",
          "completo": "Turno Completo (08:00H - 18:00H)"
        };
        const shiftLabel = shiftLabels[shift] || shift;

        // a) Notificación interna al centro (administración de admisiones)
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

        // b) Correo de confirmación al tutor, si dejó su correo electrónico
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

        return new Response(JSON.stringify({
          success: true,
          message: "Pre-inscripción registrada con éxito.",
          email_sent: emailResult.sent,
          confirmation_sent: confirmationResult.sent
        }), {
          status: 201,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }

      // 2. Mensajes de contacto
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

        return new Response(JSON.stringify({
          success: true,
          message: "Mensaje de contacto guardado.",
          email_sent: emailResult.sent
        }), {
          status: 201,
          headers: { ...corsHeaders, "Content-Type": "application/json" }
        });
      }

      // 3. Control de asistencias de tutores
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
