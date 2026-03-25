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
    Función FAARFIELD final.
    Recibe la flota con operaciones totales (Ft), el Pd, el Td y la estructura (es).
    También puede recibir una lista de espesores y módulos exactos (para el Optimizador Genético).
    Se conecta al MotorFAARFIELD y devuelve un diccionario con los 5 parámetros requeridos.
    """
    print("\n[+] INICIANDO ANÁLISIS DE DAÑO CON MOTOR FAARFIELD...")
    import sys
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if base_dir not in sys.path:
        sys.path.append(base_dir)
        
    from src.motor_faarfield import MotorFAARFIELD
    motor = MotorFAARFIELD()
    
    n_capas = es["n_capas"]
    subgrade_e_psi = es["modulo_mpa"] * 145.038
    
    if espesores is None or modulos is None:
        # Si no se pasan desde el exterior, revisamos si vienen en el dict de estructura 'es'
        if "espesores" in es and "modulos" in es:
            espesores = es["espesores"]
            modulos = es["modulos"]
        else:
            # Defaults históricos (si no hay datos directos)
            if n_capas == 3:
                espesores = [4.0, 8.0, 0.0]
                modulos = [200000.0, 36259.5, subgrade_e_psi]
            elif n_capas == 4:
                espesores = [4.0, 6.0, 8.0, 0.0]
                modulos = [200000.0, 36259.5, 21755.7, subgrade_e_psi]
            else: # 5 capas
                espesores = [4.0, 6.0, 8.0, 8.0, 0.0]
                modulos = [200000.0, 36259.5, 21755.7, 14503.8, subgrade_e_psi]
            
    z_eval = sum(espesores[:-1]) # Profundidad hasta subrasante
    cdf_subgrade = 0.0
    max_acr = 0.0
    
    for avion in Ft:
        ac_data = motor.buscar_aeronave(avion['nombre'])
        if not ac_data:
            peso_lb = avion['peso_kg'] * 2.20462
            acr_estimado = peso_lb / 2000.0
            if acr_estimado > max_acr: max_acr = acr_estimado
            continue
            
        eps_v_raw = motor.calcular_respuesta(espesores, modulos, ac_data, z_eval)
        try:
            eps_v = float(eps_v_raw)
        except:
            eps_v = 0.0
            
        if eps_v > 0.0 and eps_v != float('inf'):
            nf = (0.004 / eps_v) ** 6
            if nf > 0.0:
                cdf_subgrade += avion['operaciones_totales'] / nf
            else:
                cdf_subgrade += 1e99
                
        acr_avion = ac_data["peso"] / 2000.0
        if acr_avion > max_acr:
            max_acr = acr_avion
            
    cdf_hma = cdf_subgrade * 0.90
    vida = pd / cdf_subgrade if cdf_subgrade > 0 else 100.0
    vida = min(vida, 100.0)
    pcr = max_acr * 1.05
    
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
        print("E >= 69 MPa -> 3 capas (HMA, Base, Subgrado)")
        print("35 <= E < 69 MPa -> 4 capas (HMA, Base, Subbase, Subgrado)")
        print("E < 35 MPa -> 5 capas (HMA, Base, Subbase, Subrasante, Subgrado)")
        
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
        
        if es_mod_val >= 69:
            n_capas_val = 3
        elif 35 <= es_mod_val < 69:
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
            elif i == 4: nombre_capa = "Subrasante/Estabilizada"
            else: nombre_capa = f"Capa {i}"
            
            while True:
                try:
                    esp = float(input(f"    -> Espesor de {nombre_capa} (pulgadas): "))
                    mod = float(input(f"    -> Módulo de {nombre_capa} (MPa): "))
                    espesores_user.append(esp)
                    modulos_user.append(mod * 145.038) # Convertir a PSI para el motor
                    break
                except ValueError:
                    print("     [X] Error: Ingresa un valor numérico válido.")

        # Capa final: Subrasante (espesor 0.0)
        espesores_user.append(0.0)
        modulos_user.append(es_mod_val * 145.038)

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
