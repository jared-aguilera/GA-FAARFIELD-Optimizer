"""
Módulo Principal: Orquestador del Optimizador GA-FAARFIELD.

Este script coordina la ejecución del sistema modular, integrando la lógica
de ingeniería de pavimentos con el algoritmo genético para encontrar el
diseño estructural óptimo bajo las normativas de la FAA.
"""

from src.evaluador_pavi import EvaluadorPavimento
from src.optimizador_ga import AlgoritmoGenetico, op_recosido_simulado


def mostrar_resultados(data):
    """
    Imprime en la terminal el reporte técnico de 12 puntos.

    Presenta los resultados finales de la optimización, incluyendo
    daño acumulado (CDF), vida útil, clasificación ACR/PCR y espesores.

    Args:
        data (dict): Diccionario generado por el evaluador con los resultados.
    """
    print("\n" + "="*52)
    print("           RESULTADOS DE OPTIMIZACIÓN               ")
    print("="*52)
    print(f"1.  Subgrade CDF:         {data['cdf_s']:.4f} "
          f"({'PASO' if data['cdf_s'] <= 0.98 else 'FALLA'})")
    print(f"2.  HMA CDF:              {data['cdf_h']:.4f} "
          f"({'PASO' if data['cdf_h'] <= 0.98 else 'FALLA'})")
    print(f"3.  Vida Útil (Fatiga):   {data['vida']:.1f} años")
    print(f"4.  Tipo de Estructura:   {data['tipo']}")
    print(f"5.  ACR Mayor Flota:      {data['acr']:.1f}")
    print(f"6.  PCR Calculado:        {data['pcr']}")
    print(f"7.  Espesor Carpeta (HMA): {data['h_hma']:.0f} mm")
    print(f"8.  Espesor Base (B):      {data['h_b']:.0f} mm")
    print(f"9.  Espesor Subbase (SB):  {data['h_sb']:.0f} mm")
    print(f"10. Espesor de Capa 4:    {data['h_c4']:.0f} mm")
    print(f"11. Espesor de Capa 5:    {data['h_c5']:.0f} mm")
    print(f"12. Módulo E Carpeta:     {data['e_hma']} MPa")
    print("====================================================\n")

    if data['cdf_s'] <= 0.98:
        print("[ÉXITO]: El diseño cumple satisfactoriamente con el CDF.")
    else:
        print("[AVISO]: Se requiere mayor espesor para cumplir con el CDF.")


def principal():
    """
    Ejecuta el flujo completo de optimización.
    
    Define los parámetros de diseño, inicializa los módulos desacoplados,
    ejecuta el algoritmo genético y despliega los informes.
    """
    print("====================================================")
    print("     OPTIMIZADOR GA-FAARFIELD - SISTEMA MODULAR     ")
    print("====================================================\n")
    
    # --- PARÁMETROS DE ENTRADA ---
    # Aeronave de diseño y módulo de la subrasante según el proyecto
    AVION_DISENO = "A400M TLL1"
    E_SUELO = 40.0 # En MPa
    
    # Inicialización del evaluador (Lógica de ingeniería)
    evaluador = EvaluadorPavimento(AVION_DISENO, E_SUELO)
    
    # Impresión de datos de entrada
    print("--- DATOS DE ENTRADA ---")
    print(f"Aeronave de Diseño: {AVION_DISENO}")
    print(f"Módulo Subgrade:    {E_SUELO} MPa")
    print(f"Configuración:      {evaluador.n_capas} capas automáticas")
    print("------------------------\n")
    
    # Definición de rangos de búsqueda en pulgadas (Estándar FAA)
    # Rangos para Carpeta (HMA), Base (BG/BTA) y Subbase (SB)
    # HMA: 3-8 pulg, Base: 6-18 pulg, Subbase: 6-25 pulg
    limites_busqueda = [(3.0, 8.0), (6.0, 18.0), (6.0, 25.0)]
    
    # Configuración del Algoritmo Genético
    # Mayor población y generaciones para manejar el fitness normalizado
    ga = AlgoritmoGenetico(
        fitness_fn=evaluador.calcular_costo_aptitud,
        limites=limites_busqueda,
        pop_size=25,
        gens=40
    )
    
    # Inicio del proceso evolutivo
    print("Iniciando búsqueda de diseño óptimo (FAARFIELD Model)...")
    MejorInd, Fit, CdfFinal = ga.ejecutar_optimizacion()
    
    # Extracción de reporte técnico y muestra de resultados
    reporte = evaluador.obtener_resumen_tecnico(MejorInd, CdfFinal)
    mostrar_resultados(reporte)


if __name__ == "__main__":
    principal()