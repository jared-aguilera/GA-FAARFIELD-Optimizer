import os
import clr
import System
import System.Reflection

BIN_DIR = r"C:\Users\x\Documents\GitHub\GA-FAARFIELD-Optimizer\bin"
SEARCH_TERMS = ['cdf', 'pcr', 'acr', 'mayor', 'life', 'hma', 'subgrade', 'max']
DLLS = ['FaarFieldModel.dll', 'FaarFieldAnalysis.dll', 'ACClassLib.dll', 'LEAFClassLib.dll']

def search():
    output_path = r"C:\Users\x\Documents\GitHub\GA-FAARFIELD-Optimizer\src\modulo_analisis\busqueda_detalle.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        for dll_name in DLLS:
            path = os.path.join(BIN_DIR, dll_name)
            if not os.path.exists(path): continue
            
            f.write(f"\n{'='*50}\nDLL: {dll_name}\n{'='*50}\n")
            try:
                clr.AddReference(path)
                assembly = System.Reflection.Assembly.LoadFile(path)
                for t in assembly.GetTypes():
                    # Check class name
                    if any(s in t.Name.lower() for s in SEARCH_TERMS):
                        f.write(f"[CLASE] {t.FullName}\n")
                    
                    # Check members
                    for m in t.GetMembers():
                        if any(s in m.Name.lower() for s in SEARCH_TERMS):
                            member_type = m.MemberType.ToString()
                            f.write(f"  [{member_type}] {t.Name}.{m.Name}\n")
            except Exception as e:
                f.write(f"ERROR en {dll_name}: {e}\n")

if __name__ == "__main__":
    search()
