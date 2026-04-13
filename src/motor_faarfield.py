import os
import clr
import csv
import System
from System import Double, Array

# Localización de recursos
print("\n[DEBUG] Cargando MotorFAARFIELD desde: " + os.path.abspath(__file__))
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
        # Opción 4: AllResponses es necesaria para obtener StrainZ y StrainPrin1 simultáneamente
        self.options = clsLEAF.LEAFoptions.AllResponses

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

    def calcular_respuesta(self, espesores, modulos, ac_data, z_eval, componente="vertical"):
        """
        Ejecuta el análisis de respuesta estructural en el motor LEAF.
        
        Args:
            espesores (list): Lista de espesores por capa (EN PULGADAS).
            modulos (list): Lista de módulos elásticos por capa (EN PSI).
            ac_data (dict): Diccionario con datos de la aeronave (LBS y PSI).
            z_eval (float): Profundidad de evaluación (EN PULGADAS).
            componente (str): Tipo de deformación ("vertical" o "principal").
            
        Returns:
            float: Deformación absoluta calculada.
        """
        try:
            # Configuración de estructura
            est = clsLEAF.LEAFStrParms()
            est.NLayers = len(espesores)
            
            t, m, p, i = [0.0]*21, [0.0]*21, [0.0]*21, [0.0]*21
            for idx, (esp, mod) in enumerate(zip(espesores, modulos), 1):
                # Poisson 0.35 para pavimento, 0.40 para subrasante
                poisson = 0.40 if idx == len(espesores) else 0.35
                t[idx], m[idx], p[idx], i[idx] = float(esp), float(mod), poisson, 1.0
            
            est.Thick, est.Modulus, est.Poisson, est.InterfaceParm = Array[Double](t), Array[Double](m), Array[Double](p), Array[Double](i)
            # Offset de 0.001" para asegurar que estamos DENTRO de la capa de interés
            est.EvalDepth = float(z_eval) + 0.001
            
            # Determinación de capa: 1 para Asfalto, última para Subrasante
            if componente == "vertical":
                est.EvalLayer = float(len(espesores))
            else:
                est.EvalLayer = 1.0

            # Configuración de carga (Aeronave)
            av = clsLEAF.LEAFACParms()
            # Carga por rueda (Standard FAA)
            av.GearLoad = (ac_data["peso"] / 2.0) / float(ac_data["llantas"])
            av.NTires = ac_data["llantas"]
            
            tx, ty, tp = [0.0]*21, [0.0]*21, [0.0]*21
            for j in range(av.NTires):
                # Sincronizamos 0 y 1 para máxima compatibilidad con punteros C#
                tx[j+1] = ac_data["coords"][j*2]
                ty[j+1] = ac_data["coords"][j*2+1]
                tp[j+1] = ac_data["presion"]
                if j == 0: tx[0], ty[0], tp[0] = tx[1], ty[1], tp[1]
            
            av.TireX, av.TireY, av.TirePress = Array[Double](tx), Array[Double](ty), Array[Double](tp)
            av.NEvalPoints = 1
            ex, ey = [0.0]*21, [0.0]*21
            ex[0], ey[0] = tx[1], ty[1] # Punto bajo la primera llanta
            ex[1], ey[1] = tx[1], ty[1]
            av.EvalX, av.EvalY = Array[Double](ex), Array[Double](ey)

            matriz = Array.CreateInstance(clsLEAF.LEAFACParms, 2)
            matriz[0] = av
            matriz[1] = av
            
            out_resp = Array.CreateInstance(Double, 11, 11)
            out_all = Array.CreateInstance(clsLEAF.LEAFAllResponses, 11, 11)
            
            res = self.engine.ComputeResponse(
                self.options, 1, matriz, est, out_resp, out_all
            )
            
            all_resps = res[5]
            try:
                response = all_resps[1, 1]
                if response.StrainZ == 0: response = all_resps[0, 0]
            except:
                response = all_resps[0, 0]
                
            if componente == "vertical":
                return abs(response.StrainZ)
            elif componente == "principal":
                return abs(response.StrainPrin1)
            else:
                return abs(response.StrainZ)
                
        except Exception as e:
            print(f" [!] Error en Motor LEAF: {e}")
            return 0.0001