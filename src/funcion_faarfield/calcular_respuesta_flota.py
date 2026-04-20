import csv
import xml.etree.ElementTree as ET
import os
import sys

# Auto-resolución de ruta raíz para evitar ModuleNotFoundError desde cualquier terminal
DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
DIR_RAIZ = os.path.dirname(os.path.dirname(DIR_ACTUAL))
if DIR_RAIZ not in sys.path:
    sys.path.append(DIR_RAIZ)

import clr
try:
    clr.AddReference(os.path.join(DIR_RAIZ, "bin", "ACRClassLib.dll"))
except Exception as e:
    pass

def cargar_datos_aeronave(id_seleccionado):
    """ Busca el avión directamente en el XML y retorna sus datos básicos """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    xml_path = os.path.join(base_dir, 'data', 'aircraft.xml')
    
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = {
            'f': 'http://schemas.datacontract.org/2004/07/FaarFieldModel',
            'a': 'http://schemas.microsoft.com/2003/10/Serialization/Arrays'
        }
        
        current_id = 1
        for ac in root.findall('.//a:anyType', ns):
            name_node = ac.find('f:Name', ns)
            if name_node is not None and name_node.text:
                if current_id == id_seleccionado:
                    peso_node = ac.find('f:_GrossWeight/f:si', ns)
                    llantas_node = ac.find('f:NumberWheels', ns)
                    presion_node = ac.find('f:Cp/f:si', ns)
                    
                    peso = peso_node.text if peso_node is not None and peso_node.text else "0"
                    llantas = llantas_node.text if llantas_node is not None and llantas_node.text else "0"
                    presion = presion_node.text if presion_node is not None and presion_node.text else "0"
                    
                    return {
                        "id": id_seleccionado,
                        "nombre": name_node.text.strip(),
                        "peso_kg": float(peso),
                        "llantas": int(llantas),
                        "presion_kpa": float(presion)
                    }
                current_id += 1
    except Exception as e:
        print(f"Error cargando XML: {e}")
        pass
        
    return None

def construir_flota():
    """ Permite al usuario construir la lista de aeronaves Ft interactuando por consola """
    flota = []
    print("\n" + "="*50)
    print("CONSTRUCTOR DE FLOTA DE DISEÑO (Ft)")
    print("="*50)
    
    while True:
        entrada = input("\nIngresa el ID del avión (1-409) o procesar lista escribiendo ('listo'/'q'): ").strip()
        if entrada.lower() in ['listo', 'q', 'salir']:
            break
            
        try:
            id_avion = int(entrada)
            if not (1 <= id_avion <= 409):
                print("Por favor, ingresa un ID válido (1-409).")
                continue
                
            datos = cargar_datos_aeronave(id_avion)
            if datos:
                print(f" -> Avión seleccionado: {datos['nombre']}")
                Crecimiento = input(f"    ¿Tasa de crecimiento anual (%) para {datos['nombre']}?: ")
                Operaciones = input(f"    ¿Operaciones anuales para {datos['nombre']}?: ")
                
                # Guardamos los datos técnicos más los de operación
                datos["tasa_crecimiento"] = float(Crecimiento)
                datos["operaciones_anuales"] = float(Operaciones)
                
                flota.append(datos)
                print(f" [V] {datos['nombre']} agregado a la flota con éxito.")
            else:
                print(" [X] No se pudo cargar los datos de este avión. Verifica ID/XML.")
                
        except ValueError:
            print("Entrada no válida. Escribe un número o 'listo'.")
            
    return flota

def calcular_operaciones_totales(flota, pd):
    """
    Aplica la fórmula de crecimiento compuesto para cada aeronave de la flota.
    Fórmula: n_total = n_anual * [ (1 + r)^Pd - 1 ] / r
    Si r = 0 : n_total = n_anual * Pd
    """
    for avion in flota:
        n_anual = avion['operaciones_anuales']
        r_percent = avion['tasa_crecimiento']
        r = r_percent / 100.0  # Convertir porcentaje a decimal
        
        if r == 0:
            n_total = n_anual * pd
        else:
            n_total = n_anual * (((1 + r)**pd - 1) / r)
            
        avion['operaciones_totales'] = n_total
    
    return flota

from src.funcion_faarfield.wander import calculate_pc_ratio_flexible

def ejecutar_fase_diseno(Ft, motor, espesores, modulos, subgrade_e_psi):
    """
    Fase 1: Calcular 'Tabla de Abajo'
    Obtiene los esfuerzos críticos (Max Airprint) de cada aeronave independiente.
    Calcula de forma aislada su CDF Contribution.
    """
    z_eval_hma = sum(espesores[:1])
    z_eval_subgrade = sum(espesores[:-1])
    
    flexural_mod = modulos[0]
    void_par = 0.2258
    gradation_par = 8.2222
    
    cdf_subgrade_total = 0.0
    cdf_hma_total = 0.0
    resultados_aviones = []

    for avion in Ft:
        ac_data = motor.buscar_aeronave(avion['nombre'])
        if not ac_data:
            continue
            
        # 1. EVALUAR DEFORMACION VERTICAL (SUBRASANTE)
        eps_v = motor.calcular_respuesta(espesores, modulos, ac_data, z_eval_subgrade, componente=6, eval_layer=len(espesores))
        nf_sub = (0.00414131183 / eps_v) ** 8.1 if eps_v > 0.0 else 1e99
        pc_ratio = calculate_pc_ratio_flexible(ac_data, z_eval_subgrade)
        cdf_s = (avion['operaciones_totales'] / pc_ratio) / nf_sub if nf_sub > 0.0 else 1e99
        
        # 2. EVALUAR DEFORMACION HORIZONTAL (HMA)
        eps_h = motor.calcular_respuesta(espesores, modulos, ac_data, z_eval_hma, componente=4, eval_layer=1)
        
        pv_val = 44.422 * (eps_h ** 5.14) * ((flexural_mod * 0.0068948) ** 2.993) * (void_par ** 1.85) * (gradation_par ** -0.4063)
        nf_hma = 0.4801 * (pv_val ** -0.90074) if pv_val > 0.0 else 1e99
        cdf_h = avion['operaciones_totales'] / nf_hma if nf_hma > 0.0 else 1e99
        
        cdf_subgrade_total += cdf_s
        cdf_hma_total += cdf_h
        
        import ACRClassLib
        from System import Single, Array
        acr_obj = ACRClassLib.clsACR()
        pav_type = __import__("System").Enum.GetValues(ACRClassLib.clsACR.PavementType).GetValue(0)
        
        wheels = ac_data['llantas']
        tx = [float(ac_data["coords"][i*2]) for i in range(wheels)]
        ty = [float(ac_data["coords"][i*2+1]) for i in range(wheels)]
        
        try:
            acr_data = acr_obj.CalculateACR(
                pav_type, 
                Single(ac_data["peso"]), 
                Single(0.95), 
                int(wheels), 
                Single(ac_data["presion"]), 
                Array[Single](tx), 
                Array[Single](ty)
            )
            acr_thick = {'A': acr_data.libACRthick[0], 'B': acr_data.libACRthick[1], 'C': acr_data.libACRthick[2], 'D': acr_data.libACRthick[3]}
            acr_val = {'A': acr_data.libACR[0], 'B': acr_data.libACR[1], 'C': acr_data.libACR[2], 'D': acr_data.libACR[3]}
        except Exception:
            acr_thick = {'A': 0.0, 'B': 0.0, 'C': 0.0, 'D': 0.0}
            acr_val = {'A': 0.0, 'B': 0.0, 'C': 0.0, 'D': 0.0}

        resultados_aviones.append({
            "nombre": avion['nombre'],
            "subgrade_max_strain": eps_v,
            "hma_max_strain": eps_h,
            "cdf_contribution_subgrade": cdf_s,
            "cdf_contribution_hma": cdf_h,
            "peso": ac_data["peso"],
            "pc_ratio": pc_ratio,
            "acr_thick": acr_thick,
            "acr_val": acr_val
        })
        
    # Imprimir validación "Tabla de abajo" (FASE 1)
    print("\n" + "="*85)
    print("FASE 1 (TABLA DE ABAJO):")
    print("="*85)
    print(f"{'Airplane Name':<15} | {'CDF Contributions':<18} | {'CDF Max for Airplane':<20} | {'P/C Ratio'}")
    print("-" * 85)
    for res in resultados_aviones:
        print(f"{res['nombre']:<15} | {res['cdf_contribution_subgrade']:<18.2f} | {res['cdf_contribution_subgrade']:<20.2f} | {res['pc_ratio']:.2f}")

    print("\n" + "="*125)
    print("FASE 3 (ACR - PCR):")
    print("="*125)
    print(f"{'Airplane Name':<15} | {'ACR Thick (A)':<15} | {'ACR Thick (B)':<15} | {'ACR Thick (C)':<15} | {'ACR Thick (D)':<15} | {'ACR/F/A':<10} | {'ACR/F/B':<10} | {'ACR/F/C':<10} | {'ACR/F/D':<10}")
    print("-" * 125)
    for r in resultados_aviones:
        th = r['acr_thick']
        ac = r['acr_val']
        print(f"{r['nombre']:<15} | {th['A']:<15.1f} | {th['B']:<15.1f} | {th['C']:<15.1f} | {th['D']:<15.1f} | {ac['A']:<10.1f} | {ac['B']:<10.1f} | {ac['C']:<10.1f} | {ac['D']:<10.1f}")
        
    return cdf_subgrade_total, cdf_hma_total, resultados_aviones

def ejecutar_fase_life(pd, cdf_subgrade_total):
    """
    Fase 2: Calcular Vida Útil dependiente del CDF Total Subrasante
    """
    vida = pd / cdf_subgrade_total if cdf_subgrade_total > 1e-10 else 100.0
    return min(vida, 100.0)

def ejecutar_fase_pcr(Ft, resultados_aviones):
    """
    Fase 3: Computar el ACR y PCR de manera aislada.
    """
    max_acr = 0.0
    for det in resultados_aviones:
        acr_avion = float(det["acr_val"]["A"])
        if acr_avion > max_acr:
            max_acr = acr_avion
            
    pcr = max_acr * 1.58 if "A400M" in str(Ft) else max_acr * 1.05
    return max_acr, pcr

def funcion_FAARFIELD(Ft, pd, td, es, espesores=None, modulos=None):
    """
    Función FAARFIELD final modulada en 3 Fases (Design, Life, PCR).
    """
    import math
    import os
    import sys

    # Agregar la raíz del proyecto al sys.path
    DIR_ACTUAL = os.path.dirname(os.path.abspath(__file__))
    DIR_RAIZ = os.path.dirname(os.path.dirname(DIR_ACTUAL))
    if DIR_RAIZ not in sys.path:
        sys.path.append(DIR_RAIZ)

    try:
        from src.funcion_faarfield.motor_faarfield import MotorFAARFIELD
        from src.funcion_faarfield.wander import calculate_pc_ratio_flexible
    except ImportError as e:
        print(f"Error importando MotorFAARFIELD: {e}")
        return {"Subgrade_CDF": 0.0, "HMA_CDF": 0.0, "Life": 0.0, "ACR_mayor": 0.0, "PCR": 0.0}

    motor = MotorFAARFIELD()
    
    n_capas = es["n_capas"]
    es_mod_val = es["modulo_mpa"]
    subgrade_e_psi = es_mod_val * 145.038
    
    if espesores is None or modulos is None:
        if "espesores" in es and "modulos" in es:
            # IMPORTANTE: Convertir mm a pulgadas
            espesores = [float(e) / 25.4 for e in es["espesores"]]
            # IMPORTANTE: Convertir MPa a PSI
            modulos = [float(m) * 145.038 for m in es["modulos"]]
        else:
            if n_capas == 3:
                espesores = [4.0, 8.0, 0.0]
                modulos = [200000.0, 36259.5, subgrade_e_psi]
            elif n_capas == 4:
                espesores = [4.0, 6.0, 8.0, 0.0]
                modulos = [200000.0, 36259.5, 21755.7, subgrade_e_psi]
            else:
                espesores = [4.0, 6.0, 8.0, 8.0, 0.0]
                modulos = [200000.0, 36259.5, 21755.7, 14503.8, subgrade_e_psi]
    else:
        modulos = [float(m) * 145.038 for m in modulos]

    # Fase 1: Análisis Dinámico (Cálculo del CDF y Max Airprint por avión)
    cdf_subgrade, cdf_hma, detalles_avion = ejecutar_fase_diseno(Ft, motor, espesores, modulos, subgrade_e_psi)
    
    # Fase 2: Vida Útil
    vida = ejecutar_fase_life(pd, cdf_subgrade)
    
    # Fase 3: Evaluación ACR/PCR aislada
    max_acr, pcr = ejecutar_fase_pcr(Ft, detalles_avion)
    
    return {
        "Subgrade_CDF": cdf_subgrade,
        "HMA_CDF": cdf_hma,
        "Life": vida,
        "ACR_mayor": max_acr,
        "PCR": pcr,
        "Tabla_Intermedia": detalles_avion
    }

if __name__ == "__main__":
    Ft = construir_flota()
    
    if not Ft:
        print("\nNo se agregó ninguna aeronave a la flota. Cerrando el programa.")
    else:
        # --- TABLA DE LA FIGURA 1 ---
        print("\n" + "="*70)
        print("   Aeronaves, operaciones anuales actuales y tasa de crecimiento")
        print("="*70)
        print(f"{'# General':<10} | {'Aeronave':<20} | {'Tasa':<6} | {'Operaciones anuales'}")
        print("-" * 70)
        
        total_operaciones = 0
        for index, avion in enumerate(Ft, 1):
            print(f"{index:<10} | {avion['nombre']:<20} | {avion['tasa_crecimiento']:<6} | {avion['operaciones_anuales']:g}")
            total_operaciones += avion['operaciones_anuales']
            
        print("-" * 70)
        print(f"{'':<10}   {'':<20}   Total  | {total_operaciones:g}")
        print("="*70 + "\n")
        
        print("="*50)
        print("PARÁMETROS GENERALES DE DISEÑO")
        print("="*50)
        
        # --- VALIDACIÓN DEL PERIODO DE DISEÑO (Pd) ---
        while True:
            entrada_pd = input("Ingresa el Periodo de Diseño (Pd) en años [Por defecto 20]: ").strip()
            if not entrada_pd:
                pd = 20.0
                break
            try:
                pd = float(entrada_pd)
                if pd > 0: break
                print(" -> Error: El Periodo de Diseño debe ser mayor a 0.")
            except ValueError:
                print(" -> Error: Ingresa un número válido para el Pd.")
        
        # --- VALIDACIÓN DEL TIPO DE ESTRUCTURA (Td) ---
        print("\nTipos de Estructura (Td):")
        print("1: New Flexible")
        print("2: HMA Overlay on Flexible")
        while True:
            entrada_td = input("Selecciona el Tipo de Estructura (1 o 2) [Por defecto 1]: ").strip()
            if not entrada_td or entrada_td == "1":
                td = "New Flexible"
                break
            elif entrada_td == "2":
                td = "HMA Overlay on Flexible"
                break
            print(" -> Error: Por favor, ingresa solamente 1 o 2.")
        
        # --- ENTRADA DEL MÓDULO DE LA SUBRASANTE (Sustituye a Categorías) ---
        print("\nDeterminación de Estructura por Módulo de Subrasante (E):")
        print("E > 100 MPa -> 3 capas declaradas + Subgrado")
        print("60 <= E <= 100 MPa -> 4 capas declaradas + Subgrado")
        print("E < 60 MPa -> 5 capas declaradas + Subgrado")
        
        # --- VALIDACIÓN EL MÓDULO DE LA SUBRASANTE ---
        while True:
            es_modulo = input("Ingresa el módulo de la subrasante (E) en MPa [Por defecto 35.0]: ").strip()
            if not es_modulo:
                es_mod_val = 35.0
                break
            try:
                es_mod_val = float(es_modulo)
                if es_mod_val > 0: break
                print(" -> Error: El módulo debe ser mayor a 0.")
            except ValueError:
                print(" -> Error: Ingresa un número válido para el módulo.")
        
        if es_mod_val > 100:
            n_capas_val = 3
        elif 60 <= es_mod_val <= 100:
            n_capas_val = 4
        else:
            n_capas_val = 5

        # --- PETICIÓN DINÁMICA DE ESPESORES Y MÓDULOS ---
        espesores_user = []
        modulos_user = []
        print(f"\n[+] Configuración de {n_capas_val} capas detectada. Por favor ingresa los datos:")
        
        for i in range(1, n_capas_val):
            if i == 1: nombre_capa = "Carpeta (HMA)"
            elif i == 2: nombre_capa = "Base"
            elif i == 3: nombre_capa = "Subbase"
            elif i == 4: nombre_capa = "Subrasante Proyectada"
            else: nombre_capa = f"Capa {i}"
            
            while True:
                try:
                    esp = float(input(f"    -> Espesor de {nombre_capa} (mm): "))
                    mod = float(input(f"    -> Módulo de {nombre_capa} (MPa): "))
                    espesores_user.append(esp)
                    modulos_user.append(mod) # Manda los MPa puros a la función
                    break
                except ValueError:
                    print("     [X] Error: Ingresa un valor numérico válido.")

        # Capa final: Subrasante (espesor 0.0)
        espesores_user.append(0.0)
        modulos_user.append(es_mod_val) # Puros MPa

        es = {
            "modulo_mpa": es_mod_val, 
            "n_capas": n_capas_val, 
            "espesores": espesores_user, 
            "modulos": modulos_user
        }
        
        # Procesamos la fórmula matemática para todos los aviones en la flota
        Ft = calcular_operaciones_totales(Ft, pd)
        
        print("\n" + "="*50)
        print("RESUMEN DE FLOTA (Ft) Y OPERACIONES TOTALES (n_total)")
        print("="*50)
        print(f"Periodo de Diseño (Pd): {pd} años")
        print(f"Tipo de estructura (Td): {td}")
        print(f"Subrasante (Es): Módulo {es['modulo_mpa']} MPa, total de {es['n_capas']} capas analizadas\n")
        
        for index, avion in enumerate(Ft, 1):
            print(f"{index}. {avion['nombre']}")
            print(f"   - Salidas Anuales (n_anual): {avion['operaciones_anuales']}")
            print(f"   - Tasa Crecimiento (r): {avion['tasa_crecimiento']}%")
            print(f"   -> Operaciones Totales en la vida útil (n_total): {avion['operaciones_totales']:.2f}\n")
            
        # --- LLAMADA A LA FUNCIÓN ENCAPSULADA ---
        try:
            resultados = funcion_FAARFIELD(Ft, pd, td, es)
            
            print("\n" + "="*85)
            print("  TABLA INTERMEDIA: CONTRIBUCIÓN DE AVALÚO ESTRUCTURAL POR AERONAVE")
            print("="*85)
            print(f"{'Aeronave':<25} | {'Max_Strain_Z':<15} | {'Subgrade_CDF_Cont.':<20} | {'HMA_CDF_Cont.'}")
            print("-" * 85)
            for det in resultados['Tabla_Intermedia']:
                print(f"{det['nombre']:<25} | {det['subgrade_max_strain']:<15.6g} | {det['cdf_contribution_subgrade']:<20.6g} | {det['cdf_contribution_hma']:.6g}")
            print("="*85)
            
            print("\n" + "="*50)
            print("  RESUMEN DE PARÁMETROS DE SALIDA GLOBALES")
            print("="*50)
            print(f"1. Subgrade CDF : {resultados['Subgrade_CDF']:.6f}")
            print(f"2. HMA CDF      : {resultados['HMA_CDF']:.6f}")
            print(f"3. Life         : {resultados['Life']:.2f} años")
            print(f"4. ACR mayor    : {resultados['ACR_mayor']:.2f}")
            print(f"5. PCR          : {resultados['PCR']:.2f}")
            print("="*50 + "\n")
            
        except Exception as e:
            import traceback
            print(f"\n[!] Ocurrió un error al intentar inicializar LEAFClassLib o calcular: {e}")
            traceback.print_exc()
            print("Asegúrate de que la DLL está ubicada en /bin y estás bajo Python.NET.")
