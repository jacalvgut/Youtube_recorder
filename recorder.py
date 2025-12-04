import os
import time
import re
import logging
import platform
from pathlib import Path

# Importar librerías para control de ventanas en Windows
WINDOWS_API_AVAILABLE = False
if platform.system() == "Windows":
    try:
        import win32gui
        import win32con
        import win32api
        WINDOWS_API_AVAILABLE = True
    except ImportError:
        WINDOWS_API_AVAILABLE = False
        # El warning se mostrará más tarde cuando se intente usar

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.options import Options
except ImportError:
    print("Error: Faltan bibliotecas de Selenium. Ejecuta: pip install selenium webdriver-manager")
    exit()

try:
    import obsws_python as obs
    from obsws_python.error import OBSSDKError
except ImportError:
    print("Error: Falta la biblioteca de OBS. Ejecuta: pip install obsws-python")
    exit()

# --- CONFIGURACIÓN ---
# ¡IMPORTANTE! Cambia esto por la contraseña que configuraste en el plugin obs-websocket de OBS.
# Si no configuraste contraseña en OBS, deja este campo como una cadena vacía: ""
OBS_PASSWORD = "l4MTFqrpVY1gpEVm"  # Cambia esto si configuraste una contraseña en OBS
OBS_HOST = "localhost"
OBS_PORT = 4455
URL_FILE = "ulrls.txt"

# Margen de tiempo en segundos antes y después de la grabación del video.
# En modo prueba, estos márgenes se reducen para obtener duraciones más precisas
MARGEN_INICIAL = 4
MARGEN_FINAL = 4
MARGEN_INICIAL_PRUEBA = 1  # Margen reducido en modo prueba
MARGEN_FINAL_PRUEBA = 1  # Margen reducido en modo prueba

# --- CONFIGURACIÓN DEL NAVEGADOR ---
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

# --- MODO DE PRUEBA ---
# Configuración para hacer pruebas antes de ejecutar el proceso completo
MODO_PRUEBA = True  # Cambia a False para procesar todos los videos
MAX_MODULOS_PRUEBA = 1  # Número máximo de módulos a procesar en modo prueba (None = todos)
MAX_VIDEOS_POR_MODULO_PRUEBA = 2  # Número máximo de videos por módulo en modo prueba (None = todos)
DURACION_MAXIMA_PRUEBA = 15  # Duración máxima en segundos para cada video en modo prueba (None = duración real)
# Si DURACION_MAXIMA_PRUEBA está configurado, los videos se grabarán solo durante ese tiempo
# Útil para verificar que todo funciona sin esperar videos completos

# --- INICIO DEL SCRIPT ---

def configurar_logging():
    """Configura el sistema de logging para mostrar información clara."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parsear_archivo_urls(filepath):
    """
    Lee el archivo de texto y lo convierte en un diccionario de módulos y URLs.
    Formato esperado: #MODXX_xxxx_xxxx seguido de URLs
    """
    logging.info("=" * 70)
    logging.info("VERIFICACIÓN: Leyendo archivo de URLs...")
    logging.info("=" * 70)
    
    if not Path(filepath).exists():
        logging.error(f"ERROR CRÍTICO: El archivo '{filepath}' no se encuentra en este directorio.")
        return None
    
    logging.info(f"✓ Archivo encontrado: {filepath}")
    
    modulos = {}
    modulo_actual = None
    lineas_procesadas = 0
    modulos_encontrados = 0
    urls_encontradas = 0
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for num_linea, linea in enumerate(f, 1):
                linea = linea.strip()
                if not linea:
                    continue
                
                lineas_procesadas += 1
                
                if linea.startswith('#'):
                    # Elimina el '#' y cualquier espacio al principio
                    modulo_actual = linea.lstrip('# ').strip()
                    if modulo_actual:
                        modulos[modulo_actual] = []
                        modulos_encontrados += 1
                        logging.info(f"✓ Módulo encontrado (línea {num_linea}): '{modulo_actual}'")
                    else:
                        logging.warning(f"ADVERTENCIA: Línea {num_linea} tiene '#' pero está vacía")
                elif modulo_actual and linea.startswith('http'):
                    modulos[modulo_actual].append(linea)
                    urls_encontradas += 1
                elif modulo_actual:
                    logging.warning(f"ADVERTENCIA: Línea {num_linea} ignorada (no es URL válida): {linea[:50]}")
        
        logging.info("=" * 70)
        logging.info(f"RESUMEN DE LECTURA:")
        logging.info(f"  - Líneas procesadas: {lineas_procesadas}")
        logging.info(f"  - Módulos encontrados: {modulos_encontrados}")
        logging.info(f"  - URLs encontradas: {urls_encontradas}")
        logging.info("=" * 70)
        
        if not modulos:
            logging.error("ERROR CRÍTICO: No se encontraron módulos en el archivo.")
            return None
        
        # Verificar que cada módulo tenga al menos una URL
        modulos_sin_urls = [mod for mod, urls in modulos.items() if not urls]
        if modulos_sin_urls:
            logging.warning(f"ADVERTENCIA: Módulos sin URLs: {modulos_sin_urls}")
        
        return modulos
        
    except Exception as e:
        logging.error(f"ERROR CRÍTICO al leer archivo: {e}")
        return None

def sanitizar_nombre_archivo(nombre):
    """
    Limpia un string para que sea un nombre de archivo válido.
    """
    nombre = re.sub(r'[\s|:]+', '_', nombre) # Reemplaza espacios, | y : con _
    nombre = re.sub(r'[\\/*?"<>|]', "", nombre) # Elimina caracteres no válidos
    return nombre[:150] # Limita la longitud

def parsear_duracion_a_segundos(duration_str):
    """
    Convierte un string de duración (ej. "1:05:30" o "15:20") a segundos.
    """
    if not duration_str or not duration_str.strip():
        return 0
    
    try:
        # Limpiar el string y dividir por ':'
        partes_str = duration_str.strip().split(':')
        # Filtrar partes vacías y convertir a int
        partes = [int(p) for p in partes_str if p.strip()]
        
        if len(partes) == 3: # HH:MM:SS
            return partes[0] * 3600 + partes[1] * 60 + partes[2]
        if len(partes) == 2: # MM:SS
            return partes[0] * 60 + partes[1]
        if len(partes) == 1: # SS
            return partes[0]
        return 0
    except (ValueError, IndexError) as e:
        logging.warning(f"Error al parsear duración '{duration_str}': {e}")
        return 0

def formatear_tiempo(segundos):
    """
    Convierte segundos a un formato legible (días, horas, minutos, segundos).
    """
    if segundos < 60:
        return f"{segundos} segundo(s)"
    
    minutos = segundos // 60
    segundos_restantes = segundos % 60
    
    if minutos < 60:
        if segundos_restantes > 0:
            return f"{minutos} minuto(s) y {segundos_restantes} segundo(s)"
        return f"{minutos} minuto(s)"
    
    horas = minutos // 60
    minutos_restantes = minutos % 60
    
    if horas < 24:
        if minutos_restantes > 0:
            return f"{horas} hora(s) y {minutos_restantes} minuto(s)"
        return f"{horas} hora(s)"
    
    dias = horas // 24
    horas_restantes = horas % 24
    
    if horas_restantes > 0:
        return f"{dias} día(s) y {horas_restantes} hora(s)"
    return f"{dias} día(s)"

def formatear_tamaño(bytes_size):
    """
    Convierte bytes a un formato legible (KB, MB, GB, TB).
    """
    if bytes_size < 1024:
        return f"{bytes_size} B"
    
    kb = bytes_size / 1024
    if kb < 1024:
        return f"{kb:.2f} KB"
    
    mb = kb / 1024
    if mb < 1024:
        return f"{mb:.2f} MB"
    
    gb = mb / 1024
    if gb < 1024:
        return f"{gb:.2f} GB"
    
    tb = gb / 1024
    return f"{tb:.2f} TB"

def crear_navegador():
    """
    Inicializa y devuelve una instancia del navegador Selenium.
    Si USAR_NAVEGADOR_EXISTENTE es True, se conecta a una instancia existente del navegador.
    """
    if USAR_NAVEGADOR_EXISTENTE:
        return conectar_a_navegador_existente()
    else:
        return abrir_nueva_ventana_navegador()

def obtener_ruta_navegador():
    """
    Obtiene la ruta del ejecutable del navegador según la configuración.
    """
    if NAVEGADOR.lower() == "brave":
        # Rutas comunes de Brave en Windows
        rutas_brave = [
            os.path.expanduser("~\\AppData\\Local\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"),
            "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            "C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
        ]
        for ruta in rutas_brave:
            if os.path.exists(ruta):
                return ruta
        return "brave.exe"  # Intentar desde PATH
    else:
        # Rutas comunes de Chrome en Windows
        rutas_chrome = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        ]
        for ruta in rutas_chrome:
            if os.path.exists(ruta):
                return ruta
        return "chrome.exe"  # Intentar desde PATH

def verificar_puerto_disponible(port):
    """
    Verifica si un puerto está disponible/abierto.
    """
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0  # True si el puerto está abierto
    except:
        return False

def abrir_brave_con_puerto_depuracion():
    """
    Intenta abrir Brave automáticamente con el puerto de depuración habilitado.
    """
    import subprocess
    nombre_navegador = "Brave" if NAVEGADOR.lower() == "brave" else "Chrome"
    ruta_navegador = obtener_ruta_navegador()
    
    if not os.path.exists(ruta_navegador):
        logging.error(f"No se encontró {nombre_navegador} en: {ruta_navegador}")
        return False
    
    try:
        logging.info(f"Abriendo {nombre_navegador} con puerto de depuración...")
        # Abrir Brave con el puerto de depuración en segundo plano
        subprocess.Popen([
            ruta_navegador,
            f"--remote-debugging-port={DEBUG_PORT}",
            "--new-window"
        ], shell=False)
        
        # Esperar a que el puerto esté disponible
        logging.info(f"Esperando a que {nombre_navegador} inicie el puerto de depuración...")
        for intento in range(10):
            time.sleep(1)
            if verificar_puerto_disponible(DEBUG_PORT):
                logging.info(f"✓ {nombre_navegador} iniciado correctamente con puerto de depuración")
                return True
        
        logging.warning(f"{nombre_navegador} se abrió pero el puerto aún no está disponible")
        return False
        
    except Exception as e:
        logging.error(f"Error al abrir {nombre_navegador}: {e}")
        return False

def conectar_a_navegador_existente():
    """
    Se conecta a una instancia existente del navegador que debe estar ejecutándose
    con el flag --remote-debugging-port. Si no está abierto, intenta abrirlo automáticamente.
    """
    nombre_navegador = "Brave" if NAVEGADOR.lower() == "brave" else "Chrome"
    logging.info(f"VERIFICACIÓN: Intentando conectarse a {nombre_navegador}...")
    
    # Verificar primero si el puerto está disponible
    if not verificar_puerto_disponible(DEBUG_PORT):
        logging.info("=" * 70)
        logging.info(f"El puerto {DEBUG_PORT} no está disponible")
        logging.info("=" * 70)
        logging.info("")
        logging.info(f"{nombre_navegador} no está abierto con el puerto de depuración habilitado.")
        logging.info("")
        logging.info(f"ACCION: Abriendo {nombre_navegador} automáticamente con el puerto de depuración...")
        logging.info("")
        
        # Intentar abrir Brave automáticamente
        if abrir_brave_con_puerto_depuracion():
            # Esperar un poco más para asegurar que esté listo
            time.sleep(3)
            logging.info(f"✓ {nombre_navegador} abierto correctamente")
        else:
            logging.error("=" * 70)
            logging.error(f"ERROR: No se pudo abrir {nombre_navegador} automáticamente")
            logging.error("=" * 70)
            logging.error("")
            logging.error("SOLUCIÓN MANUAL:")
            logging.error("")
            logging.error("1. Cierra TODAS las ventanas de Brave")
            logging.error("")
            logging.error("2. Abre PowerShell y ejecuta:")
            logging.error("")
            ruta_navegador = obtener_ruta_navegador()
            if os.path.exists(ruta_navegador):
                logging.error(f'   & "{ruta_navegador}" --remote-debugging-port={DEBUG_PORT}')
            else:
                if NAVEGADOR.lower() == "brave":
                    logging.error(f'   brave.exe --remote-debugging-port={DEBUG_PORT}')
                else:
                    logging.error(f'   chrome.exe --remote-debugging-port={DEBUG_PORT}')
            logging.error("")
            logging.error("3. Luego ejecuta este script nuevamente")
            logging.error("")
            logging.error("=" * 70)
            return None
    
    try:
        chrome_options = Options()
        # Conectar al navegador existente usando el puerto de depuración
        chrome_options.add_experimental_option("debuggerAddress", f"localhost:{DEBUG_PORT}")
        
        # No necesitamos Service ya que no vamos a iniciar el navegador
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        logging.info(f"✓ Conectado exitosamente a {nombre_navegador} existente (puerto {DEBUG_PORT})")
        logging.info(f"  Ventana actual: {driver.title}")
        logging.info(f"  URL actual: {driver.current_url}")
        
        return driver
        
    except WebDriverException as e:
        error_str = str(e)
        logging.error("=" * 70)
        logging.error(f"ERROR: No se pudo conectar a {nombre_navegador} existente")
        logging.error("=" * 70)
        logging.error("")
        
        if "cannot connect to chrome" in error_str.lower() or "not reachable" in error_str.lower():
            logging.error(f"El puerto {DEBUG_PORT} está abierto pero {nombre_navegador} no responde.")
            logging.error("")
            logging.error("POSIBLES CAUSAS:")
            logging.error("  1. Brave está abierto pero NO con --remote-debugging-port")
            logging.error("  2. Hay múltiples instancias de Brave abiertas")
            logging.error("  3. El puerto está siendo usado por otra aplicación")
            logging.error("")
            logging.error("SOLUCIÓN:")
            logging.error("  1. Cierra TODAS las ventanas de Brave (Ctrl+Shift+Esc para ver procesos)")
            logging.error("  2. Termina todos los procesos de Brave en el Administrador de tareas")
            logging.error("  3. Abre Brave NUEVAMENTE con el comando correcto:")
            logging.error("")
            ruta_navegador = obtener_ruta_navegador()
            if os.path.exists(ruta_navegador):
                logging.error(f'     & "{ruta_navegador}" --remote-debugging-port={DEBUG_PORT}')
            else:
                nombre_exe = "brave.exe" if NAVEGADOR.lower() == "brave" else "chrome.exe"
                logging.error(f'     {nombre_exe} --remote-debugging-port={DEBUG_PORT}')
        else:
            logging.error(f"Error inesperado al conectar con {nombre_navegador}.")
            logging.error("")
            logging.error("Asegúrate de que:")
            logging.error(f"  1. {nombre_navegador} esté abierto con --remote-debugging-port={DEBUG_PORT}")
            logging.error("  2. No haya otras instancias de Brave abiertas")
            logging.error("  3. El puerto {DEBUG_PORT} no esté siendo usado por otra aplicación")
        
        logging.error("")
        logging.error("=" * 70)
        logging.error(f"Error técnico: {e}")
        return None

def abrir_nueva_ventana_navegador():
    """
    Abre una nueva ventana del navegador (Chrome o Brave).
    """
    nombre_navegador = "Brave" if NAVEGADOR.lower() == "brave" else "Chrome"
    logging.info(f"Abriendo nueva ventana de {nombre_navegador}...")
    try:
        chrome_options = Options()
        
        # Si es Brave, especificar la ruta del ejecutable
        if NAVEGADOR.lower() == "brave":
            ruta_brave = obtener_ruta_navegador()
            if os.path.exists(ruta_brave):
                chrome_options.binary_location = ruta_brave
                logging.info(f"Usando Brave en: {ruta_brave}")
            else:
                logging.warning(f"No se encontró Brave en las rutas comunes. Intentando desde PATH...")
        
        # NO usar headless - la ventana debe ser visible para OBS
        chrome_options.add_argument("--start-maximized")  # Maximizar en lugar de fullscreen
        chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # Asegurar que el navegador cargue correctamente
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Deshabilitar notificaciones y popups que puedan interferir
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            # Permitir imágenes y contenido multimedia
            "profile.managed_default_content_settings.images": 1,
            "profile.default_content_setting_values.media_stream": 1,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Esperar un momento para que la ventana se cree
        time.sleep(2)
        
        # Asegurar que la ventana esté en primer plano y maximizada
        driver.maximize_window()
        
        # Navegar a una página de prueba para asegurar que el navegador funciona
        try:
            driver.get("about:blank")
            time.sleep(1)
        except:
            pass
        
        logging.info(f"✓ {nombre_navegador} iniciado correctamente")
        return driver
    except WebDriverException as e:
        logging.error(f"Error al iniciar {nombre_navegador}. ¿Está instalado? Error: {e}")
        if NAVEGADOR.lower() == "brave":
            logging.error("Asegúrate de tener Brave Browser instalado.")
            logging.error("Puedes descargarlo desde: https://brave.com")
        else:
            logging.error("Asegúrate de tener Google Chrome instalado.")
        return None

def detectar_monitor_obs(cliente_obs):
    """
    Detecta qué monitor está usando OBS basándose en las fuentes de Display Capture.
    Retorna el número de monitor (1 = primario, 2 = secundario, etc.) o None si no se puede detectar.
    """
    try:
        escenas = cliente_obs.get_scene_list()
        if not escenas.scenes:
            return None
        
        # Buscar en todas las escenas
        for escena_info in escenas.scenes:
            escena_nombre = escena_info.get('sceneName', escena_info.get('name', ''))
            try:
                # Obtener las fuentes de la escena
                items = cliente_obs.get_scene_item_list(escena_nombre)
                
                for item in items.scene_items:
                    # Buscar fuentes de tipo Display Capture
                    if item.get('inputKind') == 'monitor_capture' or item.get('sourceKind') == 'monitor_capture':
                        # Intentar obtener la configuración de la fuente
                        try:
                            config = cliente_obs.get_source_settings(item.get('sourceName', ''))
                            # El monitor puede estar en diferentes campos según la versión de OBS
                            monitor_id = config.source_settings.get('monitor', None)
                            if monitor_id is not None:
                                # Los monitores suelen estar indexados desde 0, convertir a 1-based
                                return int(monitor_id) + 1
                        except:
                            pass
            except:
                continue
        
        return None
    except Exception as e:
        logging.warning(f"No se pudo detectar el monitor de OBS: {e}")
        return None

def obtener_nombre_ventana_navegador(driver):
    """
    Obtiene el nombre/título de la ventana del navegador para usar en OBS Window Capture.
    """
    try:
        # Obtener el handle de la ventana
        hwnd = obtener_handle_ventana_navegador(driver)
        if hwnd and WINDOWS_API_AVAILABLE:
            titulo = win32gui.GetWindowText(hwnd)
            return titulo
        else:
            # Fallback: usar el título de Selenium
            return driver.title if driver.title else f"{NAVEGADOR.capitalize()} Browser"
    except Exception as e:
        logging.warning(f"No se pudo obtener el nombre de la ventana: {e}")
        return f"{NAVEGADOR.capitalize()} Browser"

def configurar_obs_window_capture(cliente_obs, driver, nombre_fuente="Captura_Navegador"):
    """
    Configura OBS automáticamente para capturar la ventana del navegador usando Window Capture.
    """
    try:
        # Obtener la escena activa
        escenas = cliente_obs.get_scene_list()
        if not escenas.scenes:
            logging.error("No hay escenas disponibles en OBS. Crea una escena primero.")
            return False
        
        escena_activa = escenas.scenes[0].get('sceneName', escenas.scenes[0].get('name', 'Scene'))
        logging.info(f"Usando escena: {escena_activa}")
        
        # Obtener el nombre de la ventana del navegador
        nombre_ventana = obtener_nombre_ventana_navegador(driver)
        logging.info(f"Nombre de ventana detectado: {nombre_ventana}")
        
        # Esperar un momento para que la ventana esté completamente cargada
        time.sleep(1)
        
        # Verificar si la fuente ya existe
        try:
            items = cliente_obs.get_scene_item_list(escena_activa)
            fuente_existente = None
            for item in items.scene_items:
                if item.get('sourceName') == nombre_fuente:
                    fuente_existente = item
                    break
            
            if fuente_existente:
                # La fuente ya existe, actualizar su configuración
                logging.info(f"Actualizando fuente existente: {nombre_fuente}")
                configuracion = {
                    'window': nombre_ventana,
                    'capture_cursor': True,
                    'method': 0,
                    'priority': 2
                }
                try:
                    cliente_obs.set_source_settings(nombre_fuente, configuracion)
                    logging.info(f"✓ Fuente '{nombre_fuente}' actualizada para capturar: {nombre_ventana}")
                except Exception as e:
                    logging.warning(f"No se pudo actualizar la fuente automáticamente: {e}")
                    logging.info("La fuente existe pero puede necesitar configuración manual")
            else:
                # Crear nueva fuente de Window Capture
                logging.info(f"Creando nueva fuente de Window Capture: {nombre_fuente}")
                
                # Configuración de la fuente
                configuracion = {
                    'window': nombre_ventana,
                    'capture_cursor': True,
                    'compatibility': False,
                    'method': 0,  # Método de captura: 0 = BitBlt (Windows), 1 = Windows Graphics Capture
                    'priority': 2  # Prioridad: 2 = Window Match (más confiable)
                }
                
                # Crear la fuente usando la API de OBS
                try:
                    # Intentar crear la fuente
                    resultado = cliente_obs.create_source(
                        sourceName=nombre_fuente,
                        sourceKind='window_capture',
                        sceneName=escena_activa,
                        sourceSettings=configuracion
                    )
                    logging.info(f"✓ Fuente '{nombre_fuente}' creada para capturar: {nombre_ventana}")
                except Exception as e:
                    # Si falla, intentar método alternativo
                    logging.warning(f"Error al crear fuente con create_source: {e}")
                    logging.info("Intentando método alternativo de creación...")
                    try:
                        # Método alternativo: crear fuente básica y luego configurarla
                        resultado = cliente_obs.create_source(
                            sourceName=nombre_fuente,
                            sourceKind='window_capture',
                            sceneName=escena_activa
                        )
                        time.sleep(0.5)
                        cliente_obs.set_source_settings(nombre_fuente, configuracion)
                        logging.info(f"✓ Fuente '{nombre_fuente}' creada usando método alternativo")
                    except Exception as e2:
                        logging.error(f"Error en método alternativo: {e2}")
                        logging.warning("No se pudo crear la fuente automáticamente.")
                        logging.warning(f"Por favor, crea manualmente una fuente 'Window Capture' llamada '{nombre_fuente}'")
                        logging.warning(f"y selecciona la ventana: {nombre_ventana}")
                        return False
            
            # Asegurar que la fuente esté visible
            try:
                items = cliente_obs.get_scene_item_list(escena_activa)
                for item in items.scene_items:
                    if item.get('sourceName') == nombre_fuente:
                        item_id = item.get('sceneItemId')
                        cliente_obs.set_scene_item_enabled(escena_activa, item_id, True)
                        break
            except:
                pass
            
            return True
            
        except Exception as e:
            logging.error(f"Error al configurar Window Capture en OBS: {e}")
            logging.warning("Intentando método alternativo...")
            # Método alternativo: usar el nombre de la ventana directamente
            try:
                configuracion = {
                    'window': nombre_ventana,
                    'capture_cursor': True,
                    'method': 0,
                    'priority': 2
                }
                cliente_obs.set_source_settings(nombre_fuente, configuracion)
                logging.info(f"✓ Configuración aplicada usando método alternativo")
                return True
            except Exception as e2:
                logging.error(f"Error en método alternativo: {e2}")
                return False
        
    except Exception as e:
        logging.error(f"Error al configurar OBS automáticamente: {e}")
        return False

def configurar_obs_para_captura(cliente_obs, driver):
    """
    Verifica y configura OBS para capturar la ventana del navegador.
    Si CONFIGURAR_OBS_AUTOMATICAMENTE es True, configura OBS automáticamente.
    """
    try:
        nombre_navegador = "Brave" if NAVEGADOR.lower() == "brave" else "Chrome"
        
        # Si se debe configurar automáticamente y no estamos usando navegador existente
        if CONFIGURAR_OBS_AUTOMATICAMENTE and not USAR_NAVEGADOR_EXISTENTE:
            logging.info("")
            logging.info("=" * 70)
            logging.info("CONFIGURANDO OBS AUTOMÁTICAMENTE")
            logging.info("=" * 70)
            
            # Detectar el monitor que OBS está usando
            monitor_obs = detectar_monitor_obs(cliente_obs)
            if monitor_obs:
                logging.info(f"Monitor detectado de OBS: Monitor {monitor_obs}")
                # Mover la ventana al monitor de OBS
                if mover_ventana_a_monitor(driver, monitor_obs):
                    logging.info(f"✓ Ventana de {nombre_navegador} movida al monitor {monitor_obs}")
                else:
                    logging.warning("No se pudo mover la ventana automáticamente. Asegúrate de que esté en el monitor correcto.")
            else:
                logging.info("No se pudo detectar el monitor de OBS. Usando monitor primario.")
                mover_ventana_a_monitor(driver, 1)
            
            # Configurar OBS para capturar la ventana del navegador
            # Esperar a que la ventana esté completamente cargada y visible
            logging.info("Esperando a que la ventana del navegador esté lista...")
            time.sleep(3)
            
            # Asegurar que la ventana esté visible
            asegurar_ventana_visible(driver)
            driver.switch_to.window(driver.current_window_handle)
            driver.execute_script("window.focus();")
            time.sleep(1)
            
            if configurar_obs_window_capture(cliente_obs, driver):
                logging.info("✓ OBS configurado automáticamente para capturar la ventana del navegador")
                
                # Verificar que la fuente esté visible y activa
                try:
                    escenas = cliente_obs.get_scene_list()
                    if escenas.scenes:
                        escena_activa = escenas.scenes[0].get('sceneName', escenas.scenes[0].get('name', 'Scene'))
                        items = cliente_obs.get_scene_item_list(escena_activa)
                        for item in items.scene_items:
                            if 'Captura_Navegador' in item.get('sourceName', ''):
                                item_id = item.get('sceneItemId')
                                # Asegurar que esté visible
                                cliente_obs.set_scene_item_enabled(escena_activa, item_id, True)
                                logging.info("✓ Fuente de captura verificada y activada")
                                break
                except Exception as e:
                    logging.warning(f"No se pudo verificar la fuente: {e}")
                
                logging.info("=" * 70)
                logging.info("")
                return True
            else:
                logging.warning("No se pudo configurar OBS automáticamente. Revisa la configuración manualmente.")
                logging.info("=" * 70)
                logging.info("")
        
        # Obtener escenas disponibles
        escenas = cliente_obs.get_scene_list()
        if not escenas.scenes:
            logging.warning("No se encontraron escenas en OBS.")
            logging.warning("IMPORTANTE: Crea una escena en OBS antes de continuar.")
        else:
            escena_actual = escenas.scenes[0].get('sceneName', escenas.scenes[0].get('name', 'Scene'))
            logging.info(f"Escena activa en OBS: {escena_actual}")
        
        # Mostrar instrucciones según el modo
        if USAR_NAVEGADOR_EXISTENTE:
            logging.info("")
            logging.info("=" * 70)
            logging.info(f"MODO: Usando {nombre_navegador} existente")
            logging.info("=" * 70)
            logging.info(f"El script usará la ventana de {nombre_navegador} que ya tienes abierta.")
            logging.info("Asegúrate de que:")
            logging.info(f"  1. {nombre_navegador} esté iniciado con --remote-debugging-port={DEBUG_PORT}")
            logging.info("  2. OBS esté configurado para capturar esa ventana específica")
            logging.info("  3. La ventana del navegador esté visible (no minimizada)")
            if NAVEGADOR.lower() == "brave":
                logging.info("  4. Brave tiene bloqueo de anuncios integrado (recomendado)")
            logging.info("=" * 70)
            logging.info("")
        else:
            # Si no se configuró automáticamente, mostrar instrucciones
            if not CONFIGURAR_OBS_AUTOMATICAMENTE:
                logging.warning("")
                logging.warning("=" * 70)
                logging.warning("CONFIGURACIÓN REQUERIDA EN OBS STUDIO")
                logging.warning("=" * 70)
                logging.warning("Para que OBS capture el contenido del navegador, debes configurar:")
                logging.warning("")
                logging.warning("OPCIÓN 1 - Captura de Ventana (Recomendado):")
                logging.warning("  1. En OBS, en la sección 'Fuentes', haz clic en '+'")
                logging.warning(f"  2. Selecciona 'Captura de ventana' (Window Capture)")
                nombre_ventana = obtener_nombre_ventana_navegador(driver)
                logging.warning(f"  3. En 'Ventana', selecciona: {nombre_ventana}")
                logging.warning("  4. Asegúrate de que la fuente esté visible y activa")
                logging.warning("")
                logging.warning("OPCIÓN 2 - Captura de Pantalla (Alternativa):")
                logging.warning("  1. En OBS, en la sección 'Fuentes', haz clic en '+'")
                logging.warning("  2. Selecciona 'Captura de pantalla' (Display Capture)")
                logging.warning(f"  3. Selecciona el monitor donde está {nombre_navegador}")
                logging.warning("")
                logging.warning("IMPORTANTE:")
                logging.warning(f"  - La ventana de {nombre_navegador} DEBE estar visible (no minimizada)")
                logging.warning(f"  - {nombre_navegador} debe estar en el monitor que OBS está capturando")
                logging.warning("  - Asegúrate de que la fuente esté visible en la vista previa de OBS")
                logging.warning("")
                logging.warning("TIP: Cambia CONFIGURAR_OBS_AUTOMATICAMENTE = True para configuración automática")
                logging.warning("=" * 70)
                logging.warning("")
                logging.warning("El script continuará en 3 segundos...")
                time.sleep(3)
        
        return True
        
    except Exception as e:
        logging.error(f"Error al verificar configuración de OBS: {e}")
        return False

def obtener_handle_ventana_navegador(driver):
    """
    Obtiene el handle de la ventana de Windows para el navegador (Chrome o Brave).
    """
    if not WINDOWS_API_AVAILABLE:
        return None
    
    try:
        # Obtener el título de la ventana actual de Selenium
        titulo_ventana = driver.title if driver.title else ""
        current_url = driver.current_url if hasattr(driver, 'current_url') else ""
        
        # Buscar la ventana del navegador usando EnumWindows
        windows_found = []
        nombre_buscar = "brave" if NAVEGADOR.lower() == "brave" else "chrome"
        
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                # Buscar ventanas del navegador
                if nombre_buscar in window_title.lower() or "google chrome" in window_title.lower():
                    # Verificar que sea la ventana principal (sin padre)
                    if win32gui.GetParent(hwnd) == 0:
                        windows_found.append(hwnd)
            return True
        
        # Enumerar todas las ventanas
        win32gui.EnumWindows(callback, None)
        
        # Si encontramos ventanas, usar la primera (o la más reciente)
        if windows_found:
            # Intentar encontrar la ventana que coincide con el título actual
            for hwnd in windows_found:
                window_title = win32gui.GetWindowText(hwnd)
                if titulo_ventana and titulo_ventana.lower() in window_title.lower():
                    return hwnd
            # Si no hay coincidencia, usar la primera ventana encontrada
            return windows_found[0]
        
        return None
    except Exception as e:
        logging.warning(f"No se pudo obtener el handle de la ventana: {e}")
        return None

def mover_ventana_a_monitor(driver, monitor_num=1):
    """
    Mueve la ventana del navegador al monitor especificado.
    monitor_num: 1 = primario, 2 = secundario, etc.
    """
    if not WINDOWS_API_AVAILABLE or platform.system() != "Windows":
        logging.warning("No se puede controlar la posición de la ventana en este sistema.")
        return False
    
    try:
        # Obtener el handle de la ventana
        hwnd = obtener_handle_ventana_navegador(driver)
        if not hwnd:
            logging.warning("No se pudo encontrar la ventana de Chrome.")
            return False
        
        # Obtener información de los monitores
        import ctypes
        from ctypes import wintypes
        
        monitors = []
        
        def callback(hmonitor, hdc, lprect, lparam):
            if lprect:
                rect = lprect.contents
                monitors.append({
                    'left': rect.left,
                    'top': rect.top,
                    'right': rect.right,
                    'bottom': rect.bottom,
                    'width': rect.right - rect.left,
                    'height': rect.bottom - rect.top
                })
            return True
        
        MonitorEnumProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.POINTER(wintypes.RECT),
            ctypes.c_ulong
        )
        
        user32 = ctypes.windll.user32
        callback_ptr = MonitorEnumProc(callback)
        user32.EnumDisplayMonitors(None, None, callback_ptr, 0)
        
        if not monitors:
            logging.warning("No se pudieron detectar los monitores. Usando método alternativo.")
            # Método alternativo: usar GetSystemMetrics para el monitor primario
            if monitor_num == 1:
                width = win32api.GetSystemMetrics(0)  # SM_CXSCREEN
                height = win32api.GetSystemMetrics(1)  # SM_CYSCREEN
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, 0, 0, width, height, win32con.SWP_SHOWWINDOW)
                logging.info(f"Ventana de Chrome movida al monitor primario ({width}x{height})")
                return True
            else:
                logging.warning(f"No se puede mover al monitor {monitor_num} sin información de monitores.")
                return False
        
        if monitor_num < 1 or monitor_num > len(monitors):
            logging.warning(f"Monitor {monitor_num} no existe. Usando monitor primario.")
            monitor_num = 1
        
        # Obtener las coordenadas del monitor destino
        monitor = monitors[monitor_num - 1]
        left = monitor['left']
        top = monitor['top']
        width = monitor['width']
        height = monitor['height']
        
        # Mover y redimensionar la ventana
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOP,
            left,
            top,
            width,
            height,
            win32con.SWP_SHOWWINDOW
        )
        
        nombre_navegador = "Brave" if NAVEGADOR.lower() == "brave" else "Chrome"
        logging.info(f"Ventana de {nombre_navegador} movida al monitor {monitor_num} ({width}x{height})")
        return True
        
    except Exception as e:
        logging.warning(f"No se pudo mover la ventana al monitor: {e}")
        nombre_navegador = "Brave" if NAVEGADOR.lower() == "brave" else "Chrome"
        logging.warning(f"Asegúrate de que {nombre_navegador} esté en el monitor correcto manualmente.")
        return False

def asegurar_ventana_visible(driver):
    """
    Asegura que la ventana del navegador esté visible y enfocada.
    Si estamos usando Chrome existente, no intenta mover la ventana.
    """
    try:
        # Cambiar a la ventana actual
        driver.switch_to.window(driver.current_window_handle)
        
        # Si no estamos usando navegador existente, podemos intentar mover la ventana
        if not USAR_NAVEGADOR_EXISTENTE:
            # Maximizar la ventana solo si no es Chrome existente
            try:
                driver.maximize_window()
            except:
                pass
        
        # Traer la ventana al frente (usando JavaScript)
        driver.execute_script("window.focus();")
        time.sleep(0.5)
        return True
    except Exception as e:
        logging.warning(f"No se pudo asegurar que la ventana esté visible: {e}")
        return False

def cerrar_popups_youtube(driver, max_intentos=5):
    """
    Cierra todos los tipos de popups, banners y anuncios de YouTube.
    Incluye: cookies, inicio de sesión, premium, anuncios, etc.
    """
    popups_cerrados = 0
    
    # Lista exhaustiva de selectores para diferentes tipos de popups
    selectores_popups = [
        # Banner de cookies
        "button[aria-label*='Aceptar']",
        "button[aria-label*='Accept']",
        "button[aria-label*='Aceptar todo']",
        "button[aria-label*='Accept all']",
        "ytd-consent-bump-v2-lightbox button",
        "#content button[aria-label*='Aceptar']",
        
        # Botones de cerrar (X)
        "button[aria-label*='Cerrar']",
        "button[aria-label*='Close']",
        "button[aria-label*='Dismiss']",
        "button[aria-label*='Descartar']",
        ".ytp-ad-overlay-close-button",
        "button.close-button",
        "button.dismiss-button",
        
        # Avisos de inicio de sesión
        "ytd-popup-container button",
        "ytd-modal-with-title-and-button-renderer button",
        "#dismiss-button",
        "button[aria-label*='No, gracias']",
        "button[aria-label*='No thanks']",
        "button[aria-label*='Ahora no']",
        "button[aria-label*='Not now']",
        
        # Ofertas de Premium
        "button[aria-label*='Cerrar']",
        "ytd-mealbar-promo-renderer button",
        "ytd-popup-container ytd-mealbar-promo-renderer button",
        
        # Anuncios de video (Skip Ad)
        "button.ytp-ad-skip-button",
        ".ytp-ad-skip-button",
        "button[aria-label*='Omitir']",
        "button[aria-label*='Skip']",
        "button.ytp-ad-skip-button-modern",
        
        # Overlays de anuncios
        ".ytp-ad-overlay-close-container",
        ".ytp-ad-overlay-close-button",
        "button.ytp-ad-overlay-close-button",
        
        # Banners superiores
        "ytd-banner-promo-renderer button",
        "#dismiss-button",
        "ytd-popup-container #dismiss-button",
    ]
    
    for intento in range(max_intentos):
        popups_encontrados = False
        
        for selector in selectores_popups:
            try:
                elementos = driver.find_elements(By.CSS_SELECTOR, selector)
                for elemento in elementos:
                    try:
                        # Verificar que el elemento sea visible y clickeable
                        if elemento.is_displayed() and elemento.is_enabled():
                            # Intentar hacer scroll al elemento si es necesario
                            driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
                            time.sleep(0.2)
                            
                            # Intentar hacer clic
                            elemento.click()
                            logging.info(f"Popup cerrado: {selector[:50]}...")
                            popups_cerrados += 1
                            popups_encontrados = True
                            time.sleep(0.5)
                            break
                    except Exception as e:
                        # Si el clic normal falla, intentar con JavaScript
                        try:
                            driver.execute_script("arguments[0].click();", elemento)
                            logging.info(f"Popup cerrado (JS): {selector[:50]}...")
                            popups_cerrados += 1
                            popups_encontrados = True
                            time.sleep(0.5)
                            break
                        except:
                            continue
            except:
                continue
        
        # Si no encontramos más popups, salir
        if not popups_encontrados:
            break
        
        time.sleep(0.3)
    
    if popups_cerrados > 0:
        logging.info(f"Total de popups cerrados: {popups_cerrados}")
    
    return popups_cerrados > 0

def intentar_omitir_anuncios(driver, max_intentos=10):
    """
    Intenta omitir anuncios de YouTube si están presentes.
    Busca botones de 'Omitir anuncio' y los hace clic.
    """
    for intento in range(max_intentos):
        try:
            # Buscar botón "Omitir anuncio" (Skip Ad)
            selectores_skip = [
                "button.ytp-ad-skip-button",
                ".ytp-ad-skip-button",
                "button[aria-label*='Omitir']",
                "button[aria-label*='Skip']",
                ".ytp-ad-overlay-close-button",
                "button.ytp-ad-skip-button-modern"
            ]
            
            for selector in selectores_skip:
                try:
                    boton_skip = driver.find_element(By.CSS_SELECTOR, selector)
                    if boton_skip.is_displayed():
                        # Intentar clic normal primero
                        try:
                            boton_skip.click()
                        except:
                            # Si falla, usar JavaScript
                            driver.execute_script("arguments[0].click();", boton_skip)
                        logging.info("Anuncio omitido exitosamente")
                        time.sleep(1)
                        return True
                except:
                    continue
            
            # Verificar si aún hay un anuncio activo
            try:
                # Si no hay botón de skip visible, puede que el anuncio ya terminó
                driver.find_element(By.CLASS_NAME, "ytp-ad-module")
                time.sleep(0.5)  # Esperar un poco más
            except:
                # No hay anuncio activo
                break
                
        except Exception as e:
            pass
        
        time.sleep(0.5)
    
    return False

def main():
    """
    Función principal que orquesta la automatización.
    """
    configurar_logging()
    
    # Mostrar información del modo de prueba
    if MODO_PRUEBA:
        logging.warning("=" * 60)
        logging.warning("MODO DE PRUEBA ACTIVADO")
        logging.warning("=" * 60)
        if MAX_MODULOS_PRUEBA:
            logging.info(f"  - Máximo de módulos a procesar: {MAX_MODULOS_PRUEBA}")
        if MAX_VIDEOS_POR_MODULO_PRUEBA:
            logging.info(f"  - Máximo de videos por módulo: {MAX_VIDEOS_POR_MODULO_PRUEBA}")
        if DURACION_MAXIMA_PRUEBA:
            logging.info(f"  - Duración máxima por video: {DURACION_MAXIMA_PRUEBA} segundos (modo prueba)")
        logging.warning("=" * 60)
        logging.warning("Para procesar todos los videos, cambia MODO_PRUEBA = False")
        logging.warning("=" * 60)
        time.sleep(3)  # Pausa para que el usuario vea el mensaje
    
    # Inicializar estadísticas de ejecución y variables para el resumen
    estadisticas = {
        'videos_grabados': 0,
        'duracion_total_segundos': 0,
        'tamaño_total_bytes': 0,
        'archivos_grabados': []  # Lista de rutas de archivos grabados
    }
    modulos_procesados = []  # Lista de módulos procesados para el resumen final
    
    # 1. Parsear el archivo de URLs
    modulos = parsear_archivo_urls(URL_FILE)
    if not modulos:
        return
    
    # Limitar módulos en modo prueba
    if MODO_PRUEBA and MAX_MODULOS_PRUEBA:
        modulos_lista = list(modulos.items())
        modulos_limitados = dict(modulos_lista[:MAX_MODULOS_PRUEBA])
        modulos_omitidos = len(modulos) - len(modulos_limitados)
        if modulos_omitidos > 0:
            logging.info(f"Modo prueba: Procesando solo {len(modulos_limitados)} de {len(modulos)} módulos")
        modulos = modulos_limitados
    
    # Guardar lista de módulos procesados para el resumen final
    modulos_procesados = list(modulos.keys())
    
    # Mostrar resumen de lo que se procesará
    total_videos = sum(len(urls) for urls in modulos.values())
    if MODO_PRUEBA and MAX_VIDEOS_POR_MODULO_PRUEBA:
        total_videos = sum(min(len(urls), MAX_VIDEOS_POR_MODULO_PRUEBA) for urls in modulos.values())
    
    logging.info("")
    logging.info("=" * 60)
    logging.info(f"RESUMEN: Se procesarán {len(modulos)} módulo(s) con {total_videos} video(s) en total")
    logging.info("=" * 60)
    logging.info("")

    # 2. Conectar con OBS
    try:
        password_info = "con contraseña" if OBS_PASSWORD else "sin contraseña"
        logging.info(f"Conectando a OBS en {OBS_HOST}:{OBS_PORT} ({password_info})...")
        cliente_obs = obs.ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD, timeout=10)
        version = cliente_obs.get_version()
        logging.info(f"Conexión con OBS exitosa (Versión de OBS: {version.obs_version}, Plugin Websocket: {version.obs_web_socket_version})")
    except (ConnectionRefusedError, OBSSDKError, Exception) as e:
        logging.error("No se pudo conectar a OBS. Verifica que:")
        logging.error("1. OBS Studio esté abierto.")
        logging.error("2. El plugin 'obs-websocket' esté instalado y activado.")
        logging.error("   Ve a: Herramientas > Configuración del servidor WebSocket")
        logging.error("   Asegúrate de que el servidor esté habilitado.")
        if OBS_PASSWORD:
            logging.error(f"3. La contraseña en el script sea correcta (actualmente configurada).")
        else:
            logging.error("3. Si configuraste una contraseña en OBS, agrega 'OBS_PASSWORD = \"tu_contraseña\"' en el script.")
        logging.error(f"Error original: {e}")
        return
        
    # 3. Iniciar el navegador
    logging.info("")
    logging.info("=" * 70)
    logging.info("VERIFICACIÓN: Iniciando navegador Brave...")
    logging.info("=" * 70)
    
    driver = crear_navegador()
    if not driver:
        logging.error("ERROR CRÍTICO: No se pudo iniciar o conectar al navegador.")
        logging.error("El script no puede continuar sin el navegador.")
        return
    
    # Verificar que el navegador está funcionando
    try:
        driver.current_url
        logging.info("✓ Navegador conectado y funcionando")
        logging.info(f"  - URL actual: {driver.current_url}")
        logging.info(f"  - Título: {driver.title}")
        logging.info(f"  - Ventanas abiertas: {len(driver.window_handles)}")
    except Exception as e:
        logging.error(f"ERROR CRÍTICO: El navegador no responde: {e}")
        return
    
    logging.info("=" * 70)
    
    # Verificar configuración de OBS (solo informativo, no configura automáticamente)
    logging.info("")
    logging.info("=" * 70)
    logging.info("CONFIGURACIÓN REQUERIDA")
    logging.info("=" * 70)
    logging.info("IMPORTANTE: Asegúrate de que:")
    logging.info("  1. Brave esté abierto con --remote-debugging-port=9222")
    logging.info("  2. OBS esté configurado para capturar la ventana de Brave")
    logging.info("  3. La ventana de Brave esté visible en el monitor correcto")
    logging.info("=" * 70)
    logging.info("")
    time.sleep(2)
    
    # Asegurar que la ventana esté visible y enfocada
    asegurar_ventana_visible(driver)
    time.sleep(1)

    # 4. Procesar cada módulo y video
    directorio_base = Path.cwd()
    try:
        for nombre_modulo, urls in modulos.items():
            logging.info("")
            logging.info("=" * 70)
            logging.info(f"VERIFICACIÓN: Procesando Módulo: {nombre_modulo}")
            logging.info("=" * 70)
            
            ruta_modulo = directorio_base / nombre_modulo
            
            # Crear carpeta (sobreescribir si existe)
            if ruta_modulo.exists():
                logging.info(f"ADVERTENCIA: La carpeta '{nombre_modulo}' ya existe. Se sobreescribirán archivos.")
            else:
                logging.info(f"Creando carpeta: {nombre_modulo}")
            
            ruta_modulo.mkdir(exist_ok=True)
            logging.info(f"✓ Carpeta lista: {ruta_modulo}")
            
            # Establecer el directorio de grabación en OBS
            try:
                cliente_obs.set_record_directory(str(ruta_modulo.resolve()))
                logging.info(f"✓ Directorio de grabación OBS configurado: {ruta_modulo}")
            except Exception as e:
                logging.error(f"ERROR CRÍTICO: No se pudo configurar directorio en OBS: {e}")
                continue
            
            # Limitar videos por módulo en modo prueba
            urls_a_procesar = urls
            if MODO_PRUEBA and MAX_VIDEOS_POR_MODULO_PRUEBA:
                urls_a_procesar = urls[:MAX_VIDEOS_POR_MODULO_PRUEBA]
                if len(urls) > MAX_VIDEOS_POR_MODULO_PRUEBA:
                    logging.info(f"Modo prueba: Procesando solo {len(urls_a_procesar)} de {len(urls)} videos en este módulo")

            for i, url in enumerate(urls_a_procesar, 1):
                try:
                    logging.info("")
                    logging.info("=" * 70)
                    logging.info(f"Procesando video {i}/{len(urls_a_procesar)}: {url}")
                    logging.info("=" * 70)
                    
                    # Asegurar que estamos en una ventana válida
                    try:
                        ventanas_antes = driver.window_handles
                        logging.info(f"Ventanas abiertas antes: {len(ventanas_antes)}")
                    except:
                        logging.error("Error al obtener ventanas. Reintentando conexión...")
                        driver = crear_navegador()
                        if not driver:
                            logging.error("No se pudo reconectar al navegador. Saltando video.")
                            continue
                    
                    # VERIFICACIÓN: Abrir URL en el navegador
                    logging.info("")
                    logging.info("=" * 70)
                    logging.info("VERIFICACIÓN: Cargando video en navegador...")
                    logging.info("=" * 70)
                    logging.info(f"URL: {url}")
                    
                    try:
                        # Intentar abrir en nueva pestaña
                        driver.execute_script(f"window.open('{url}', '_blank');")
                        time.sleep(2)
                        
                        # Verificar que se creó una nueva pestaña
                        ventanas_despues = driver.window_handles
                        logging.info(f"Ventanas antes: {len(ventanas_antes)}, después: {len(ventanas_despues)}")
                        
                        if len(ventanas_despues) > len(ventanas_antes):
                            nueva_ventana = [w for w in ventanas_despues if w not in ventanas_antes][0]
                            driver.switch_to.window(nueva_ventana)
                            logging.info("✓ Nueva pestaña creada y activada")
                        elif len(ventanas_despues) > 0:
                            driver.switch_to.window(ventanas_despues[-1])
                            logging.info("✓ Usando última pestaña disponible")
                        else:
                            logging.warning("No se pudo abrir nueva pestaña. Usando driver.get()...")
                            driver.get(url)
                    except Exception as e:
                        logging.warning(f"Error al abrir nueva pestaña: {e}")
                        logging.info("Intentando con driver.get() directamente...")
                        driver.get(url)
                    
                    # VERIFICACIÓN: Esperar a que la página cargue completamente
                    wait = WebDriverWait(driver, 30)
                    try:
                        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
                        logging.info("✓ Página cargada completamente (readyState = complete)")
                    except TimeoutException:
                        logging.error("ERROR: Timeout esperando carga completa de la página")
                        logging.error("El video puede no haberse cargado correctamente.")
                        continue
                    
                    # Verificar que estamos en YouTube
                    url_actual = driver.current_url
                    if "youtube.com" not in url_actual.lower():
                        logging.error(f"ERROR: No se está en YouTube. URL actual: {url_actual}")
                        continue
                    logging.info(f"✓ Confirmado: Estamos en YouTube ({url_actual[:50]}...)")
                    
                    # Esperar adicional para que YouTube cargue completamente
                    time.sleep(5)
                    logging.info("✓ Tiempo de espera adicional completado")
                    
                    # Cerrar todos los popups, banners y anuncios iniciales
                    logging.info("Cerrando popups y banners iniciales...")
                    cerrar_popups_youtube(driver, max_intentos=5)
                    time.sleep(2)
                    
                    # Esperar a que el título y la duración estén disponibles
                    wait = WebDriverWait(driver, 30)
                    
                    # Intentar múltiples selectores para el título
                    titulo_video = None
                    selectores_titulo = [
                        "h1.ytd-watch-metadata yt-formatted-string",
                        "h1.style-scope.ytd-watch-metadata",
                        "h1.ytd-video-primary-info-renderer",
                        ".ytd-watch-metadata h1"
                    ]
                    
                    for selector in selectores_titulo:
                        try:
                            titulo_elemento = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                            titulo_video = titulo_elemento.text
                            if titulo_video:
                                break
                        except:
                            continue
                    
                    if not titulo_video:
                        logging.warning(f"No se pudo obtener el título del video. Intentando continuar...")
                        titulo_video = f"video_{i}"
                    
                    logging.info(f"Título obtenido: {titulo_video}")
                    
                    # Esperar a que la duración esté disponible
                    try:
                        duracion_elemento = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ytp-time-duration")))
                        duracion_str = duracion_elemento.text
                    except:
                        # Intentar obtener duración de otro elemento
                        try:
                            duracion_elemento = driver.find_element(By.CSS_SELECTOR, ".ytp-time-duration")
                            duracion_str = duracion_elemento.text
                        except:
                            logging.warning(f"No se pudo obtener la duración. Usando duración por defecto.")
                            duracion_str = "0:00"
                    
                    duracion_segundos = parsear_duracion_a_segundos(duracion_str)
                    logging.info(f"Duración detectada: {duracion_str} ({duracion_segundos} segundos)")

                    if duracion_segundos == 0:
                        logging.warning(f"No se pudo obtener la duración para '{titulo_video}'. Saltando video.")
                        continue
                    
                    # Aplicar limitación de duración en modo prueba
                    duracion_original = duracion_segundos
                    if MODO_PRUEBA and DURACION_MAXIMA_PRUEBA:
                        duracion_segundos = min(duracion_segundos, DURACION_MAXIMA_PRUEBA)
                        if duracion_original > DURACION_MAXIMA_PRUEBA:
                            logging.info(f"Modo prueba: Limitando grabación a {DURACION_MAXIMA_PRUEBA}s (duración real: {duracion_str})")
                    
                    nombre_archivo_saneado = sanitizar_nombre_archivo(titulo_video)
                    
                    logging.info(f"Video detectado: '{titulo_video}' (Duración: {duracion_str})")
                    
                    # Asegurar que no hay grabación activa antes de empezar
                    try:
                        estado_grabacion = cliente_obs.get_record_status()
                        if estado_grabacion.output_active:
                            logging.warning("Hay una grabación activa. Deteniéndola...")
                            try:
                                cliente_obs.stop_record()
                                time.sleep(2)  # Esperar a que se detenga completamente
                            except:
                                pass
                    except:
                        pass
                    
                    # Asegurar que la pestaña esté enfocada y visible
                    driver.switch_to.window(driver.current_window_handle)
                    driver.execute_script("window.focus();")
                    
                    # Traer la ventana al frente usando Windows API si está disponible
                    if WINDOWS_API_AVAILABLE:
                        try:
                            hwnd = obtener_handle_ventana_navegador(driver)
                            if hwnd:
                                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                                win32gui.SetForegroundWindow(hwnd)
                                win32gui.BringWindowToTop(hwnd)
                        except:
                            pass
                    
                    time.sleep(1)
                    
                    # Hacer scroll al inicio para asegurar que el reproductor esté visible
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(0.5)
                    
                    # Reproducir el video PRIMERO (antes de iniciar la grabación)
                    logging.info("Iniciando reproducción del video...")
                    try:
                        boton_play = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "ytp-play-button")))
                        boton_play.click()
                        logging.info("✓ Reproducción iniciada")
                    except:
                        logging.warning("No se pudo hacer clic en el botón de reproducción. Intentando métodos alternativos...")
                        try:
                            driver.execute_script("document.querySelector('.ytp-play-button').click();")
                        except:
                            pass
                    
                    # Esperar a que el video realmente comience a reproducirse
                    logging.info("Esperando a que el video comience a reproducirse...")
                    time.sleep(3)  # Esperar a que el video cargue y comience
                    
                    # Cerrar cualquier popup que haya aparecido
                    cerrar_popups_youtube(driver, max_intentos=3)
                    
                    # Intentar omitir anuncios iniciales
                    intentar_omitir_anuncios(driver)
                    
                    # Asegurar que la ventana esté visible antes de grabar (CRÍTICO para captura visual)
                    logging.info("Asegurando que la ventana esté visible para OBS...")
                    if WINDOWS_API_AVAILABLE:
                        try:
                            hwnd = obtener_handle_ventana_navegador(driver)
                            if hwnd:
                                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                                win32gui.SetForegroundWindow(hwnd)
                                win32gui.BringWindowToTop(hwnd)
                                logging.info("✓ Ventana traída al frente")
                        except:
                            pass
                    driver.execute_script("window.focus();")
                    driver.maximize_window()  # Maximizar para asegurar visibilidad completa
                    time.sleep(1)  # Tiempo para que la ventana se muestre completamente
                    
                    # Usar márgenes reducidos en modo prueba
                    margen_inicial = MARGEN_INICIAL_PRUEBA if MODO_PRUEBA else MARGEN_INICIAL
                    margen_final = MARGEN_FINAL_PRUEBA if MODO_PRUEBA else MARGEN_FINAL
                    
                    # Asegurar que el directorio de grabación esté configurado antes de iniciar
                    try:
                        cliente_obs.set_record_directory(str(ruta_modulo.resolve()))
                        logging.info(f"✓ Directorio de grabación OBS verificado: {ruta_modulo}")
                    except Exception as e:
                        logging.warning(f"Advertencia al configurar directorio: {e}")
                    
                    # VERIFICACIÓN: Iniciar grabación en OBS
                    logging.info("")
                    logging.info("=" * 70)
                    logging.info("VERIFICACIÓN: Iniciando grabación en OBS...")
                    logging.info("=" * 70)
                    
                    try:
                        # Verificar que no hay grabación activa antes de iniciar
                        estado_antes = cliente_obs.get_record_status()
                        if estado_antes.output_active:
                            logging.warning("Hay una grabación activa. Deteniéndola antes de iniciar nueva...")
                            cliente_obs.stop_record()
                            time.sleep(2)
                        
                        # Iniciar la grabación
                        logging.info("Ejecutando cliente_obs.start_record()...")
                        try:
                            resultado_start = cliente_obs.start_record()
                            if resultado_start:
                                logging.info(f"Resultado de start_record(): {resultado_start}")
                            logging.info("Comando start_record() ejecutado. Esperando a que OBS inicie la grabación...")
                        except Exception as e_start:
                            logging.error(f"Error al ejecutar start_record(): {e_start}")
                            logging.warning("Intentando continuar de todas formas...")
                        time.sleep(3)  # Esperar más tiempo a que la grabación inicie completamente
                        
                        # VERIFICAR que la grabación se inició correctamente (múltiples verificaciones)
                        intentos_verificacion = 0
                        grabacion_iniciada = False
                        estado_grabacion_final = None
                        while intentos_verificacion < 10:  # Aumentar intentos
                            try:
                                estado_grabacion = cliente_obs.get_record_status()
                                estado_grabacion_final = estado_grabacion
                                # Verificar tanto output_active como output_paused
                                if hasattr(estado_grabacion, 'output_active') and estado_grabacion.output_active:
                                    grabacion_iniciada = True
                                    logging.info("✓ Grabación iniciada correctamente en OBS")
                                    logging.info(f"  - Estado output_active: {estado_grabacion.output_active}")
                                    if hasattr(estado_grabacion, 'output_paused'):
                                        logging.info(f"  - Estado output_paused: {estado_grabacion.output_paused}")
                                    if hasattr(estado_grabacion, 'output_timecode'):
                                        logging.info(f"  - Tiempo de grabación: {estado_grabacion.output_timecode}")
                                    break
                                else:
                                    # Log detallado del estado
                                    logging.info(f"Intento {intentos_verificacion + 1}/10: Verificando estado de grabación...")
                                    if hasattr(estado_grabacion, 'output_active'):
                                        logging.info(f"  - output_active: {estado_grabacion.output_active}")
                                    if hasattr(estado_grabacion, 'output_paused'):
                                        logging.info(f"  - output_paused: {estado_grabacion.output_paused}")
                                    intentos_verificacion += 1
                                    time.sleep(0.5)
                            except Exception as e:
                                logging.warning(f"Error al verificar estado (intento {intentos_verificacion + 1}): {e}")
                                intentos_verificacion += 1
                                time.sleep(0.5)
                        
                        if not grabacion_iniciada:
                            logging.warning("ADVERTENCIA: No se pudo verificar que la grabación se inició correctamente")
                            logging.warning("Continuando de todas formas - la grabación puede estar activa aunque no se detecte")
                            if estado_grabacion_final:
                                logging.info(f"Estado final detectado: {estado_grabacion_final}")
                            logging.warning("Si la grabación no funciona, verifica:")
                            logging.warning("  1. OBS debe tener al menos una fuente configurada en la escena")
                            logging.warning("  2. El formato de salida debe estar configurado en OBS")
                            logging.warning("  3. Verifica los logs de OBS para más detalles")
                            # NO hacer continue - continuar con el proceso de todas formas
                    except Exception as e:
                        logging.error(f"ERROR CRÍTICO al iniciar grabación: {e}")
                        logging.error("Saltando este video...")
                        continue
                    
                    logging.info("=" * 70)
                    
                    # Esperar margen inicial (reducido en modo prueba)
                    if margen_inicial > 0:
                        time.sleep(margen_inicial)
                    
                    logging.info(f"Grabando video durante {duracion_segundos} segundos (duración del contenido)...")
                    
                    # Monitorear y omitir anuncios durante la reproducción
                    tiempo_transcurrido = 0
                    intervalo_verificacion = 2  # Verificar más frecuentemente
                    
                    while tiempo_transcurrido < duracion_segundos:
                        tiempo_restante = duracion_segundos - tiempo_transcurrido
                        tiempo_dormir = min(intervalo_verificacion, tiempo_restante)
                        time.sleep(tiempo_dormir)
                        tiempo_transcurrido += tiempo_dormir
                        
                        # Intentar cerrar popups y omitir anuncios periódicamente
                        if tiempo_transcurrido % 5 == 0:  # Cada 5 segundos
                            cerrar_popups_youtube(driver, max_intentos=1)
                            intentar_omitir_anuncios(driver, max_intentos=2)
                    
                    # Esperar margen final (reducido en modo prueba)
                    if margen_final > 0:
                        logging.info("Esperando margen final antes de detener la grabación...")
                        time.sleep(margen_final)
                    
                    # VERIFICACIÓN: Detener grabación (solo si se inició)
                    logging.info("")
                    logging.info("=" * 70)
                    logging.info("VERIFICACIÓN: Verificando estado de grabación antes de detener...")
                    logging.info("=" * 70)
                    
                    ruta_original = None
                    grabacion_estaba_activa = False
                    
                    # Verificar si hay una grabación activa antes de intentar detenerla
                    try:
                        estado_antes_detener = cliente_obs.get_record_status()
                        if hasattr(estado_antes_detener, 'output_active') and estado_antes_detener.output_active:
                            grabacion_estaba_activa = True
                            logging.info("✓ Hay una grabación activa. Deteniéndola...")
                            
                            try:
                                info_grabacion = cliente_obs.stop_record()
                                time.sleep(2)  # Esperar a que se detenga completamente
                                
                                # VERIFICAR que la grabación se detuvo
                                estado_despues = cliente_obs.get_record_status()
                                if hasattr(estado_despues, 'output_active') and estado_despues.output_active:
                                    logging.warning("ADVERTENCIA: La grabación aún está activa. Forzando detención...")
                                    cliente_obs.stop_record()
                                    time.sleep(2)
                                else:
                                    logging.info("✓ Grabación detenida correctamente")
                                
                                # Obtener la ruta del archivo
                                if hasattr(info_grabacion, 'output_path') and info_grabacion.output_path:
                                    ruta_original = Path(info_grabacion.output_path)
                                    logging.info(f"✓ Archivo guardado temporalmente en: {ruta_original}")
                                else:
                                    logging.warning("No se pudo obtener la ruta del archivo desde stop_record()")
                                    # Intentar obtener desde el estado
                                    try:
                                        estado_actual = cliente_obs.get_record_status()
                                        if hasattr(estado_actual, 'output_path') and estado_actual.output_path:
                                            ruta_original = Path(estado_actual.output_path)
                                            logging.info(f"✓ Ruta obtenida desde estado: {ruta_original}")
                                    except:
                                        pass
                            except Exception as e:
                                logging.error(f"Error al detener grabación: {e}")
                                # Intentar obtener el archivo de todas formas
                                try:
                                    estado_grabacion = cliente_obs.get_record_status()
                                    if hasattr(estado_grabacion, 'output_path') and estado_grabacion.output_path:
                                        ruta_original = Path(estado_grabacion.output_path)
                                        logging.info(f"✓ Ruta obtenida desde estado después del error: {ruta_original}")
                                except:
                                    logging.warning("No se pudo obtener la ruta del archivo después del error")
                        else:
                            logging.warning("ADVERTENCIA: No hay grabación activa para detener")
                            logging.warning("Esto puede significar que la grabación nunca se inició correctamente")
                    except Exception as e:
                        logging.error(f"Error al verificar estado antes de detener: {e}")
                        logging.warning("Continuando sin detener grabación...")
                    
                    # Si no se obtuvo la ruta, intentar una vez más
                    if not ruta_original:
                        try:
                            estado_final = cliente_obs.get_record_status()
                            if hasattr(estado_final, 'output_path') and estado_final.output_path:
                                ruta_original = Path(estado_final.output_path)
                                logging.info(f"✓ Ruta obtenida en verificación final: {ruta_original}")
                        except:
                            pass
                    
                    # Si aún no hay ruta, continuar de todas formas (el archivo puede no haberse guardado)
                    if not ruta_original:
                        logging.warning("No se pudo obtener la ruta del archivo grabado")
                        logging.warning("Continuando con el siguiente video...")
                        # NO hacer continue aquí - continuar con el proceso para limpiar y pasar al siguiente video
                    
                    logging.info("=" * 70)
                    
                    # VERIFICACIÓN: Renombrar y mover archivo (solo si hay archivo)
                    if ruta_original:
                        logging.info("")
                        logging.info("=" * 70)
                        logging.info("VERIFICACIÓN: Guardando archivo grabado...")
                        logging.info("=" * 70)
                        
                        time.sleep(2) # Pausa para que OBS libere el archivo
                        
                        # Verificar que el archivo existe antes de renombrar
                        if not ruta_original.exists():
                            logging.warning(f"El archivo {ruta_original} no existe. Esperando más tiempo...")
                            for espera in range(5):
                                time.sleep(2)
                                if ruta_original.exists():
                                    break
                                logging.info(f"Esperando archivo... ({espera + 1}/5)")
                        
                        if ruta_original.exists():
                            logging.info(f"✓ Archivo encontrado: {ruta_original}")
                            extension = ruta_original.suffix
                            # Agregar sufijo en modo prueba
                            sufijo_prueba = "_PRUEBA" if MODO_PRUEBA else ""
                            nuevo_nombre = f"{i:02d}_{nombre_archivo_saneado}{sufijo_prueba}{extension}"
                            nueva_ruta = ruta_modulo / nuevo_nombre
                            
                            # SOBREESCRIBIR si el archivo ya existe (según especificación)
                            if nueva_ruta.exists():
                                logging.info(f"ADVERTENCIA: El archivo '{nuevo_nombre}' ya existe. Sobreescribiendo...")
                                try:
                                    nueva_ruta.unlink()  # Eliminar archivo existente
                                    logging.info("✓ Archivo existente eliminado")
                                except Exception as e:
                                    logging.warning(f"No se pudo eliminar archivo existente: {e}")
                            
                            # Renombrar y mover el archivo
                            try:
                                ruta_original.rename(nueva_ruta)
                                logging.info(f"✓ Archivo renombrado y guardado: {nueva_ruta.name}")
                                
                                # VERIFICAR que el archivo se guardó correctamente
                                if nueva_ruta.exists():
                                    tamaño_archivo = nueva_ruta.stat().st_size
                                    logging.info(f"✓ Archivo verificado: {formatear_tamaño(tamaño_archivo)}")
                                    
                                    # Actualizar estadísticas
                                    estadisticas['videos_grabados'] += 1
                                    estadisticas['duracion_total_segundos'] += duracion_segundos
                                    estadisticas['tamaño_total_bytes'] += tamaño_archivo
                                    estadisticas['archivos_grabados'].append(nueva_ruta)
                                else:
                                    logging.error("ERROR CRÍTICO: El archivo no existe después de renombrar")
                            except Exception as e:
                                logging.error(f"ERROR CRÍTICO al renombrar archivo: {e}")
                    else:
                        if ruta_original:
                            logging.error(f"ERROR CRÍTICO: No se pudo encontrar el archivo grabado: {ruta_original}")
                        else:
                            logging.warning("No se pudo obtener la ruta del archivo - la grabación puede no haberse iniciado")
                        logging.warning("Continuando con el siguiente video...")
                    
                    logging.info("=" * 70)
                    
                    # Pausa entre videos - asegurar que la grabación se detuvo completamente
                    logging.info("Esperando antes del siguiente video...")
                    time.sleep(2)
                    
                    # Verificar que no hay grabación activa
                    try:
                        estado_grabacion = cliente_obs.get_record_status()
                        if estado_grabacion.output_active:
                            logging.warning("Aún hay grabación activa. Forzando detención...")
                            cliente_obs.stop_record()
                            time.sleep(2)
                    except:
                        pass
                    
                    # Cerrar la pestaña actual antes del siguiente video (solo si no es el último)
                    if i < len(urls_a_procesar):
                        logging.info(f"Preparando para el siguiente video ({i+1}/{len(urls_a_procesar)})...")
                        try:
                            ventanas_actuales = driver.window_handles
                            logging.info(f"Cerrando pestaña actual. Pestañas restantes: {len(ventanas_actuales)}")
                            
                            # Cerrar la pestaña actual
                            driver.close()
                            time.sleep(1)
                            
                            # Cambiar a otra pestaña si existe
                            ventanas_restantes = driver.window_handles
                            if ventanas_restantes:
                                driver.switch_to.window(ventanas_restantes[0])
                                logging.info(f"✓ Cambiado a pestaña restante. Total: {len(ventanas_restantes)}")
                            else:
                                # Si no hay más pestañas, se abrirá una nueva en el siguiente video
                                logging.info("No hay pestañas restantes. Se abrirá una nueva en el siguiente video.")
                        except Exception as e:
                            logging.warning(f"Error al cerrar pestaña: {e}")
                            # Intentar recuperar el control
                            try:
                                ventanas = driver.window_handles
                                if ventanas:
                                    driver.switch_to.window(ventanas[0])
                                    logging.info("✓ Control recuperado")
                            except:
                                pass
                    
                    logging.info("=" * 70)
                    logging.info(f"✓ Video {i}/{len(urls_a_procesar)} completado")
                    logging.info("=" * 70)
                    logging.info("")

                except TimeoutException as e:
                    logging.error(f"Tiempo de espera agotado al cargar el video {url}")
                    logging.error(f"Puede ser un video privado, eliminado o la conexión es lenta.")
                    logging.error(f"Error: {e}")
                    # Si la grabación estaba activa, intenta detenerla
                    try:
                        estado_grabacion = cliente_obs.get_record_status()
                        if estado_grabacion.output_active:
                            cliente_obs.stop_record()
                            logging.warning("Se ha detenido una grabación que estaba en curso debido al error.")
                    except:
                        pass
                except Exception as e:
                    logging.error(f"Ocurrió un error inesperado al procesar {url}: {e}")
                    logging.error(f"Tipo de error: {type(e).__name__}")
                    import traceback
                    logging.error(f"Traceback completo:\n{traceback.format_exc()}")
                    # Si la grabación estaba activa, intenta detenerla
                    try:
                        estado_grabacion = cliente_obs.get_record_status()
                        if estado_grabacion.output_active:
                            cliente_obs.stop_record()
                            logging.warning("Se ha detenido una grabación que estaba en curso debido al error.")
                    except:
                        pass
                
    finally:
        # 5. Limpieza final y resumen de estadísticas
        logging.info("")
        logging.info("=" * 70)
        logging.info("RESUMEN FINAL DE EJECUCIÓN")
        logging.info("=" * 70)
        
        # Calcular tamaño total de archivos en las carpetas de módulos procesados
        directorio_base = Path.cwd()
        tamaño_total_calculado = 0
        archivos_encontrados = 0
        
        try:
            # Buscar todas las carpetas de módulos en el directorio actual
            for nombre_modulo in modulos_procesados:
                ruta_modulo = directorio_base / nombre_modulo
                if ruta_modulo.exists() and ruta_modulo.is_dir():
                    for archivo in ruta_modulo.iterdir():
                        if archivo.is_file():
                            tamaño_total_calculado += archivo.stat().st_size
                            archivos_encontrados += 1
        except Exception as e:
            logging.warning(f"Error al calcular tamaño total: {e}")
        
        # Usar el tamaño calculado si es mayor (por si hay archivos adicionales)
        if tamaño_total_calculado > estadisticas['tamaño_total_bytes']:
            estadisticas['tamaño_total_bytes'] = tamaño_total_calculado
        
        # Mostrar estadísticas
        logging.info(f"  ✓ Videos grabados exitosamente: {estadisticas['videos_grabados']}")
        
        if estadisticas['duracion_total_segundos'] > 0:
            tiempo_formateado = formatear_tiempo(estadisticas['duracion_total_segundos'])
            logging.info(f"  ✓ Duración total grabada: {tiempo_formateado}")
            # También mostrar en horas para referencia
            horas_totales = estadisticas['duracion_total_segundos'] / 3600
            if horas_totales >= 1:
                logging.info(f"    ({horas_totales:.2f} horas)")
        else:
            logging.info(f"  ✓ Duración total grabada: 0 segundos")
        
        if estadisticas['tamaño_total_bytes'] > 0:
            tamaño_formateado = formatear_tamaño(estadisticas['tamaño_total_bytes'])
            logging.info(f"  ✓ Tamaño total de archivos: {tamaño_formateado}")
        else:
            logging.info(f"  ✓ Tamaño total de archivos: 0 bytes")
        
        logging.info("=" * 70)
        logging.info("")
        
        # Limpieza final
        logging.info("Proceso completado. Cerrando el navegador.")
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()