/**
 * upload.js — Subida de imágenes a Supabase Storage (T-V5-06, identidad).
 *
 * Bucket `media` (público en lectura). La política RLS del bucket exige que el PRIMER segmento
 * del path sea el uid del usuario autenticado (`{uid}/...`) para INSERT/UPDATE/DELETE, así que
 * todas las subidas van a `media/{uid}/{kind}-{timestamp}.jpg`.
 *
 * La imagen se REDIMENSIONA en el cliente (canvas → JPEG) antes de subir: el bucket no crece con
 * fotos de 12 MP y la app carga rápido. En modo test no hay Supabase real → bfPickAndUploadImage
 * rechaza con un mensaje claro (los tests cubren el guardado de la URL vía API, no la subida).
 *
 * Requiere auth.js cargado antes (getConfig/getSupabase/getSession globales).
 */

// Redimensiona un File de imagen con lado máximo `maxSide` (mantiene proporción).
// Los formatos CON transparencia (PNG/WebP/GIF/SVG — logos típicos) se exportan como PNG para
// conservar el alfa: recomprimirlos a JPEG aplastaría lo transparente a NEGRO (revisión T-V5-06).
// Las fotos (JPEG y demás) salen como JPEG comprimido. Devuelve { blob, ext, mime }.
async function _bfResizeImage(file, maxSide, quality) {
    const keepAlpha = /png|webp|gif|svg/i.test(file.type);
    const bitmap = await createImageBitmap(file);
    const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
    const w = Math.max(1, Math.round(bitmap.width * scale));
    const h = Math.max(1, Math.round(bitmap.height * scale));
    const canvas = document.createElement('canvas');
    canvas.width = w; canvas.height = h;
    canvas.getContext('2d').drawImage(bitmap, 0, 0, w, h);
    bitmap.close();
    const mime = keepAlpha ? 'image/png' : 'image/jpeg';
    const blob = await new Promise((res) => canvas.toBlob(res, mime, quality));
    if (!blob) throw new Error('No se pudo procesar la imagen');
    return { blob, ext: keepAlpha ? 'png' : 'jpg', mime };
}

/**
 * Redimensiona una imagen y la devuelve como data URL (base64), SIN subirla a Storage.
 * Para enviar una foto a la IA de visión (foto→partitura, T-V5-11). Funciona en modo test
 * (no toca Supabase). `maxSide` grande (1600) para no perder legibilidad de los acordes.
 */
async function bfImageToDataUrl(file, maxSide = 1600) {
    if (!file || !file.type.startsWith('image/')) throw new Error('Elige un archivo de imagen.');
    const { blob } = await _bfResizeImage(file, maxSide, 0.85);
    return await new Promise((res, rej) => {
        const r = new FileReader();
        r.onload = () => res(r.result);
        r.onerror = () => rej(new Error('No se pudo leer la imagen.'));
        r.readAsDataURL(blob);
    });
}

/**
 * Sube una imagen al Storage y devuelve su URL pública.
 * @param {File} file    imagen elegida por el usuario
 * @param {string} kind  prefijo del archivo ('avatar' | 'band-logo' | 'band-cover' | ...)
 * @param {number} maxSide lado máximo en px (512 avatares, 1600 fondos)
 */
async function bfUploadImage(file, kind, maxSide = 512) {
    if ((await getConfig()).test_mode) {
        throw new Error('La subida de imágenes no está disponible en modo test.');
    }
    if (!file || !file.type.startsWith('image/')) {
        throw new Error('Elige un archivo de imagen.');
    }
    const session = await getSession();
    if (!session) throw new Error('Sesión caducada. Vuelve a entrar.');

    const { blob, ext, mime } = await _bfResizeImage(file, maxSide, 0.85);
    const path = `${session.user.id}/${kind}-${Date.now()}.${ext}`;
    const sb = await getSupabase();
    const { error } = await sb.storage.from('media').upload(path, blob, {
        contentType: mime, upsert: false,
    });
    if (error) throw new Error('No se pudo subir la imagen: ' + (error.message || 'error de Storage'));
    const { data } = sb.storage.from('media').getPublicUrl(path);
    if (!data || !data.publicUrl) throw new Error('No se pudo obtener la URL pública.');
    return data.publicUrl;
}

/**
 * Abre el selector de archivos, sube la imagen y llama a `onDone(url)`.
 * Muestra toasts de progreso/error (helper único para perfil y banda).
 */
function bfPickAndUploadImage(kind, maxSide, onDone) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.addEventListener('change', async () => {
        const file = input.files && input.files[0];
        if (!file) return;
        try {
            toast('Subiendo imagen…', 'info');
            const url = await bfUploadImage(file, kind, maxSide);
            await onDone(url);
        } catch (e) {
            toast(e.message || 'No se pudo subir la imagen.', 'error');
        }
    });
    input.click();
}
