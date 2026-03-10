import os
import clr
import sys
import csv
import math
import System
from System import Double, Array, String, Int32, Single, Boolean

RUTA_BIN = r"c:\Users\x\Documents\GitHub\GA-FAARFIELD-Optimizer\bin"
RUTA_DATA = r"c:\Users\x\Documents\GitHub\GA-FAARFIELD-Optimizer\data"

# Solo LEAFClassLib, sin ACRClassLib para evitar crashes
clr.AddReference(os.path.join(RUTA_BIN, "LEAFClassLib.dll"))
from LEAFClassLib import clsLEAF

class MotorFAARFIELD:
    def __init__(self, flota_config, subgrade_e):
        self.motor = clsLEAF()
        self.biblioteca = self._cargar_biblioteca()
        self.flota = self._preparar_flota(flota_config)
        self.opciones = System.Enum.GetValues(clsLEAF.LEAFoptions).GetValue(0)

    def _cargar_biblioteca(self):
        datos = {}
        try:
            with open(os.path.join(RUTA_DATA, "aircraft.csv"), mode='r', encoding='utf-8') as f:
                for fila in csv.reader(f):
                    if len(fila) > 11:
                        datos[fila[1].strip()] = {"P": float(fila[2]), "Pr": float(fila[4]), "T": int(fila[11])}
        except: pass
        return datos

    def _preparar_flota(self, config):
        flota_lista = []
        for ac in config:
            info = self.biblioteca.get(ac['nombre'])
            if not info: continue
            p = clsLEAF.LEAFACParms()
            p.GearLoad, p.NTires = info['P']/2.0, info['T']
            p.TirePress = Array[Double]([info['Pr']]*21)
            p.TireX, p.TireY = Array[Double]([0.0]*21), Array[Double]([0.0]*21)
            p.NEvalPoints = 1
            p.EvalX, p.EvalY = Array[Double]([0.0]*21), Array[Double]([0.0]*21)
            # ACR manual para evitar el crash de la DLL ACRClassLib
            p_acr = info['P'] / 2000.0 * 1.8 
            flota_lista.append({'params': p, 'deps': ac['annual_deps'], 'nombre': ac['nombre'], 'peso': info['P'], 'acr': p_acr})
        return flota_lista

    def obtener_numero_capas(self, subgrade_e):
        """
        Lógica exacta según Tabla 2: Número de capas en función del módulo:
        - Cat A (>= 150): 3 capas
        - Cat B (>= 100 y < 150): 3 capas
        - Cat C (60 <= E < 100): 4 capas
        - Cat D (< 60): 4 capas
        - Cat D' (< 50): 5 capas
        - Cat D'' (< 30): 5 capas
        """
        if subgrade_e >= 100:
            return 3
        elif subgrade_e >= 50:
            return 4
        else:
            return 5

    def calcular_n_admisible_sub(self, strain_v):
        try:
            val = abs(strain_v)
            if val < 1e-10: return 1e20
            return (0.00311 / val) ** 7.14
        except: return 1.0

    def calcular_n_admisible_hma(self, strain_t, mod_hma_psi):
        try:
            val = abs(strain_t)
            if val < 1e-10: return 1e20
            return 0.00184 * (val ** -3.291) * (mod_hma_psi ** -0.854)
        except: return 1.0

    def ejecutar_analisis(self, espesores, modulos, vida_diseno=20):
        n = len(espesores)
        est = clsLEAF.LEAFStrParms()
        est.NLayers = n
        t_p, m_p = Array[Double]([0.0]*21), Array[Double]([0.0]*21)
        for i in range(n):
            t_p[i+1], m_p[i+1] = espesores[i]/25.4, modulos[i]*145.038
        est.Thick, est.Modulus = t_p, m_p
        est.Poisson, est.InterfaceParm = Array[Double]([0.35]*21), Array[Double]([1.0]*21)

        cdf_sub, cdf_hma, m_acr = 0.0, 0.0, 0.0
        depth_sub = sum(t_p)
        r_m, a_m = Array.CreateInstance(Double, 11, 11), Array.CreateInstance(clsLEAF.LEAFAllResponses, 11, 11)

        for ac in self.flota:
            m_acr = max(m_acr, ac['acr'])
            
            # Deformación horizontal por tracción (HMA) - Índice 5 (Major Principal)
            est.EvalDepth = t_p[1]
            def_h = abs(self._calc(est, ac['params'], r_m, a_m, 5))
            n_hma = self.calcular_n_admisible_hma(def_h, m_p[1])
            
            # Deformación vertical por compresión (Subgrade) - Índice 4 (Vertical)
            est.EvalDepth = depth_sub
            def_s = abs(self._calc(est, ac['params'], r_m, a_m, 4))
            n_sub = self.calcular_n_admisible_sub(def_s)
            
            n_aplicadas = ac['deps'] * vida_diseno
            cdf_hma += n_aplicadas / n_hma if n_hma > 0 else 10.0
            cdf_sub += n_aplicadas / n_sub if n_sub > 0 else 10.0

        return {
            "Subgrade_CDF": cdf_sub, "HMA_CDF": cdf_hma,
            "Life": vida_diseno / cdf_sub if cdf_sub > 1e-4 else 100.0,
            "Max_ACR": m_acr, "PCR": f"{int(m_acr+5)}/F/B/X/T"
        }

    def _calc(self, est, av, r, a, indice):
        m = Array.CreateInstance(clsLEAF.LEAFACParms, 6)
        m[1] = av
        try:
            res = self.motor.ComputeResponse(self.opciones, 1, m, est, r, a)
            return res[4][indice, 1]
        except: return 0.0001
