"""
=============================================================
  Inspector de DLL .NET con pythonnet
  DLL: LEAFClassLib.dll (FAARFIELD)
=============================================================
"""

import os
import clr
import System
import System.Reflection

# ─────────────────────────────────────────────
# CONFIGURACIÓN — ajusta esta ruta
# ─────────────────────────────────────────────
DIR_BIN = r"C:\Users\x\Documents\GitHub\GA-FAARFIELD-Optimizer\bin"   # <── cambia esto
DLL_NAME = "LEAFClassLib.dll"
DLL_PATH = os.path.abspath(os.path.join(DIR_BIN, DLL_NAME))

# ─────────────────────────────────────────────
# 1. CARGAR EL ASSEMBLY
# ─────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  Cargando: {DLL_PATH}")
print(f"{'='*60}\n")

clr.AddReference(DLL_PATH)
assembly = System.Reflection.Assembly.LoadFile(DLL_PATH)

print(f"✅ Assembly cargado: {assembly.FullName}\n")

# ─────────────────────────────────────────────
# 2. LISTAR TODOS LOS TIPOS (CLASES) DE LA DLL
# ─────────────────────────────────────────────
print(f"{'='*60}")
print(f"  TIPOS ENCONTRADOS EN LA DLL")
print(f"{'='*60}")

tipos = assembly.GetTypes()
nombres_tipos = [t.FullName for t in tipos]

for nombre in nombres_tipos:
    print(f"  📦 {nombre}")

print(f"\nTotal de tipos: {len(nombres_tipos)}\n")

# ─────────────────────────────────────────────
# 3. INSPECCIÓN DETALLADA DE CADA TIPO
# ─────────────────────────────────────────────
# Flags para incluir miembros públicos e instancia
flags = (System.Reflection.BindingFlags.Public |
         System.Reflection.BindingFlags.Instance |
         System.Reflection.BindingFlags.Static)

for tipo in tipos:
    print(f"\n{'='*60}")
    print(f"  CLASE: {tipo.FullName}")
    print(f"{'='*60}")

    # ── Constructores ──────────────────────────
    constructores = tipo.GetConstructors()
    if constructores:
        print(f"\n  🏗️  CONSTRUCTORES ({len(constructores)}):")
        for c in constructores:
            params = c.GetParameters()
            param_str = ", ".join(
                [f"{p.ParameterType.Name} {p.Name}" for p in params]
            ) if params else "void"
            print(f"      {tipo.Name}({param_str})")

    # ── Propiedades ────────────────────────────
    propiedades = tipo.GetProperties(flags)
    if propiedades:
        print(f"\n  📋 PROPIEDADES ({len(propiedades)}):")
        for p in propiedades:
            acceso = []
            if p.CanRead:
                acceso.append("get")
            if p.CanWrite:
                acceso.append("set")
            print(f"      {p.PropertyType.Name:<20} {p.Name:<30} [{', '.join(acceso)}]")

    # ── Métodos ────────────────────────────────
    metodos = tipo.GetMethods(flags)
    # Filtrar métodos heredados de System.Object para reducir ruido
    metodos_filtrados = [
        m for m in metodos
        if m.DeclaringType.FullName != "System.Object"
        and not m.Name.startswith("get_")
        and not m.Name.startswith("set_")
    ]
    if metodos_filtrados:
        print(f"\n  🔧 MÉTODOS ({len(metodos_filtrados)}):")
        for m in metodos_filtrados:
            params = m.GetParameters()
            param_str = ", ".join(
                [f"{p.ParameterType.Name} {p.Name}" for p in params]
            ) if params else ""
            estatico = " [static]" if m.IsStatic else ""
            print(f"      {m.ReturnType.Name:<20} {m.Name}({param_str}){estatico}")

    # ── Campos (Fields / datos) ────────────────
    campos = tipo.GetFields(flags)
    if campos:
        print(f"\n  📌 CAMPOS / DATOS ({len(campos)}):")
        for c in campos:
            estatico = " [static]" if c.IsStatic else ""
            print(f"      {c.FieldType.Name:<20} {c.Name}{estatico}")

    # ── Eventos ────────────────────────────────
    eventos = tipo.GetEvents(flags)
    if eventos:
        print(f"\n  🔔 EVENTOS ({len(eventos)}):")
        for e in eventos:
            print(f"      {e.EventHandlerType.Name:<20} {e.Name}")

# ─────────────────────────────────────────────
# 4. PRUEBA DE INSTANCIACIÓN DE clsLEAF
# ─────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  PRUEBA DE INSTANCIACIÓN: clsLEAF")
print(f"{'='*60}\n")

try:
    from LEAFClassLib import clsLEAF
    print(f"  Tipo importado: {type(clsLEAF)}")

    obj = clsLEAF()
    print(f"  ✅ Instancia creada: {obj}")
    print(f"\n  dir(instancia):")
    miembros = [m for m in dir(obj) if not m.startswith("__")]
    for m in miembros:
        print(f"      {m}")

except Exception as e:
    print(f"  ⚠️  No se pudo instanciar clsLEAF: {e}")
    print(f"      Puede requerir parámetros en el constructor.")

print(f"\n{'='*60}")
print(f"  Inspección finalizada")
print(f"{'='*60}\n")