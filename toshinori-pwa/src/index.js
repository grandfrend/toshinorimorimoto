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
