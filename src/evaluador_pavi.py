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
        # FAA: Estructura de 3 capas (HMA, P-209, Subgrade) o 5 capas (con subbase y base tratada)
        self.n_capas = 5 if subgrade_e < 35 else 3
        self.paso_10mm = 0.3937  # Equivalente a 10 mm en pulgadas

        # Parámetros de diseño (de la notebook)
        self.periodo_diseno = 20.0
        self.target_cdf_s = 0.98
        self.target_cdf_h = 0.98

        # Rangos de normalización
        self.norm_range = {
            "cdf_s": (0.96, 0.99),
            "cdf_h": (0.96, 0.99),
            "vida": (20.0, 22.0)
        }

        # Pesos de fitness (w1:Subgrade, w2:HMA, w3:Thickness/Cost)
        self.weights = (0.5, 0.3, 0.2)

    def normalizar(self, valor, vmin, vmax):
        """Escala un valor al rango [0, 1] respecto a los límites vmin y vmax."""
        if vmax == vmin:
            return 0.0
        return abs(valor - vmin) / (vmax - vmin)

    def calcular_costo_aptitud(self, cromosomas):
        """
        Evalúa un diseño candidato usando errores normalizados ponderados.
        
        Args:
            cromosomas (list): Lista de variables [t_hma, t_base, t_subbase, e_hma].
            
        Returns:
            tuple: (valor_aptitud, cdf_calculado)
        """
        t_hma, t_base, t_subbase, e_hma_mpa = cromosomas
        
        # Ajuste a incrementos de 10mm
        t_hma = round(t_hma / self.paso_10mm) * self.paso_10mm
        t_base = round(t_base / self.paso_10mm) * self.paso_10mm
        t_subbase = round(t_subbase / self.paso_10mm) * self.paso_10mm
        
        e_hma_psi = e_hma_mpa * 145.038
        e_p209_psi = 250.0 * 145.038
        e_p154_psi = 150.0 * 145.038
        e_p152_psi = 100.0 * 145.038
        e_subgrade_psi = self.subgrade_e * 145.038
        
        if self.n_capas == 3:
            espesores = [t_hma, t_base, 0.0]
            modulos = [e_hma_psi, e_p209_psi, e_subgrade_psi]
        else:
            t_p152 = round(8.0 / self.paso_10mm) * self.paso_10mm
            espesores = [t_hma, t_base, t_subbase, t_p152, 0.0]
            modulos = [e_hma_psi, e_p209_psi, e_p154_psi, e_p152_psi, e_subgrade_psi]
            
        z_eval = sum(espesores[:-1])
        respuesta = self.motor.calcular_respuesta(espesores, modulos, self.ac_data, z_eval)
        
        # El motor actual devuelve una deformación vertical en la subrasante
        # Convertimos deformación a CDF usando la ley de fatiga FAA: Nf = (0.004 / eps_v) ^ 6
        # Simplificación de la notebook:
        cdf_s = respuesta / 0.000411 # Ajustado para que ~0.0004 sea 1.0 CDF
        
        # Normalización de errores para fitness
        target_n = self.normalizar(self.target_cdf_s, *self.norm_range["cdf_s"])
        actual_n = self.normalizar(cdf_s, *self.norm_range["cdf_s"])
        
        error_cdf = abs(target_n - actual_n)
        error_grosor = sum(espesores) / 50.0 # Normalización básica de espesor total
        
        # Fitness final (Minimización)
        aptitud = (self.weights[0] * error_cdf) + (self.weights[2] * error_grosor)
        
        # Penalización si CDF excede severamente el máximo
        if cdf_s > 1.2:
            aptitud += 10.0
            
        return aptitud, cdf_s

    def obtener_resumen_tecnico(self, diseño, cdf_s):
        """
        Genera el reporte final de 12 puntos para el diseño optimizado.
        """
        vida = 20 / cdf_s if cdf_s > 0 else 100.0
        acr = self.ac_data["peso"] / 2000.0 if self.ac_data else 50.0
        
        t_hma, t_base, t_subbase, e_hma_mpa = diseño
        
        if self.n_capas == 3:
            espesores_pulg = [t_hma, t_base, 0.0, 0.0, 0.0]
        else:
            espesores_pulg = [t_hma, t_base, t_subbase, 8.0, 0.0]
            
        # Espesores en mm para reporte
        espesores_mm = [round(e * 25.4 / 10) * 10 for e in espesores_pulg]
            
        return {
            "cdf_s": cdf_s,
            "cdf_h": cdf_s * 0.9, # Estimación ponderada
            "vida": min(vida, 100.0),
            "tipo": "Flexible (FAA Standar)",
            "acr": acr,
            "pcr": f"{acr * 1.05:.1f}/F/B/X/T",
            "h_hma": espesores_mm[0],
            "h_b": espesores_mm[1],
            "h_sb": espesores_mm[2],
            "h_c4": espesores_mm[3],
            "h_c5": espesores_mm[4],
            "e_hma": round(e_hma_mpa, 1)
        }