# Configuración de OBS Studio para Grabación de Videos

Esta guía explica cómo configurar OBS Studio correctamente para:
1. **Solo capturar el audio del video** (sin micrófono ni otras fuentes)
2. **Capturar el video en pantalla completa** del navegador

---

## 🎤 Configuración de Audio

### Problema Común
OBS puede estar capturando múltiples fuentes de audio:
- El audio del video del navegador ✅ (deseado)
- El micrófono del PC ❌ (no deseado)
- El audio del escritorio ❌ (no deseado)
- Otras fuentes de audio ❌ (no deseado)

### Solución: Configurar OBS para Solo Capturar Audio del Video

#### Paso 1: Abrir Configuración de Audio

1. Abre **OBS Studio**
2. Ve a **Configuración** (Settings) → **Audio**
   - O presiona `Ctrl + ,` y selecciona la pestaña **Audio**

#### Paso 2: Desactivar Fuentes de Audio no Deseadas

En la sección **Dispositivos de Audio**:

1. **Desktop Audio (Audio de Escritorio):**
   - Cambia a **"Deshabilitado"** o selecciona **"Ninguno"**
   - O desactiva el checkbox si está disponible

2. **Desktop Audio 2 (Audio de Escritorio 2):**
   - Cambia a **"Deshabilitado"** o **"Ninguno"**

3. **Micrófono/Auxiliar Audio (Mic/Aux):**
   - Cambia a **"Deshabilitado"** o **"Ninguno"**
   - Esto evitará que se capture tu micrófono

4. **Micrófono/Auxiliar Audio 2, 3, etc.:**
   - Cambia todos a **"Deshabilitado"** o **"Ninguno"**

#### Paso 3: Verificar Fuentes de Audio en la Escena

1. En la ventana principal de OBS, mira la sección **"Fuentes"** (Sources)
2. **NO debes tener** fuentes de audio separadas como:
   - "Captura de audio de escritorio"
   - "Dispositivo de captura de audio"
   - "Micrófono"
3. **Solo debes tener:**
   - La fuente de captura de ventana del navegador (ej: "Captura_Navegador")
   - Esta fuente capturará automáticamente el audio del navegador

#### Paso 4: Configurar la Fuente de Captura de Ventana

1. Selecciona tu fuente de captura de ventana en la lista
2. Haz clic derecho → **Propiedades** (Properties)
3. Asegúrate de que esté seleccionada la ventana correcta del navegador
4. Verifica que la opción de capturar audio esté habilitada (si está disponible)

---

## 🖥️ Configuración de Video - Pantalla Completa

El script ahora configura automáticamente el video en pantalla completa, pero si necesitas verificarlo manualmente:

### Verificación Manual

1. **En el Navegador:**
   - El script activará automáticamente la pantalla completa del reproductor de YouTube
   - Si no funciona, puedes hacer clic en el botón de pantalla completa del reproductor manualmente

2. **En OBS:**
   - Asegúrate de que la fuente de captura de ventana capture toda la ventana
   - Si es necesario, ajusta el tamaño de la fuente en OBS para que coincida con la ventana completa

---

## ✅ Verificación Final

Antes de ejecutar el script:

1. **Verifica Audio:**
   - En OBS, mira el mezclador de audio (Audio Mixer)
   - Deberías ver solo **UNA barra de audio** (la del navegador)
   - No deberías ver barras para micrófono, escritorio, etc.

2. **Prueba de Grabación Corta:**
   - Haz una grabación de prueba de 10 segundos
   - Reproduce el video grabado
   - Verifica que solo escuches el audio del video, sin ruidos del micrófono

3. **Verifica Video:**
   - El video debe estar en pantalla completa
   - No debe haber barras negras alrededor

---

## 🔧 Solución de Problemas

### Problema: Sigue capturando el micrófono

**Solución:**
1. Ve a **Configuración** → **Audio**
2. Asegúrate de que TODOS los dispositivos auxiliares estén en **"Deshabilitado"**
3. Ve a **Configuración** → **Audio Avanzado**
4. Verifica que no haya fuentes de audio adicionales habilitadas

### Problema: No se escucha el audio del video

**Solución:**
1. Verifica que el volumen del navegador esté alto
2. En OBS, verifica que el nivel de audio del navegador no esté silenciado
3. Asegúrate de que la fuente de captura de ventana esté activa y visible

### Problema: El video no está en pantalla completa

**Solución:**
1. El script intenta activar pantalla completa automáticamente
2. Si no funciona, haz clic manualmente en el botón de pantalla completa del reproductor de YouTube
3. Verifica que la ventana del navegador esté maximizada

---

## 📝 Resumen de Configuración Recomendada

### Audio en OBS:
- ✅ Desktop Audio: **Deshabilitado**
- ✅ Desktop Audio 2: **Deshabilitado**
- ✅ Micrófono/Aux: **Deshabilitado**
- ✅ Solo fuente de captura de ventana del navegador

### Video en OBS:
- ✅ Fuente: Captura de ventana del navegador
- ✅ Ventana seleccionada: Brave/Chrome con YouTube
- ✅ El script configurará automáticamente pantalla completa

---

## 💡 Nota Importante

El script verificará automáticamente la configuración cuando se conecte a OBS y mostrará estas instrucciones. Sin embargo, es recomendable configurar OBS manualmente antes de ejecutar el script para evitar problemas.

