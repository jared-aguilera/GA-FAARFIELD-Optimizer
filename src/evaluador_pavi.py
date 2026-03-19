from src.motor_faarfield import MotorFAARFIELD


class EvaluadorPavimento:
    """
    Módulo de lógica de ingeniería de pavimentos. 
    Aplica normativas de diseño, validación de capas y generación de reportes.
    """

    def __init__(self, avion_id, subgrade_e):
        """
        Prepara el evaluador con las reglas de diseño FAA.
        
        Args:
            avion_id (str): Nombre de la aeronave de diseño.
            subgrade_e (float): Módulo de la subrasante en MPa.
        """
        self.motor = MotorFAARFIELD()
        self.avion_id = avion_id
        self.subgrade_e = subgrade_e
        self.ac_data = self.motor.buscar_aeronave(avion_id)
        
        # Selección automática de capas según módulo de terreno natural
        self.n_capas = 5 if subgrade_e < 30 else 3
        self.paso_10mm = 0.3937  # Equivalente a 10 mm en pulgadas

    def calcular_costo_aptitud(self, cromosomas):
        """
        Evalúa un diseño candidato y devuelve su aptitud (fitness).
        
        Args:
            cromosomas (list): Lista de espesores sugeridos por el GA.
            
        Returns:
            tuple: (valor_aptitud, cdf_calculado)
        """
        # Ajuste a incrementos de 10mm para cumplimiento normativo
        espesores = [round(e / self.paso_10mm) * self.paso_10mm for e in cromosomas]
        
        # Asignación de módulos elásticos por jerarquía de capas
        if self.n_capas == 3:
            modulos = [400000, 20000, self.subgrade_e]
        else:
            modulos = [400000, 25000, 15000, 8000, self.subgrade_e]
            
        deformacion = self.motor.calcular_respuesta(
            espesores, modulos, self.ac_data, espesores[0]
        )
        
        # Estimación de CDF basada en deformación admisible (Objetivo: 0.98)
        limite_falla = 0.0004
        cdf = deformacion / limite_falla
        
        # Función de penalización por incumplimiento de fatiga
        penalizacion = 0
        if cdf > 0.98:
            penalizacion = (cdf - 0.98) * 100000
            
        return sum(espesores) + penalizacion, cdf

    def obtener_resumen_tecnico(self, diseño, cdf):
        """
        Genera el reporte final de 12 puntos para el diseño optimizado.
        """
        vida = 20 / cdf if cdf > 0 else 100.0
        acr = self.ac_data["peso"] / 2000.0
        
        # Normalización de espesores para salida en mm
        espesores_mm = [round(e * 25.4 / 10) * 10 for e in diseño]
        while len(espesores_mm) < 5:
            espesores_mm.append(0)
            
        return {
            "cdf_s": cdf,
            "cdf_h": cdf * 0.85,
            "vida": min(vida, 100.0),
            "tipo": "Nueva Flexible",
            "acr": acr,
            "pcr": f"{acr * 1.08:.1f}/F/B/X/T",
            "h_hma": espesores_mm[0],
            "h_b": espesores_mm[1],
            "h_sb": espesores_mm[2],
            "h_c4": espesores_mm[3],
            "h_c5": espesores_mm[4],
            "e_hma": 3500
        }