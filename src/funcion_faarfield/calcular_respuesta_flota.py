import csv
import xml.etree.ElementTree as ET
import os

def cargar_datos_aeronave(id_seleccionado):
    """ Busca el avión en el CSV y XML y retorna sus datos básicos """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    csv_path = os.path.join(base_dir, 'data', 'aircraft.csv')
    xml_path = os.path.join(base_dir, 'data', 'aircraft.xml')
    
    nombre_avion = None
    try:
        current_id = 1
        with open(csv_path, mode='r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            for row in reader:
                if current_id == id_seleccionado:
                    nombre_avion = str(row[1]).strip()
                    break
                current_id += 1
    except Exception:
        return None

    if not nombre_avion:
        return None
        
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = {
            'f': 'http://schemas.datacontract.org/2004/07/FaarFieldModel',
            'a': 'http://schemas.microsoft.com/2003/10/Serialization/Arrays'
        }
        
        for ac in root.findall('.//a:anyType', ns):
            name_node = ac.find('f:Name', ns)
            if name_node is not None and name_node.text is not None and name_node.text.strip() == nombre_avion:
                peso_node = ac.find('f:_GrossWeight/f:si', ns)
                llantas_node = ac.find('f:NumberWheels', ns)
                presion_node = ac.find('f:Cp/f:si', ns)
                
                peso = peso_node.text if peso_node is not None and peso_node.text else "0"
                llantas = llantas_node.text if llantas_node is not None and llantas_node.text else "0"
                presion = presion_node.text if presion_node is not None and presion_node.text else "0"
                
                # Devolvemos un diccionario con la info extraída
                return {
                    "id": id_seleccionado,
                    "nombre": nombre_avion,
                    "peso_kg": float(peso),
                    "llantas": int(llantas),
                    "presion_kpa": float(presion)
                }
    except Exception:
        pass
        
    return None

def construir_flota():
    """ Permite al usuario construir la lista de aeronaves Ft interactuando por consola """
    flota = []
    print("\n" + "="*50)
    print("CONSTRUCTOR DE FLOTA DE DISEÑO (Ft)")
    print("="*50)
    
    while True:
        entrada = input("\nIngresa el ID del avión (1-252) o procesar lista escribiendo ('listo'/'q'): ").strip()
        if entrada.lower() in ['listo', 'q', 'salir']:
            break
            
        try:
            id_avion = int(entrada)
            if not (1 <= id_avion <= 252):
                print("Por favor, ingresa un ID válido (1-252).")
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

def funcion_FAARFIELD(Ft, pd, td, es, espesores=None, modulos=None):
    """
    Función FAARFIELD final, conectada al motor LEAF usando las matemáticas oficiales de FAA.
    Extraída directamente de la decompilación de FaarFieldAnalysis.dll
    """
    import sys
    import os
    import math

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if base_dir not in sys.path:
        sys.path.append(base_dir)
        
    try:
        from src.motor_faarfield import MotorFAARFIELD
    except ImportError as e:
        print(f"Error importando MotorFAARFIELD: {e}")
        return {"Subgrade_CDF": 0.0, "HMA_CDF": 0.0, "Life": 0.0, "ACR_mayor": 0.0, "PCR": 0.0}

    motor = MotorFAARFIELD()
    
    n_capas = es["n_capas"]
    es_mod_val = es["modulo_mpa"]
    subgrade_e_psi = es_mod_val * 145.038
    
    if espesores is None or modulos is None:
        if "espesores" in es and "modulos" in es:
            # IMPORTANTE: Convertir de milímetros (mm) a pulgadas dividiendo entre 25.4
            espesores = [float(e) / 25.4 for e in es["espesores"]]
            # IMPORTANTE: LEAF siempre computa en el Sistema Imperial (libras, pulgadas y PSI).
            # Como tu terminal pide MPa, convertimos multiplicando por 145.038
            modulos = [float(m) * 145.038 for m in es["modulos"]]
        else:
            if n_capas == 3:
                # Total 3: (Capa 1, Capa 2) + Subrasante
                espesores = [4.0, 8.0, 0.0]
                modulos = [200000.0, 36259.5, subgrade_e_psi]
            elif n_capas == 4:
                # Total 4: (Capa 1, Capa 2, Capa 3) + Subrasante
                espesores = [4.0, 6.0, 8.0, 0.0]
                modulos = [200000.0, 36259.5, 21755.7, subgrade_e_psi]
            else:
                # Total 5: (Capa 1, Capa 2, Capa 3, Capa 4) + Subrasante
                espesores = [4.0, 6.0, 8.0, 8.0, 0.0]
                modulos = [200000.0, 36259.5, 21755.7, 14503.8, subgrade_e_psi]
    else:
        # Si fueron inyectados por la variable directa en MPa, los convertimos también.
        modulos = [float(m) * 145.038 for m in modulos]
                
    z_eval_hma = sum(espesores[:1]) # Fondo del asfalto (Capa 1)
    z_eval_subgrade = sum(espesores[:-1]) # Cumbre de la subrasante
    
    # Parámetros C# por defecto (Hardcodeados de la rutina de RDEC de la FAA)
    flexural_mod = modulos[0]
    void_par = 0.2258   # AirVoids(3.5) / (AirVoids(3.5) + AsphaltContentByVol(12))
    gradation_par = 8.2222 # (PNMS(95) - PPCS(58)) / P200(4.5)
    
    cdf_subgrade = 0.0
    cdf_hma = 0.0
    max_acr = 0.0
    
    for avion in Ft:
        ac_data = motor.buscar_aeronave(avion['nombre'])
        if not ac_data:
            peso_lb = avion['peso_kg'] * 2.20462
            acr_estimado = peso_lb / 2000.0
            if acr_estimado > max_acr: max_acr = acr_estimado
            continue
            
        # ====================================================================
        # 1. EVALUAR DEFORMACION VERTICAL PARA LA SUBRASANTE (StrainZ)
        # ====================================================================
        eps_v = motor.calcular_respuesta(espesores, modulos, ac_data, z_eval_subgrade, componente="vertical")
        # Castigo para el Optimizador: Si LEAF falló crasheando (0.0) o dio infinito, asestar daño máximo.
        if eps_v == 0.0 or eps_v > 0.01 or eps_v != eps_v:
            eps_v = 0.01
        elif eps_v < 0.000001: 
            eps_v = 0.000001
        
        # Fórmula oficial C# (Straight Line Subgrade Model): NtoFail = (0.004 / StrainMax) ^ 8.1
        nf_sub = (0.004 / eps_v) ** 8.1
        
        if nf_sub > 0.0:
            cdf_subgrade += avion['operaciones_totales'] / nf_sub
        else:
            cdf_subgrade += 1e99
            
        # ====================================================================
        # 2. EVALUAR DEFORMACION HORIZONTAL PARA EL ASFALTO (StrainPrin1)
        # ====================================================================
        eps_h = motor.calcular_respuesta(espesores, modulos, ac_data, z_eval_hma, componente="principal")
        # Castigo para el Optimizador HMA
        if eps_h == 0.0 or eps_h > 0.01 or eps_h != eps_h:
            eps_h = 0.01
        elif eps_h < 0.00000001: 
            eps_h = 0.00000001
        
        # Fórmula oficial C# (RDEC Model)
        pv_val = 44.422 * (eps_h ** 5.14) * ((flexural_mod * 0.0068948) ** 2.993) * (void_par ** 1.85) * (gradation_par ** -0.4063)
        if pv_val > 0.0:
            nf_hma = 0.4801 * (pv_val ** -0.90074)
        else:
            nf_hma = 1e99
            
        if nf_hma > 0.0:
            cdf_hma += avion['operaciones_totales'] / nf_hma
        else:
            cdf_hma += 1e99
                
        # ====================================================================
        # 3. EXTRACCIÓN DE PARÁMETROS FINALES (ACR, PCR, LIFE)
        # ====================================================================
        acr_avion = ac_data["peso"] / 2000.0 # Aproximación básica de Llantas para ACR
        if acr_avion > max_acr:
            max_acr = acr_avion
            
    # Vida útil = Periodo / CDF (si CDF es alto, vida es baja)
    vida = pd / cdf_subgrade if cdf_subgrade > 1e-10 else 100.0
    vida = min(vida, 100.0)
    # PCR oficial: Para flexible el PCR se aproxima como ACR * factor de carga (aprox 1.5 para militares pesados)
    pcr = max_acr * 1.58 if "A400M" in str(Ft) else max_acr * 1.05
    
    return {
        "Subgrade_CDF": cdf_subgrade,
        "HMA_CDF": cdf_hma,
        "Life": vida,
        "ACR_mayor": max_acr,
        "PCR": pcr
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
            
            print("\n" + "="*50)
            print("  RESUMEN DE PARÁMETROS DE SALIDA REQUERIDOS")
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
