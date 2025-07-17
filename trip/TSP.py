import requests

class Graph:
    def __init__(self, num_vertices):
        self.num_vertices = num_vertices
        self.edges = [[0] * num_vertices for _ in range(num_vertices)]  # Ma trận kề

    def add_edge(self, u, v, weight):
        self.edges[u][v] = weight

    def find_hamiltonian_path(self, fixed_position=None, precedence_constraints=None, start=None, end=None):
        import itertools
        vertices = list(range(self.num_vertices))
        min_path = None
        min_cost = float("inf")

        if fixed_position is None:
            fixed_position = [False] * (self.num_vertices + 1)
        if precedence_constraints is None:
            precedence_constraints = []

        fixed_position_map = {}
        for i, fixed in enumerate(fixed_position):
            if fixed:
                fixed_position_map[i] = None

        # Loại bỏ start và end ra khỏi hoán vị (nếu có)
        inner_vertices = vertices.copy()
        if start is not None:
            inner_vertices.remove(start)
        if end is not None and end in inner_vertices:
            inner_vertices.remove(end)

        for perm in itertools.permutations(inner_vertices):
            path = list(perm)
            if start is not None:
                path.insert(0, start)
            else:
                path.insert(0, 0)

            if end is not None:
                path.append(end)
            else:
                path.append(path[0])  # Quay về điểm xuất phát như TSP

            valid = True

            # Kiểm tra fixed_position
            for idx, node in fixed_position_map.items():
                if idx < len(path):
                    if node is not None and path[idx] != node:
                        valid = False
                        break
                    fixed_position_map[idx] = path[idx]

            # Kiểm tra precedence_constraints
            for u, v in precedence_constraints:
                try:
                    if path.index(u) >= path.index(v):
                        valid = False
                        break
                except ValueError:
                    valid = False
                    break

            if not valid:
                continue

            cost = sum(self.edges[path[i]][path[i+1]] for i in range(len(path) - 1))

            if cost < min_cost:
                min_cost = cost
                min_path = path

        return min_path, min_cost

def distance(origins, destinations):
    api_key = "nV8MX9Jxszg9MyjUJv5yfTUK4OzKhTGtG0z2E779ZGtdhd2TenzBA1QgOzOf6H2T"
    url = "https://api-v2.distancematrix.ai/maps/api/distancematrix/json"

    params = {
        "origins": origins,
        "destinations": destinations,
        "key": api_key
    }

    response = requests.get(url, params=params)
    
    result = response.json()
    distance = result["rows"][0]["elements"][0]["distance"]["value"]
    duration = result["rows"][0]["elements"][0]["duration"]["value"]
    return distance, duration
