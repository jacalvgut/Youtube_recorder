"""
Módulo para gestionar la conexión al navegador.

Este módulo se encarga de:
- Verificar puertos disponibles
- Obtener rutas del navegador
- Abrir navegador con puerto de depuración
- Conectar a navegador existente
"""

import os
import time
import logging
import socket
import subprocess
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import config


def verificar_puerto_disponible(port: int) -> bool:
    """
    Verifica si un puerto está disponible/abierto.
    
    Args:
        port: Número de puerto a verificar.
    
    Returns:
        bool: True si el puerto está abierto, False en caso contrario.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    except Exception as e:
        logging.warning(f"Error al verificar puerto {port}: {e}")
        return False


def obtener_ruta_navegador(nombre_navegador: str) -> str:
    """
    Obtiene la ruta del ejecutable del navegador según la configuración.
    
    Args:
        nombre_navegador: Nombre del navegador ("Brave" o "Chrome").
    
    Returns:
        str: Ruta al ejecutable del navegador.
    """
    if nombre_navegador.lower() == "brave":
        rutas_brave = [
            os.path.expanduser("~\\AppData\\Local\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"),
            "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            "C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
        ]
        for ruta in rutas_brave:
            if os.path.exists(ruta):
                return ruta
        return "brave.exe"
    else:
        rutas_chrome = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        ]
        for ruta in rutas_chrome:
            if os.path.exists(ruta):
                return ruta
        return "chrome.exe"


def abrir_navegador_con_puerto_depuracion(nombre_navegador: str) -> bool:
    """
    Intenta abrir el navegador automáticamente con el puerto de depuración habilitado.
    
    Args:
        nombre_navegador: Nombre del navegador.
    
    Returns:
        bool: True si se abrió correctamente, False en caso contrario.
    """
    ruta_navegador = obtener_ruta_navegador(nombre_navegador)
    
    if not os.path.exists(ruta_navegador):
        logging.error(f"No se encontró {nombre_navegador} en: {ruta_navegador}")
        return False
    
    try:
        logging.info(f"Abriendo {nombre_navegador} con puerto de depuración...")
        subprocess.Popen([
            ruta_navegador,
            f"--remote-debugging-port={config.DEBUG_PORT}",
            "--new-window"
        ], shell=False)
        
        # Esperar a que el puerto esté disponible
        logging.info(f"Esperando a que {nombre_navegador} inicie el puerto de depuración...")
        for intento in range(10):
            time.sleep(1)
            if verificar_puerto_disponible(config.DEBUG_PORT):
                logging.info(f"✓ {nombre_navegador} iniciado correctamente con puerto de depuración")
                return True
        
        logging.warning(f"{nombre_navegador} se abrió pero el puerto aún no está disponible")
        return False
    
    except Exception as e:
        logging.error(f"Error al abrir {nombre_navegador}: {e}")
        return False


def mostrar_instrucciones_conexion(nombre_navegador: str) -> None:
    """Muestra instrucciones para conectar manualmente al navegador."""
    logging.error("=" * 70)
    logging.error(f"ERROR: No se pudo abrir {nombre_navegador} automáticamente")
    logging.error("=" * 70)
    logging.error("")
    logging.error("SOLUCIÓN MANUAL:")
    logging.error("")
    logging.error(f"1. Cierra TODAS las ventanas de {nombre_navegador}")
    logging.error("")
    logging.error("2. Abre PowerShell y ejecuta:")
    logging.error("")
    ruta_navegador = obtener_ruta_navegador(nombre_navegador)
    if os.path.exists(ruta_navegador):
        logging.error(f'   & "{ruta_navegador}" --remote-debugging-port={config.DEBUG_PORT}')
    else:
        nombre_exe = "brave.exe" if nombre_navegador.lower() == "brave" else "chrome.exe"
        logging.error(f'   {nombre_exe} --remote-debugging-port={config.DEBUG_PORT}')
    logging.error("")
    logging.error("3. Luego ejecuta este script nuevamente")
    logging.error("")
    logging.error("=" * 70)


def conectar_a_navegador_existente(nombre_navegador: str) -> Optional[webdriver.Chrome]:
    """
    Se conecta a una instancia existente del navegador.
    
    Args:
        nombre_navegador: Nombre del navegador.
    
    Returns:
        webdriver.Chrome si la conexión fue exitosa, None en caso contrario.
    """
    logging.info(f"VERIFICACIÓN: Intentando conectarse a {nombre_navegador}...")
    
    # Verificar primero si el puerto está disponible
    if not verificar_puerto_disponible(config.DEBUG_PORT):
        logging.info("=" * 70)
        logging.info(f"El puerto {config.DEBUG_PORT} no está disponible")
        logging.info("=" * 70)
        logging.info("")
        logging.info(f"{nombre_navegador} no está abierto con el puerto de depuración habilitado.")
        logging.info("")
        logging.info(f"ACCION: Abriendo {nombre_navegador} automáticamente con el puerto de depuración...")
        logging.info("")
        
        # Intentar abrir navegador automáticamente
        if abrir_navegador_con_puerto_depuracion(nombre_navegador):
            time.sleep(3)
            logging.info(f"✓ {nombre_navegador} abierto correctamente")
        else:
            mostrar_instrucciones_conexion(nombre_navegador)
            return None
    
    try:
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", f"localhost:{config.DEBUG_PORT}")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        logging.info(f"✓ Conectado exitosamente a {nombre_navegador} existente (puerto {config.DEBUG_PORT})")
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
            logging.error(f"El puerto {config.DEBUG_PORT} está abierto pero {nombre_navegador} no responde.")
            logging.error("")
            logging.error("POSIBLES CAUSAS:")
            logging.error(f"  1. {nombre_navegador} está abierto pero NO con --remote-debugging-port")
            logging.error(f"  2. Hay múltiples instancias de {nombre_navegador} abiertas")
            logging.error("  3. El puerto está siendo usado por otra aplicación")
        else:
            logging.error(f"Error inesperado al conectar con {nombre_navegador}.")
        
        logging.error(f"Error técnico: {e}")
        return None
    except Exception as e:
        logging.error(f"ERROR inesperado al conectar al navegador: {e}")
        return None

