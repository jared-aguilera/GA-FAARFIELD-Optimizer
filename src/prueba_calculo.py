import os
import csv
import clr
import System
from System import Double, Int32, Array, String

RUTA_SRC = os.path.dirname(os.path.abspath(__file__))
RUTA_PROYECTO = os.path.dirname(RUTA_SRC)

ARCHIVO_AIRCRAFT = os.path.join(RUTA_PROYECTO, "data", "aircraft.csv")
RUTA_DLL = os.path.join(RUTA_PROYECTO, "bin", "LEAFClassLib.dll")

clr.AddReference(RUTA_DLL)
from LEAFClassLib import clsLEAF

def extraer_parametros_avion(nombre_avion):
    try:
        with open(ARCHIVO_AIRCRAFT, mode='r', encoding='utf-8') as f:
            lector = csv.reader(f)
            for fila in lector:
                if len(fila) > 1 and nombre_avion.upper() in fila[1].upper():
                    n_tires = int(fila[11])
                    return {
                        "peso": float(fila[2]),
                        "presion": float(fila[4]),
                        "n_tires": n_tires,
                        "coords": [float(x) for x in fila[12:12 + (n_tires * 2)]]
                    }
    except Exception: pass
    return None

def evaluar_espesor(espesor_asfalto, nombre_avion="A400M TLL1"):
    datos_ac = extraer_parametros_avion(nombre_avion)
    if not datos_ac: return None

    motor = clsLEAF()
    try:
        est = clsLEAF.LEAFStrParms()
        est.NLayers = 3
        
        thick, mod, poi, inter = [0.0]*21, [0.0]*21, [0.0]*21, [0.0]*21
        
        thick[1], mod[1], poi[1], inter[1] = float(espesor_asfalto), 400000.0, 0.35, 1.0
        thick[2], mod[2], poi[2], inter[2] = 6.0, 20000.0, 0.35, 1.0
        thick[3], mod[3], poi[3], inter[3] = 0.0, 5000.0, 0.40, 1.0
        
        est.Thick, est.Modulus = Array[Double](thick[:20]), Array[Double](mod[:20])
        est.Poisson, est.InterfaceParm = Array[Double](poi[:20]), Array[Double](inter[:20])
        
        est.EvalDepth, est.EvalLayer = float(espesor_asfalto), 1.0
        est.lngDummy, est.dblDummy = Array[Int32]([0]*20), Array[Double]([0.0]*20)
        est.strDummy = Array[String]([""] * 20)

        av = clsLEAF.LEAFACParms()
        av.ACname = nombre_avion
        av.GearLoad = datos_ac["peso"] / 2.0
        av.NTires = datos_ac["n_tires"]
        
        tx, ty, tp = [0.0]*21, [0.0]*21, [0.0]*21
        for i in range(datos_ac["n_tires"]):
            tx[i+1] = datos_ac["coords"][i*2]
            ty[i+1] = datos_ac["coords"][i*2 + 1]
            tp[i+1] = datos_ac["presion"]
            
        av.TireX, av.TireY = Array[Double](tx[:20]), Array[Double](ty[:20])
        av.TirePress = Array[Double](tp[:20])
        
        av.NEvalPoints = 1
        ex, ey = [0.0]*21, [0.0]*21
        ex[1], ey[1] = tx[1], ty[1]
        av.EvalX, av.EvalY = Array[Double](ex[:20]), Array[Double](ey[:20])

        matriz_aviones = Array.CreateInstance(clsLEAF.LEAFACParms, 5)
        matriz_aviones[1] = av

        op = System.Enum.GetValues(clsLEAF.LEAFoptions).GetValue(0)
        res = motor.ComputeResponse(op, 1, matriz_aviones, est, 
                                    Array.CreateInstance(Double, 10, 10), 
                                    Array.CreateInstance(clsLEAF.LEAFAllResponses, 10, 10))
        
        return res[4][1, 1]
    except Exception: return None