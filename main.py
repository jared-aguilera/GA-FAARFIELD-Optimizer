import sys
import os
import pandas as pd
from src.optimizador_ga import OptimizadorPavimento

def principal():
    print("====================================================")
    print("     OPTIMIZADOR GA-FAARFIELD - PROTOTIPO FINAL     ")
    print("====================================================\n")
    print("Cargo csv\n")
    csvFile = pd.read_csv("../data/aircraft.csv")
    print(csvFile)

    flota = [
        {'nombre': 'A320-200 Twin std', 'annual_deps': 3775, 'growth': 10.0},
        {'nombre': 'B737-800', 'annual_deps': 8, 'growth': 4.0},
        {'nombre': 'A321-200 std', 'annual_deps': 180, 'growth': 5.0}
    ]
    vida_diseno = 20
    # El usuario cambió el módulo a 60 MPa en su última ejecución
    subgrade_e = 40
    
    print(f"Configuración de Diseño:")
    print(f"- Periodo de diseño: {vida_diseno} años")
    print(f"- Módulo Subgrade: {subgrade_e} MPa")
    print(f"- Flota: {len(flota)} aeronaves cargadas.\n")
    
    print("Iniciando optimización por Algoritmo Genético...")
    optimizador = OptimizadorPavimento(flota, vida_diseno, subgrade_e)
    mejor = optimizador.evolucionar()
    
    if not mejor:
        print("No se encontró una solución válida.")
        return

    ind, fit, res = mejor
    
    def fmt_cdf(v):
        if v > 10.0: return f"{v:.1f} (REQUERIDO: AUMENTAR ESPESOR)"
        if v > 1.0: return f"{v:.4f} (FALLA)"
        return f"{v:.4f} (PASO)"

    print("\n" + "="*52)
    print("           RESULTADOS DE OPTIMIZACIÓN               ")
    print("="*52)
    print(f"1.  Subgrade CDF:         {fmt_cdf(res['Subgrade_CDF'])}")
    print(f"2.  HMA CDF:              {fmt_cdf(res['HMA_CDF'])}")
    print(f"3.  Vida Útil (Fatiga):   {res['Life']:.1f} años")
    print(f"4.  Tipo de Estructura:   Nueva Flexible")
    print(f"5.  ACR Mayor Flota:      {res['Max_ACR']:.1f}")
    print(f"6.  PCR Calculado:        {res['PCR']}")
    
    # Nombres dinámicos para las capas para completar los 12 parámetros
    labels = [
        "7.  Espesor Carpeta (HMA):",
        "8.  Espesor Base (B):     ",
        "9.  Espesor Subbase (SB): ",
        "10. Espesor de Capa 4:    ",
        "11. Espesor de Capa 5:    "
    ]
    
    for i in range(5):
        if i < len(ind):
            print(f"{labels[i]} {ind[i]} mm")
        else:
            print(f"{labels[i]} 0 mm")

    print(f"12. Módulo E Carpeta:     3500 MPa")
    print("="*52)
    
    if res['Subgrade_CDF'] > 1.0 or res['HMA_CDF'] > 1.0:
        print("\n[ALERTA]: El diseño propuesto NO cumple con la resistencia necesaria.")
    else:
        print("\n[ÉXITO]: El diseño es óptimo y cumple con los estándares FAA.")

if __name__ == "__main__":
    principal()
