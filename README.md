# Sistema de Grabación Automatizada de Videos de YouTube

Sistema automatizado profesional para grabar videos de YouTube utilizando Brave Browser y OBS Studio. El proyecto ha sido completamente refactorizado con una **arquitectura modular ultra-optimizada**, donde cada archivo tiene una responsabilidad única y específica, garantizando máxima legibilidad y mantenibilidad.

## 📋 Tabla de Contenidos

- [Estructura del Proyecto](#estructura-del-proyecto)
- [Descripción de Módulos](#descripción-de-módulos)
- [Orquestación del Sistema](#orquestación-del-sistema)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Guía de Ejecución](#guía-de-ejecución)
- [Formato del Archivo de URLs](#formato-del-archivo-de-urls)
- [Características](#características)
- [Solución de Problemas](#solución-de-problemas)

---

## 📁 Estructura del Proyecto

```
videos_ucm/
│
├── config.py                      # Configuración centralizada (~88 líneas)
├── utils.py                       # Utilidades compartidas (~170 líneas)
│
├── url_processor.py              # Procesamiento principal de URLs (~200 líneas)
├── url_validator.py              # Validación de URLs (~20 líneas)
├── url_filters.py                 # Filtros y aplicaciones (~80 líneas)
│
├── browser_manager.py            # Gestión principal del navegador (~150 líneas)
├── browser_connection.py         # Conexión al navegador (~150 líneas)
├── browser_url_loader.py         # Carga de URLs (~100 líneas)
├── browser_info.py               # Extracción de información (~150 líneas)
├── browser_controls.py           # Control de reproducción (~200 líneas)
├── browser_popups.py             # Gestión de popups (~120 líneas)
│
├── obs_manager.py                # Gestión principal de OBS (~150 líneas)
├── obs_connection.py             # Conexión con OBS (~100 líneas)
├── obs_recording.py              # Control de grabaciones (~200 líneas)
│
├── video_processor.py            # Procesamiento de videos (~320 líneas)
├── file_manager.py               # Gestión de archivos (~230 líneas)
│
├── orchestrator.py               # Orquestador principal (~250 líneas)
├── orchestrator_setup.py         # Configuración inicial (~50 líneas)
├── orchestrator_summary.py       # Resúmenes y estadísticas (~80 líneas)
│
├── ulrls.txt                     # Archivo con URLs organizadas por módulos
├── requirements.txt              # Dependencias del proyecto
└── README.md                     # Este archivo
```

---

## 🔧 Descripción de Módulos

### Módulos de Configuración y Utilidades

#### `config.py` (~88 líneas)
**Propósito**: Configuración centralizada del sistema.

**Contenido**:
- Configuración de OBS Studio (host, puerto, contraseña)
- Configuración del navegador (Brave/Chrome, puerto de depuración)
- Configuración de archivos (ruta del archivo de URLs)
- Márgenes de grabación (inicial y final, normales y de prueba)
- Configuración del modo de prueba
- Configuración de continuación de grabación

#### `utils.py` (~170 líneas)
**Propósito**: Funciones auxiliares compartidas.

**Funciones principales**:
- `sanitizar_nombre_archivo()`: Limpia nombres de archivo
- `parsear_duracion_a_segundos()`: Convierte duración a segundos
- `formatear_tiempo()`: Formatea tiempo legible
- `formatear_tamaño()`: Formatea tamaño de archivos
- `configurar_logging()`: Configura el sistema de logging

---

### Módulos de Procesamiento de URLs

#### `url_processor.py` (~200 líneas)
**Propósito**: Procesamiento principal del archivo de URLs.

**Clase**: `URLProcessor`

**Funcionalidades**:
- `parsear_archivo_urls()`: Lee y parsea el archivo de URLs
- `crear_estructura_carpetas()`: Crea carpetas para cada módulo
- `obtener_todos_los_modulos()`: Retorna todos los módulos procesados
- Delega validación a `url_validator.py`
- Delega filtros a `url_filters.py`

#### `url_validator.py` (~20 líneas)
**Propósito**: Validación de URLs de YouTube.

**Funciones**:
- `validar_url_youtube()`: Valida que una URL sea válida para YouTube

#### `url_filters.py` (~80 líneas)
**Propósito**: Aplicación de filtros a módulos y URLs.

**Funciones**:
- `aplicar_modulo_inicio()`: Filtra módulos por inicio
- `aplicar_limites_prueba()`: Aplica límites del modo de prueba
- `aplicar_inicio_video()`: Configura índices de inicio de video

---

### Módulos de Gestión del Navegador

#### `browser_manager.py` (~150 líneas)
**Propósito**: Gestión principal del navegador.

**Clase**: `BrowserManager`

**Funcionalidades principales**:
- `inicializar_navegador()`: Conecta o abre el navegador
- `cargar_url()`: Carga URLs en el navegador
- `cerrar_pestaña_actual()`: Cierra la pestaña actual
- `cerrar_navegador()`: Cierra completamente el navegador
- Delega conexión a `browser_connection.py`
- Delega carga de URLs a `browser_url_loader.py`
- Delega información a `browser_info.py`
- Delega controles a `browser_controls.py`

#### `browser_connection.py` (~150 líneas)
**Propósito**: Gestión de la conexión al navegador.

**Funciones**:
- `verificar_puerto_disponible()`: Verifica si un puerto está disponible
- `obtener_ruta_navegador()`: Obtiene la ruta del ejecutable
- `abrir_navegador_con_puerto_depuracion()`: Abre el navegador automáticamente
- `conectar_a_navegador_existente()`: Conecta a navegador existente
- `mostrar_instrucciones_conexion()`: Muestra instrucciones de conexión

#### `browser_url_loader.py` (~100 líneas)
**Propósito**: Carga de URLs en el navegador.

**Funciones**:
- `cargar_url_en_navegador()`: Carga una URL en una nueva pestaña
- Verifica carga completa de páginas
- Valida que estamos en YouTube

#### `browser_info.py` (~150 líneas)
**Propósito**: Extracción de información de videos.

**Clase**: `BrowserInfo`

**Funcionalidades**:
- `obtener_titulo_video()`: Obtiene el título del video
- `obtener_duracion_video_continuo()`: Obtiene la duración de forma continua
- `_obtener_duracion_por_selectores()`: Obtiene duración por CSS
- `_obtener_duracion_por_javascript()`: Obtiene duración por JavaScript

#### `browser_controls.py` (~200 líneas)
**Propósito**: Control de reproducción y visualización.

**Clase**: `BrowserControls`

**Funcionalidades**:
- `reproducir_video()`: Inicia la reproducción del video
- `configurar_pantalla_completa()`: Activa pantalla completa
- `salir_pantalla_completa()`: Sale de pantalla completa
- `monitorear_reproduccion()`: Monitorea la reproducción
- Usa `browser_popups.py` para gestionar popups

#### `browser_popups.py` (~120 líneas)
**Propósito**: Gestión de popups y anuncios.

**Funciones**:
- `cerrar_popups_youtube()`: Cierra popups y banners de YouTube
- `intentar_omitir_anuncios()`: Intenta omitir anuncios de YouTube

---

### Módulos de Gestión de OBS

#### `obs_manager.py` (~150 líneas)
**Propósito**: Gestión principal de OBS Studio.

**Clase**: `OBSManager`

**Funcionalidades principales**:
- `conectar()`: Conecta con OBS Studio
- `configurar_directorio_grabacion()`: Configura directorio de salida
- `iniciar_grabacion()`: Inicia una grabación
- `detener_grabacion()`: Detiene la grabación
- `verificar_grabacion_activa()`: Verifica estado de grabación
- `mostrar_informacion_escenas()`: Muestra información de escenas
- `verificar_configuracion_audio()`: Muestra instrucciones de audio
- Delega conexión a `obs_connection.py`
- Delega grabaciones a `obs_recording.py`

#### `obs_connection.py` (~100 líneas)
**Propósito**: Gestión de la conexión con OBS.

**Funciones**:
- `conectar_obs()`: Conecta con OBS Studio vía WebSocket
- `verificar_conexion_obs()`: Verifica que la conexión esté activa
- Maneja errores de conexión

#### `obs_recording.py` (~200 líneas)
**Propósito**: Control de grabaciones en OBS.

**Funciones**:
- `iniciar_grabacion_obs()`: Inicia una grabación
- `detener_grabacion_obs()`: Detiene la grabación y obtiene ruta
- `verificar_grabacion_activa()`: Verifica si hay grabación activa
- `asegurar_grabacion_detenida()`: Asegura que no haya grabación activa

---

### Módulos de Procesamiento de Videos

#### `video_processor.py` (~320 líneas)
**Propósito**: Coordinación del procesamiento de videos individuales.

**Clase**: `VideoProcessor`

**Funcionalidades**:
- `procesar_video()`: Procesa un video completo desde URL hasta archivo final
  - Coordina todos los pasos del proceso
  - Maneja errores durante la grabación
  - Gestiona el flujo completo

#### `file_manager.py` (~230 líneas)
**Propósito**: Gestión de archivos grabados.

**Clase**: `FileManager`

**Funcionalidades**:
- `gestionar_archivo_grabado()`: Gestiona el archivo completo (renombrado y movimiento)
- `buscar_archivo_reciente()`: Busca el archivo más reciente en un directorio
- `_esperar_archivo()`: Espera a que un archivo exista
- `_generar_ruta_archivo()`: Genera la ruta completa del archivo renombrado
- `_eliminar_archivo_existente()`: Elimina archivo existente si es necesario
- `_renombrar_archivo()`: Renombra y mueve el archivo actualizando estadísticas

---

### Módulos de Orquestación

#### `orchestrator.py` (~250 líneas)
**Propósito**: Orquestador principal del sistema.

**Clase**: `Orchestrator`

**Funcionalidades principales**:
- `ejecutar()`: Ejecuta el proceso completo de grabación
- `_procesar_urls()`: Procesa el archivo de URLs
- `_crear_estructura_carpetas()`: Crea estructura de carpetas
- `_conectar_obs()`: Conecta con OBS
- `_inicializar_navegador()`: Inicializa el navegador
- `_procesar_modulos()`: Procesa todos los módulos y videos
- `_limpiar_recursos()`: Limpia recursos utilizados
- Usa `orchestrator_setup.py` para configuración inicial
- Usa `orchestrator_summary.py` para resúmenes

#### `orchestrator_setup.py` (~50 líneas)
**Propósito**: Configuración inicial del orquestador.

**Funciones**:
- `mostrar_info_modo_prueba()`: Muestra información del modo de prueba
- `mostrar_instrucciones_configuracion()`: Muestra instrucciones de configuración

#### `orchestrator_summary.py` (~80 líneas)
**Propósito**: Generación de resúmenes y estadísticas.

**Funciones**:
- `calcular_tamaño_total()`: Calcula tamaño total de archivos
- `mostrar_resumen_final()`: Muestra resumen final de ejecución

---

## 🔄 Orquestación del Sistema

### Flujo Principal

```
orchestrator.py (main)
    │
    ├──> orchestrator_setup.py
    │       └──> mostrar_info_modo_prueba()
    │       └──> mostrar_instrucciones_configuracion()
    │
    ├──> URLProcessor.parsear_archivo_urls()
    │       ├──> url_validator.py (validación)
    │       └──> url_filters.py (filtros)
    │
    ├──> URLProcessor.crear_estructura_carpetas()
    │
    ├──> OBSManager.conectar()
    │       └──> obs_connection.py
    │
    ├──> BrowserManager.inicializar_navegador()
    │       ├──> browser_connection.py
    │       ├──> browser_info.py
    │       └──> browser_controls.py
    │               └──> browser_popups.py
    │
    └──> Para cada módulo:
            └──> Para cada video:
                    └──> VideoProcessor.procesar_video()
                            ├──> OBSManager (obs_recording.py)
                            ├──> BrowserManager (browser_url_loader.py)
                            ├──> BrowserControls (browser_popups.py)
                            └──> FileManager
                                    └──> orchestrator_summary.py
```

### Dependencias entre Módulos

```
orchestrator.py
    ├──> orchestrator_setup.py
    ├──> orchestrator_summary.py
    ├──> url_processor.py
    │       ├──> url_validator.py
    │       └──> url_filters.py
    ├──> obs_manager.py
    │       ├──> obs_connection.py
    │       └──> obs_recording.py
    ├──> browser_manager.py
    │       ├──> browser_connection.py
    │       ├──> browser_url_loader.py
    │       ├──> browser_info.py
    │       ├──> browser_controls.py
    │       └──> browser_popups.py
    ├──> video_processor.py
    └──> file_manager.py

Todos los módulos pueden usar:
    └──> utils.py
    └──> config.py
```

---

## 📦 Requisitos

### Software Requerido

1. **Python 3.8 o superior**
2. **OBS Studio** con el plugin `obs-websocket` instalado y activado
3. **Brave Browser** o **Google Chrome**

### Dependencias de Python

Ver `requirements.txt`:
- `selenium>=4.0.0`
- `webdriver-manager>=3.8.0`
- `obsws-python>=1.2.0`
- `pywin32>=300` (solo Windows)

---

## 🚀 Instalación

### Paso 1: Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Paso 2: Configurar OBS Studio

1. Abrir OBS Studio
2. Instalar plugin `obs-websocket`: Herramientas > Complementos
3. Configurar servidor WebSocket: Herramientas > Configuración del servidor WebSocket
4. Configurar escena de grabación con captura de ventana del navegador
5. Configurar audio (solo audio del navegador)

### Paso 3: Preparar el Navegador

Abrir Brave/Chrome con puerto de depuración:
```powershell
& "C:\Users\[TU_USUARIO]\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe" --remote-debugging-port=9222
```

---

## ⚙️ Configuración

Editar `config.py` con tus configuraciones (ver documentación completa en el archivo).

---

## 🎬 Guía de Ejecución

```bash
python orchestrator.py
```

---

## 📝 Formato del Archivo de URLs

El archivo `ulrls.txt` debe seguir este formato:

```
#MOD01_python
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2

#MOD02_sql
https://www.youtube.com/watch?v=VIDEO_ID_3
```

---

## ✨ Características

### Arquitectura Modular Ultra-Optimizada

- ✅ **Separación extrema de responsabilidades**: Cada módulo tiene una función única y específica
- ✅ **Archivos pequeños y legibles**: Todos los archivos están optimizados para máxima legibilidad
- ✅ **Código limpio y profesional**: Sin duplicación, fácil de mantener y extender
- ✅ **Documentación completa**: Cada módulo está completamente documentado
- ✅ **Fácil de testear**: Módulos pequeños facilitan pruebas unitarias
- ✅ **Fácil de extender**: Nueva funcionalidad se añade sin modificar código existente

### Funcionalidades Principales

- ✅ **Grabación automatizada**: Graba videos de YouTube automáticamente
- ✅ **Organización automática**: Crea carpetas y organiza archivos por módulos
- ✅ **Renombrado inteligente**: Renombra archivos con número y título del video
- ✅ **Manejo de popups**: Cierra automáticamente popups y anuncios de YouTube
- ✅ **Pantalla completa automática**: Activa pantalla completa para mejor calidad
- ✅ **Modo de prueba**: Permite probar el sistema con límites reducidos
- ✅ **Continuación de grabación**: Puede continuar desde un módulo o video específico
- ✅ **Logging detallado**: Información clara de cada paso del proceso
- ✅ **Manejo robusto de errores**: Recuperación automática de errores comunes
- ✅ **Estadísticas finales**: Resumen con videos grabados, duración y tamaño

---

## 🐛 Solución de Problemas

Ver sección completa en el README original para problemas comunes y soluciones.

---

## 📄 Licencia

Este proyecto es de uso personal/educativo.

---

**Última actualización**: Proyecto refactorizado con arquitectura modular ultra-optimizada para máxima legibilidad y mantenibilidad.
