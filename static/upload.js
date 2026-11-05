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

/**
 * T-V6-85 — Sube un adjunto (PDF, audio o imagen) al bucket `media` y devuelve
 * `{ url, kind }`. Límite 20 MB. Las imágenes se reducen como siempre; PDF y audio van tal cual.
 * Si el bucket no admite ese tipo de archivo, el error de Storage lo explica: en ese caso, el
 * usuario puede pegar un enlace (Drive/Dropbox) en el mismo diálogo.
 */
async function bfUploadFile(file, kind = 'adjunto') {
    if ((await getConfig()).test_mode) throw new Error('La subida de archivos no está disponible en modo test.');
    if (!file) throw new Error('Elige un archivo.');
    if (file.size > 20 * 1024 * 1024) throw new Error('El archivo pasa de 20 MB. Comprímelo o pega un enlace.');
    const type = file.type || '';
    const k = type === 'application/pdf' ? 'pdf' : type.startsWith('audio/') ? 'audio' : type.startsWith('image/') ? 'image' : null;
    if (!k) throw new Error('Solo PDF, audio o imagen.');
    if (k === 'image') return { url: await bfUploadImage(file, kind, 1600), kind: 'image' };
    const session = await getSession();
    if (!session) throw new Error('Sesión caducada. Vuelve a entrar.');
    const ext = (file.name.split('.').pop() || (k === 'pdf' ? 'pdf' : 'webm')).toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 5) || 'bin';
    const path = `${session.user.id}/${kind}-${Date.now()}.${ext}`;
    const sb = await getSupabase();
    const { error } = await sb.storage.from('media').upload(path, file, { contentType: type, upsert: false });
    if (error) throw new Error('No se pudo subir: ' + (error.message || 'error de Storage') + '. Prueba a pegar un enlace.');
    const { data } = sb.storage.from('media').getPublicUrl(path);
    if (!data || !data.publicUrl) throw new Error('No se pudo obtener la URL pública.');
    return { url: data.publicUrl, kind: k };
}

/**
 * T-V6-85 — Grabadora mínima con MediaRecorder sobre un botón: 1er clic graba, 2º para y llama a
 * `onDone(blob, segundos)`. Pensada para el móvil en el local de ensayo.
 */
async function bfRecorder(btn, onDone) {
    if (btn._rec) { btn._rec.stop(); return; }
    if (!navigator.mediaDevices || !window.MediaRecorder) { toast('Tu navegador no permite grabar audio.', 'error'); return; }
    let stream;
    try { stream = await navigator.mediaDevices.getUserMedia({ audio: true }); }
    catch (e) { toast('Sin permiso para el micrófono.', 'error'); return; }
    const rec = new MediaRecorder(stream);
    const chunks = [];
    const label = btn.innerHTML;
    const t0 = Date.now();
    const timer = setInterval(() => {
        const s = Math.round((Date.now() - t0) / 1000);
        btn.textContent = `Parar · ${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
    }, 500);
    rec.ondataavailable = (e) => { if (e.data && e.data.size) chunks.push(e.data); };
    rec.onstop = () => {
        clearInterval(timer);
        stream.getTracks().forEach(t => t.stop());
        btn._rec = null;
        btn.innerHTML = label;
        btn.classList.remove('is-recording');
        const blob = new Blob(chunks, { type: rec.mimeType || 'audio/webm' });
        onDone(blob, Math.round((Date.now() - t0) / 1000));
    };
    btn._rec = rec;
    btn.classList.add('is-recording');
    rec.start();
}
