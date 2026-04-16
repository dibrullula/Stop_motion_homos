import random
import numpy as np
import time

# Assicurati che i nomi dei file siano corretti per i tuoi import
from utils import GraphFactory
from skeleton_mapper import CoreRegistryBuilder
from skeleton_mapper import SkeletonMapper
from base_explorer import LagrangianExplorer
from gradient_flow import SpatiotemporalGradientFlow

# ==========================================
# 1. ORACOLO TOPOLOGICO (Background Checker)
# ==========================================
def get_homotopy_class(loop, n=3):
    """Classifica matematicamente la classe di omotopia [Wx, Wy]."""
    if not loop or len(loop) < 2:
        return [0, 0]
    closed_loop = list(loop) + [loop[0]]
    X_unwrapped, Y_unwrapped = 0, 0 
    for i in range(len(closed_loop) - 1):
        u, v = closed_loop[i], closed_loop[i+1]
        dx = (v % n - u % n + 1) % n - 1
        dy = (v // n - u // n + 1) % n - 1
        X_unwrapped += dx
        Y_unwrapped += dy
    return [X_unwrapped // n, - Y_unwrapped // n]

def run_background_topological_check(mapper, sample_size=15, n=3):
    """Verifica la consistenza tra i risultati del Mapper e l'Oracolo."""
    risultati = getattr(mapper, 'primary_results', {}) or getattr(mapper, 'support_registry', {})
    if not risultati: return
    
    sample = random.sample(list(risultati.keys()), min(sample_size, len(risultati)))
    errori = []
    for geo in sample:
        pred = risultati[geo]
        vera = get_homotopy_class(geo, n=n)
        # Check flessibile per nomi stringa o liste
        if not (str(vera) in pred or (vera == [0,0] and "Triviale" in pred)):
            errori.append((geo, pred, vera))

    if errori:
        print("\n🚨 [WARNING] DISCREPANZA TOPOLOGICA RILEVATA!")
        for geo, p, v in errori:
            print(f"  Loop: {str(geo)[:20]}... | Predetta: {p} | Vera: {v}")
    else:
        print("✅ [Checker] Consistenza Topologica Validata.")

# ==========================================
# 2. SETUP PIPELINE (Motore Unico)
# ==========================================
print("="*60)
print("⚙️ INIZIALIZZAZIONE MOTORE FISICO-TOPOLOGICO")
print("="*60)

# A. Manifold
manifold, faces = GraphFactory.create_torus_3x3()

# B. Fisica: Lagrangiana con Buca di Potenziale al centro (nodo 4)
def lagrangiana_fisica(node, speed):
    T = 0.5 * (speed ** 2)
    V = 10.0 if node == 4 else 0.0
    return T - V

# C. Stack Tecnologico: Un solo Explorer, un solo Flow Engine
explorer_phys = LagrangianExplorer(manifold, faces, lagrangiana_fisica, T_total=1.0)
flow_engine_phys = SpatiotemporalGradientFlow(explorer_phys)

# ==========================================
# 3. COSTRUZIONE CORE REGISTRY
# ==========================================
print("\n🛠️  Costruzione Core Registry (Geodetiche Fisiche Base)...")
def invert_loop(loop): 
    inverted = [loop[0], ] + loop[1:][::-1]
    return inverted
    
def generate_torus_loop(max_n = 2):
    hor_loop = [0, 1, 2]
    vert_loop = [0, 3, 6]
    loop_list = []
    class_name = []
    for i in range(max_n):
        for j in range(max_n):
           if i != 0 or j != 0: # Escludiamo il loop banale (0,0)
                loop_list.append(hor_loop*i + vert_loop * j)
                class_name.append(f"Classe_[{i}, {j}]")
                loop_list.append(invert_loop(hor_loop)*i + vert_loop * j) # Loop inverso
                class_name.append(f"Classe_[{-i}, {-j}]")
                loop_list.append(hor_loop*i + invert_loop(vert_loop) * j) # Loop misto
                class_name.append(f"Classe_[{i}, {-j}]")
                loop_list.append(invert_loop(hor_loop)*i + invert_loop(vert_loop) * j) # Loop misto inverso
                class_name.append(f"Classe_[{-i}, {j}]")
    return loop_list, class_name

builder = CoreRegistryBuilder(manifold, faces, explorer_phys, flow_engine_phys)
rappresentanti, nomi_classi = generate_torus_loop(2)
_, _, core_registry = builder.build_core_list(rappresentanti, labels=nomi_classi)

# --- INIZIO NUOVE RIGHE DA AGGIUNGERE ---
print("\n" + "-"*60)
print(f"📚 CONTENUTO DEL CORE REGISTRY (Totale: {len(core_registry)} geodetiche)")
print("-"*60)
# Raggruppiamo per nome classe per una lettura più pulita
registry_sorted = sorted(core_registry.items(), key=lambda x: x[1])
for opt_loop, cls_name in registry_sorted:
    # Calcoliamo l'azione al volo per vedere quanto "costa" questa geodetica base
    azione_minima = explorer_phys.get_cost(opt_loop)
    print(f"  ► {cls_name:<15} | Azione: {azione_minima:>7.2f} | Loop: {opt_loop}")
print("-"*60 + "\n")
# --- FINE NUOVE RIGHE ---

# ==========================================
# 4. MAPPATURA DELLO SPAZIO (Skeleton Mapper)
# ==========================================
# Il Mapper ora è rigido: usa lo stack fisico per tutto
mapper = SkeletonMapper(explorer_phys, flow_engine_phys, core_registry)

start_time = time.time()
mapper.map_space(max_k_hops=4, cost_barrier=20.0)
duration = time.time() - start_time

run_background_topological_check(mapper, n=3)

# ==========================================
# 5. ANALISI RISULTATI (Audit Fisico)
# ==========================================
print("\n" + "="*60)
print(f"📊 REPORT FINALE (Esecuzione: {duration:.2f}s)")
print("="*60)

targets = ["Classe_[1, 0]", "Classe_[0, 1]", "Classe_[1, 1]"]
for t_name in targets:
    print(f"\n🟢 Target: {t_name}")
    
    # Cerchiamo se il mapper ha trovato una geodetica per questa classe
    found_loop = None
    results = getattr(mapper, 'primary_results', {})
    for loop, cls in results.items():
        if cls == t_name:
            found_loop = loop
            break
            
    if found_loop:
        dt_init = [explorer_phys.T_total / len(found_loop)] * len(found_loop)
        # Ottimizziamo i tempi per l'output finale
        opt_loop, opt_dt = flow_engine_phys.flow_to_optimum(found_loop)
        azione = explorer_phys.get_action(opt_loop, opt_dt)
        
        print(f"  ► Geodetica: {opt_loop}")
        print(f"  ► Tempi (dt): {[round(d, 3) for d in opt_dt]}")
        print(f"  ► Azione Finale: {azione:.4f}")
    else:
        print(f"  ⚠️ Classe non campionata durante la mappatura batch.")

print("\n" + "="*60)
print("🏁 PIPELINE COMPLETATA")
print("="*60 + "\n")