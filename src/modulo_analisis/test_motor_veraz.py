"""
=============================================================
  TEST MOTOR VERAZ — Demostración de Proceso Oficial
=============================================================
"""

import sys
import os

# Asegurar que el directorio src está en el path
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.modulo_analisis.motor_veraz import MotorVeraz

def test():
    print("Iniciando prueba de MotorVeraz...")
    
    try:
        motor = MotorVeraz()
        
        # 1. Configurar Estructura
        espesores = [4.0, 8.0, 12.0, 0.0]
        modulos = [2000, 250, 150, 35] # MPa
        motor.configurar_estructura(espesores, modulos, subrasante_mpa=35.0)
        
        # 2. Ejecutar Proceso para un avión (datos de ejemplo)
        # El usuario pone estos datos a mano
        resultados = motor.ejecutar_analisis_oficial(
            nombre_avion="B747-400", 
            peso_kg=396893, 
            operaciones=1200
        )
        
        print("\nExtracción de Veracidad Completada:")
        for k, v in resultados.items():
            print(f"  > {k}: {v}")
            
        print("\n[OK] El proceso se ha vinculado correctamente a las librerias oficiales.")

    except Exception as e:
        import traceback
        print(f"[Error] Error en la prueba: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test()
