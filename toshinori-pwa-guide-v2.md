# Guía Técnica Avanzada PWA (v2): Despliegue en Cloudflare (Pages, Workers, D1)

Esta guía ha sido actualizada para facilitar la descarga completa de todo el código de la **Aplicación Web Progresiva (PWA)** del **Centro Privado Toshinori Morimoto de Baney**.

Dado que la plataforma del Studio restringe los archivos comprimidos `.zip` por seguridad, hemos creado un script automatizado en Python: **`toshinori_pwa_generator.py`**, el cual ya se encuentra disponible para su descarga en su panel de Studio.

Al ejecutar este script en su ordenador, se creará automáticamente toda la estructura de carpetas y archivos con el código fuente 100% fidedigno del centro (incluyendo la interfaz gráfica con Tailwind CSS, lógicas de sincronización sin conexión y la base de datos).

---

## 1. Estructura que se Generará en su Ordenador

Cuando descargue y ejecute `toshinori_pwa_generator.py`, se creará la siguiente estructura de archivos:

```text
toshinori-pwa/
├── wrangler.toml        # Configuración del Cloudflare Worker y enlace con D1
├── schema.sql           # Estructura de tablas SQLite para la base de datos D1
├── src/
│   └── index.js         # Lógica serverless de la API (Endpoints REST)
└── public/
    ├── index.html       # Interfaz de usuario SPA moderna (Tailwind + Lucide Icons)
    ├── app.js           # Sincronización inteligente y colas offline en el cliente
    ├── manifest.json    # Metadatos de la PWA para su instalación móvil/escritorio
    └── sw.js            # Service Worker (Caché y soporte para navegación offline)
```

---

## 2. Instrucciones para Generar su Código Localmente

Siga estos pasos sencillos en su ordenador:

1.  **Descargue el archivo `toshinori_pwa_generator.py`** desde el panel de Studio en la derecha.
2.  Coloque el archivo en una carpeta vacía de su ordenador.
3.  Abra su terminal o consola de comandos (Command Prompt / Terminal) en esa carpeta y ejecute:
    ```bash
    python toshinori_pwa_generator.py
    ```
4.  ¡Listo! Aparecerá la carpeta `toshinori-pwa` con todos los archivos perfectamente estructurados y listos para ser desplegados en Cloudflare.

---

## 3. Guía de Despliegue Paso a Paso en Cloudflare

Una vez generados los archivos localmente, siga esta guía técnica para realizar el despliegue en la infraestructura global de Cloudflare:

### Paso 1: Configurar Wrangler (Consola de Cloudflare)
1.  Abra la terminal en su ordenador local dentro de la carpeta generada: `toshinori-pwa`.
2.  Instale o ejecute la herramienta de desarrollo Wrangler e inicie sesión en su consola de Cloudflare:
    ```bash
    npx wrangler login
    ```
    *Se abrirá una ventana en su navegador web para autorizar el acceso a su cuenta de Cloudflare (la cual es gratuita).*

### Paso 2: Crear la Base de Datos Relacional (Cloudflare D1)
1.  Cree la base de datos en la red global de Cloudflare ejecutando el siguiente comando:
    ```bash
    npx wrangler d1 create toshinori_db
    ```
2.  La terminal le devolverá una información similar a esta:
    ```toml
    [[d1_databases]]
    binding = "DB"
    database_name = "toshinori_db"
    database_id = "xxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    ```
3.  **Copie el identificador único (`database_id`)** que le proporcionó la consola y péguelo dentro del archivo `wrangler.toml` reemplazando el texto `"TU_DATABASE_ID"`.

### Paso 3: Inicializar las Tablas en Producción
Ejecute el script del esquema relacional `schema.sql` para crear las tablas de pre-inscripciones, contactos y control de firmas de tutores en su base de datos remota de Cloudflare D1:
```bash
npx wrangler d1 execute toshinori_db --file=schema.sql --remote
```

### Paso 4: Desplegar la API Serverless (Workers)
Publique la API backend para que comience a recibir peticiones de inserción y lectura en la base de datos D1:
```bash
npx wrangler deploy
```
Al finalizar, la consola de Cloudflare le mostrará la URL pública de producción del Worker (ej. `https://toshinori-morimoto-api.tu-usuario.workers.dev`).
1.  **Copie esa URL**.
2.  Abra el archivo `public/app.js` en su editor de código.
3.  Busque la constante `API_URL` al inicio del archivo y reemplace el valor temporal con su URL de producción:
    ```javascript
    const API_URL = "https://toshinori-morimoto-api.tu-usuario.workers.dev";
    ```

### Paso 5: Desplegar el Frontend PWA (Cloudflare Pages)
1.  Inicie sesión en el panel web de **[Cloudflare Dashboard](https://dash.cloudflare.com/)**.
2.  En el menú lateral izquierdo, haga clic en **Workers & Pages** y presione el botón **Create application**.
3.  Seleccione la pestaña **Pages** y haga clic en **Upload assets**.
4.  Asígnele el nombre al proyecto (por ejemplo, `toshinori-morimoto`).
5.  **Arrastre y suelte la carpeta `public`** que se encuentra dentro de su directorio local (que contiene `index.html`, `app.js`, `sw.js`, `manifest.json` y los iconos de la app).
6.  Haga clic en **Deploy site**.

¡Felicidades! Su aplicación web ya estará en línea en un dominio seguro con certificado HTTPS (por ejemplo, `https://toshinori-morimoto.pages.dev`).

---

## 4. Detalles sobre los Iconos de la Aplicación

Para que una PWA sea "instalable" en dispositivos móviles y ordenadores, requiere obligatoriamente iconos en resoluciones estándar (`192x192` píxeles y `512x512` píxeles) referenciados en el archivo `manifest.json`. 

*   **¿Cómo resolver esto?** El script generador buscará de forma predeterminada los archivos `icon-192.png` y `icon-512.png`.
*   **Recomendación:** Puede diseñar un logotipo escolar para el centro (usando el escudo oficial o un libro) en formato cuadrado, guardarlo con esos nombres exactos en formato PNG en la carpeta `public`, y reemplazar los marcadores temporales. Esto asegurará que al instalarse en pantallas táctiles de móviles o tablets en Baney, la aplicación muestre la identidad visual institucional correcta del centro.

---

## 4.1. Conexión Frontend ↔ Backend y Notificaciones por Correo (actualizado)

El sitio estático (`toshinori-morimoto`) y la API (`toshinori-morimoto-api`) son **dos Workers distintos** en Cloudflare. El frontend (`public/app.js`) ya está configurado para apuntar siempre a la URL de producción de la API:

```javascript
const API_URL = "https://toshinori-morimoto-api.grandfrend-media.workers.dev";
```

Además, el backend (`toshinori-pwa/src/index.js`) ahora envía una notificación por correo (vía [Resend](https://resend.com), API HTTP gratuita hasta 3.000 correos/mes) cada vez que llega una **pre-inscripción** o un **mensaje de contacto**, además de guardarlos en D1. Para activar el envío de correos, faltan dos pasos manuales que solo se pueden hacer desde la consola de Cloudflare o la terminal (no se pueden automatizar desde el repositorio por seguridad):

1.  Crea una cuenta gratuita en **[resend.com](https://resend.com)** y obtén una API key. Lo ideal es verificar el dominio `toshinorimorimoto.gq` como remitente; mientras tanto puedes usar el remitente de pruebas de Resend.
2.  Configura la API key como **secreto** del Worker (nunca como variable de texto plano en `wrangler.toml`):
    ```bash
    cd toshinori-pwa
    npx wrangler secret put RESEND_API_KEY
    ```
3.  Vuelve a desplegar la API:
    ```bash
    npx wrangler deploy
    ```

Si `RESEND_API_KEY` no está configurada, las inscripciones y mensajes se siguen guardando con normalidad en D1; simplemente no se envía el correo de aviso (el campo `email_sent` en la respuesta de la API lo indica).

El correo de destino se controla con la variable `ADMIN_EMAIL` en `toshinori-pwa/wrangler.toml` (por defecto `guillermonohanikobara@gmail.com`).

---

## 5. Justificación Técnica de la Arquitectura Seleccionada

Esta arquitectura web moderna ha sido diseñada de forma rigurosa por un experto pensando en las necesidades del **Centro Toshinori Morimoto**:

*   **Costo Cero Permanente (Capa Gratuita):** Cloudflare Pages, Workers y D1 ofrecen límites de uso gratuito extremadamente generosos que superan con creces las necesidades del centro en Baney (hasta 100.000 peticiones diarias gratuitas en Workers y 5 millones de filas de almacenamiento en D1), lo que elimina los costos fijos de servidores físicos o bases de datos de pago.
*   **Inmunidad ante Cortes de Red:** Gracias al Service Worker (`sw.js`), la aplicación cargará instantáneamente en los teléfonos de padres y docentes, cargando el portal escolar completo incluso en zonas con cobertura nula o fluctuante.
*   **Transparencia de Datos:** La base de datos D1 procesará con absoluta integridad relacional el control de firmas del centro escolar y las solicitudes de pre-inscripción móvil para su posterior revisión administrativa.
