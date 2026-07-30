from typing import Union


class Drone:
    """
    Basic drone class with the necessary information
    id, path, animation path, index and arrival state.
    As well as a helper method.
    """
    def __init__(self, d_id: str) -> None:
        self.d_id = d_id
        self.path: list[tuple[str, int]] = []
        self.anim_path: list[str] = []
        self.man_anim_path: list[str] = []
        self.path_error = ""
        self.i = 0
        self.arrived = False

    def expand_path(self, path: list[tuple[str, int]]) -> None:
        """
        This method simply expands the path with connections
        in case of the existence of a restricted area in the path.
        """
        expanded = []
        for i in range(len(path) - 1):
            current_zone, current_t = path[i]
            next_zone, next_t = path[i+1]
            # ------> if start or any zone
            if i == 0 or current_t != next_t:
                expanded.append(current_zone)
            # ------> if restricted area
            if next_t - current_t == 2:
                conn = f"{current_zone}-{next_zone}"
                expanded.append(conn)
        expanded.append(path[-1][0])
        self.anim_path.extend(expanded)


class Zone:
    """
    Basic zone class with the necessary information
    name, coords, color, type, max drones and connections.
    as well as 2 helper methods.
    """
    def __init__(
            self, name: str, x: int, y: int,
            color: str, zone_type: str,
            max_drones: int, connected_to: Union[list[tuple], None] = None
            ) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.color = color
        self.zone_type = zone_type
        self.max_drones = max_drones
        if connected_to is None:
            self.connected_to = []
        else:
            self.connected_to = connected_to

    def connection_inspection(self, config: dict) -> None:
        """
        A simple helper method that checks which zones are connected
        and what their max link capacity is.
        """
        for key, value in config.items():
            if key.startswith("connection") and len(value) == 1:
                zone1, zone2 = value[0].split('-')
                if zone1 == self.name:
                    self.connected_to.append(tuple([zone2, 1]))
                    continue
                elif zone2 == self.name:
                    self.connected_to.append(tuple([zone1, 1]))
                    continue

            elif key.startswith("connection") and len(value) == 2:
                zone1, zone2 = value[0].split('-')
                connection_metadata = value[1].strip("[]").split('=')
                max_link = round(float(connection_metadata[1]))
                if zone1 == self.name:
                    self.connected_to.append(tuple([zone2, max_link]))
                    continue
                elif zone2 == self.name:
                    self.connected_to.append(tuple([zone1, max_link]))
                    continue
            else:
                continue

    def get_zone_data(self) -> None:
        """
        A simple helper method that displays zone info on the terminal.
        """
        print("Zone name:", self.name)
        print(f"Zone x = {self.x} | y = {self.y}")
        print("Zone color:", self.color)
        print("Zone type:", self.zone_type)
        print("Zone max_drones:", self.max_drones)
        print("Zone connected to:", self.connected_to)
        print()


class SetupFactory:
    """
    A factory class that produces a list of zones and drones
    for pathfinding and visualizing.
    """
    def __init__(self, config: dict) -> None:
        self.config = config

    def create_drones(self) -> list[Drone]:
        """
        A simple method that returns a list of drones
        and assigns them ids.
        """
        drones = []
        drone_id = 1
        nb_drones = self.config["nb_drones"]
        for i in range(drone_id, nb_drones + 1):
            drones.append(Drone("D" + str(i)))

        return drones

    def metadata_inspection(self, target: str) -> dict:
        """
        A simple helper method that checks for zone metadata.
        it will return a dictionary containing appropriate
        metadata for the target zone.
        """
        metadata_dict = {}
        if target == "start_hub":
            metadata_dict["max_drones"] = self.config["nb_drones"]
            if len(self.config[target]) == 3:
                metadata_list = []
            else:
                metadata_list = self.config[target][3].strip("[]").split(' ')

            for pair in metadata_list:
                if pair.startswith("color"):
                    key, value = pair.split('=')
                    metadata_dict[key] = value
                elif pair.startswith("zone"):
                    key, value = pair.split('=')
                    metadata_dict[key] = value
                else:
                    continue

            try:
                metadata_dict["color"]
            except KeyError:
                metadata_dict["color"] = "gray"
            try:
                metadata_dict["zone"]
            except KeyError:
                metadata_dict["zone"] = "normal"

        elif target.startswith("hub"):
            if len(self.config[target]) == 3:
                metadata_list = []
            else:
                metadata_list = self.config[target][3].strip("[]").split(' ')

            for pair in metadata_list:
                if pair.startswith("color"):
                    key, value = pair.split('=')
                    metadata_dict[key] = value
                elif pair.startswith("zone"):
                    key, value = pair.split('=')
                    metadata_dict[key] = value
                elif pair.startswith("max_drones"):
                    key, value = pair.split('=')
                    metadata_dict[key] = round(float(value))

            try:
                metadata_dict["max_drones"]
            except KeyError:
                metadata_dict["max_drones"] = 1
            try:
                metadata_dict["color"]
            except KeyError:
                metadata_dict["color"] = "gray"
            try:
                metadata_dict["zone"]
            except KeyError:
                metadata_dict["zone"] = "normal"

        elif target == "end_hub":
            metadata_dict["max_drones"] = self.config["nb_drones"]
            if len(self.config[target]) == 3:
                metadata_list = []
            else:
                metadata_list = self.config[target][3].strip("[]").split(' ')

            for pair in metadata_list:
                if pair.startswith("color"):
                    key, value = pair.split('=')
                    metadata_dict[key] = value
                elif pair.startswith("zone"):
                    key, value = pair.split('=')
                    metadata_dict[key] = value
                else:
                    continue

            try:
                metadata_dict["color"]
            except KeyError:
                metadata_dict["color"] = "gray"
            try:
                metadata_dict["zone"]
            except KeyError:
                metadata_dict["zone"] = "normal"

        return metadata_dict

    def create_zones(self) -> list[Zone]:
        """
        A simple method that returns a list of zones
        and assigns them metadata, connection data, etc...
        """
        zones = []
        for key, value in self.config.items():
            if key == "start_hub":
                metadata = self.metadata_inspection(key)
                zones.append(
                        Zone(
                            value[0],
                            round(float(value[1])),
                            round(float(value[2])),
                            metadata["color"],
                            metadata["zone"],
                            metadata["max_drones"]
                            )
                        )
            elif key.startswith("hub"):
                metadata = self.metadata_inspection(key)
                zones.append(
                        Zone(
                            value[0],
                            round(float(value[1])),
                            round(float(value[2])),
                            metadata["color"],
                            metadata["zone"],
                            metadata["max_drones"]
                            )
                        )
            elif key == "end_hub":
                metadata = self.metadata_inspection(key)
                zones.append(
                        Zone(
                            value[0],
                            round(float(value[1])),
                            round(float(value[2])),
                            metadata["color"],
                            metadata["zone"],
                            metadata["max_drones"]
                            )
                        )
            else:
                continue

        for zone in zones:
            zone.connection_inspection(self.config)

        return zones
