# Sistema de Grabación de Videos de YouTube

Sistema automatizado para grabar videos de YouTube utilizando Brave Browser y OBS Studio.

## 📋 Estructura del Proyecto

El proyecto ha sido refactorizado en una arquitectura modular profesional:

```
videos_ucm/
│
├── config.py              # Configuración centralizada del sistema
├── utils.py               # Funciones auxiliares compartidas
├── url_processor.py       # Procesador de URLs y creación de carpetas
├── browser_manager.py     # Gestor del navegador Brave
├── obs_manager.py         # Gestor de OBS Studio
├── orchestrator.py        # Orquestador principal (punto de entrada)
├── recorder.py            # Archivo original (deprecated)
├── ulrls.txt             # Archivo con URLs organizadas por módulos
└── README.md             # Este archivo
```

## 🔧 Módulos del Sistema

### 1. `config.py`
Archivo de configuración centralizado que contiene todas las constantes:
- Configuración de OBS Studio (host, puerto, contraseña)
- Configuración del navegador (Brave/Chrome)
- Configuración de archivos (ruta del archivo de URLs)
- Márgenes de grabación
- Configuración del modo de prueba

### 2. `utils.py`
Funciones auxiliares compartidas:
- `sanitizar_nombre_archivo()`: Limpia nombres de archivo
- `parsear_duracion_a_segundos()`: Convierte duración a segundos
- `formatear_tiempo()`: Formatea tiempo legible
- `formatear_tamaño()`: Formatea tamaño de archivos
- `configurar_logging()`: Configura el sistema de logging

### 3. `url_processor.py`
Gestiona el procesamiento de URLs:
- **`URLProcessor`**: Clase principal que:
  - Lee el archivo de texto con URLs organizadas por módulos
  - Valida URLs de YouTube
  - Crea la estructura de carpetas para cada módulo
  - Organiza URLs en diccionarios estructurados
  - Aplica límites de modo prueba

### 4. `browser_manager.py`
Gestiona el navegador Brave:
- **`BrowserManager`**: Clase principal que:
  - Conecta o abre el navegador Brave
  - Carga URLs de YouTube
  - Obtiene información de videos (título, duración)
  - Cierra popups y anuncios
  - Controla la reproducción de videos
  - Monitorea la reproducción

### 5. `obs_manager.py`
Gestiona OBS Studio:
- **`OBSManager`**: Clase principal que:
  - Conecta con OBS Studio vía WebSocket
  - Configura directorios de grabación
  - Inicia y detiene grabaciones
  - Verifica el estado de las grabaciones
  - Maneja errores de conexión

### 6. `orchestrator.py`
Coordina todos los módulos:
- **`Orchestrator`**: Clase principal que:
  - Orquesta el flujo completo del proceso
  - Coordina URLProcessor, BrowserManager y OBSManager
  - Gestiona el procesamiento de módulos y videos
  - Maneja archivos grabados (renombrado, movimiento)
  - Genera estadísticas y resúmenes
  - Maneja errores y limpieza de recursos

## 🚀 Uso

### Requisitos Previos

1. **Python 3.8 o superior**
2. **OBS Studio** con el plugin `obs-websocket` instalado y activado
3. **Brave Browser** (o Chrome) instalado
4. **Dependencias de Python** (ver `requirements.txt`)

### Instalación

1. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

2. Configurar OBS Studio:
   - Abrir OBS Studio
   - Instalar el plugin `obs-websocket` si no está instalado
   - Ir a: Herramientas > Configuración del servidor WebSocket
   - Habilitar el servidor WebSocket
   - Configurar la contraseña (si deseas) y copiarla a `config.py`

3. Configurar el navegador:
   - Cerrar todas las ventanas de Brave
   - Abrir PowerShell y ejecutar:
   ```powershell
   & "C:\Users\[TU_USUARIO]\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe" --remote-debugging-port=9222
   ```
   - O ajustar la ruta según tu instalación

### Configuración

Editar `config.py` con tus configuraciones:

```python
# Configuración de OBS
OBS_PASSWORD = "tu_contraseña"  # O "" si no usas contraseña
OBS_HOST = "localhost"
OBS_PORT = 4455

# Archivo de URLs
URL_FILE = "ulrls.txt"

# Modo de prueba (True para pruebas, False para producción)
MODO_PRUEBA = True
MAX_MODULOS_PRUEBA = 1
MAX_VIDEOS_POR_MODULO_PRUEBA = 2
DURACION_MAXIMA_PRUEBA = 15
```

### Ejecución

Ejecutar el orquestador principal:

```bash
python orchestrator.py
```

## 📝 Formato del Archivo de URLs

El archivo `ulrls.txt` debe seguir este formato:

```
#MOD01_python
https://www.youtube.com/watch?v=VIDEO_ID_1
https://www.youtube.com/watch?v=VIDEO_ID_2
https://www.youtube.com/watch?v=VIDEO_ID_3

#MOD02_sql
https://www.youtube.com/watch?v=VIDEO_ID_4
https://www.youtube.com/watch?v=VIDEO_ID_5
```

- Las líneas que empiezan con `#` definen módulos (nombres de carpetas)
- Las líneas que empiezan con `http` son URLs de videos de YouTube
- Las líneas vacías se ignoran

## 🛠️ Características

- ✅ **Arquitectura modular**: Separación clara de responsabilidades
- ✅ **Manejo robusto de errores**: Depuración completa en todos los módulos
- ✅ **Logging detallado**: Información clara de cada paso del proceso
- ✅ **Modo de prueba**: Permite probar el sistema con límites reducidos
- ✅ **Cierre automático de popups**: Maneja anuncios y banners de YouTube
- ✅ **Organización automática**: Crea carpetas y organiza archivos automáticamente
- ✅ **Estadísticas**: Resumen final con videos grabados, duración y tamaño

## 📊 Flujo del Proceso

1. **Procesamiento de URLs**: Lee y organiza las URLs por módulos
2. **Creación de carpetas**: Crea la estructura de directorios
3. **Conexión con OBS**: Conecta con OBS Studio
4. **Inicialización del navegador**: Conecta o abre Brave Browser
5. **Procesamiento de videos**:
   - Carga cada URL
   - Obtiene información del video (título, duración)
   - Inicia la grabación en OBS
   - Reproduce el video
   - Monitorea la reproducción
   - Detiene la grabación
   - Renombra y organiza el archivo
6. **Limpieza**: Cierra recursos y muestra resumen final

## ⚠️ Notas Importantes

- El navegador **debe estar abierto** con `--remote-debugging-port=9222` antes de ejecutar el script
- OBS Studio **debe estar abierto** y configurado para capturar la ventana del navegador
- En modo prueba, los videos se limitan según la configuración
- Los archivos existentes se sobreescriben automáticamente

## 🐛 Solución de Problemas

### No se puede conectar a OBS
- Verifica que OBS Studio esté abierto
- Verifica que el plugin `obs-websocket` esté instalado y activado
- Verifica la contraseña en `config.py`
- Verifica que el puerto sea el correcto (por defecto 4455)

### No se puede conectar al navegador
- Verifica que Brave esté abierto con `--remote-debugging-port=9222`
- Cierra todas las ventanas de Brave antes de abrir con el puerto de depuración
- Verifica que no haya otras instancias del navegador abiertas

### Los videos no se graban
- Verifica que OBS tenga al menos una fuente configurada en la escena
- Verifica que el formato de salida esté configurado en OBS
- Verifica que la ventana del navegador esté visible (no minimizada)
- Revisa los logs de OBS para más detalles

## 📄 Licencia

Este proyecto es de uso personal/educativo.

## 👤 Autor

Sistema de grabación automatizada desarrollado para uso educativo.

