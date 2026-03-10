import random
from src.motor_faarfield import MotorFAARFIELD

TAMANO_POBLACION = 20
GENERACIONES = 15
TASA_MUTACION = 0.2

class OptimizadorPavimento:
    def __init__(self, flota, vida_diseno, subgrade_e):
        self.motor = MotorFAARFIELD(flota, subgrade_e)
        self.vida_diseno = vida_diseno
        self.n = self.motor.obtener_numero_capas(subgrade_e)
        # Rangos balanceados para optimización de costo y seguridad
        self.rangos = [
            (100, 250, 5),   # Carpeta (HMA)
            (150, 450, 10),  # Base
            (150, 600, 20),  # Subbase
            (200, 800, 50),  # Capa 4
            (200, 800, 50)   # Capa 5
        ]
        mod_b = [3500, 2800, 220, 180, 150]
        self.modulos = mod_b[:self.n-1] + [subgrade_e]

    def aptitud(self, espesores):
        res = self.motor.ejecutar_analisis(espesores + [0.0], self.modulos, self.vida_diseno)
        s, h = res['Subgrade_CDF'], res['HMA_CDF']
        
        # Penalización si falla (>1.0)
        penalizacion = 0
        if s > 1.0: penalizacion += (s - 1.0) * 20000 + 100000
        if h > 1.0: penalizacion += (h - 1.0) * 20000 + 100000
        
        # Objetivo: Acercarse a 1.0 (Eficiencia máxima sin fallar)
        # Si s es muy bajo (ej. 0.0), el error es alto, lo que obliga a adelgazar
        error_objetivo = abs(s - 0.95) * 5000 + abs(h - 0.95) * 5000
        
        # PRIORIDAD: Costo (Espesor total). Aumentamos el peso significativamente.
        costo_espesor = sum(espesores) * 2.0 
        
        fit = error_objetivo + penalizacion + costo_espesor
        return fit, res

    def generar(self):
        return [random.randrange(r[0], r[1]+1, r[2]) for r in self.rangos[:self.n-1]]

    def evolucionar(self):
        pob = [self.generar() for _ in range(TAMANO_POBLACION)]
        mejor = None
        
        for gen in range(GENERACIONES):
            # Evaluar y ordenar
            ev = []
            for ind in pob:
                fit, res = self.aptitud(ind)
                ev.append((ind, fit, res))
            
            ev.sort(key=lambda x: x[1])
            if not mejor or ev[0][1] < mejor[1]: mejor = ev[0]
            
            # Selección Elitista
            nueva = [e[0] for e in ev[:TAMANO_POBLACION//4]]
            
            # Reproducción y Mutación
            while len(nueva) < TAMANO_POBLACION:
                p1, p2 = random.sample(nueva[:6], 2)
                hijo = [random.choice([p1[i], p2[i]]) for i in range(len(p1))]
                
                if random.random() < TASA_MUTACION:
                    idx = random.randrange(len(hijo))
                    r = self.rangos[idx]
                    hijo[idx] = random.randrange(r[0], r[1]+1, r[2])
                nueva.append(hijo)
            pob = nueva
            
        return mejor