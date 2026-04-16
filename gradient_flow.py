
import numpy as np

class GradientFlow:
    def __init__(self, explorer):
        """
        Inizializza il calcolatore del flusso del gradiente usando 
        l'interfaccia astratta (MetricExplorer o LagrangianExplorer).
        """
        self.explorer = explorer

    def flow_to_optimum(self, start_loop, verbose=True):
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
import numpy as np

class SpatiotemporalGradientFlow:
    def __init__(self, explorer):
        self.explorer = explorer

    def optimize_timing(self, spatial_loop, dt_array, steps=20):
        """
        GRADIENTE PURO (Old School).
        Niente bisezioni o fisiche instabili. Solo discesa matematica.
        """
        n = len(dt_array)
        if n <= 1: return list(dt_array)
        
        curr_dt = np.array(dt_array)
        t_total = self.explorer.T_total
        lr = 0.02 # Passo cauto ma deciso
        current_action = self.explorer.get_action(spatial_loop, curr_dt)
        current_action0 = current_action
        for _ in range(steps):
            eps = 1e-4
            grad = np.zeros(n)
            
            for i in range(n):
                dt_tmp = curr_dt.copy()
                dt_tmp[i] += eps
                dt_tmp *= (t_total / np.sum(dt_tmp))
                newAction = self.explorer.get_action(spatial_loop, dt_tmp)
                grad[i] = (newAction - current_action) / eps
            
            grad -= np.mean(grad)
            # Discesa moltiplicativa per stabilità (evita tempi negativi)
            if(newAction < current_action):
                curr_dt -= lr * grad * curr_dt 
                curr_dt = np.maximum(curr_dt, 1e-5) # Limite inferiore di sicurezza
                curr_dt *= (t_total / np.sum(curr_dt))
                current_action = self.explorer.get_action(spatial_loop, curr_dt)
            
            
        if current_action > current_action0:
            # Se il gradiente ha peggiorato la situazione, torniamo indietro al punto di partenza
            return list(dt_array)
            print(f"⚠️  ATTENZIONE: Il gradiente ha peggiorato l'azione! ({current_action:.4f} > {current_action0:.4f})")   
        
        return list(curr_dt)

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
        current_dt = self.optimize_timing(current_loop, current_dt, steps=25)
        current_action = self.explorer.get_action(current_loop, current_dt)
        
        history = set()
        new_dt = 0
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
                    current_dt = self.optimize_timing(neighbor, new_dt, steps=3)
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