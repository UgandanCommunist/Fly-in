from typing import Union


class ParsingError(Exception):
    """
    Custom Exception class made to catch errors related to parsing.
    """
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


def validate_file(file_name: str) -> bool:
    """
    Validates the existence of the chosen file.
    Prints 'File found!' if found.
    Else returns False so that we can raise an error in the next func.
    """
    try:
        with open(file_name, 'r') as map_file:
            if map_file.readable():
                return True
            else:
                return False
    except FileNotFoundError:
        return False


def process_map(file_name: str) -> list[tuple[int, str]]:
    """
    Checks if the file is valid (found).
    If valid processes the file into a list of numbered lines.
    Else raises a ParsingError.
    """
    # -------------> func def and docstrings found on line 13.
    if not validate_file(file_name):
        raise ParsingError(f"'{file_name}' not found or unreadable!")

    # -------------> Opens the file, creates list of lines (stripped&lowered)
    with open(file_name, 'r') as map_file:
        # ---------> Creates a list of lines and then numbers it using enum.
        lines_list: list[str] = [
                line.strip().lower() for line in map_file.readlines()
                ]

        numbered_line_list = list(enumerate(lines_list, start=1))

        # ---------> Removes unneccessary lines from the numbered list.
        removes = []

        for line in numbered_line_list:
            if line[1].startswith('#') or line[1] == '':
                removes.append(line)

        for line in removes:
            numbered_line_list.remove(line)

        return numbered_line_list


def tally_keywords(
        keywords: list, lines: list, errors: list
        ) -> list:
    """
    Tallies the number of times a certain keyword has been used.
    Returns a list of duplicates if there are dupes.
    Else returns an empty list.
    Also used to handle the case where certain keywords aren't used entirely.
    """
    tally_list = [0, 0, 0]
    duplicates = []
    for keyword in keywords:
        for line_number, content in lines:
            if content.startswith(keyword) and keyword == keywords[0]:
                tally_list[0] += 1
                if tally_list[0] > 1:
                    duplicates.append(tuple([line_number, content]))
            elif content.startswith(keyword) and keyword == keywords[1]:
                tally_list[1] += 1
                if tally_list[1] > 1:
                    duplicates.append(tuple([line_number, content]))
            elif content.startswith(keyword) and keyword == keywords[2]:
                tally_list[2] += 1
                if tally_list[2] > 1:
                    duplicates.append(tuple([line_number, content]))
            else:
                continue

    if not all(tally_list):
        if tally_list[0] == 0:
            errors.append(
                    f"Critical Error: '{keywords[0]}' isn't used in map.\n"
                    )
        if tally_list[1] == 0:
            errors.append(
                    f"Critical Error: '{keywords[1]}' isn't used in map.\n"
                    )
        if tally_list[2] == 0:
            errors.append(
                    f"Critical Error: '{keywords[2]}' isn't used in map.\n"
                    )

    return duplicates


def validate_drones(line_number: int, drones_line: str) -> Union[int, str]:
    """
    Checks if the number of drones is valid
    by trying to convert it into a floating-point number
    and rounding it to the nearest integer.
    If it succeeds it returns the number.
    Else it returns an appropriate error message.
    """
    split_line = drones_line.split(':')
    if split_line[0] != "nb_drones":
        return (
                f"Error in line {line_number}: "
                f"{drones_line}. Map file must start with 'nb_drones'.\n"
                )
    else:
        try:
            drone_count = round(float(split_line[1].strip()))
            if drone_count <= 0:
                return (
                        f"Error in line {line_number}: "
                        f"{drone_count} is invalid. (must be >= 1)\n"
                        )
            return drone_count
        except ValueError:
            return (
                    f"Error in line {line_number}: "
                    f"{split_line[1]} is a string. Use an int.\n"
                    )
        except OverflowError:
            return (
                    f"Error in line {line_number}: "
                    f"{split_line[1]} is too large."
                    " (maximum capacity is 10 ** 308)\n"
                    )


def check_zone_name(
        line_number: int, content: str, names: list
        ) -> Union[bool, list]:
    """
    Checks if hub names are unique, if not returns a list of errors.
    If no errors are encountered, returns True.
    """
    split_line = content.split(' ')
    errors = []
    if split_line[1] in names:
        errors.append(
                f"Error in line {line_number}:"
                f" {content}. Zone name must be unique.\n"
                )
    else:
        if len(split_line[1].split('-')) != 1:
            errors.append(
                    f"Error in line {line_number}:"
                    f" {content}. Zone name cannot have '-'.\n"
                    )
        names.append(split_line[1])

    if errors:
        return errors

    return True


def check_zone_coordinates(
        line_number: int, content: str, coordinates: list
        ) -> Union[bool, list]:
    """
    Checks if all zone coordinates are valid integers
    if invalid, returns a list of errors encountered.
    Else returns True.
    """
    split_line = content.split(' ')
    errors = []
    try:
        x = round(float(split_line[2]))
        y = round(float(split_line[3]))
        if tuple([x, y]) in coordinates:
            errors.append(
                    f"Error in line {line_number}: "
                    f"{content}. Coordinates must be unique.\n"
                    )
        else:
            coordinates.append(tuple([x, y]))
    except ValueError:
        x_str = split_line[2]
        y_str = split_line[3]
        errors.append(
                f"Error in line {line_number}:"
                f" {content}. Invalid coordinate value(s)."
                f" Possible cause(s): x: {x_str} |  y: {y_str}. \n"
                )
    except OverflowError:
        errors.append(
                f"Error in line {line_number}:"
                f" {content}. Invalid coordinate value"
                " Maximum supported is 10 ** 308\n"
                )
    finally:
        if errors:
            return errors

        return True


def check_zone_metadata(
        line_number: int, content: str
        ) -> Union[bool, list[str]]:
    """
    Checks zone metadata. If metadata is valid returns True.
    Otherwise returns a list of relevant errors.
    Assumes valid zone.
    """
    split_line = content.split(' ')
    errors = []
    keywords = ["zone", "color", "max_drones"]

    zone_metadata = ' '.join(split_line[4:]).strip('[]')
    split_zone_metadata = zone_metadata.split(' ')

    # -------------> Checks if any keywords are duplicated
    tally_list = [0, 0, 0]
    dupes = []
    for keyword in keywords:
        for metadata in split_zone_metadata:
            if metadata.startswith(keyword) and keyword == keywords[0]:
                tally_list[0] += 1
                if tally_list[0] > 1:
                    dupes.append(tuple([line_number, metadata]))
            elif metadata.startswith(keyword) and keyword == keywords[1]:
                tally_list[1] += 1
                if tally_list[1] > 1:
                    dupes.append(tuple([line_number, metadata]))
            elif metadata.startswith(keyword) and keyword == keywords[2]:
                tally_list[2] += 1
                if tally_list[2] > 1:
                    dupes.append(tuple([line_number, metadata]))
            else:
                continue

    if dupes:
        for dupe_line_number, dupe_metadata in dupes:
            errors.append(
                    f"Error in line {dupe_line_number}: "
                    f"duplicate keyword {dupe_metadata}\n"
                    )

    # -------------> Checks if any keywords are invalid
    keywords_set = {keyword.split('=')[0] for keyword in split_zone_metadata}
    for keyword in keywords_set:
        if keyword not in keywords and keyword != '':
            errors.append(
                    f"Error in line {line_number}: "
                    f" {content}. invalid metadata keyword {keyword}.\n"
                    )

    # -------------> Checks if keyword values are invalid
    allowed_zone_values = [
            "normal", "blocked", "restricted", "priority"
            ]

    allowed_color_values = [
            "red", "green", "blue", "yellow", "orange", "purple",
            "cyan", "gray", "black", "brown", "maroon", "gold", "darkred",
            "violet", "crimson", "rainbow", "lime", "magenta"
            ]

    for metadata in split_zone_metadata:
        split_metadata = metadata.split('=')
        try:
            keyword, value = split_metadata
        except ValueError:
            errors.append(
                    f"Error in line {line_number}: "
                    f" {content}. Invalid metadata format."
                    f" Please use the format '[keyword=value]'.\n"
                    )
        if (keyword == "zone" and value in allowed_zone_values):
            continue
        elif (keyword == "color" and value in allowed_color_values):
            continue
        elif keyword == "max_drones":
            try:
                zone_max_drones = round(float(value))
                if zone_max_drones < 1:
                    raise ValueError
            except ValueError:
                errors.append(
                        f"Error in line {line_number}: "
                        f"{content}. Invalid value for {keyword}:{value}"
                        "\n"
                        )
            except OverflowError:
                errors.append(
                        f"Error in line {line_number}: "
                        f"{content}. Invalid value for {keyword}:{value}"
                        f" Maximum supported is 10 ** 308\n"
                        )
            finally:
                continue
        else:
            errors.append(
                    f"Error in line {line_number}: "
                    f"{content}. Invalid value for {keyword}:{value}\n"
                    )

    if errors:
        return errors

    return True


def check_zone(
        line_number: int, content: str, names: list,
        coordinates: list
        ) -> Union[bool, list]:
    """
    Checks if the zone is structured correctly
    (i.e hub: name x y [metadata]).
    Returns True if valid.
    Else returns a list of errors.
    """
    split_line = content.split(' ')
    zone_metadata = ''
    errors = []

    try:
        if (split_line[4].startswith('[') and split_line[-1].endswith(']')):
            zone_metadata += ' '.join(split_line[4:])
        else:
            errors.append(
                    f"Error in line {line_number}: "
                    f"{content}. Invalid zone format."
                    " Follow the format (hub: name x y [metadata=optional])\n"
                    )
    except IndexError:
        pass

    for i in range(0, len(split_line) - 4):
        split_line.pop()

    if zone_metadata != '':
        split_line.append(zone_metadata)

    if len(split_line) == 5:
        # ===============> Helper func definition and docstrings in line 143
        name_check = check_zone_name(line_number, content, names)
        if isinstance(name_check, list):
            errors.extend(name_check)

        # ===============> Helper func definition and docstrings in line 171
        coord_check = check_zone_coordinates(line_number, content, coordinates)
        if isinstance(coord_check, list):
            errors.extend(coord_check)

        # ===============> Helper func definition and docstrings in line 215
        metadata_check = check_zone_metadata(line_number, content)
        if isinstance(metadata_check, list):
            errors.extend(metadata_check)

    elif len(split_line) == 4:
        name_check = check_zone_name(line_number, content, names)
        if isinstance(name_check, list):
            errors.extend(name_check)

        coord_check = check_zone_coordinates(line_number, content, coordinates)
        if isinstance(coord_check, list):
            errors.extend(coord_check)

    else:
        errors.append(
                f"Error in line {line_number}: "
                f"{content}. Invalid zone format."
                " Follow the format (hub: name x y [metadata=optional])\n"
                )

    if errors:
        return errors

    return True


def validate_connections(
        line_number: int, content: str,
        names: list, connections: list
        ) -> Union[bool, list]:
    """
    Checks if connections are valid according to subject criteria.
    If valid the function returns True.
    Else it returns a list of errors.
    """
    errors = []
    full_connection = content.split(':')
    names_list = full_connection[1].split('-')
    name1 = names_list[0].strip()
    name2 = names_list[1].split(' ')[0]

    # -------------> Checks if connections are in valid format.
    # -------------> And checks if both zone names in connections are valid.
    if len(content.split('-')) != 2:
        errors.append(
                f"Error in line {line_number}:"
                f" {content}. Invalid connection format."
                " Use the following format 'connection: zone1-zone2'.\n"
                )

    elif not (name1 in names and name2 in names):
        errors.append(
                f"Error in line {line_number}: {content}."
                " Invalid zone names used in connection"
                f" {name1} - {name2}.\n"
                )
        print(name1, name2, names)
    else:
        if tuple([name1, name2]) in connections:
            errors.append(
                    f"Error in line {line_number}: {content}."
                    f" Duplicate connection: {name1} - {name2}.\n"
                    )
        connections.append(tuple([name1, name2]))
        connections.append(tuple([name2, name1]))

    # -------------> Checks if connection metadata is valid.
    # -------------> For scalability I'll use a list of allowed keywords.
    # -------------> It's redundant for now though since we only accept 1 kw.
    allowed_keywords = ["max_link_capacity"]
    keyword_tally = [0]
    dupes = []
    split_line = content.strip().split(' ')

    # -------------> We don't need split_line[0] nor split_line[1].
    # -------------> Validity has already been checked in the previous steps.
    # -------------> Keywords can be added through the "allowed_keywords" list
    # -------------> The entire metadata validation system can be scaled
    # -------------> by extending the lists and handling errors.
    try:
        metadata = " ".join(split_line[2:])
    except IndexError:
        metadata = None

    if metadata:
        if not (metadata.startswith('[') and metadata.endswith(']')):
            errors.append(
                    f"Error in line {line_number}: {content}."
                    " Invalid connection format. Metadata must be in '[]'."
                    " Please follow the format: connection: zone1-zone2"
                    " [metadata = optional]\n"
                    )
        split_metadata = metadata.strip('[]').split(' ')
        keyword_value_pairs = [pair.split('=') for pair in split_metadata]

        for pair in keyword_value_pairs:
            try:
                keyword, value = pair
            except ValueError:
                errors.append(
                        f"Error in line {line_number}: {content}."
                        f" Invalid metadata format '{pair}'"
                        " Please use the format '[keyword=value]'\n"
                        )
            else:
                if keyword not in allowed_keywords:
                    errors.append(
                            f"Error in line {line_number}: {content}."
                            f" Invalid keyword metadata '{keyword}'.\n"
                            )
                elif keyword == allowed_keywords[0]:
                    keyword_tally[0] += 1
                    if keyword_tally[0] > 1:
                        dupes.append(
                                tuple([line_number, f"{keyword}={value}"])
                                )
                    try:
                        max_link = round(float(value))
                        if max_link < 1:
                            raise ValueError
                    except ValueError:
                        errors.append(
                                f"Error in line {line_number}: {content}."
                                f" Invalid value for {keyword}: {value}."
                                " Value must be higher than 0.\n"
                                )
                    except TypeError:
                        errors.append(
                                f"Error in line {line_number}: {content}."
                                f" Invalid value for {keyword}: {value}."
                                " Value must be a positive number.\n"
                                )
                    except OverflowError:
                        errors.append(
                                f"Error in line {line_number}: {content}."
                                f" Invalid value for {keyword}: {value}."
                                " Value must be less than 10**308.\n"
                                )
        if dupes:
            for dupe_line_number, dupe_metadata in dupes:
                errors.append(
                        f"Error in line {line_number}: {content}."
                        f" duplicate keyword {dupe_metadata}.\n"
                        )

    if errors:
        return errors

    return True


def validate_zone_format(
        lines: list
        ) -> Union[bool, list]:
    """
    Checks if the zone format and connections comply with subject criteria
    for every line that's classified as a 'hub' or a 'connection'.
    Returns a list of errors if invalid.
    Otherwise returns true
    """
    errors = []
    names: list[str] = []
    coords: list[str] = []
    connections: list[str] = []

    # --------------> Checks if hub names are unique.
    # --------------> And checks if hub coordinates are valid
    # -------------> Checks if connections are valid.
    # -------------> No duplicate connections, no disconnected zones...
    # ===============> Relevant helper function def and docs -> 316 and 386
    for line_number, content in lines:
        if content.startswith("start_hub"):
            zone_validity = check_zone(line_number, content, names, coords)
            if isinstance(zone_validity, list):
                errors.extend(zone_validity)
        elif content.startswith("hub"):
            zone_validity = check_zone(line_number, content, names, coords)
            if isinstance(zone_validity, list):
                errors.extend(zone_validity)
        elif content.startswith("end_hub"):
            zone_validity = check_zone(line_number, content, names, coords)
            if isinstance(zone_validity, list):
                errors.extend(zone_validity)
        elif content.startswith("connection"):
            connections_validity = validate_connections(
                    line_number, content, names, connections
                    )
            if isinstance(connections_validity, list):
                errors.extend(connections_validity)
        else:
            continue

    if errors:
        return errors

    return True


def validate_map_format(
        lines: list
        ) -> Union[bool, list]:
    """
    Checks if the file format is valid
    with accordance to subject requirements.
    Returns True if valid.
    Else appends an error to the errors list
    and returns the list of errors.
    """
    errors_list = []
    try:
        drone_line_number, drone_line = lines[0]
    except IndexError:
        errors_list.append("Critical Error: Map file is empty!\n")

    # -------------> Checks if any keywords are invalid
    allowed_keywords = [
            "nb_drones", "start_hub", "hub", "end_hub", "connection"
            ]
    for line_number, content in lines:
        keyword = content.split(':')[0]
        if not (keyword in allowed_keywords):
            errors_list.append(
                    f"Error in line {line_number}: "
                    f"{content}. Invalid keyword '{keyword}'.\n"
                    )

    # -------------> Checks if any unique keywords are duplicated.
    # ===============>  (i.e: nb_drones, start_hub and end_hub)
    unique_keywords = ["nb_drones", "start_hub", "end_hub"]

    # -------------> func def and docstrings found on line 62
    duplicates = tally_keywords(unique_keywords, lines, errors_list)

    if duplicates:
        for dupe_line_number, dupe_content in duplicates:
            errors_list.append(
                    f"Error in line {dupe_line_number}: "
                    f"duplicate keyword in {dupe_content}\n"
                    )

    # -------------> Drone number validation
    # -------------> Checks if nb_drones is the first line in the map file.
    # -------------> func def and docstrings found on line 107
    try:
        drone_number = validate_drones(drone_line_number, drone_line)
    except UnboundLocalError:
        drone_number = False

    if isinstance(drone_number, str):
        errors_list.append(drone_number)

    # -------------> Zone name, coordinate and metadata validation.
    # ==============> Helper function definition and docstrings in line 507
    map_format_validity = validate_zone_format(lines)
    if isinstance(map_format_validity, list):
        errors_list.extend(map_format_validity)

    # -------------> Checks if the map file is following the sequence in order.
    # -------------> nb_drones -> start_hub -> hubs -> end_hub -> connections.
    # -------------> Only checks if no prior errors are detected.
    if lines and not errors_list:
        end_hub_tuple = []
        for line_number, content in lines:
            if content.startswith("end_hub"):
                end_hub_tuple = ([line_number, content])
        start_hub_line, start_hub_content = lines[1]
        end_hub_line, end_hub_content = end_hub_tuple
        for line_number, content in lines:
            if (line_number in range(start_hub_line + 1, end_hub_line)
                    and not content.startswith("hub")):
                errors_list.append(
                        f"Error in line {line_number}: {content}."
                        " Please reformat the map file"
                        " in the following structure:"
                        " 'nb_drones=n' -> 'hubs: name x y"
                        " [metadata=optional]' (starting with 'start_hub' and"
                        " ending with 'end_hub') -> 'connections: hub1-hub2'"
                        " [metadata=optional]\n"
                        )
            elif (line_number > end_hub_line
                    and not content.startswith("connection")):
                errors_list.append(
                        f"Error in line {line_number}: {content}."
                        " Please reformat the map file"
                        " in the following structure:"
                        " 'nb_drones=n' -> 'hubs: name x y"
                        " [metadata=optional]' (starting with 'start_hub' and"
                        " ending with 'end_hub') -> 'connections: hub1-hub2'"
                        " [metadata=optional]\n"
                        )

    if errors_list:
        error_message = "\n"
        criticals = []
        for error in errors_list:
            if error.startswith("Critical"):
                error_message += ("  " + error)
                criticals.append(error)
        for critical_error in criticals:
            errors_list.remove(critical_error)

        if errors_list:
            formatted_errors_list = sorted(
                    errors_list,
                    key=lambda x: int(x.split(':')[0].split(' ')[3])
                    )
            error_message += "  "
            error_message += "  ".join(formatted_errors_list)

        raise ParsingError(error_message)

    return True


def parse(path: str) -> Union[dict, str]:
    """
    This function returns a dictionary filled with map
    information if all prior steps go well.
    Otherwise a ParsingError will be raised and it will
    return an error message.
    """
    map_info: dict[str, Union[list, str, int]] = {}
    try:
        lines = process_map(path)
    except ParsingError as e:
        return (f"Parsing Error: {e}")
    else:
        try:
            validate_map_format(lines)
        except ParsingError as e:
            return (f"Parsing Error(s) found: {e}")
        else:
            map_content = [content for line, content in lines]
            indexes = [1, 1]
            for obj in map_content:
                key, value = obj.split(':')
                if key == "nb_drones":
                    map_info[key] = round(float(value.strip()))
                elif key == "start_hub":
                    lst_value = value.strip().split(' ')
                    if len(lst_value) > 3:
                        metadata = ' '.join(lst_value[3:])
                        for i in range(3, len(lst_value)):
                            lst_value.pop()
                        lst_value.append(metadata)

                    map_info[key] = lst_value
                elif key == "hub":
                    lst_value = value.strip().split(' ')
                    if len(lst_value) > 3:
                        metadata = ' '.join(lst_value[3:])
                        for i in range(3, len(lst_value)):
                            lst_value.pop()
                        lst_value.append(metadata)

                    map_info[key + str(indexes[0])] = lst_value
                    indexes[0] += 1
                elif key == "end_hub":
                    lst_value = value.strip().split(' ')
                    if len(lst_value) > 3:
                        metadata = ' '.join(lst_value[3:])
                        for i in range(3, len(lst_value)):
                            lst_value.pop()
                        lst_value.append(metadata)

                    map_info[key] = lst_value
                elif key == "connection":
                    map_info[key + str(indexes[1])] = value.strip().split(' ')
                    indexes[1] += 1

    return map_info


if __name__ == "__main__":
    info = parse("./test.txt")
    if isinstance(info, str):
        print(info)
    else:
        for key, value in info.items():
            print(f"{key}: {value}")
