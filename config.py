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

# IMPORTANTE: El script requiere que el navegador esté abierto con --remote-debugging-port=9222
# El usuario debe configurar OBS manualmente para capturar la ventana del navegador
# Puerto de depuración remota (debe coincidir con el usado al iniciar el navegador)
# Brave usa el mismo protocolo que Chrome (Chrome DevTools Protocol)
DEBUG_PORT = 9222

# ==============================================================================
# MODO DE PRUEBA
# ==============================================================================

# Configuración para hacer pruebas antes de ejecutar el proceso completo
MODO_PRUEBA = False  # Cambia a False para procesar todos los videos
MAX_MODULOS_PRUEBA = None  # Número máximo de módulos a procesar en modo prueba (None = todos)
MAX_VIDEOS_POR_MODULO_PRUEBA = None  # Número máximo de videos por módulo en modo prueba (None = todos)
DURACION_MAXIMA_PRUEBA = None  # Duración máxima en segundos para cada video en modo prueba (None = duración real)

# Si DURACION_MAXIMA_PRUEBA está configurado, los videos se grabarán solo durante ese tiempo
# Útil para verificar que todo funciona sin esperar videos completos

# ==============================================================================
# CONFIGURACIÓN DE CONTINUACIÓN DE GRABACIÓN
# ==============================================================================

# Nombre del módulo desde el cual empezar a grabar (None = empezar desde el primer módulo)
# Útil para continuar grabando después de haber completado módulos anteriores
# Ejemplo: "MOD02_sql" para empezar desde el segundo módulo
MODULO_INICIO = None  # None para empezar desde el primer módulo, o "MOD02_sql" para empezar desde el segundo

# Índice desde el cual empezar a grabar videos (1 = primer video, 11 = empezar desde el video 11)
# Útil para continuar grabando después de haber grabado algunos videos previamente
# None = empezar desde el primer video
# Ejemplo: Si ya grabaste los primeros 10 videos, configura INICIO_VIDEO = 11
INICIO_VIDEO = None  # Cambia a None para empezar desde el primer video, o a 11 para continuar desde el video 11

# Si quieres especificar diferentes índices de inicio por módulo, usa un diccionario:
# INICIO_VIDEO_POR_MODULO = {
#     "MOD01_python": 11,  # Empezar desde el video 11 del módulo 1
#     "MOD02_sql": 1,      # Empezar desde el primer video del módulo 2
# }
# Si INICIO_VIDEO_POR_MODULO está definido, tiene prioridad sobre INICIO_VIDEO
INICIO_VIDEO_POR_MODULO = None  # None o un diccionario como el ejemplo de arriba

