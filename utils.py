import networkx as nx


class GraphFactory:
    @staticmethod
    def create_torus_3x3():
        """
        Creates a 3x3 torus manifold represented as a graph.

        Nodes are arranged as:
        0 1 2
        3 4 5
        6 7 8

        With wraparound connections (edges) to form a torus topology.
        """
        G = nx.Graph()
        n_rows, n_cols = 3, 3

        # Add nodes
        for i in range(n_rows * n_cols):
            G.add_node(i)

        # Add edges (horizontal and vertical with wraparound)
        for i in range(n_rows):
            for j in range(n_cols):
                node = i * n_cols + j

                # Horizontal edge (with wraparound)
                right_node = i * n_cols + (j + 1) % n_cols
                G.add_edge(node, right_node, weight=1.0)

                # Vertical edge (with wraparound)
                down_node = ((i + 1) % n_rows) * n_cols + j
                G.add_edge(node, down_node, weight=1.0)

        # Define faces (2-dimensional cycles that bound the manifold)
        # For a torus grid, faces are the elementary squares
        faces = []
        for i in range(n_rows):
            for j in range(n_cols):
                # Elementary square face with wraparound
                v0 = i * n_cols + j
                v1 = i * n_cols + (j + 1) % n_cols
                v2 = ((i + 1) % n_rows) * n_cols + (j + 1) % n_cols
                v3 = ((i + 1) % n_rows) * n_cols + j
                faces.append((v0, v1, v2, v3))

        return G, faces
