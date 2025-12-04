"""
Módulo para procesar el archivo de URLs y crear la estructura de carpetas.

Este módulo se encarga de:
- Leer el archivo de texto con las URLs organizadas por módulos
- Crear las carpetas correspondientes para cada módulo
- Interpretar y validar las URLs
- Organizar los datos en una estructura de datos útil
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import config


class URLProcessor:
    """
    Clase encargada de procesar el archivo de URLs y crear la estructura de directorios.
    
    Esta clase maneja toda la lógica relacionada con la lectura y organización
    de URLs desde el archivo de texto.
    """
    
    def __init__(self, url_file: str = None):
        """
        Inicializa el procesador de URLs.
        
        Args:
            url_file: Ruta al archivo de texto con las URLs. Si es None, usa el valor de config.
        """
        self.url_file = url_file or config.URL_FILE
        self.modulos: Dict[str, List[str]] = {}
    
    def parsear_archivo_urls(self) -> Optional[Dict[str, List[str]]]:
        """
        Lee el archivo de texto y lo convierte en un diccionario de módulos y URLs.
        
        Formato esperado:
            #MODXX_xxxx_xxxx
            https://www.youtube.com/watch?v=...
            https://www.youtube.com/watch?v=...
        
        Returns:
            Dict con el formato {nombre_modulo: [lista_de_urls]}, o None si hay error.
        
        Raises:
            FileNotFoundError: Si el archivo no existe.
            IOError: Si hay un error al leer el archivo.
        """
        logging.info("=" * 70)
        logging.info("VERIFICACIÓN: Leyendo archivo de URLs...")
        logging.info("=" * 70)
        
        filepath = Path(self.url_file)
        
        # Verificar que el archivo existe
        if not filepath.exists():
            logging.error(f"ERROR CRÍTICO: El archivo '{self.url_file}' no se encuentra en este directorio.")
            logging.error(f"Ruta esperada: {filepath.resolve()}")
            return None
        
        logging.info(f"✓ Archivo encontrado: {filepath.resolve()}")
        
        modulos = {}
        modulo_actual = None
        lineas_procesadas = 0
        modulos_encontrados = 0
        urls_encontradas = 0
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for num_linea, linea in enumerate(f, 1):
                    linea = linea.strip()
                    
                    # Ignorar líneas vacías
                    if not linea:
                        continue
                    
                    lineas_procesadas += 1
                    
                    # Detectar inicio de módulo (línea que empieza con #)
                    if linea.startswith('#'):
                        # Eliminar el '#' y espacios al principio
                        modulo_actual = linea.lstrip('# ').strip()
                        if modulo_actual:
                            modulos[modulo_actual] = []
                            modulos_encontrados += 1
                            logging.info(f"✓ Módulo encontrado (línea {num_linea}): '{modulo_actual}'")
                        else:
                            logging.warning(f"ADVERTENCIA: Línea {num_linea} tiene '#' pero está vacía")
                    
                    # Detectar URL (línea que empieza con http)
                    elif modulo_actual and linea.startswith('http'):
                        # Validar que sea una URL válida de YouTube
                        if self._validar_url_youtube(linea):
                            modulos[modulo_actual].append(linea)
                            urls_encontradas += 1
                        else:
                            logging.warning(f"ADVERTENCIA: URL inválida en línea {num_linea}: {linea[:50]}...")
                    
                    # Línea que no es módulo ni URL válida
                    elif modulo_actual:
                        logging.warning(f"ADVERTENCIA: Línea {num_linea} ignorada (no es URL válida): {linea[:50]}")
            
            # Mostrar resumen de la lectura
            logging.info("=" * 70)
            logging.info(f"RESUMEN DE LECTURA:")
            logging.info(f"  - Líneas procesadas: {lineas_procesadas}")
            logging.info(f"  - Módulos encontrados: {modulos_encontrados}")
            logging.info(f"  - URLs encontradas: {urls_encontradas}")
            logging.info("=" * 70)
            
            # Validar que se encontraron módulos
            if not modulos:
                logging.error("ERROR CRÍTICO: No se encontraron módulos en el archivo.")
                return None
            
            # Verificar que cada módulo tenga al menos una URL
            modulos_sin_urls = [mod for mod, urls in modulos.items() if not urls]
            if modulos_sin_urls:
                logging.warning(f"ADVERTENCIA: Módulos sin URLs: {modulos_sin_urls}")
            
            self.modulos = modulos
            return modulos
        
        except FileNotFoundError:
            logging.error(f"ERROR CRÍTICO: No se pudo encontrar el archivo '{self.url_file}'")
            return None
        except IOError as e:
            logging.error(f"ERROR CRÍTICO al leer archivo: {e}")
            return None
        except Exception as e:
            logging.error(f"ERROR CRÍTICO inesperado al leer archivo: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _validar_url_youtube(self, url: str) -> bool:
        """
        Valida que una URL sea válida para YouTube.
        
        Args:
            url: La URL a validar.
        
        Returns:
            bool: True si la URL es válida, False en caso contrario.
        """
        if not url or not isinstance(url, str):
            return False
        
        # Verificar que sea una URL de YouTube
        youtube_domains = ['youtube.com', 'youtu.be', 'www.youtube.com']
        return any(domain in url.lower() for domain in youtube_domains)
    
    def crear_estructura_carpetas(self, directorio_base: Path = None) -> Dict[str, Path]:
        """
        Crea las carpetas para cada módulo en el directorio especificado.
        
        Args:
            directorio_base: Directorio base donde crear las carpetas. 
                           Si es None, usa el directorio actual.
        
        Returns:
            Dict con el formato {nombre_modulo: ruta_carpeta_creada}
        
        Raises:
            PermissionError: Si no se tienen permisos para crear carpetas.
            OSError: Si hay un error al crear las carpetas.
        """
        if not self.modulos:
            logging.error("ERROR: No hay módulos procesados. Ejecuta parsear_archivo_urls() primero.")
            return {}
        
        if directorio_base is None:
            directorio_base = Path.cwd()
        
        logging.info("")
        logging.info("=" * 70)
        logging.info("VERIFICACIÓN: Creando estructura de carpetas...")
        logging.info("=" * 70)
        
        carpetas_creadas = {}
        
        try:
            for nombre_modulo, urls in self.modulos.items():
                if not urls:
                    logging.warning(f"Saltando módulo '{nombre_modulo}' sin URLs")
                    continue
                
                ruta_modulo = directorio_base / nombre_modulo
                
                # Crear carpeta si no existe
                try:
                    if ruta_modulo.exists():
                        logging.info(f"ADVERTENCIA: La carpeta '{nombre_modulo}' ya existe. Se sobreescribirán archivos.")
                    else:
                        logging.info(f"Creando carpeta: {nombre_modulo}")
                    
                    ruta_modulo.mkdir(exist_ok=True)
                    carpetas_creadas[nombre_modulo] = ruta_modulo
                    logging.info(f"✓ Carpeta lista: {ruta_modulo.resolve()}")
                
                except PermissionError as e:
                    logging.error(f"ERROR: Sin permisos para crear carpeta '{nombre_modulo}': {e}")
                    continue
                except OSError as e:
                    logging.error(f"ERROR al crear carpeta '{nombre_modulo}': {e}")
                    continue
            
            logging.info("=" * 70)
            logging.info(f"✓ Estructura de carpetas creada: {len(carpetas_creadas)} módulo(s)")
            logging.info("=" * 70)
            
            return carpetas_creadas
        
        except Exception as e:
            logging.error(f"ERROR CRÍTICO inesperado al crear carpetas: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            return carpetas_creadas
    
    def obtener_urls_por_modulo(self, nombre_modulo: str) -> List[str]:
        """
        Obtiene las URLs de un módulo específico.
        
        Args:
            nombre_modulo: Nombre del módulo del cual obtener las URLs.
        
        Returns:
            Lista de URLs del módulo. Lista vacía si el módulo no existe.
        """
        return self.modulos.get(nombre_modulo, [])
    
    def obtener_todos_los_modulos(self) -> Dict[str, List[str]]:
        """
        Obtiene todos los módulos y sus URLs.
        
        Returns:
            Dict con todos los módulos y sus URLs.
        """
        return self.modulos.copy()
    
    def aplicar_limites_prueba(self) -> None:
        """
        Aplica los límites configurados para el modo de prueba.
        
        Modifica internamente el diccionario de módulos según las configuraciones
        de MAX_MODULOS_PRUEBA y MAX_VIDEOS_POR_MODULO_PRUEBA.
        """
        if not config.MODO_PRUEBA:
            return
        
        if config.MAX_MODULOS_PRUEBA:
            modulos_lista = list(self.modulos.items())
            modulos_limitados = dict(modulos_lista[:config.MAX_MODULOS_PRUEBA])
            modulos_omitidos = len(self.modulos) - len(modulos_limitados)
            
            if modulos_omitidos > 0:
                logging.info(f"Modo prueba: Procesando solo {len(modulos_limitados)} de {len(self.modulos)} módulos")
            
            self.modulos = modulos_limitados
        
        if config.MAX_VIDEOS_POR_MODULO_PRUEBA:
            for modulo, urls in self.modulos.items():
                if len(urls) > config.MAX_VIDEOS_POR_MODULO_PRUEBA:
                    urls_limitadas = urls[:config.MAX_VIDEOS_POR_MODULO_PRUEBA]
                    logging.info(f"Modo prueba: Limitando '{modulo}' a {len(urls_limitadas)} de {len(urls)} videos")
                    self.modulos[modulo] = urls_limitadas

