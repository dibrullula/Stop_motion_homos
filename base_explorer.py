import networkx as nx
import numpy as np
import inspect

class MetricExplorer:
    def __init__(self, G, faces):
        self.G = G
        self.faces = self._build_face_map(faces)
        
        # ==========================================
        # MATRICE DELLE DISTANZE (Look-up O(1))
        # ==========================================
        self.dist_matrix = {}
        for u, v, data in self.G.edges(data=True):
            dist = data.get('weight', 1.0)
            self.dist_matrix[(u, v)] = dist
            self.dist_matrix[(v, u)] = dist # Bidirezionale
            
        for node in self.G.nodes():
            self.dist_matrix[(node, node)] = 0.0

        self._validate_manifold()

    def _validate_manifold(self):
        """Verifica hardware: ogni spigolo delle facce deve esistere."""
        for face in self.faces:
            n = len(face)
            for i in range(n):
                u = face[i]
                v = face[(i + 1) % n]
                if (u, v) not in self.dist_matrix:
                    raise ValueError(
                        f"🚨 ERRORE DI DESIGN DEL MANIFOLD: La faccia {face} "
                        f"richiede l'arco ({u}, {v}), ma non esiste nel grafo!"
                    )
    def _build_face_map(self, faces):
        """Genera una lookup table per sostituzioni omotopiche istantanee."""
        totalFaces = []
        for face in faces: 
            for i in range(len(face)):
                rotated = tuple(face[i:] + face[:i])
                totalFaces.append(rotated)
                totalFaces.append(rotated[::-1])
        return set(totalFaces)
    
    def get_neighbors(self, loop, verbose=False):
        """
        Genera vicini tramite mosse di omotopia (n-agoni) e spike.
        Stutter spaziali (nodi ripetuti) rimossi alla radice.
        """
        neighbors = set()
        loop_list = list(loop)
        n = len(loop_list)
        
        if n == 0: 
            return neighbors

        if verbose:
            print(f"🔍 Generating neighbors for loop: {loop}")

        # 1. OMOTORIA ATTRAVERSO LE FACCE (Lookup Table)
        # Sfruttiamo il set self.faces pre-calcolato nel costruttore
        max_face_len = max(len(f) for f in self.faces) if self.faces else 0
        for k in range(1, max_face_len):
            if n < k + 1: continue 
            
            for i in range(n):
                # Estraiamo segmento di k+1 nodi (k archi)
                segment = tuple(loop_list[(i + j) % n] for j in range(k + 1))
                
                # Cerchiamo un match nelle varianti delle facce
                for face in self.faces:
                    fn = len(face)
                    if k < fn and face[:k+1] == segment:
                        # Calcoliamo il percorso alternativo (il resto della faccia)
                        alt_path = [face[0]] + list(face[:k:-1])
                        
                        # Ricostruzione Loop (Deformazione Omotopica)
                        rotated_loop = loop_list[i:] + loop_list[:i]
                        new_loop = alt_path + rotated_loop[k+1:]
                        new_loop.insert(len(alt_path), rotated_loop[k])
                        
                        # Canonicalize trasforma in tupla e pulisce eventuali stutter residui
                        neighbors.add(self.canonicalize(new_loop))

        # 2. RIMOZIONE SPIKE (u, v, u -> u)
        # Lo stutter (u, u) non viene più generato, quindi gestiamo solo gli spike
        if n == 2:
            # Collasso di uno spike minimo verso il punto fermo
            neighbors.add(self.canonicalize((loop_list[0],)))
            neighbors.add(self.canonicalize((loop_list[1],)))
        elif n >= 3:
            for j in range(n):
                # Se il nodo j-1 e j+1 coincidono, il nodo j è uno spike
                if loop_list[j-1] == loop_list[(j+1) % n]:
                    new_l = [loop_list[idx] for idx in range(n) if idx != j]
                    neighbors.add(self.canonicalize(new_l))

        # 3. AGGIUNTA SPIKE (u -> u, v, u)
        for j in range(n):
            u = loop_list[j]
            for v in self.G.neighbors(u):
                if v == u: continue # Salta stutter espliciti
                
                if n == 1:
                    # Da un punto fermo a un'oscillazione (u, v, u)
                    neighbors.add(self.canonicalize((u, v, u)))
                else:
                    # Inserisce uno spike (v, u) dopo il nodo corrente
                    new_l = loop_list[:j+1] + [v, u] + loop_list[j+1:]
                    neighbors.add(self.canonicalize(new_l))
        if verbose:
            print(f"  -> Trovati {len(neighbors)} neighbors.")
            for i in neighbors: 
                print(f"     {i}")

        return neighbors

    def canonicalize(self, loop):
        """Standardizza il loop e rimuove stutter (nodi doppi consecutivi)."""
        if not loop: return ()
        
        # 1. RIMOZIONE STUTTER (es. [0, 1, 1, 2] -> [0, 1, 2])
        cleaned = []
        for node in loop:
            if not cleaned or node != cleaned[-1]:
                cleaned.append(node)
        
        # Controllo stutter ciclico (ultimo == primo)
        if len(cleaned) > 1 and cleaned[0] == cleaned[-1]:
            cleaned.pop()
            
        loop_tuple = tuple(cleaned)
        if len(loop_tuple) <= 1: return loop_tuple
        
        # 2. ROTAZIONE LESSICOGRAFICA MINIMA
        rotations = [loop_tuple[i:] + loop_tuple[:i] for i in range(len(loop_tuple))]
        return min(rotations)
    def get_length(self, loop):
        if len(loop) <= 1: return 0.0
        length = 0.0
        for i in range(len(loop)):
            u = loop[i]
            v = loop[(i + 1) % len(loop)]
            if u != v:
                if (u, v) not in self.dist_matrix:
                    return float('inf')
                length += self.dist_matrix[(u, v)]
        return length

    def get_cost(self, loop):
        return self.get_length(loop)

class LagrangianExplorer(MetricExplorer):
    def __init__(self, G, faces, L, T_total):
        super().__init__(G, faces) # Costruisce la dist_matrix e valida le facce
        self.L = L
        self.T_total = T_total
        
        sig = inspect.signature(self.L)
        self.is_time_dependent = len(sig.parameters) >= 3
        
        self.time_flags = [0.0, self.T_total]
        if self.is_time_dependent:
            self._build_time_partition()

    def _build_time_partition(self):
        print("🔍 [Explorer] Analisi pre-flight della Lagrangiana tempo-dipendente...")
        N_samples = 1000
        dt_sample = self.T_total / N_samples
        nodes = list(self.G.nodes())
        
        def get_V_grid(t):
            return np.array([-self.L(n, 0.0, t) for n in nodes])
            
        flags = [0.0]
        last_flag_t = 0.0
        last_V_grid = get_V_grid(0.0)
        
        for i in range(1, N_samples + 1):
            t = i * dt_sample
            current_V_grid = get_V_grid(t)
            max_abs_V = np.max(np.abs(last_V_grid))
            diff = np.max(np.abs(current_V_grid - last_V_grid))
            threshold = 0.05 * max_abs_V if max_abs_V > 1e-5 else 0.05
            
            if diff > threshold:
                flags.append(t)
                last_V_grid = current_V_grid
                last_flag_t = t
                
        if self.T_total not in flags:
            flags.append(self.T_total)
            
        self.time_flags = sorted(list(set(flags)))
        print(f"⏱️  [Explorer] Trovate {len(self.time_flags)-2} discontinuità. Bandierine temporali generate.")

    def get_action(self, spatial_loop, dt_array):
        n = len(spatial_loop)
        
        # --- CASO 1: NODO SINGOLO (Punto fermo assoluto) ---
        if n == 1:
            u = spatial_loop[0]
            if not self.is_time_dependent:
                return self.L(u, 0.0) * self.T_total
            else:
                action = 0.0
                for i in range(len(self.time_flags) - 1):
                    t_start = self.time_flags[i]
                    t_end = self.time_flags[i+1]
                    t_mid = (t_start + t_end) / 2.0
                    action += self.L(u, 0.0, t_mid) * (t_end - t_start)
                return action
                
        action = 0.0
        current_time = 0.0
        
        # --- CASO 2: LAGRANGIANA STATICA (Time-Independent) ---
        if not self.is_time_dependent:
            for i in range(n):
                u = spatial_loop[i]
                v = spatial_loop[(i + 1) % n]
                
                # FIX CRITICO: Se la corda respira/si ferma, la distanza è 0
                if u == v:
                    dist = 0.0
                else:
                    dist = self.dist_matrix.get((u, v), float('inf'))
                    
                # Protezione divisione per zero
                dt = max(dt_array[i], 1e-7)
                speed = dist / dt
                
                # S = L * dt
                action += self.L(u, speed) * dt
            return action

        # --- CASO 3: LAGRANGIANA TEMPO-DIPENDENTE (Es. Ciclone) ---
        for i in range(n):
            u = spatial_loop[i]
            v = spatial_loop[(i + 1) % n]
            segment_dt = max(dt_array[i], 1e-7)
            
            # FIX CRITICO: Gestione distanza 0 per stuttering
            if u == v:
                dist = 0.0
            else:
                if (u, v) not in self.dist_matrix:
                    raise ValueError(
                        f"🚨 ERRORE TOPOLOGICO: Salto illegale ({u}->{v})"
                    )
                dist = self.dist_matrix[(u, v)]
                
            speed = dist / segment_dt
            t_start = current_time
            t_end = current_time + segment_dt
            
            # Integrazione sulle partizioni temporali (Flags)
            relevant_flags = [f for f in self.time_flags if t_start < f < t_end]
            sub_intervals = [t_start] + relevant_flags + [t_end]
            
            for j in range(len(sub_intervals) - 1):
                sub_t_start = sub_intervals[j]
                sub_t_end = sub_intervals[j+1]
                sub_dt = sub_t_end - sub_t_start
                if sub_dt < 1e-9: continue
                    
                t_mid = (sub_t_start + sub_t_end) / 2.0
                L_u = self.L(u, speed, t_mid)
                L_v = self.L(v, speed, t_mid)
                L_avg = (L_u + L_v) / 2.0
                action += L_avg * sub_dt 
                
            current_time = t_end
            
        return action