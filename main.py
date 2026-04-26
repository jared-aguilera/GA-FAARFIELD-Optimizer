import subprocess
import sys
import os

if __name__ == "__main__":
    script_path = os.path.join("src", "funcion_faarfield", "calcular_respuesta_flota.py")
    
    # Mandamos a llamar el archivo original de forma directa
    subprocess.run([sys.executable, script_path])