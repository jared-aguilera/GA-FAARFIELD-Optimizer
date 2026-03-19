import os
import clr
import csv
import System
from System import Double, Array

# Localización de recursos
DIR_SRC = os.path.dirname(os.path.abspath(__file__))
DIR_RAIZ = os.path.dirname(DIR_SRC)
DIR_BIN = os.path.join(DIR_RAIZ, "bin")
PATH_AIRCRAFT = os.path.join(DIR_RAIZ, "data", "aircraft.csv")

# Carga de biblioteca técnica FAARFIELD
clr.AddReference(os.path.join(DIR_BIN, "LEAFClassLib.dll"))
from LEAFClassLib import clsLEAF


class MotorFAARFIELD:
    """
    Controlador del motor de cálculo LEAF para análisis de esfuerzos.
    Maneja la comunicación con la DLL y la extracción de datos de aeronaves.
    """

    def __init__(self):
        """Inicializa el motor de cálculo y carga opciones predeterminadas."""
        self.engine = clsLEAF()
        self.options = System.Enum.GetValues(clsLEAF.LEAFoptions).GetValue(0)

    def buscar_aeronave(self, nombre):
        """
        Extrae parámetros físicos de una aeronave desde el archivo CSV.
        
        Args:
            nombre (str): Nombre o identificador de la aeronave.
            
        Returns:
            dict: Datos técnicos (peso, presión, llantas, coordenadas) o None.
        """
        try:
            with open(PATH_AIRCRAFT, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) > 11 and nombre.upper() in row[1].upper():
                        n_tires = int(row[11])
                        return {
                            "peso": float(row[2]),
                            "presion": float(row[4]),
                            "llantas": n_tires,
                            "coords": [float(x) for x in row[12:12+(n_tires*2)]]
                        }
        except Exception:
            return None
        return None

    def calcular_respuesta(self, espesores, modulos, ac_data, z_eval):
        """
        Ejecuta el análisis de respuesta estructural en el motor LEAF.
        
        Args:
            espesores (list): Lista de espesores por capa.
            modulos (list): Lista de módulos elásticos por capa.
            ac_data (dict): Diccionario con datos de la aeronave.
            z_eval (float): Profundidad de evaluación.
            
        Returns:
            float: Deformación vertical calculada.
        """
        try:
            # Configuración de estructura
            est = clsLEAF.LEAFStrParms()
            est.NLayers = len(espesores)
            
            t, m, p, i = [0.0]*21, [0.0]*21, [0.0]*21, [0.0]*21
            for idx, (esp, mod) in enumerate(zip(espesores, modulos), 1):
                t[idx], m[idx], p[idx], i[idx] = float(esp), float(mod), 0.35, 1.0
            
            est.Thick = Array[Double](t[:20])
            est.Modulus = Array[Double](m[:20])
            est.Poisson = Array[Double](p[:20])
            est.InterfaceParm = Array[Double](i[:20])
            est.EvalDepth, est.EvalLayer = float(z_eval), 1.0

            # Configuración de carga (Aeronave)
            av = clsLEAF.LEAFACParms()
            av.GearLoad = ac_data["peso"] / 2.0
            av.NTires = ac_data["llantas"]
            
            tx, ty, tp = [0.0]*21, [0.0]*21, [0.0]*21
            for j in range(av.NTires):
                tx[j+1] = ac_data["coords"][j*2]
                ty[j+1] = ac_data["coords"][j*2+1]
                tp[j+1] = ac_data["presion"]
            
            av.TireX = Array[Double](tx[:20])
            av.TireY = Array[Double](ty[:20])
            av.TirePress = Array[Double](tp[:20])
            
            # Punto de evaluación bajo la primera llanta
            av.NEvalPoints = 1
            ex, ey = [0.0]*21, [0.0]*21
            ex[1], ey[1] = tx[1], ty[1]
            av.EvalX, av.EvalY = Array[Double](ex[:20]), Array[Double](ey[:20])

            # Ejecución de cálculo
            matriz = Array.CreateInstance(clsLEAF.LEAFACParms, 2)
            matriz[1] = av
            
            res = self.engine.ComputeResponse(
                self.options, 1, matriz, est, 
                Array.CreateInstance(Double, 10, 10), 
                Array.CreateInstance(clsLEAF.LEAFAllResponses, 10, 10)
            )
            return abs(res[4][1, 1])
        except Exception:
            return 0.0