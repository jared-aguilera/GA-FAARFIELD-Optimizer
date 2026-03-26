"""
=============================================================
  Buscador de Variables en DLLs .NET
  Busca términos específicos como CDF, Life, ACR, PCR
=============================================================
"""

import os
import clr
import System
import System.Reflection

DIR_ROOT = r"C:\Users\x\Documents\GitHub\GA-FAARFIELD-Optimizer"
DIR_BIN = os.path.join(DIR_ROOT, "bin")

# Términos a buscar (en minúsculas para búsqueda insensible a mayúsculas)
TERMINOS_BUSQUEDA = ["cdf", "life", "acr", "pcr", "subgrade", "hma"]

def buscar_en_dll(dll_path):
    dll_name = os.path.basename(dll_path)
    resultados = []

    try:
        clr.AddReference(dll_path)
        assembly = System.Reflection.Assembly.LoadFile(dll_path)
        tipos = assembly.GetTypes()
        
        flags = (System.Reflection.BindingFlags.Public |
                 System.Reflection.BindingFlags.Instance |
                 System.Reflection.BindingFlags.Static |
                 System.Reflection.BindingFlags.NonPublic) # Incluimos no públicos por si acaso

        for tipo in tipos:
            # Buscar en nombre de la clase
            if any(t in tipo.FullName.lower() for t in TERMINOS_BUSQUEDA):
                resultados.append(f"[CLASE] {tipo.FullName}")

            # Buscar en propiedades
            for p in tipo.GetProperties(flags):
                if any(t in p.Name.lower() for t in TERMINOS_BUSQUEDA):
                    resultados.append(f"  [PROP]  {tipo.Name}.{p.Name} ({p.PropertyType.Name})")

            # Buscar en campos
            for f in tipo.GetFields(flags):
                if any(t in f.Name.lower() for t in TERMINOS_BUSQUEDA):
                    resultados.append(f"  [CAMPO] {tipo.Name}.{f.Name} ({f.FieldType.Name})")

            # Buscar en métodos
            for m in tipo.GetMethods(flags):
                if any(t in m.Name.lower() for t in TERMINOS_BUSQUEDA) and not m.Name.startswith("get_") and not m.Name.startswith("set_"):
                    resultados.append(f"  [MÉTODO] {tipo.Name}.{m.Name}")

    except Exception as e:
        pass # Ignorar errores de carga para este script de búsqueda rápida

    return resultados

def main():
    dlls = [f for f in os.listdir(DIR_BIN) if f.lower().endswith(".dll")]
    print(f"Buscando términos: {TERMINOS_BUSQUEDA}\n")

    for dll in dlls:
        dll_path = os.path.abspath(os.path.join(DIR_BIN, dll))
        resultados = buscar_en_dll(dll_path)
        if resultados:
            print(f"--- Resultados en {dll}: ---")
            for r in resultados:
                print(r)
            print()

if __name__ == "__main__":
    main()
