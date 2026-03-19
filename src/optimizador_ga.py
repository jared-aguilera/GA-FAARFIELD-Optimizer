import random


class AlgoritmoGenetico:
    """
    Motor de optimización heurística agnóstico al dominio.
    Implementa selección elitista, cruce y mutación.
    """

    def __init__(self, fitness_fn, limites, pop_size=12, gens=20):
        """
        Configura los hiperparámetros del algoritmo.
        
        Args:
            fitness_fn (callable): Función que evalúa la calidad de un individuo.
            limites (list): Lista de tuplas (min, max) para cada variable.
        """
        self.evaluar = fitness_fn
        self.limites = limites
        self.pop_size = pop_size
        self.gens = gens

    def ejecutar_optimizacion(self):
        """
        Inicia el proceso evolutivo para encontrar el mínimo global.
        
        Returns:
            tuple: (mejor_individuo, mejor_fitness, metrica_adicional)
        """
        # Población inicial aleatoria
        poblacion = [
            [random.uniform(l[0], l[1]) for l in self.limites]
            for _ in range(self.pop_size)
        ]
        
        mejor_global = None

        for g in range(self.gens):
            evaluaciones = []
            for ind in poblacion:
                fit, meta = self.evaluar(ind)
                evaluaciones.append((ind, fit, meta))
            
            # Ordenamiento por aptitud (minimización)
            evaluaciones.sort(key=lambda x: x[1])
            mejor_actual = evaluaciones[0]
            
            if not mejor_global or mejor_actual[1] < mejor_global[1]:
                mejor_global = mejor_actual
                
            print(f"Generación {g+1:02d} | Costo: {mejor_actual[1]:.2f} | CDF: {mejor_actual[2]:.4f}")

            # Selección de élite y reproducción
            padres = [e[0] for e in evaluaciones[:self.pop_size // 2]]
            nueva_gen = padres[:]
            
            while len(nueva_gen) < self.pop_size:
                m1, m2 = random.sample(padres, 2)
                # Crossover aritmético con mutación pequeña
                hijo = []
                for i in range(len(m1)):
                    gene = (m1[i] + m2[i]) / 2 + random.uniform(-0.2, 0.2)
                    # Forzar límites
                    gene = max(self.limites[i][0], min(self.limites[i][1], gene))
                    hijo.append(gene)
                nueva_gen.append(hijo)
                
            poblacion = nueva_gen
            
        return mejor_global

class op_recosido_simulado:
    """
    Motor de optimización heurística agnóstico al dominio.
    Implementa selección elitista, cruce y mutación.
    """

    def __init__(self, fitness_fn, limites, pop_size=12, gens=20):
        """
        Configura los hiperparámetros del algoritmo.
        
        Args:
            fitness_fn (callable): Función que evalúa la calidad de un individuo.
            limites (list): Lista de tuplas (min, max) para cada variable.
        """
        self.evaluar = fitness_fn
        self.limites = limites
        self.pop_size = pop_size
        self.gens = gens

    def ejecutar_optimizacion(self):
        """
        Inicia el proceso evolutivo para encontrar el mínimo global.
        
        Returns:
            tuple: (mejor_individuo, mejor_fitness, metrica_adicional)
        """
        # Población inicial aleatoria
        poblacion = [
            [random.uniform(l[0], l[1]) for l in self.limites]
            for _ in range(self.pop_size)
        ]
        
        mejor_global = None

        for g in range(self.gens):
            evaluaciones = []
            for ind in poblacion:
                fit, meta = self.evaluar(ind)
                evaluaciones.append((ind, fit, meta))
            
            # Ordenamiento por aptitud (minimización)
            evaluaciones.sort(key=lambda x: x[1])
            mejor_actual = evaluaciones[0]
            
            if not mejor_global or mejor_actual[1] < mejor_global[1]:
                mejor_global = mejor_actual
                
            print(f"Generación {g+1:02d} | Costo: {mejor_actual[1]:.2f} | CDF: {mejor_actual[2]:.4f}")

            # Selección de élite y reproducción
            padres = [e[0] for e in evaluaciones[:self.pop_size // 2]]
            nueva_gen = padres[:]
            
            while len(nueva_gen) < self.pop_size:
                m1, m2 = random.sample(padres, 2)
                # Crossover aritmético con mutación pequeña
                hijo = []
                for i in range(len(m1)):
                    gene = (m1[i] + m2[i]) / 2 + random.uniform(-0.2, 0.2)
                    # Forzar límites
                    gene = max(self.limites[i][0], min(self.limites[i][1], gene))
                    hijo.append(gene)
                nueva_gen.append(hijo)
                
            poblacion = nueva_gen
            
        return mejor_global