import numpy as np

class GradientFlow:
    def __init__(self, explorer):
        """
        Inizializza il calcolatore del flusso del gradiente usando 
        l'interfaccia astratta (MetricExplorer o LagrangianExplorer).
        """
        self.explorer = explorer

    def flow_to_optimum(self, start_loop, verbose=False):
        """
        Esegue la discesa del gradiente dal loop di partenza fino a un minimo locale.
        
        Ritorna:
            - optimum_loop: La tupla del loop che rappresenta il minimo del costo.
            - path: La lista dei loop attraversati durante la discesa.
        """
        current_loop = self.explorer.canonicalize(start_loop)
        current_cost = self.explorer.get_cost(current_loop)
        
        path = [current_loop] 
        
        if verbose:
            print(f"🌊 Inizio Gradient Flow da: {current_loop} (Costo={current_cost:.2f})")
            
        step = 0
        
        while True:
            neighbors = self.explorer.get_neighbors(current_loop)
            
            best_neighbor = None
            best_cost = current_cost
            
            for nxt in neighbors:
                nxt_cost = self.explorer.get_cost(nxt)
                
                if nxt_cost < best_cost - 1e-6:
                    best_cost = nxt_cost
                    best_neighbor = nxt
            
            if best_neighbor is not None:
                current_loop = best_neighbor
                current_cost = best_cost
                path.append(current_loop)
                step += 1
                
                if verbose:
                    print(f"  Step {step}: sceso a {current_loop} (Costo={current_cost:.2f})")
            else:
                if verbose:
                    print(f"🎯 Minimo locale raggiunto in {step} step!")
                    print(f"   Traiettoria ottimale: {current_loop} (Costo={current_cost:.2f})\n")
                break
                
        return current_loop, path

class SpatiotemporalGradientFlow:
    def __init__(self, explorer):
        self.explorer = explorer

    def _adapt_dt(self, current_dt, nxt_len):
        """
        LA SPALMATURA (Resampling lineare).
        Stira o comprime l'array dei tempi per adattarlo alla nuova lunghezza.
        """
        curr_len = len(current_dt)
        if curr_len == nxt_len:
            return list(current_dt)
        if nxt_len <= 1:
            return [sum(current_dt)] if nxt_len == 1 else []
            
        old_indices = np.linspace(0, 1, curr_len)
        new_indices = np.linspace(0, 1, nxt_len)
        
        # Interpola i vecchi tempi sui nuovi indici
        new_dt = np.interp(new_indices, old_indices, current_dt)
        
        # Normalizza a T_total
        t_total = sum(current_dt)
        new_dt *= (t_total / np.sum(new_dt))
        return list(new_dt)

    def flow_to_optimum(self, start_loop, verbose=False):
        current_loop = self.explorer.canonicalize(start_loop)
        n_steps = len(current_loop)
        
        # 1. INIZIALIZZAZIONE: Ottimizziamo per bene il punto di partenza
        current_dt = [self.explorer.T_total / n_steps] * n_steps if n_steps > 0 else []
        current_dt = self.explorer.optimize_timing(current_loop, current_dt, steps=25)
        current_action = self.explorer.get_action(current_loop, current_dt)
        
        history = set()
        if verbose:
            print(f"\n🌊 Start Flow: {current_loop} | Azione = {current_action:.2f}")

        while True:
            # Protezione anti-loop infinito
            if current_loop in history: break
            if len(history) > 50: break
            history.add(current_loop)
            catcher = False
            neighbors = list(self.explorer.get_neighbors(current_loop))
            for neighbor in neighbors: 
                new_dt = self._adapt_dt(current_dt, len(neighbor))
                new_action = self.explorer.get_action(neighbor, new_dt)
                if new_action < current_action - 1e-6:
                    current_loop = neighbor
                    current_dt = self.explorer.optimize_timing(neighbor, new_dt, steps=15)
                    current_action = new_action
                    catcher = True
                    if verbose:
                        print(f"  ► Sceso a {current_loop} | Azione = {current_action:.2f}")
                    break
            if not catcher:
                if verbose:
                    print(f"🎯 Ottimo locale raggiunto: {current_loop} | Azione = {current_action:.2f}\n")
                break
        return current_loop, current_dt
