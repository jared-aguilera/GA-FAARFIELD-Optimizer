import os
import clr
import xml.etree.ElementTree as ET
import System
from System import Double, Array

# Localización de recursos
DIR_SRC = os.path.dirname(os.path.abspath(__file__))
# DIR_SRC is .../src/funcion_faarfield
# DIR_RAIZ should be .../GA-FAARFIELD-Optimizer
DIR_RAIZ = os.path.dirname(os.path.dirname(DIR_SRC))
DIR_BIN = os.path.join(DIR_RAIZ, "bin")
PATH_AIRCRAFT_XML = os.path.join(DIR_RAIZ, "data", "aircraft.xml")

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

    def obtener_catalogo_aeronaves(self):
        """ Retorna la lista completa de aviones disponibles en la base de datos XML. """
        catalogo = []
        try:
            tree = ET.parse(PATH_AIRCRAFT_XML)
            root = tree.getroot()
            ns = {
                'f': 'http://schemas.datacontract.org/2004/07/FaarFieldModel',
                'a': 'http://schemas.microsoft.com/2003/10/Serialization/Arrays'
            }
            idx = 1
            for ac in root.findall('.//a:anyType', ns):
                name_node = ac.find('f:Name', ns)
                if name_node is not None and name_node.text:
                    catalogo.append({"id": idx, "nombre": name_node.text.strip()})
                    idx += 1
            return catalogo
        except Exception:
            return catalogo

    def buscar_aeronave(self, nombre):
        """
        Extrae parámetros físicos de una aeronave desde el archivo XML nativo.
        
        Args:
            nombre (str): Nombre o identificador de la aeronave.
            
        Returns:
            dict: Datos técnicos (peso, presión, llantas, coordenadas) o None.
        """
        try:
            tree = ET.parse(PATH_AIRCRAFT_XML)
            root = tree.getroot()
            ns = {
                'f': 'http://schemas.datacontract.org/2004/07/FaarFieldModel',
                'a': 'http://schemas.microsoft.com/2003/10/Serialization/Arrays'
            }
            
            for ac in root.findall('.//a:anyType', ns):
                name_node = ac.find('f:Name', ns)
                if name_node is not None and name_node.text and nombre.upper() in name_node.text.upper():
                    peso_node = ac.find('f:_GrossWeight/f:us', ns)
                    presion_node = ac.find('f:Cp/f:us', ns)
                    llantas_node = ac.find('f:NumberWheels', ns)
                    coords_node = ac.find('f:WheelCoordinates', ns)
                    
                    if not (peso_node is not None and presion_node is not None and llantas_node is not None):
                        continue
                        
                    peso = float(peso_node.text)
                    presion = float(presion_node.text)
                    llantas = int(llantas_node.text)
                    
                    coords = []
                    if coords_node is not None:
                        for wc in coords_node.findall('a:anyType', ns):
                            x_node = wc.find('f:X/f:us', ns)
                            y_node = wc.find('f:Y/f:us', ns)
                            if x_node is not None and y_node is not None:
                                coords.extend([float(x_node.text), float(y_node.text)])
                    
                    return {
                        "peso": peso,
                        "presion": presion,
                        "llantas": llantas,
                        "coords": coords
                    }
        except Exception as e:
            return None
        return None

    def calcular_respuesta(self, espesores, modulos, ac_data, z_eval, componente=6, eval_layer=1):
        """
        Ejecuta el análisis de respuesta estructural en el motor LEAF.
        """
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
        est.EvalDepth, est.EvalLayer = float(z_eval), float(eval_layer)

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
        
        # Puntos de evaluación: Exclusivamente debajo de las llantas + Promedios (Centros geométricos)
        ex, ey = [0.0]*50, [0.0]*50
        n_pts = 0
        
        # 1. Directamente bajo cada llanta
        for j in range(1, av.NTires + 1):
            n_pts += 1
            ex[n_pts] = tx[j]
            ey[n_pts] = ty[j]
            
        # 2. Puntos intermedios (Centroides)
        if av.NTires > 1:
            avg_x = sum(tx[1:av.NTires+1]) / av.NTires
            avg_y = sum(ty[1:av.NTires+1]) / av.NTires
            n_pts += 1
            ex[n_pts] = avg_x
            ey[n_pts] = avg_y
            
            # Midpoints entre llantas consecutivas
            for j in range(1, av.NTires):
                n_pts += 1
                ex[n_pts] = (tx[j] + tx[j+1]) / 2.0
                ey[n_pts] = (ty[j] + ty[j+1]) / 2.0
                
        av.NEvalPoints = n_pts
        av.EvalX, av.EvalY = Array[Double](ex[:n_pts+1]), Array[Double](ey[:n_pts+1])

        # Ejecución de cálculo
        matriz = Array.CreateInstance(clsLEAF.LEAFACParms, 2)
        matriz[1] = av
        
        res = self.engine.ComputeResponse(
            self.options, 1, matriz, est, 
            Array.CreateInstance(Double, 21, 21), 
            Array.CreateInstance(clsLEAF.LEAFAllResponses, 21, 21)
        )
        
        # res[4] es la matriz MaxResponses[IndiceAeronave, Componente] (C# DLL ya calcula el pico absoluto automáticamente)
        # IndiceAeronave = 1, Componente = 6 (Ver. Strain) o 4 (Hor. Strain)
        try:
            return abs(res[4][1, componente])
        except Exception:
            return 0.0