import os
import clr
import sys

base_dir = r"c:\Users\PC\Documents\Documentos de Universidad\Trabajos\4to Semestre\faarfield\GA-FAARFIELD-Optimizer"
bin_dir = os.path.join(base_dir, "bin")

try:
    clr.AddReference(os.path.join(bin_dir, "FaarFieldModel.dll"))
    clr.AddReference(os.path.join(bin_dir, "FaarFieldAnalysis.dll"))
except Exception as e:
    print(f"Error cargando DLLs: {e}")
    sys.exit(1)

import FaarFieldModel
import FaarFieldAnalysis

print("====== FaarFieldModel ======")
print("\nIntentando instanciar AirplaneInfo...")
try:
    av = FaarFieldModel.AirplaneInfo()
    print("AirplaneInfo instanciado exitosamente.")
    print("Algunas Propiedades en AirplaneInfo:")
    for prop in dir(av):
        if 'cdf' in prop.lower() or 'pcr' in prop.lower() or 'acr' in prop.lower():
            print(f"   > {prop}")
except Exception as e:
    print(f"Error instanciando AirplaneInfo: {e}")

print("\nIntentando instanciar Section...")
try:
    sec = FaarFieldModel.Section()
    print("Section instanciado exitosamente.")
    print("Algunas Propiedades en Section:")
    for prop in dir(sec):
        if 'cdf' in prop.lower() or 'life' in prop.lower() or 'pcn' in prop.lower() or 'pcr' in prop.lower():
            print(f"   > {prop}")
except Exception as e:
    print(f"Error instanciando Section: {e}")

print("\n====== FaarFieldAnalysis ======")
print("Classes en FaarFieldAnalysis:")
for item in dir(FaarFieldAnalysis):
    if not item.startswith("__"):
        print(f" - {item}")

print("\nIntentando inspeccionar CDF class en FaarFieldAnalysis...")
try:
    # Podría ser estática o requerir parámetros
    for prop in dir(FaarFieldAnalysis.CDF):
        pass # just to see if we can access it
    print("Clase CDF accesible. Funciones estáticas o miembros:")
    for item in dir(FaarFieldAnalysis.CDF):
        if not item.startswith("__"):
            print(f"   > {item}")
except Exception as e:
    print(f"Error inspeccionando CDF: {e}")
