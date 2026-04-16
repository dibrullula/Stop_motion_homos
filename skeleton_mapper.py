import heapq
import time
import itertools

class SkeletonMapper:
    def __init__(self, explorer, flow_engine, core_registry):
        """
        Mapper Omotopico a Motore Singolo (Fisico).
        Usa l'explorer per la metrica/struttura e il flow_engine per il collasso dell'Azione.
        """
        self.explorer = explorer
        self.flow_engine = flow_engine
        self.core_registry = core_registry
        self.support_registry = {} 
        self.path_memory = {}

    # ==========================================
    # METODO 1: BATCH PROCESSING 
    # ==========================================
    def map_space(self, max_k_hops, cost_barrier=5.0, timeout_seconds=15.0):
        print(f"\n🗺️ [BATCH] INIZIO MAPPATURA (Max salti: {max_k_hops}, Barriera Costo: +{cost_barrier})", flush=True)
        
        unknown_optima = self._discover_unknown_optima(max_k_hops)
        total = len(unknown_optima)
        self.primary_results = {}
        
        print(f"   Trovate {total} traiettorie ottimali. Ricerca ponti in corso...\n", flush=True)

        success_count = 0
        for idx, opt_loop in enumerate(unknown_optima):
            percent = (idx + 1) / total
            bar_length = 40
            filled = int(bar_length * percent)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            print(f"\r   ⏳ [{bar}] {percent:.1%} ({idx+1}/{total})", end=" " * 10, flush=True)
            
            result = self._bridge_to_known(opt_loop, cost_barrier, timeout_seconds)
            if result:
                target_class, _ = result
                success_count += 1
                self.primary_results[opt_loop] = target_class 

        full_bar = '█' * 40
        print(f"\r   ✅ [{full_bar}] 100.0% ({total}/{total})" + " " * 15, flush=True)
        print(f"\n🏁 MAPPATURA COMPLETATA. {success_count}/{total} classificate.\n")

    def _discover_unknown_optima(self, max_k):
        candidates = set()
        manifold = self.explorer.G
        
        def dfs(current_path):
            if len(current_path) > max_k + 1: return
            if len(current_path) > 1 and current_path[0] == current_path[-1]:
                candidates.add(self.explorer.canonicalize(tuple(current_path[:-1])))
            
            last_node = current_path[-1]
            for neighbor in manifold.neighbors(last_node):
                if len(current_path) >= 2 and neighbor == current_path[-2]: continue
                dfs(current_path + [neighbor])

        for n in manifold.nodes():
            dfs([n])
            
        unknown_optima = set()
        print(f"   Collasso Fisico di {len(candidates)} loop grezzi...", flush=True)
        
        for loop in candidates:
            # 1. Collassiamo il loop grezzo nel minimo di Azione (S = T - V)
            result = self.flow_engine.flow_to_optimum(loop, verbose=False)
            if result[0] is None: continue 
                
            opt_loop = self.explorer.canonicalize(result[0])
            if opt_loop not in self.core_registry and opt_loop not in unknown_optima:
                unknown_optima.add(opt_loop)
                
        # Ordiniamo i loop ottimali per costo strutturale per facilitare il bridging
        return sorted(list(unknown_optima), key=lambda x: self.explorer.get_cost(x))

    # ==========================================
    # METODO 2: STREAMING DINAMICO
    # ==========================================
    def map_space_dynamic(self, max_k_hops, cost_barrier=5.0, timeout_seconds=15.0):
        print(f"\n🌊 [DYNAMIC] INIZIO MAPPATURA STREAMING (Max salti: {max_k_hops}, Barriera Costo: +{cost_barrier})", flush=True)
        
        manifold = self.explorer.G
        failed_optima = set()
        seen_raw_loops = set()
        stats = {"generati": 0, "traiettorie_uniche": 0, "successi": 0}

        def process_loop_on_the_fly(current_path):
            loop = self.explorer.canonicalize(tuple(current_path[:-1]))
            
            if loop in seen_raw_loops: return
            seen_raw_loops.add(loop)
            stats["generati"] += 1
            
            result = self.flow_engine.flow_to_optimum(loop, verbose=False)
            if result[0] is None: return 
                
            opt_loop = self.explorer.canonicalize(result[0])

            if opt_loop in self.core_registry or opt_loop in self.support_registry or opt_loop in failed_optima:
                return 

            stats["traiettorie_uniche"] += 1
            
            bridge_result = self._bridge_to_known(opt_loop, cost_barrier, timeout_seconds)
            
            if bridge_result:
                target_class, path = bridge_result
                stats["successi"] += 1
            else:
                failed_optima.add(opt_loop) 

        tie_breaker = itertools.count()
        pq = []
        for n in manifold.nodes():
            heapq.heappush(pq, (0.0, next(tie_breaker), n, [n]))

        while pq:
            current_cost, _, current_node, path = heapq.heappop(pq)
            
            if len(path) > 1 and path[0] == current_node:
                process_loop_on_the_fly(path)
                
            if len(path) > max_k_hops: continue

            for neighbor in manifold.neighbors(current_node):
                if len(path) >= 2 and neighbor == path[-2]: continue
                edge_cost = self.explorer.dist_matrix.get((current_node, neighbor), 1.0)
                heapq.heappush(pq, (current_cost + edge_cost, next(tie_breaker), neighbor, path + [neighbor]))

        print(f"🏁 MAPPATURA COMPLETATA. {stats['successi']}/{stats['traiettorie_uniche']} classificate su {stats['generati']} loop grezzi.")

    # ==========================================
    # LOGICA DI RICERCA PONTI (A* Heuristic)
    # ==========================================
    def _bridge_to_known(self, start_loop, cost_barrier, timeout_seconds):
        start_cost = self.explorer.get_cost(start_loop)
        max_allowed_cost = start_cost + cost_barrier
        
        tie_breaker = itertools.count()
        pq = [(start_cost, 0, next(tie_breaker), start_loop, [start_loop])]
        visited = {start_loop}
        
        start_time = time.time()
        expansions = 0
        max_expansions = 5000 

        while pq:
            expansions += 1
            if expansions > max_expansions or time.time() - start_time > timeout_seconds:
                return None

            curr_cost, steps, _, current, path = heapq.heappop(pq)

            if current in self.core_registry:
                target_class = self.core_registry[current]
                self._update_all_path_nodes(path, target_class)
                return target_class, path
                
            if current in self.support_registry:
                target_class = self.support_registry[current]
                self._update_all_path_nodes(path, target_class)
                return target_class, path

            for neighbor in self.explorer.get_neighbors(current):
                if neighbor in visited: continue
                
                neighbor_cost = self.explorer.get_cost(neighbor)
                if neighbor_cost > max_allowed_cost: continue
                
                visited.add(neighbor)
                heapq.heappush(pq, (neighbor_cost, steps + 1, next(tie_breaker), neighbor, path + [neighbor]))
        
        return None

    def _update_all_path_nodes(self, path, target_class):
        for i, loop in enumerate(path):
            if loop not in self.core_registry and loop not in self.support_registry:
                self.support_registry[loop] = target_class
                self.path_memory[loop] = path[i:]
        return None