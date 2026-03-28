"""
=============================================================
  INTERFAZ FAA OFICIAL — Menú Interactivo de Veracidad
  Permite al usuario ingresar datos manualmente y obtener
  los 5 valores oficiales de FAARFIELD.
=============================================================
"""

import sys
import os
import csv

# Asegurar acceso a los módulos src
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from src.modulo_analisis.modelo_faa_oficial import ModeloFAAOficial

def cargar_datos_aeronave(id_seleccionado):
    """ Busca el avión en el CSV y retorna sus datos básicos """
    csv_path = os.path.join(base_dir, 'data', 'aircraft.csv')
    try:
        current_id = 1
        with open(csv_path, mode='r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            for row in reader:
                if current_id == id_seleccionado:
                    return {
                        "id": id_seleccionado,
                        "nombre": str(row[1]).strip(),
                        "peso_kg": float(row[2]),
                        "llantas": int(row[11]),
                        "presion_kpa": float(row[4]),
                        "coords": [float(x) for x in row[12:12+(int(row[11])*2)]]
                    }
                current_id += 1
    except Exception as e:
        print(f"Error cargando avión: {e}")
    return None

def construir_flota_interactiva(pd):
    """ Menú para armar la lista de aviones """
    flota = []
    print("\n" + "="*50)
    print("CONSTRUCTOR DE FLOTA (DATOS OFICIALES)")
    print("="*50)
    
    while True:
        entrada = input("\nIngresa el ID del avión (1-252) o 'listo'/'q' para procesar: ").strip()
        if entrada.lower() in ['listo', 'q', 'salir']:
            break
            
        try:
            id_avion = int(entrada)
            datos = cargar_datos_aeronave(id_avion)
            if datos:
                print(f" -> Seleccionado: {datos['nombre']}")
                n_anual = float(input(f"    ¿Operaciones anuales iniciales?: "))
                tasa = float(input(f"    ¿Tasa de crecimiento anual (%)?: "))
                
                # Cálculo de Operaciones Totales (Fórmula de Crecimiento Compuesto)
                r = tasa / 100.0
                if r == 0:
                    n_total = n_anual * pd
                else:
                    n_total = n_anual * (((1 + r)**pd - 1) / r)
                
                datos["operaciones_anuales"] = n_anual
                datos["tasa_crecimiento"] = tasa
                datos["operaciones_totales"] = n_total
                
                flota.append(datos)
                print(f" [V] Agregado con éxito. (Total en vida útil: {n_total:.2f})")
            else:
                print(" [X] ID no encontrado.")
        except ValueError:
            print("Entrada no válida.")
            
    return flota

def main():
    print("INICIANDO INTERFAZ FAA OFICIAL...")
    modelo = ModeloFAAOficial()
    
    # 1. Periodo de Diseño primero
    try:
        pd = float(input("\n¿Periodo de Diseño en años? [20]: ") or 20.0)
    except ValueError:
        pd = 20.0

    # 2. Armar Flota con Crecimiento
    flota = construir_flota_interactiva(pd)
    if not flota:
        print("No se seleccionaron aviones. Saliendo.")
        return

    # 3. Determinar Estructura por Módulo de Subrasante
    print("\n" + "="*50)
    print("CONFIGURACIÓN DE ESTRUCTURA DE PAVIMENTO")
    print("="*50)
    
    try:
        subrasante_mpa = float(input(" -> Ingresa el módulo de la subrasante (E) en MPa: "))
        
        # Lógica de capas basada en E
        if subrasante_mpa >= 69:
            n_capas = 3
        elif 35 <= subrasante_mpa < 69:
            n_capas = 4
        else:
            n_capas = 5
            
        print(f" [+] Estructura detectada: {n_capas} capas basadas en E={subrasante_mpa} MPa.")
        
        espesores = []
        modulos = []
        
        for i in range(1, n_capas):
            if i == 1: nombre = "Carpeta (HMA)"
            elif i == 2: nombre = "Base"
            elif i == 3: nombre = "Subbase"
            elif i == 4: nombre = "Subrasante/Estabilizada"
            else: nombre = f"Capa {i}"
            
            esp = float(input(f"    -> Espesor de {nombre} (pulgadas): "))
            mod_mpa = float(input(f"    -> Módulo de {nombre} (MPa): "))
            espesores.append(esp)
            modulos.append(mod_mpa * 145.038) # Convertir a PSI
            
        espesores.append(0.0) # Capa infinita (Subgrado)
        modulos.append(subrasante_mpa * 145.038)
        
        estructura = {"espesores": espesores, "modulos": modulos}

        # 4. Calcular Resultados Oficiales
        print("\n[+] Calculando resultados con el Motor FAA Oficial (Veracidad)...")
        resultados = modelo.obtener_resultados_oficiales(flota, estructura, pd=pd)

        # 5. Mostrar Resultados
        print("\n" + "="*60)
        print("          RESUMEN DE RESULTADOS OFICIALES (FAA)")
        print("="*60)
        print(f"1. Subgrade CDF : {resultados['Subgrade_CDF']:.6f}")
        print(f"2. HMA CDF      : {resultados['HMA_CDF']:.6f}")
        print(f"3. Life         : {resultados['Life']:.2f} años")
        print(f"4. ACR mayor    : {resultados['ACR_mayor']:.2f}")
        print(f"5. PCR          : {resultados['PCR']:.2f}")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n[!] Error en el procesamiento: {e}")

if __name__ == "__main__":
    main()
