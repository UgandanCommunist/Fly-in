import heapq
from utils import Drone, Zone
from typing import Any, Union


class Pathfinder:
    """
    The main pathfinder class.
    """
    def __init__(
            self, drones: list[Drone], zones: list[Zone]
            ) -> None:
        self.drones = drones
        self.zones = zones
        self.zone_reserve: dict[Any, float] = {}
        self.link_reserve: dict[Any, float] = {}
        self.distances: dict[Any, float] = {}
        self.benchmark: Union[int, None] = 0

    def yank_zone(self, name: str) -> Any:
        """
        A simple helper method that searches the list of zones
        and finds a zone with a matching name.
        """
        for zone in self.zones:
            if zone.name == name:
                return zone
            continue
        return None

    def find_heuristic(self, start_hub: Zone) -> None:
        """
        A helper method that calculates an heuristic
        for the A* algorithm, it simply runs dijkstra's
        and returns the shortest path, priority zones are preferred.
        """
        # ------> We initialize the distance dict
        # ------> And the heapq list
        self.distances[start_hub.name] = 0
        heap: list[tuple[float, str]] = [(0, start_hub.name)]

        # ------> We run a loop that calculates the shortest distance
        # ------> To every zone using dijkstra's algorithm
        while heap:
            dist, zone_name = heapq.heappop(heap)
            if dist != self.distances.get(zone_name, float('inf')):
                continue

            zone = self.yank_zone(zone_name)
            if zone is None:
                continue

            for link, _ in zone.connected_to:
                li = self.yank_zone(link)
                # ------> We ignore blocked zones
                if li.zone_type == "blocked":
                    continue
                cost = 1 if li.zone_type != "restricted" else 2
                new_dist: float = dist + cost
                # ------> We give a slight bias to priority zones.
                if li.zone_type == "priority":
                    new_dist *= 0.9

                if new_dist < self.distances.get(li.name, float('inf')):
                    self.distances[li.name] = new_dist
                    heapq.heappush(heap, (new_dist, li.name))

    def reserve_path(self, path: list) -> None:
        """
        A helper method that reserves a path in a specific time span.
        """
        # ------> We investigate the path until the end.
        for i in range(len(path) - 1):
            from_zone, at_turn = path[i]
            to_zone, arrival_turn = path[i + 1]

            # ------> If to_zone isn't end_hub
            # ------> and not start_hub at turn 0
            # ------> then we reserve the zone for the turn
            if (to_zone != self.zones[-1].name
                    and not (to_zone == self.zones[0].name and arrival_turn == 0)):
                    self.zone_reserve[
                            (to_zone, arrival_turn)
                            ] = self.zone_reserve.get((to_zone, arrival_turn), 0) + 1

            # ------> If we moved then we reserve the connection for the turn
            if from_zone != to_zone:
                for turn in range(at_turn, arrival_turn):
                    self.link_reserve[
                            (from_zone, to_zone, turn)
                            ] = self.link_reserve.get(
                                    (from_zone, to_zone, turn), 0
                                    ) + 1

    def valid_move(
            self, from_zone: str, to_zone: str, curr_turn: int
            ) -> bool:
        """
        A helper method that validates a move from a zone
        to another zone at a specific turn.
        """
        to = self.yank_zone(to_zone)
        frm = self.yank_zone(from_zone)

        # ------> if the zones are the same (drone is waiting)
        if from_zone == to_zone:
            wait_turn = curr_turn + 1

            # ------> if it's not end_hub or start_hub on turn 0
            if (to.name == self.zones[-1].name
                    or (to.name == self.zones[0].name and wait_turn == 0)):
                return True

            # -------> if the drone is going to cause a collision in a zone
            # -------> return false else true
            if self.zone_reserve.get(
                    (to.name, wait_turn), 0
                    ) + 1 > to.max_drones:
                return False
            return True

        # ------> Movement cost calculations
        cost = 1 if to.zone_type != "restricted" else 2
        arrival_turn = curr_turn + cost

        # ------> If destination isn't end_hub or start_hub on turn 0
        if (to.name != self.zones[-1].name
                and not (to.name == self.zones[0].name) and arrival_turn == 0):
            # ------> if the drone is going to cause a collision in a zone
            # ------> return False
            if self.zone_reserve.get(
                    (to.name, arrival_turn), 0
                    ) + 1 > to.max_drones:
                return False

        # ------> Initialize link_cap and match it to the connection link_cap
        link_cap = 1
        for link, cap in frm.connected_to:
            if link == to.name:
                link_cap = cap
                break

        # ------> Check if the connection is reserved for every turn
        # ------> Between the current turn and arrival turn
        for turn in range(curr_turn, arrival_turn):
            if self.link_reserve.get(
                    (frm.name, to.name, turn), 0
                    ) + 1 > link_cap:
                # ------> if a collision will happen in a connection
                # ------> return false
                return False

            # -------> bidirectional support
            if self.link_reserve.get(
                    (to.name, frm.name, turn), 0
                    ) + 1 > link_cap:
                return False

        # ------> No collisions == move is valid
        return True

    def plan_drone(
            self, drone: Drone, start: Zone, end: Zone, max_turns: int = 200
            ) -> Any:
        """
        A low level planner that paths for a drone using A*.
        it checks for connection conflicts, blocked zones,
        and zone conflicts.
        """
        # -----> Initializing useful variables including
        # -----> heapq, move counter, starting path, A*'s base cost.
        heap: list = []
        counter = 0
        start_path = [(start.name, 0)]
        a_star_f = self.distances.get(start.name, float('inf'))

        # ------> Initial turn 0 setup.
        heapq.heappush(heap, (a_star_f, counter, start.name, 0, start_path, 0))
        counter += 1
        visited = set()

        while heap:
            # ------> counter is useless for A* itself.
            f, _, zone_name, curr_turn, path, a_star_g = heapq.heappop(heap)

            # -----> current zone and turn.
            key = (zone_name, curr_turn)
            if key in visited:
                continue
            visited.add(key)

            # -----> if the drone arrives return the path.
            if zone_name == end.name:
                return path

            # -----> iteration limit
            if curr_turn > max_turns:
                continue

            zone = self.yank_zone(zone_name)
            if zone is None:
                continue

            # -----> if we're waiting, validate that there won't be a conflict
            wait_turns = curr_turn + 1
            if self.valid_move(zone.name, zone.name, curr_turn):
                new_path = path + [(zone.name, wait_turns)]
                new_g = a_star_g + 1
                new_f = new_g + self.distances.get(zone.name, float('inf'))
                heapq.heappush(
                        heap,
                        (
                            new_f, counter, zone.name,
                            wait_turns, new_path, new_g
                            )
                        )
                counter += 1

            # -----> if we're moving check if dst is connected and not blocked
            for link, _ in zone.connected_to:
                li = self.yank_zone(link)
                if li.zone_type == "blocked":
                    continue
                cost = 1 if li.zone_type != "restricted" else 2
                # -----> actual cost for A* base cost + heuristic.
                arrival_turn = curr_turn + cost

                # -----> if no conflicts in zone movement push move to path.
                if self.valid_move(zone.name, link, curr_turn):
                    new_path = path + [(li.name, arrival_turn)]
                    new_g = a_star_g + cost
                    new_f = new_g + self.distances.get(
                            li.name, float('inf')
                            )
                    heapq.heappush(
                            heap,
                            (
                                new_f, counter, li.name,
                                arrival_turn, new_path, new_g
                                )
                            )
                    counter += 1

        return None

    def solve(self) -> bool:
        """
        This method acts as the high level planner.
        It will manage multiple agents by providing paths.
        It will give the first drone the most optimal path,
        second drone the second best option,
        and the last drone the worst option.
        It ends up not mattering since all drones have the same
        start and goal.
        """
        # ------> Calculate heuristic for all zones.
        self.find_heuristic(self.zones[0])

        # ------> make sure that reserves are empty
        self.zone_reserve.clear()
        self.link_reserve.clear()

        # ------> reserve the start zone at turn 0 for all drones.
        self.zone_reserve[(self.zones[0].name, 0)] = len(self.drones)

        # ------> Plan a path for each drone
        for drone in self.drones:
            path = self.plan_drone(drone, self.zones[0], self.zones[-1])

            # -----> if pathfinding failed return an error
            if path is None:
                drone.path_error = f"Failed to plan {drone.d_id}"
                self.benchmark = None
                return False
            # -----> Else provide the drone with its individual path
            # -----> and reserve it for the turns it will move.
            drone.path = path
            self.reserve_path(path)

        # ------> Total turns used for all drones to arrive at end_hub.
        self.benchmark = max(
                drone.path[-1][1] for drone in self.drones if drone.path
                )

        # ------> If no errors encountered return True
        return True
