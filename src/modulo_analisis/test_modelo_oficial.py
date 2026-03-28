"""
=============================================================
  TEST MODELO OFICIAL — Verificación de los 5 Valores
=============================================================
"""

import sys
import os

# Asegurar que el directorio src está en el path
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.modulo_analisis.modelo_faa_oficial import ModeloFAAOficial

def test():
    print("Iniciando Verificación de ModeloFAAOficial...")
    
    try:
        modelo = ModeloFAAOficial()
        
        # 1. Datos de Estructura (Ejemplo FAA)
        # HMA (4in), Base (8in), Subbase (12in), Subgrado
        estructura = {
            "espesores": [4.0, 8.0, 12.0, 0.0],
            "modulos": [200000.0, 36259.5, 21755.7, 5076.3] # Módulos en PSI
        }
        
        # 2. Datos de Flota (1 avión para simplificar)
        flota = [{
            "nombre": "B747-400",
            "peso_kg": 396893,
            "llantas": 16,
            "presion_kpa": 1400,
            "operaciones_totales": 1200,
            "coords": [-11.0, 22.0, 11.0, 22.0] # Coordenadas ejemplo (abreviado)
        }]
        
        # 3. Ejecutar Cálculo Oficial
        resultados = modelo.obtener_resultados_oficiales(flota, estructura, pd=20.0)
        
        print("\n--- RESULTADOS OFICIALES (FAA 240356) ---")
        print(f"1. Subgrade CDF : {resultados['Subgrade_CDF']:.6f}")
        print(f"2. HMA CDF      : {resultados['HMA_CDF']:.6f}")
        print(f"3. Life         : {resultados['Life']:.2f} años")
        print(f"4. ACR mayor    : {resultados['ACR_mayor']:.4f}")
        print(f"5. PCR          : {resultados['PCR']:.4f}")
        print("\n✅ Verificación completada con éxito.")

    except Exception as e:
        print(f"❌ Error en la verificación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()
