import math

# Función teórica normal-CDF vía Erf
def norm_cdf(x):
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

def gauss_area(a, b, sigma):
    if sigma <= 0.0:
        if a <= 0.0 and b >= 0.0:
            return 1.0
        return 0.0
    return norm_cdf(b / sigma) - norm_cdf(a / sigma)

def calculate_pc_ratio_flexible(ac_data, depth, gear_num=1, offset=0.0):
    """
    Python clone of CoverageToPassFlexGeneral13B
    Returns Pass/Coverage Ratio
    """
    sigma_w = 30.435  # Wander width standard (inches)
    
    peso_lb = ac_data['peso']
    presion = ac_data['presion'] 
    
    n_tires = ac_data['llantas']
    tire_load = (peso_lb / 2.0) / n_tires
    area = tire_load / presion
    
    # Ancho de huella según el estándar. Area = pi * L * W / 4, con L=1.4W. W = sqrt(Area/1.099)
    # Empíricamente en FAA a veces se usa 0.8712.
    tire_width = math.sqrt(area / 0.8712) * 0.6 
    if tire_width < 5.0: tire_width = 16.0  
    
    coords = ac_data['coords']
    tx_raw = [coords[i*2] for i in range(n_tires)]
    ty = [coords[i*2+1] for i in range(n_tires)]
    
    # Calcular el centro lateral real del engranaje (xCenter en VB)
    x_center = sum(tx_raw) / len(tx_raw)
    tx = [(x - x_center) for x in tx_raw]
        
    # Agrupación de llantas en columnas (X)
    columns = []
    for x, y in zip(tx, ty):
        placed = False
        for col in columns:
            if abs(x - col['x']) <= tire_width / 2.0:
                col['tires'].append((x, y))
                placed = True
                break
        if not placed:
            columns.append({'x': x, 'tires': [(x, y)]})
            
    # Determinar si aplicamos Tandem Fnew (True = se ignora multiplicador tandem para Flexible)
    tandem_fnew = True # As in FAARFIELD 1.4+
    
    # Calcular CtoP para múltiples offsets y tomar el máximo
    max_ctop1 = 0.0
    gp = abs(depth) + tire_width
    columns.sort(key=lambda col: col['x'])
    
    for off_step in range(0, 42): # 0 to 410 inches
        offset = off_step * 10.0
        
        ctop1 = 0.0
        for i, col in enumerate(columns):
            # 1. Calcular multiplicador Tandem (Overlap de Bulbos de Esfuerzo)
            multiplier = 1.0
            if not tandem_fnew:
                for j in range(1, len(col['tires'])):
                    td = col['tires'][j][1] - col['tires'][j-1][1]
                    gap = td - tire_width
                    if gap <= 0: gap = 0.01 
                    if depth > 2 * gap:
                        pass 
                    elif depth > gap:
                        if j == 1: multiplier = 3.0 - (depth / gap)
                        else: multiplier += 2.0 - (depth / gap)
                    else:
                        multiplier += 1.0
        
        # 2. Calcular fronteras izquierda y derecha (para GaussArea)
        # Asumiendo expansión 'gp'
        cx = col['x']
        left = cx - gp/2.0
        right = cx + gp/2.0
        
        if i > 0:
            mid = (columns[i-1]['x'] + cx) / 2.0
            if mid > left: left = mid
        if i < len(columns) - 1:
            mid = (columns[i+1]['x'] + cx) / 2.0
            if mid < right: right = mid
            
            # Eval area overlaps with offset
            la_off = left - offset
            ra_off = right - offset
            
            area_overlap = gauss_area(la_off, ra_off, sigma_w)
            ctop1 += area_overlap * multiplier
            
        if ctop1 > max_ctop1:
            max_ctop1 = ctop1
            
    c_to_p = max_ctop1 if max_ctop1 > 0 else 1.0
    return 1.0 / c_to_p if c_to_p > 0 else 1.0
