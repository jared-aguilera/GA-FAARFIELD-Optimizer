# Consolidación del Algoritmo Final usando LEAF y Fórmulas Originales

Tras descubrir y analizar el archivo madre `modCDF.vb` de FAARFIELD, se confirmaron matemáticamente las fórmulas reales de fatiga que la FAA utiliza para el asfalto y la subrasante. Este plan propone reconstruir tu función usando directamente la DLL base física.

## Background Clave del Código Extraído
Del código recién enviado descubrí dos cosas maravillosas:
1. **La fórmula de Subrasante (Suelo)**: Originalmente tenías en Python `(0.004 / eps_v) ** 6`. ¡La fórmula real oficial "Straight Line" que programa la FAA usando esa semilla no usa el exponente 6, sino **8.1**! (`NtoFail = (0.004 / StrainMax) ^ 8.1`). Además la FAA tiene subcondiciones dependiendo de qué tan grande sea el esfuerzo (Bleasdale / Orig).
2. **La fórmula de Asfalto (HMA)**: Ustedes calculaban el asfalto aproximando el daño del suelo (`cdf_hma = cdf_subgrade * 0.90`). La FAA realmente usa el "RDEC Model" que hace algo mucho más complejo: `PV = 44.422 * (StrainMax ^ 5.14) * Constantes_de_la_mezcla`, y luego `NtoFail = 0.4801 * (PV ^ -0.90074)`. 

## Cambios Propuestos
### src/funcion_faarfield

#### [MODIFY] `calcular_respuesta_flota.py`
Se eliminará el llamado a `conector_dll.py` y restauraremos el enlace a `MotorFAARFIELD` pero inyectando ahora la "Traducción Oficial" que obtuve del código VB de la FAA:
- Para cada aeronave, llamará al motor matricial (LEAF) dos veces o leerá ambos vectores: Esfuerzo Horizontal en el fondo del asfalto, y Esfuerzo Vertical sobre la subrasante.
- Calcularemos `HMA CDF` usando la rutina RDEC original transcrita a Python (asumiendo mezclas estándar de flexión a 600,000 PSI).
- Calcularemos `Subgrade CDF` usando el modelo Bleasdale / StraightLine a la potencia `8.1` y la semilla base.
- Con las sumativas verdaderas, computaremos el `Life` (Total / CDF).

#### [DELETE] `conector_dll.py`
Podemos borrarlo de nuestra mente, ya que intentaba comunicarse con las ventanas truncas de FAARFIELD.
