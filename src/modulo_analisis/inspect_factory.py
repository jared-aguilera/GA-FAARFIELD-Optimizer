import sys, os, clr

base_dir = r"c:\Users\PC\Documents\Documentos de Universidad\Trabajos\4to Semestre\faarfield\GA-FAARFIELD-Optimizer"
bin_dir = os.path.join(base_dir, "bin")

clr.AddReference(os.path.join(bin_dir, "FaarFieldModel.dll"))

from FaarFieldModel import Weight, Metric
try:
    w = Weight(100.0, Metric())
    print(f"Weight created: {w}")
except Exception as e:
    print(f"Failed: {e}")
