"""
=============================================================
  Inspector de DLL .NET con pythonnet (MODO MASIVO)
  Analiza todas las DLLs en el directorio bin
=============================================================
"""

import os
import clr
import System
import System.Reflection

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
DIR_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DIR_BIN = os.path.join(DIR_ROOT, "bin")

def inspeccionar_dll(dll_path):
    dll_name = os.path.basename(dll_path)
    print(f"\n{'#'*80}")
    print(f"### PROCESANDO: {dll_name}")
    print(f"### RUTA: {dll_path}")
    print(f"{'#'*80}\n")

    try:
        # Cargar el assembly
        clr.AddReference(dll_path)
        assembly = System.Reflection.Assembly.LoadFile(dll_path)
        print(f"✅ Assembly cargado: {assembly.FullName}\n")

        # Listar Tipos
        tipos = assembly.GetTypes()
        print(f"📦 TIPOS ENCONTRADOS: {len(tipos)}")
        
        # Flags para miembros
        flags = (System.Reflection.BindingFlags.Public |
                 System.Reflection.BindingFlags.Instance |
                 System.Reflection.BindingFlags.Static)

        for tipo in tipos:
            print(f"\n  {'─'*40}")
            print(f"  CLASE: {tipo.FullName}")
            print(f"  {'─'*40}")

            # Constructores
            constructores = tipo.GetConstructors()
            if constructores:
                print(f"    🏗️  Constructores ({len(constructores)}):")
                for c in constructores:
                    params = c.GetParameters()
                    param_str = ", ".join([f"{p.ParameterType.Name} {p.Name}" for p in params]) if params else "void"
                    print(f"      - {tipo.Name}({param_str})")

            # Propiedades
            propiedades = tipo.GetProperties(flags)
            if propiedades:
                print(f"    📋 Propiedades ({len(propiedades)}):")
                for p in propiedades:
                    acceso = [a for a, cond in [("get", p.CanRead), ("set", p.CanWrite)] if cond]
                    print(f"      - {p.PropertyType.Name:<20} {p.Name:<30} [{', '.join(acceso)}]")

            # Métodos
            metodos = tipo.GetMethods(flags)
            metodos_filtrados = [
                m for m in metodos
                if m.DeclaringType.FullName != "System.Object"
                and not m.Name.startswith("get_")
                and not m.Name.startswith("set_")
            ]
            if metodos_filtrados:
                print(f"    🔧 Métodos ({len(metodos_filtrados)}):")
                for m in metodos_filtrados:
                    params = m.GetParameters()
                    param_str = ", ".join([f"{p.ParameterType.Name} {p.Name}" for p in params]) if params else ""
                    estatico = " [static]" if m.IsStatic else ""
                    print(f"      - {m.ReturnType.Name:<20} {m.Name}({param_str}){estatico}")

            # Campos
            campos = tipo.GetFields(flags)
            if campos:
                print(f"    📌 Campos ({len(campos)}):")
                for c in campos:
                    estatico = " [static]" if c.IsStatic else ""
                    print(f"      - {c.FieldType.Name:<20} {c.Name}{estatico}")

    except Exception as e:
        print(f"❌ Error procesando {dll_name}: {e}")

def main():
    if not os.path.exists(DIR_BIN):
        print(f"Error: No se encontró la carpeta bin en {DIR_BIN}")
        return

    dlls = [f for f in os.listdir(DIR_BIN) if f.lower().endswith(".dll")]
    
    if not dlls:
        print(f"No se encontraron DLLs en {DIR_BIN}")
        return

    print(f"Se encontraron {len(dlls)} DLLs para analizar.\n")
    
    for dll in dlls:
        dll_path = os.path.abspath(os.path.join(DIR_BIN, dll))
        inspeccionar_dll(dll_path)

if __name__ == "__main__":
    main()
