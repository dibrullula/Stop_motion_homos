# Stop Motion Homos 🎬

A physics-topology engine for discovering and classifying geodesics on manifolds using Lagrangian mechanics and homotopy theory.

## Overview

This project combines **differential geometry**, **Lagrangian mechanics**, and **computational topology** to explore loops on manifolds. It finds optimal trajectories by minimizing the action functional and classifies loops by their homotopy equivalence classes.

### Key Features

- 🌀 **Manifold Explorer**: Navigate loops on topological spaces with automatic stutter removal and canonical normalization
- ⚡ **Lagrangian Physics Engine**: Compute actions using kinetic and potential energy with support for time-dependent potentials
- 🎯 **Gradient Flow Optimization**: Discover local minima in the action landscape through spatiotemporal descent
- 🗺️ **Homotopy Mapper**: Automatically classify loops by their topological equivalence classes
- ✅ **Topological Validation**: Background oracle verifies consistency between computed and theoretical results

## Installation

### Requirements
- Python 3.8+
- NumPy
- NetworkX

### Setup

```bash
git clone https://github.com/yourusername/Stop-motion-homos.git
cd Stop-motion-homos
pip install -r requirements.txt
```

Or install dependencies manually:

```bash
pip install numpy networkx
```

## Quick Start

```bash
python main.py
```

This runs a complete pipeline on a 3×3 torus manifold:
1. Builds a core registry of 9 constant loops (points) and 8 representative geodesics
2. Discovers non-trivial loops up to 4 hops away
3. Classifies them by homotopy class using A* search with cost barriers
4. Reports optimal trajectories and their actions

### Example Output

```
🟢 Target: Classe_[1, 0]
  ► Geodetica: (3, 4, 5)
  ► Tempi (dt): [0.209, 0.583, 0.209]
  ► Azione Finale: -0.1762
```

## Project Structure

```
Stop-motion-homos/
├── main.py                  # Pipeline orchestration & homotopy classification
├── base_explorer.py         # Manifold navigation & Lagrangian mechanics
├── gradient_flow.py         # Action minimization via gradient descent
├── skeleton_mapper.py       # Homotopy class discovery & bridging
├── utils.py                 # Graph factory (torus construction)
└── README.md               # This file
```

## Core Components

### 1. **MetricExplorer** (`base_explorer.py`)
Provides the foundation for navigating manifolds:
- Builds distance matrices from graph edges
- Generates topologically-valid neighbors via homotopy moves and spike operations
- Canonicalizes loops (removes stutters, normalizes orientation)
- Validates manifold consistency

```python
explorer = MetricExplorer(graph, faces)
neighbors = explorer.get_neighbors(loop)
canonical = explorer.canonicalize(loop)
```

### 2. **LagrangianExplorer** (`base_explorer.py`)
Adds physics by computing actions from Lagrangian densities:
- Supports time-independent and time-dependent Lagrangians
- Optimizes timing (dt array) to minimize action
- Automatically detects potential discontinuities
- Uses gradient descent with adaptive learning rates

```python
def lagrangian(node, speed, time=None):
    T = 0.5 * speed**2
    V = 10.0 if node == 4 else 0.0  # Potential well at center
    return T - V

explorer = LagrangianExplorer(graph, faces, lagrangian, T_total=1.0)
action = explorer.get_action(spatial_loop, dt_array)
opt_dt = explorer.optimize_timing(spatial_loop)
```

### 3. **SpatiotemporalGradientFlow** (`gradient_flow.py`)
Optimizes both spatial and temporal aspects of trajectories:
- Descends in the action landscape via neighboring loops
- Adapts timing arrays when topology changes
- Terminates at local minima with anti-loop protection

```python
flow_engine = SpatiotemporalGradientFlow(explorer)
optimum_loop, path = flow_engine.flow_to_optimum(start_loop, verbose=True)
```

### 4. **CoreRegistryBuilder** (`skeleton_mapper.py`)
Constructs the foundational set of geodesics:
- Adds all constant loops (topologically trivial)
- Flows representative loops to local minima
- Assigns homotopy class labels

```python
builder = CoreRegistryBuilder(manifold, faces, explorer, flow_engine)
_, _, core_registry = builder.build_core_list(representatives, labels=class_names)
```

### 5. **SkeletonMapper** (`skeleton_mapper.py`)
Discovers and classifies the full space of loops:
- **Batch mode**: Discovers loops via DFS, collapses to optima, bridges to known classes
- **Dynamic mode**: Streaming priority-queue based exploration
- Uses A* heuristic with cost barriers to prune search space

```python
mapper = SkeletonMapper(explorer, flow_engine, core_registry)
mapper.map_space(max_k_hops=4, cost_barrier=20.0)
for loop, homotopy_class in mapper.primary_results.items():
    print(f"{loop} → {homotopy_class}")
```

## Physics Model

The engine minimizes the **action functional**:

$$S[\gamma, t(s)] = \int_0^{T} L(\gamma(s(t)), \dot{\gamma}(s(t)), t) \, dt$$

where:
- $\gamma$ is a spatial loop on the manifold
- $L$ is the Lagrangian density (kinetic minus potential energy)
- $t(s)$ is the time reparameterization

For a discrete loop with $n$ steps:

$$S = \sum_{i=0}^{n-1} L(x_i, v_i) \Delta t_i$$

where $v_i = \text{dist}(x_i, x_{i+1}) / \Delta t_i$

## Homotopy Classes

Loops are classified by how they wind around the torus:

| Class | Description | Winding |
|-------|-------------|---------|
| $[0,0]$ (Triviale) | Contractible loops | 0 wraps both directions |
| $[1,0]$ | Winds once horizontally | 1 horizontal, 0 vertical |
| $[0,1]$ | Winds once vertically | 0 horizontal, 1 vertical |
| $[1,1]$ | Winds both directions | 1 horizontal, 1 vertical |

## Example: Custom Manifold & Lagrangian

```python
from base_explorer import LagrangianExplorer
from gradient_flow import SpatiotemporalGradientFlow
import networkx as nx

# Create a square lattice
G = nx.grid_2d_graph(4, 4)
faces = [...]  # Define 2D faces

# Define a time-varying potential (e.g., rotating vortex)
def rotating_potential(node, speed, time):
    x, y = node
    theta = 2 * np.pi * time  # Rotates over one period
    dist_sq = (x - 2)**2 + (y - 2)**2
    return -5.0 * np.exp(-dist_sq) * np.cos(theta)

L = lambda n, v, t: 0.5*v**2 - rotating_potential(n, v, t)

explorer = LagrangianExplorer(G, faces, L, T_total=2.0)
flow = SpatiotemporalGradientFlow(explorer)

# Find optimal trajectory
loop = [(0, 0), (0, 1), (1, 1), (1, 0)]
optimum, path = flow.flow_to_optimum(loop, verbose=True)
```

## Algorithm Overview

### 1. Core Registry Construction
```
For each representative loop:
  1. Flow spatiotemporally to local action minimum
  2. Canonicalize and store in registry
  3. Label with homotopy class
```

### 2. Discovery Phase
```
Generate all loops up to max_k_hops:
  1. DFS traversal of graph
  2. Canonicalize each closed loop
  3. Flow to optimum (eliminates duplicates)
```

### 3. Classification Phase (A* Search)
```
For each unknown optimum:
  1. Initialize priority queue with starting loop
  2. Expand neighbors using homotopy moves
  3. Prune if cost exceeds barrier
  4. Return when reaching known class
  5. Cache intermediate results
```

### 4. Validation
```
Background oracle:
  1. Randomly sample discovered loops
  2. Compute theoretical homotopy class
  3. Verify against mapper's classification
  4. Report any discrepancies
```

## Performance Notes

- **Memory**: O(L) where L is number of discovered loops (typically <1000)
- **Time**: O(L × N) where N is avg neighbors per loop (~20-50)
- **Typical runtime**: 4-5 seconds for full 3×3 torus mapping

## Customization

### Change Manifold Topology
Edit `utils.py`:
```python
@staticmethod
def create_custom_manifold():
    G = nx.Graph()
    # Add your nodes and edges
    faces = [...]  # Define faces
    return G, faces
```

### Modify Physics
In `main.py`, update the Lagrangian:
```python
def lagrangiana_fisica(node, speed, time=None):
    T = 0.5 * (speed ** 2)
    V = your_potential_function(node, time)
    return T - V
```

### Adjust Search Parameters
```python
mapper.map_space(
    max_k_hops=5,        # Increase for larger loops
    cost_barrier=30.0,   # Higher = broader search
    timeout_seconds=30.0 # Increase for complex manifolds
)
```

## References

- **Differential Geometry**: Torus topology and homotopy groups
- **Lagrangian Mechanics**: Principle of least action, energy optimization
- **Graph Theory**: Manifold representation as graphs with faces
- **Computational Topology**: Loop generation and canonical forms

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Areas of interest:

- [ ] Support for higher-dimensional tori and other manifolds
- [ ] GPU acceleration for large searches
- [ ] Visualization tools (3D loop rendering)
- [ ] Integration with symbolic geometry libraries
- [ ] Extended documentation with mathematical proofs

## Contact

Created by [Your Name] — Questions? Open an issue on GitHub.

---

**Status**: ✅ Fully Functional | **Last Updated**: 2026-09-18
