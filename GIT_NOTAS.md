# Notas sobre Git y GitHub

## Archivos Ignorados

El archivo `.gitignore` está configurado para ignorar automáticamente:

- **Todos los archivos de video** (*.mp4, *.avi, *.mkv, etc.)
- **El contenido de las carpetas de módulos** (MOD01_*, MOD02_*, etc.)
- **Archivos temporales y cache**

## Subir Videos Específicos a GitHub (Manual)

Si necesitas subir videos específicos a GitHub, puedes usar uno de estos métodos:

### Método 1: Forzar la inclusión de archivos específicos

```bash
# Subir un video específico
git add -f MOD01_python/01_video_especifico.mp4

# Subir todo el contenido de una carpeta de módulo específica
git add -f MOD01_python/

# Subir múltiples archivos
git add -f MOD01_python/video1.mp4 MOD02_sql/video2.mp4
```

### Método 2: Temporalmente modificar .gitignore

1. Abre `.gitignore`
2. Comenta temporalmente las líneas que ignoran los videos:
   ```
   # *.mp4
   ```
3. Añade los archivos que quieras:
   ```bash
   git add MOD01_python/video_especifico.mp4
   ```
4. Vuelve a descomentar las líneas en `.gitignore`
5. Haz commit:
   ```bash
   git commit -m "Añadir video específico"
   ```

### Método 3: Crear una carpeta para videos públicos

Si quieres tener algunos videos en GitHub pero no todos:

1. Crea una carpeta nueva, por ejemplo: `videos_publicos/`
2. Añade esta carpeta al `.gitignore`:
   ```
   # Videos en carpetas de módulos (ignorados)
   MOD*/**/*
   
   # Videos públicos (permitidos)
   !videos_publicos/
   ```
3. Copia los videos que quieres subir a esa carpeta
4. Añádelos normalmente:
   ```bash
   git add videos_publicos/
   ```

## Recomendaciones

- **No subas todos los videos a GitHub** - Los repositorios de GitHub tienen límites de tamaño
- **Usa Git LFS para videos grandes** - Si necesitas subir videos, considera usar Git Large File Storage:
  ```bash
  git lfs install
  git lfs track "*.mp4"
  git add .gitattributes
  ```

## Estructura del Repositorio

El repositorio incluye:
- ✅ Código fuente (Python)
- ✅ Configuración
- ✅ Documentación
- ❌ Videos (ignorados por defecto)
- ❌ Archivos temporales

