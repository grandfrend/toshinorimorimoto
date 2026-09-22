# ⚠️ Carpeta obsoleta (legado)

Esta carpeta y el Worker de Cloudflare `toshinori-morimoto-api` que desplegaba
**ya no se usan**. Toda su lógica (D1, correo, panel de admin) se fusionó en
`/src/index.js` (raíz del repo), que ahora se despliega junto con el sitio
estático como un único Worker: `toshinori-morimoto`.

No se ha borrado el Worker `toshinori-morimoto-api` de Cloudflare porque
requiere confirmación explícita antes de eliminar recursos en producción.
Puede borrarse manualmente desde el dashboard cuando se confirme que el
Worker fusionado funciona correctamente.

Esta carpeta puede eliminarse del repositorio en una futura limpieza.
