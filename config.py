"""
Archivo de configuración centralizado para el sistema de grabación de videos.

Este módulo contiene todas las constantes y configuraciones necesarias
para el funcionamiento del sistema de automatización.
"""

# ==============================================================================
# CONFIGURACIÓN DE OBS STUDIO
# ==============================================================================

# Contraseña configurada en el plugin obs-websocket de OBS
# Si no configuraste contraseña en OBS, deja este campo como una cadena vacía: ""
OBS_PASSWORD = "l4MTFqrpVY1gpEVm"

# Host y puerto del servidor WebSocket de OBS
OBS_HOST = "localhost"
OBS_PORT = 4455

# ==============================================================================
# CONFIGURACIÓN DE ARCHIVOS
# ==============================================================================

# Archivo de texto que contiene las URLs de los videos organizadas por módulos
URL_FILE = "ulrls.txt"

# ==============================================================================
# CONFIGURACIÓN DE MÁRGENES DE GRABACIÓN
# ==============================================================================

# Margen de tiempo en segundos antes y después de la grabación del video.
# En modo prueba, estos márgenes se reducen para obtener duraciones más precisas
MARGEN_INICIAL = 4
MARGEN_FINAL = 4
MARGEN_INICIAL_PRUEBA = 1  # Margen reducido en modo prueba
MARGEN_FINAL_PRUEBA = 1  # Margen reducido en modo prueba

# ==============================================================================
# CONFIGURACIÓN DEL NAVEGADOR
# ==============================================================================

# Navegador a usar: "chrome" o "brave"
# Brave tiene bloqueo de anuncios integrado, recomendado para evitar popups y anuncios
NAVEGADOR = "brave"  # Cambia a "chrome" si prefieres usar Chrome

# IMPORTANTE: El script requiere que Brave esté abierto con --remote-debugging-port=9222
# El usuario debe configurar OBS manualmente para capturar la ventana de Brave
USAR_NAVEGADOR_EXISTENTE = True  # Siempre True - el navegador debe estar abierto previamente

# Puerto de depuración remota (debe coincidir con el usado al iniciar el navegador)
DEBUG_PORT = 9222  # Puerto por defecto para Chrome DevTools Protocol

# Configurar OBS automáticamente para capturar la ventana del navegador
CONFIGURAR_OBS_AUTOMATICAMENTE = False  # False = el usuario configura OBS manualmente

# ==============================================================================
# MODO DE PRUEBA
# ==============================================================================

# Configuración para hacer pruebas antes de ejecutar el proceso completo
MODO_PRUEBA = True  # Cambia a False para procesar todos los videos
MAX_MODULOS_PRUEBA = 1  # Número máximo de módulos a procesar en modo prueba (None = todos)
MAX_VIDEOS_POR_MODULO_PRUEBA = 2  # Número máximo de videos por módulo en modo prueba (None = todos)
DURACION_MAXIMA_PRUEBA = 15  # Duración máxima en segundos para cada video en modo prueba (None = duración real)

# Si DURACION_MAXIMA_PRUEBA está configurado, los videos se grabarán solo durante ese tiempo
# Útil para verificar que todo funciona sin esperar videos completos

