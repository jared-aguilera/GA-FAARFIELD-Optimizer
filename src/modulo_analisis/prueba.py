import csv
import xml.etree.ElementTree as ET
import os

def probar_busqueda_avion(id_seleccionado):
    # 1. Configurar rutas usando __file__ para que funcione desde cualquier directorio
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    csv_path = os.path.join(base_dir, 'data', 'aircraft.csv') 
    xml_path = os.path.join(base_dir, 'data', 'aircraft.xml')

    # 2. Cargar el CSV usando el módulo csv nativo
    try:
        nombre_avion = None
        current_id = 1
        with open(csv_path, mode='r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            for row in reader:
                if current_id == id_seleccionado:
                    nombre_avion = str(row[1]).strip()
                    break
                current_id += 1
                
        if not nombre_avion:
            print(f"No se encontró el ID {id_seleccionado} en el CSV.")
            return False
            
        print(f"\n--- Selección: ID {id_seleccionado} -> {nombre_avion} ---")
    except Exception as e:
        print(f"Error al leer el CSV: {e}")
        return False

    # 3. Parsear el XML
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Definimos los "apodos" para las rutas largas del XML
        ns = {
            'f': 'http://schemas.datacontract.org/2004/07/FaarFieldModel',
            'a': 'http://schemas.microsoft.com/2003/10/Serialization/Arrays'
        }

        # 4. Buscar el avión por nombre en el XML
        avion_encontrado = None
        for ac in root.findall('.//a:anyType', ns):
            name_node = ac.find('f:Name', ns)
            if name_node is not None and name_node.text is not None and name_node.text.strip() == nombre_avion:
                avion_encontrado = ac
                break

        if avion_encontrado is not None:
            # Extraemos los datos solicitados
            peso_node = avion_encontrado.find('f:_GrossWeight/f:si', ns)
            presion_node = avion_encontrado.find('f:Cp/f:si', ns)
            tren_node = avion_encontrado.find('f:Gear', ns)

            peso = peso_node.text if peso_node is not None else "N/A"
            presion = presion_node.text if presion_node is not None else "N/A"
            tren = tren_node.text if tren_node is not None else "N/A"

            print(f"DATOS CARGADOS DEL XML:")
            print(f" > Peso Bruto (kg): {peso}")
            print(f" > Presión Inflado (kPa): {presion}")
            print(f" > Config. Tren: {tren}")
            return True
        else:
            print(f"¡Ups! El avión '{nombre_avion}' no se encontró en el XML.")
            return False

    except Exception as e:
        print(f"Error al procesar el XML: {e}")
        return False

# --- EJECUCIÓN DE PRUEBA INTERACTIVA ---
if __name__ == "__main__":
    print("=== Buscador de Aeronaves ===")
    while True:
        entrada = input("\nIngresa un ID del 1 al 252 (o 's' para salir): ")
        if entrada.lower() == 's':
            print("Saliendo de la prueba...")
            break
        
        try:
            id_sel = int(entrada)
            if 1 <= id_sel <= 252:
                probar_busqueda_avion(id_sel)
            else:
                print("Por favor, ingresa un número dentro del rango 1 - 252.")
        except ValueError:
            print("Entrada inválida. Asegúrate de ingresar un número o la letra 's'.")