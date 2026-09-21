document.addEventListener("DOMContentLoaded", () => {
  // Inicializar iconos Lucide
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
  
  // URL de la API: utiliza el servidor local o la URL configurada
  const API_URL = (typeof window !== 'undefined' && window.location && window.location.origin && !window.location.origin.startsWith('file:'))
    ? window.location.origin
    : "https://toshinori-morimoto-api.grandfrend-media.workers.dev";

  // Registro de Service Worker para capacidades PWA
  if ('serviceWorker' in navigator && window.location.protocol.startsWith('http')) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch((err) => {
        console.log('Service Worker no activo en este contexto:', err);
      });
    });
  }

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

  // Claves del localStorage para colas de sincronización local
  const OFFLINE_QUEUES = {
    enrollments: "toshinori_offline_enrollments",
    contacts: "toshinori_offline_contacts",
    attendance: "toshinori_offline_attendance"
  };

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

  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);
  updateOnlineStatus();

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
    toast.className = `p-4 mb-3 rounded-lg shadow-lg border-l-4 transition-all duration-300 transform translate-y-2 opacity-0 flex items-start gap-3 w-80 md:w-96 pointer-events-auto ${
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

  // Dinamización de Ciclos y Fechas Escolares (Basado en año actual)
  function applyDynamicDates() {
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth(); // 0 = Enero, 8 = Septiembre

    // Ciclo escolar: En Guinea Ecuatorial / sistema escolar, el curso inicia en Septiembre.
    // Si estamos entre Junio y Diciembre (mes >= 5), el ciclo activo o próximo es currentYear - (currentYear + 1).
    // Si estamos entre Enero y Mayo (mes < 5), el ciclo activo es (currentYear - 1) - currentYear.
    const startYear = currentMonth >= 5 ? currentYear : currentYear - 1;
    const endYear = startYear + 1;
    const cycleDash = `${startYear}–${endYear}`;
    const cycleHyphen = `${startYear}-${endYear}`;

    // Reemplazo en elementos con clases específicas
    document.querySelectorAll('.dynamic-cycle').forEach(el => {
      el.textContent = cycleHyphen;
    });
    document.querySelectorAll('.dynamic-cycle-dash').forEach(el => {
      el.textContent = cycleDash;
    });
    document.querySelectorAll('.dynamic-start-year').forEach(el => {
      el.textContent = startYear;
    });
    document.querySelectorAll('.dynamic-end-year').forEach(el => {
      el.textContent = endYear;
    });
    document.querySelectorAll('.dynamic-current-year').forEach(el => {
      el.textContent = currentYear;
    });
  }

  // Resaltado de enlace de navegación activo
  function highlightActiveNav() {
    const currentPath = window.location.pathname.replace(/\/$/, '') || '/';
    document.querySelectorAll('nav a, #mobile-menu a').forEach(link => {
      const href = link.getAttribute('href');
      if (!href) return;
      const cleanHref = href.replace(/\/$/, '') || '/';
      if (cleanHref === currentPath && !link.classList.contains('bg-rose-600')) {
        link.classList.add('text-rose-600', 'font-bold');
        link.classList.remove('text-gray-600', 'text-gray-700');
      }
    });
  }

  applyDynamicDates();
  highlightActiveNav();
});
