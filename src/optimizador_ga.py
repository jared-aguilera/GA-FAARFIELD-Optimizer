import random
from prueba_calculo import evaluar_espesor

TAMANO_POBLACION = 12
GENERACIONES = 20
ESPESOR_MIN, ESPESOR_MAX = 2.0, 18.0
LIMITE_DEFORMACION = 0.0004 # 400 microstrains (límite de fatiga estándar)

def calcular_aptitud(espesor):
    deformacion = evaluar_espesor(espesor, "A400M TLL1")
    if deformacion is None: return float('inf')
    
    def_abs = abs(deformacion)
    if def_abs > LIMITE_DEFORMACION:
        # Penalización si se supera el límite de fatiga
        return espesor + (def_abs - LIMITE_DEFORMACION) * 1000000
    return espesor

def ejecutar_ga():
    print("Iniciando Optimización Real para A400M TLL1...")
    pob = [random.uniform(5.0, 15.0) for _ in range(TAMANO_POBLACION)] # Inicio más realista

    for gen in range(GENERACIONES):
        res = sorted([(i, calcular_aptitud(i)) for i in pob], key=lambda x: x[1])
        mejor_e, mejor_c = res[0]
        curr_def = abs(evaluar_espesor(mejor_e, "A400M TLL1"))
        
        status = "SEGURO" if mejor_c == mejor_e else "FALLA"
        print(f"Gen {gen+1:02d} | Espesor: {mejor_e:.2f} in | Strain: {curr_def:.6f} | {status}")

        elite = [r[0] for r in res[:TAMANO_POBLACION // 2]]
        nueva_pob = elite[:]
        while len(nueva_pob) < TAMANO_POBLACION:
            p1, p2 = random.sample(elite, 2)
            hijo = (p1 + p2) / 2.0 + random.uniform(-0.5, 0.5)
            nueva_pob.append(max(ESPESOR_MIN, min(ESPESOR_MAX, hijo)))
        pob = nueva_pob
        
    return res[0][0]

if __name__ == "__main__":
    final = ejecutar_ga()
    print(f"\nDISEÑO FINAL ÓPTIMO: {final:.4f} pulgadas")