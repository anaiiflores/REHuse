"""
Siembra los ejercicios del directorio ReHuse/Archivo/ en la base de datos
unificada rehuse_db (backend FastAPI unificado, puerto 3308).

Uso (con Docker corriendo):
    cd backend/scripts
    pip install pymysql pillow
    python seed_exercises_unified.py
"""

import re
import sys
import uuid
from io import BytesIO
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("ERROR: Pillow no instalado. Ejecuta: pip install Pillow")

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    sys.exit("ERROR: PyMySQL no instalado. Ejecuta: pip install pymysql")


# ── Rutas ───────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
ARCHIVO_DIR = BACKEND_DIR.parent / "ReHuse" / "Archivo"
STATIC_EXERCISES_DIR = BACKEND_DIR / "static" / "exercises"

DB_CONFIG = {
    "host": "localhost",
    "port": 3308,
    "user": "rehuse_user",
    "password": "rehuse_pass",
    "database": "rehuse_db",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.Cursor,
}

# ── Regex para extraer datos de la descripción ──────────────────────────────

_PATRONES_REPS = [
    r'(\d+)(?:-\d+)?\s+repeticiones',
    r'de\s+(\d+)\s+a\s+\d+\s+repeticiones',
    r'realizar\s+(\d+)(?:-\d+)?\s+veces',
    r'repetir\s+(\d+)(?:-\d+)?\s+veces',
    r'(\d+)(?:-\d+)?\s+veces',
]
_PATRONES_TIEMPO_SEG = [r'(\d+)(?:-\d+)?\s*segundos']
_PATRONES_TIEMPO_MIN = [r'(\d+)(?:-\d+)?\s*minutos?']


def extraer_repeticiones(descripcion: str) -> "int | None":
    texto = descripcion.lower()
    for patron in _PATRONES_REPS:
        m = re.search(patron, texto)
        if m:
            return int(m.group(1))
    return None


def extraer_tiempo_seg(descripcion: str) -> "int | None":
    texto = descripcion.lower()
    for patron in _PATRONES_TIEMPO_SEG:
        m = re.search(patron, texto)
        if m:
            return int(m.group(1))
    for patron in _PATRONES_TIEMPO_MIN:
        m = re.search(patron, texto)
        if m:
            return int(m.group(1)) * 60
    return None


# ── Utilidades de archivos ───────────────────────────────────────────────────

def leer_descripcion(carpeta: Path) -> str:
    for nombre in ["Descripción.txt", "Descripcion.txt", "descripcion.txt", "descripción.txt"]:
        ruta = carpeta / nombre
        if ruta.exists():
            for enc in ("utf-8", "latin-1"):
                try:
                    return ruta.read_text(encoding=enc).strip()
                except UnicodeDecodeError:
                    continue
    return ""


def ordenar_imagenes(archivos: "list[Path]") -> "list[Path]":
    def num(p: Path) -> int:
        m = re.search(r"(\d+)", p.stem)
        return int(m.group(1)) if m else 0
    return sorted(archivos, key=num)


def safe_folder_name(nombre: str) -> str:
    """Convierte el nombre del ejercicio en un nombre de carpeta seguro."""
    safe = re.sub(r'[<>:"/\\|?*]', '_', nombre)
    safe = re.sub(r'\s+', '_', safe)
    return safe[:80]


def guardar_imagen(ruta_img: Path, dest_dir: Path, idx: int) -> "str | None":
    """Guarda la imagen redimensionada como JPEG y devuelve la URL relativa."""
    try:
        img = Image.open(ruta_img)
        if img.width > 400 or img.height > 400:
            img.thumbnail((400, 400), Image.Resampling.LANCZOS)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{idx}.jpg"
        img.convert("RGB").save(dest, "JPEG", quality=85, optimize=True)
        return f"/static/exercises/{dest_dir.name}/{idx}.jpg"
    except Exception as e:
        print(f"    ADVERTENCIA imagen {ruta_img.name}: {e}")
        return None


# ── Base de datos ────────────────────────────────────────────────────────────

def main():
    if not ARCHIVO_DIR.exists():
        sys.exit(f"ERROR: No se encontró {ARCHIVO_DIR}\n"
                 "Asegúrate de ejecutar el script desde backend/scripts/")

    print(f"Conectando a rehuse_db en localhost:3308...")
    try:
        conn = pymysql.connect(**DB_CONFIG)
    except pymysql.Error as e:
        sys.exit(f"ERROR de conexión: {e}\n"
                 "Asegúrate de que Docker está corriendo: docker-compose up -d")

    cursor = conn.cursor()

    # Obtener ID del primer fisioterapeuta para asignar como creador
    cursor.execute("SELECT id FROM users WHERE role IN ('physio', 'admin') ORDER BY created_at LIMIT 1")
    row = cursor.fetchone()
    physio_id = row[0] if row else None

    regiones = sorted(
        d for d in ARCHIVO_DIR.iterdir()
        if d.is_dir() and d.name != "__MACOSX"
    )
    if not regiones:
        sys.exit("ERROR: La carpeta Archivo/ está vacía.")

    total_ejercicios = 0
    total_imagenes = 0
    total_saltados = 0

    for region_dir in regiones:
        region_nombre = region_dir.name
        subdir = region_dir / region_nombre
        if not subdir.exists():
            subdir = region_dir

        ejercicio_dirs = sorted(d for d in subdir.iterdir() if d.is_dir())
        print(f"\n[{region_nombre}] {len(ejercicio_dirs)} ejercicios...")

        for ejercicio_dir in ejercicio_dirs:
            nombre = ejercicio_dir.name

            # Idempotencia: saltar si ya existe
            cursor.execute("SELECT id FROM exercises WHERE name = %s", (nombre,))
            if cursor.fetchone():
                total_saltados += 1
                continue

            descripcion = leer_descripcion(ejercicio_dir)
            reps = extraer_repeticiones(descripcion)
            total_duration = extraer_tiempo_seg(descripcion)

            imagenes = ordenar_imagenes([
                f for f in ejercicio_dir.iterdir()
                if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png")
            ])

            safe = safe_folder_name(nombre)
            exercise_static_dir = STATIC_EXERCISES_DIR / safe

            # Guardar imágenes en disco
            image_urls: list[str] = []
            for idx, img_path in enumerate(imagenes):
                url = guardar_imagen(img_path, exercise_static_dir, idx)
                if url:
                    image_urls.append(url)

            first_url = image_urls[0] if image_urls else None
            exercise_id = str(uuid.uuid4())

            cursor.execute(
                """INSERT INTO exercises
                   (id, name, description, reps, total_duration_seconds, image_url, created_by)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (exercise_id, nombre, descripcion or None, reps, total_duration, first_url, physio_id),
            )

            for idx, url in enumerate(image_urls):
                cursor.execute(
                    "INSERT INTO exercise_images (id, exercise_id, url, order_index) VALUES (%s, %s, %s, %s)",
                    (str(uuid.uuid4()), exercise_id, url, idx),
                )

            conn.commit()
            total_ejercicios += 1
            total_imagenes += len(image_urls)
            print(f"  + {nombre} ({len(image_urls)} imágenes)")

    cursor.close()
    conn.close()

    print("\n" + "=" * 55)
    print(f"  Ejercicios nuevos cargados:  {total_ejercicios}")
    print(f"  Imágenes guardadas:          {total_imagenes}")
    if total_saltados:
        print(f"  Ejercicios saltados (ya existían): {total_saltados}")
    print("=" * 55)
    print("\nListo. Reinicia el backend para servir los archivos estáticos:")
    print("  docker-compose up --build -d")


if __name__ == "__main__":
    main()
