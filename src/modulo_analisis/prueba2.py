import sys
import os

print("\n" + "="*50)
print("   ESCÁNER DE DLL (Ingeniería Inversa Básica)")
print("="*50)

# 1. Encontrar la ruta de la carpeta 'bin' donde están las DLLs
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
bin_dir = os.path.join(base_dir, 'bin')

if not os.path.exists(bin_dir):
    print(f"[X] No se encontró la carpeta bin en: {bin_dir}")
    sys.exit()

print(f"[*] Buscando DLLs en: {bin_dir}")
sys.path.append(bin_dir)

try:
    import clr
except ImportError:
    print("[X] Error: No tienes instalado pythonnet. Ejecuta: pip install pythonnet")
    sys.exit()

# =========================================================
# 2. ESCRIBE AQUÍ EL NOMBRE DE TU DLL (Sin el .dll)
# Por los errores anteriores, supongo que usas LEAFClassLib
# =========================================================
nombre_dll = "LEAFClassLib"  

try:
    # Cargar la DLL en la memoria de Python
    clr.AddReference(nombre_dll)
    
    # Importar el espacio de nombres (suele llamarse igual que la DLL)
    modulo_dll = __import__(nombre_dll)
    
    print(f"\n[V] DLL '{nombre_dll}.dll' cargada con éxito.\n")
    print("-" * 50)
    print("CONTENIDO PRINCIPAL (Clases y Funciones):")
    print("-" * 50)
    
    # Listar todo lo que hay adentro
    contenido = dir(modulo_dll)
    print(dir(modulo_dll))
    print("\n" + "-" * 50)
    print(contenido)
    for item in contenido:
        # Filtramos los métodos mágicos de Python (__algo__) para que se vea limpio
        if not item.startswith("__"):
            print(f" -> {item}")
            
    print("\n" + "="*50)
    
except Exception as e:
    print(f"\n[X] Error al intentar leer la DLL '{nombre_dll}': {e}")
    print("Asegúrate de que el nombre sea correcto y esté dentro de la carpeta /bin.")