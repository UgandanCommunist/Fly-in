from utils import parse, SetupFactory, Pathfinder
import math
import pyglet
import os
from typing import Any


class Visualizer(pyglet.window.Window):
    """
    The visualizer class will be used to power the window system.
    It will run using the Pyglet framework, which is lightweight
    and OOP friendly.
    """
    def __init__(self) -> None:
        """
        This method will initialize the window using a super() func
        which will call the Window constructor allowing us to define
        event loops as methods rather than using a wrapper.
        Additionally it will also initialize several important
        simulation state variables which will be explored individually
        in comments.
        """
        # ---------> Initializes a non-resizable 800x600 window.
        super().__init__(800, 600, resizable=False, vsync=False)

        # ---------> Sets the path for the resource command to "./resources".
        pyglet.resource.path = ['resources']
        pyglet.resource.reindex()

        # ---------> Adds the Minecraft font from "./resources".
        pyglet.resource.add_font('Minecraft.ttf')
        self.minecraft = pyglet.font.load('Minecraft')

        # ---------> Sets the window caption to Fly-in and sets a logo.
        self.set_caption('Fly-in')
        logo = pyglet.resource.image('logo.jpg')
        self.set_icon(logo)

        # ---------> Initializes the Batch class for the title screen & graph.
        # ---------> Note that a Batch is an ensemble of vertexes to render.
        self.title_batch = pyglet.graphics.Batch()
        self.graph = pyglet.graphics.Batch()

        # ---------> Initializes the Group classes for each respective layer.
        # ---------> A group controls the order in which vertexes are drawn.
        self.title_bg = pyglet.graphics.Group(order=0)
        self.title_fg = pyglet.graphics.Group(order=1)
        self.lines = pyglet.graphics.Group(order=3)
        self.zones = pyglet.graphics.Group(order=4)
        self.drones = pyglet.graphics.Group(order=5)
        self.info_group = pyglet.graphics.Group(order=6)

        # ---------> We make a preset dictionary of RGBA coded colors.
        self.colors = {
                'red': (210, 24, 24), 'blue': (24, 68, 210),
                'green': (122, 231, 27), 'yellow': (253, 235, 0),
                'orange': (255, 151, 0), 'purple': (173, 34, 240),
                'cyan': (45, 249, 234), 'gray': (105, 105, 105),
                'black': (10, 10, 10), 'brown': (118, 72, 10),
                'maroon': (111, 0, 0), 'gold': (221, 192, 77),
                'darkred': (144, 0, 0), 'violet': (140, 68, 189),
                'crimson': (197, 39, 70), 'rainbow': (210, 24, 24),
                'lime': (106, 255, 123), 'magenta': (246, 86, 228)
                }

        # ---------> Draws the welcome text in the center of the screen.
        self.title = pyglet.text.Label(
                'Welcome to Fly-in!',
                font_name='Minecraft', font_size=24,
                x=self.width//2, y=self.height//2 + 16,
                anchor_x='center', anchor_y='center',
                batch=self.title_batch, group=self.title_fg,
                color=self.colors['yellow']
                )

        self.instruction = pyglet.text.Label(
                '- Press Enter to choose your map -',
                font_name='Minecraft', font_size=22,
                x=self.width//2, y=self.height//2 - 30,
                anchor_x='center', anchor_y='center',
                batch=self.title_batch, group=self.title_fg,
                color=self.colors['yellow']
                )

        # --------> Sources and draws the title background.
        self.anim = pyglet.resource.animation('title_screen.gif')
        self.sprite = pyglet.sprite.Sprite(
                img=self.anim,
                batch=self.title_batch, group=self.title_bg
                )
        self.sprite.scale_x = 1.6
        self.sprite.scale_y = 1.36

        # --------> Simulation state bool for whether we're in the title.
        self.title_screen = True

        # --------> Simulation state variables for selection menu navigation.
        self.map_selection = False
        self.custom_map_select = False
        self.custom_len = 0
        self.selection_labels: list = []

        # --------> Simulation state bools for map difficulty.
        # ==========> These are used for different bgs for each diff level.
        self.in_map = False
        self.easy_map = False
        self.medium_map = False
        self.hard_map = False
        self.challenger_map = False
        self.custom_map = False

        # --------> Simulation variables for drone animations and turn counts.
        self.simulating = False
        self.pending_animations = 0
        self.turn_in_progress = False
        self.manual_mode = False
        self.going_back = False
        self.expansion_counter = 0
        self.info_toggle = False
        self.info: dict[str, list[str]] = {}
        self.info_display: list = []

        # --------> Simulation variables for sim conclusion.
        self.sim_over = False
        self.overviewing = False
        self.unsolvable = False
        self.overview = ""
        self.p_counter = 0

        # --------> Simulation bool in case a ParsingError is encountered.
        self.error_encounter = False

    def on_draw(self) -> None:
        """
        This method is an override of the "window.on_draw" method
        It will draw the content of our Batch objects.
        """
        self.clear()
        self.title_batch.draw()
        self.graph.draw()

    def map_selector(self) -> None:
        """
        This method transitions into the map selector
        from title screen.
        """
        # --------> This deletes the Label objects we used in the title.
        self.instruction.delete()
        self.title.delete()

        # --------> Static map support for the official 42 maps.
        # --------> Custom selector is if more maps are added.
        self.maps = pyglet.text.Label(
                'Maps:', font_name='Minecraft',
                font_size=24, x=8, y=self.height,
                anchor_x='left', anchor_y='top',
                batch=self.title_batch, group=self.title_fg,
                color=self.colors['yellow']
                )

        self.map1 = pyglet.text.Label(
                '01 - Linear Path', font_name='Minecraft',
                font_size=24, x=60, y=self.height - 50,
                anchor_x='left', anchor_y='top',
                batch=self.title_batch, group=self.title_fg
                )

        self.map2 = pyglet.text.Label(
                '02 - Simple Fork', font_name='Minecraft',
                font_size=24, x=60, y=self.height - 100,
                anchor_x='left', anchor_y='top',
                batch=self.title_batch, group=self.title_fg
                )

        self.map3 = pyglet.text.Label(
                '03 - Basic Capacity', font_name='Minecraft',
                font_size=24, x=60, y=self.height - 150,
                anchor_x='left', anchor_y='top',
                batch=self.title_batch, group=self.title_fg
                )

        self.map4 = pyglet.text.Label(
                '04 - Dead End Trap', font_name='Minecraft',
                font_size=24, x=60, y=self.height - 200,
                anchor_x='left', anchor_y='top',
                batch=self.title_batch, group=self.title_fg
                )

        self.map5 = pyglet.text.Label(
                '05 - Circular Loop', font_name='Minecraft',
                font_size=24, x=60, y=self.height - 250,
                anchor_x='left', anchor_y='top',
                batch=self.title_batch, group=self.title_fg
                )

        self.map6 = pyglet.text.Label(
                '06 - Priority Puzzle', font_name='Minecraft',
                font_size=24, x=60, y=self.height - 300,
                anchor_x='left', anchor_y='top',
                batch=self.title_batch, group=self.title_fg
                )

        self.map7 = pyglet.text.Label(
                '07 - Maze Nightmare', font_name='Minecraft',
                font_size=24, x=60, y=self.height - 350,
                anchor_x='left', anchor_y='top',
                batch=self.title_batch, group=self.title_fg
                )

        self.map8 = pyglet.text.Label(
                '08 - Capacity Hell', font_name='Minecraft',
                font_size=24, x=60, y=self.height - 400,
                anchor_x='left', anchor_y='top',
                batch=self.title_batch, group=self.title_fg
                )

        self.map9 = pyglet.text.Label(
                '09 - Ultimate Challenge', font_name='Minecraft',
                font_size=24, x=60, y=self.height - 450,
                anchor_x='left', anchor_y='top',
                batch=self.title_batch, group=self.title_fg
                )

        self.map10 = pyglet.text.Label(
                '10 - The Impossible Dream', font_name='Minecraft',
                font_size=24, x=60, y=self.height - 500,
                anchor_x='left', anchor_y='top',
                batch=self.title_batch, group=self.title_fg
                )

        # --------> Controls Label for UX.
        self.controls = pyglet.text.Label(
                'Controls: - C: Custom Map | Arrow Keys: Navigation '
                + '| Escape: Exit -',
                font_name='Minecraft', font_size=12,
                x=self.width//2, y=30, color=self.colors['yellow'],
                anchor_x='center', anchor_y='bottom',
                batch=self.title_batch, group=self.title_fg
                )

        # --------> We put all of these labels in one list.
        # ==========> It's more convenient to get rid of them this way.
        self.selection_labels.extend(
                [
                    self.maps, self.map1, self.map2, self.map3, self.map4,
                    self.map5, self.map6, self.map7, self.map8, self.map9,
                    self.map10, self.controls
                ]
            )

        # --------> Simple indicator to know which map we're selecting.
        self.indicator = pyglet.shapes.Triangle(
                x=25, y=self.height - 62,
                x2=40, y2=self.height - 70,
                x3=25, y3=self.height - 78,
                color=(253, 235, 0, 200), batch=self.title_batch,
                group=self.title_fg
                )

        # --------> We add the indicator to the list as well.
        self.selection_labels.append(self.indicator)
        self.selected: list = []

        # --------> Simulation state advancement.
        self.title_screen = False
        self.map_selection = True

    def on_key_press(self, symbol: None, modifiers: None) -> None:
        """
        This method is an override for pyglet's window.on_key_press.
        It specifically handles keyboard events.
        """

        # --------> Index for map positions by their y-coordinate.
        idx_dict = {
                1: 538, 2: 488, 3: 438,
                4: 388, 5: 338, 6: 288,
                7: 238, 8: 188, 9: 138,
                10: 88
                }

        # --------> Title screen.
        if symbol == pyglet.window.key.ENTER and self.title_screen:
            self.clear()
            self.map_selector()

        # --------> Map selection
        elif symbol == pyglet.window.key.ENTER and self.map_selection:
            # --------> Checks which map was selected and what diff it is.
            if self.indicator.y == 538:
                self.selected.append("maps/easy/01_linear_path.txt")
                self.easy_map = True
            elif self.indicator.y == 488:
                self.selected.append("maps/easy/02_simple_fork.txt")
                self.easy_map = True
            elif self.indicator.y == 438:
                self.selected.append("maps/easy/03_basic_capacity.txt")
                self.easy_map = True
            elif self.indicator.y == 388:
                self.selected.append("maps/medium/01_dead_end_trap.txt")
                self.medium_map = True
            elif self.indicator.y == 338:
                self.selected.append("maps/medium/02_circular_loop.txt")
                self.medium_map = True
            elif self.indicator.y == 288:
                self.selected.append("maps/medium/03_priority_puzzle.txt")
                self.medium_map = True
            elif self.indicator.y == 238:
                self.selected.append("maps/hard/01_maze_nightmare.txt")
                self.hard_map = True
            elif self.indicator.y == 188:
                self.selected.append("maps/hard/02_capacity_hell.txt")
                self.hard_map = True
            elif self.indicator.y == 138:
                self.selected.append("maps/hard/03_ultimate_challenge.txt")
                self.hard_map = True
            else:
                self.selected.append(
                        "maps/challenger/01_the_impossible_dream.txt"
                        )
                self.challenger_map = True

            # --------> Deletes all Label objects + indicator from screen.
            for label in self.selection_labels:
                label.delete()
            self.selection_labels.clear()

            # --------> Transitions into the actual map scene.
            self.map_selection = False
            self.create_map()

        # --------> Custom map selection.
        elif symbol == pyglet.window.key.ENTER and self.custom_map_select:
            # --------> Checks which map was selected.
            for idx, file in list(enumerate(self.files)):
                if idx_dict[idx + 1] == self.indicator2.y:
                    self.selected.append("maps/custom/" + file)

            # --------> Deletes all Label objects + indicator from screen.
            for label in self.selection_labels:
                label.delete()
            self.selection_labels.clear()

            # --------> Transitions into the actual map scene.
            self.custom_map_select = False
            self.custom_map = True
            self.create_map()

        # --------> Allowed exits.
        if symbol == pyglet.window.key.ESCAPE and self.map_selection:
            pyglet.app.exit()

        elif symbol == pyglet.window.key.ESCAPE and self.title_screen:
            pyglet.app.exit()

        elif symbol == pyglet.window.key.ESCAPE and self.error_encounter:
            pyglet.app.exit()

        elif symbol == pyglet.window.key.ESCAPE and self.in_map:
            pyglet.app.exit()

        elif symbol == pyglet.window.key.ESCAPE and self.manual_mode:
            self.turn_counter = 0
            self.going_back = False
            for drone in self.drones_list:
                drone.i = 0
                drone.arrived = False
                self.teleport_drone(drone, self.zones_list[0].name, False)
            self.manual_mode = False
            if self.info_toggle:
                self.info_toggle = False
                self.info.clear()
                pyglet.clock.unschedule(self.update_info)
                self.info_display.clear()
            self.in_map = True
            self.instruction.text = "- Space: Simulate | S: Showcase Mode -"
            self.simulation['turn'].text = f"Turn {self.turn_counter}"

        elif symbol == pyglet.window.key.ESCAPE and self.custom_map_select:
            for label in self.selection_labels:
                label.delete()
            self.selection_labels.clear()
            self.custom_map_select = False
            self.map_selector()
            self.custom_len = 0

        elif symbol == pyglet.window.key.ESCAPE and self.overviewing:
            pyglet.app.exit()

        elif symbol == pyglet.window.key.ESCAPE and self.unsolvable:
            pyglet.app.exit()

        # --------> Map selection navigating down.
        if symbol == pyglet.window.key.DOWN and self.map_selection:
            if self.indicator.y > 88:
                self.indicator.y -= 50

        # --------> Custom map selection navigating down.
        elif symbol == pyglet.window.key.DOWN and self.custom_map_select:
            try:
                if self.indicator2.y > idx_dict[self.custom_len]:
                    self.indicator2.y -= 50
            except KeyError:
                pass

        # --------> Map selection navigating up.
        if symbol == pyglet.window.key.UP and self.map_selection:
            if self.indicator.y < 538:
                self.indicator.y += 50

        # --------> Custom map selection navigating up.
        elif symbol == pyglet.window.key.UP and self.custom_map_select:
            if self.indicator2.y < 538:
                self.indicator2.y += 50

        # --------> Transitions into custom map selection.
        if symbol == pyglet.window.key.C and self.map_selection:
            # --------> Transitions simulation state to custom map selection.
            self.custom_map_select = True
            self.map_selection = False

            # --------> Deletes the labels and initial indicator from screen.
            for label in self.selection_labels:
                label.delete()
            self.selection_labels.clear()
            self.selected.clear()

            # ---------> Scene setup
            self.custom_maps = pyglet.text.Label(
                    'Custom Maps:', font_name='Minecraft',
                    font_size=24, x=8, y=self.height,
                    anchor_x='left', anchor_y='top',
                    batch=self.title_batch, group=self.title_fg,
                    color=self.colors['yellow']
                    )

            self.ccontrols = pyglet.text.Label(
                    'Controls: - Arrow Keys: Navigation '
                    + '| Escape: Back -',
                    font_name='Minecraft', font_size=12,
                    x=self.width//2, y=30, color=self.colors['yellow'],
                    anchor_x='center', anchor_y='bottom',
                    batch=self.title_batch, group=self.title_fg
                    )

            self.selection_labels.append(self.custom_maps)
            self.selection_labels.append(self.ccontrols)

            # --------> Grabs map file names from the directory
            custom = "./maps/custom/"
            self.files: list[str] = os.listdir(custom)
            self.custom_len += len(self.files)
            idx = 1

            # ===========> Initial y coordinate.
            y_coordinate = self.height - 50

            # =============> Dispalys the first 10 maps on screen.
            for file in self.files:
                if idx <= 10:
                    label = pyglet.text.Label(
                            f"0{idx} - {file.capitalize()}",
                            font_name='Minecraft', font_size=24,
                            x=60, y=y_coordinate, anchor_x='left',
                            anchor_y='top', batch=self.title_batch,
                            group=self.title_fg
                            )
                    self.selection_labels.append(label)
                    idx += 1
                    y_coordinate -= 50
                else:
                    break

            # --------> New indicator for custom maps.
            self.indicator2: Any = pyglet.shapes.Triangle(
                    x=25, y=self.height - 62,
                    x2=40, y2=self.height - 70,
                    x3=25, y3=self.height - 78,
                    color=(253, 235, 0, 200), batch=self.title_batch,
                    group=self.title_fg
                    )

            self.selection_labels.append(self.indicator2)

        # ---------> Transitions into the simulation state.
        if symbol == pyglet.window.key.SPACE and self.in_map:
            # --------> Goes from simply viewing the map to animating it.
            self.in_map = False
            self.simulating = True
            self.instruction.delete()

            # --------> If map is solved self.max_turns will not be None.
            if self.max_turns is not None:
                self.start_sim()
            else:
                self.game_over()

        # ---------> Makes sure you Space does nothing after the first time.
        elif symbol == pyglet.window.key.SPACE and self.simulating:
            pass

        # ---------> Transitions into the overview state.
        elif symbol == pyglet.window.key.SPACE and self.sim_over:
            self.sim_over = False
            self.overviewing = True
            self.start_overview()

        # ---------> Manual mode attempt.
        # ---------> Enters Manual mode.
        if symbol == pyglet.window.key.S and self.in_map:
            if self.max_turns is None:
                self.in_map = False
                self.instruction.delete()
                self.game_over()
            else:
                self.in_map = False
                self.manual_mode = True
                self.instruction.delete()
                for drone in self.drones_list:
                    if self.expansion_counter == 0:
                        drone.expand_path(drone.path)
                if self.expansion_counter == 0:
                    self.expansion_counter += 1
                self.instruction = pyglet.text.Label(
                        '- A: Previous Move | D: Next Move | I: Toggle Info -',
                        font_name='Minecraft', font_size=14,
                        anchor_x='center', anchor_y='bottom', y=30,
                        x=self.width / 2, color=self.colors['yellow'],
                        group=self.title_fg, batch=self.title_batch
                        )
                self.manual_path()

        # ---------> Handles moving drones forward.
        if symbol == pyglet.window.key.D and self.manual_mode:
            self.going_back = False
            for drone in self.drones_list:
                next_i = drone.i + 1
                if next_i >= len(drone.man_anim_path):
                    continue
                target_zone = drone.man_anim_path[next_i]
                self.teleport_drone(drone, target_zone, self.going_back)
                drone.i += 1

            if isinstance(self.max_turns, int):
                max_turns: int = self.max_turns
            if self.turn_counter < max_turns:
                self.next_turn()

        # ---------> Handles moving drones backwards.
        if symbol == pyglet.window.key.A and self.manual_mode:
            self.going_back = True
            for drone in self.drones_list:
                prev_i = drone.i - 1
                if prev_i < 0:
                    continue
                target_zone = drone.man_anim_path[prev_i]
                self.teleport_drone(drone, target_zone, self.going_back)
                drone.i -= 1

            if self.turn_counter > 0:
                self.prev_turn()

        # ---------> Outputs zone & connection information in manual_mode.
        if symbol == pyglet.window.key.I and self.manual_mode:
            if not self.info_toggle:
                self.info_toggle = True
                pyglet.clock.schedule_interval(self.update_info, 1/2)
            else:
                self.info_toggle = False
                pyglet.clock.unschedule(self.update_info)
                self.info_display.clear()

        # ---------> Restarts relevant vars, goes back to map select.
        if symbol == pyglet.window.key.M and self.overviewing:
            # --------> Restart bools.
            self.overviewing = False
            self.easy_map = False
            self.medium_map = False
            self.hard_map = False
            self.custom_map = False
            self.challenger_map = False
            self.expansion_counter = 0
            self.info.clear()

            # --------> Title screen.
            self.sprite = pyglet.sprite.Sprite(
                    img=self.anim,
                    batch=self.title_batch, group=self.title_bg
                    )
            self.sprite.scale_x = 1.6
            self.sprite.scale_y = 1.36

            # --------> Deletes overview screen and restarts overview vars.
            self.overview_screen.delete()
            self.overview = ""
            self.p_counter = 0
            for text in self.overview_labels:
                text.delete()

            # --------> Fires up the initial map selection.
            self.map_selector()

        # --------> Restarts relevant vars, goes back to map select.
        elif symbol == pyglet.window.key.M and self.unsolvable:
            # --------> Restart bools.
            self.unsolvable = False
            self.easy_map = False
            self.medium_map = False
            self.hard_map = False
            self.custom_map = False
            self.challenger_map = False
            self.expansion_counter = 0

            # --------> Title screen.
            self.sprite = pyglet.sprite.Sprite(
                    img=self.anim,
                    batch=self.title_batch, group=self.title_bg
                    )
            self.sprite.scale_x = 1.6
            self.sprite.scale_y = 1.36

            # --------> Deletes overview screen and restarts overview vars.
            self.overview_screen.delete()
            self.overview = ""
            for text in self.unsolvable_labels:
                text.delete()
            self.map_selector()

        # ---------> Prints drone paths once when overviewing.
        if (symbol == pyglet.window.key.P
                and (self.overviewing and self.p_counter == 0)):
            self.test: list[str] = []
            for drone in self.drones_list:
                for zone, turn in iter(drone.path):
                    if zone != "start":
                        print(f"turn {turn}: {drone.d_id} ---> {zone}")
                print('')

            self.p_counter += 1

    def create_map(self) -> None:
        """
        This method creates the map scene if the parsed file is valid.
        Otherwise it creates an error scene listing all the possible errors
        it encountered.
        """
        # --------> Try-Except block prevents a crash
        # --------> When pressing ENTER in custom maps
        # --------> When no files are in the custom folder
        try:
            target = self.selected[0]
        except IndexError:
            target = "Custom map"
        self.result = parse(target)

        # --------> Parsing returns a string of errors or a dictionary
        # --------> Parsing file is fully documented if you want to see
        # --------> How that works
        if isinstance(self.result, str):
            # --------> Error(s) encountered -> Error screen
            self.error_encounter = True
            self.sprite.delete()
            self.err_anm = pyglet.resource.animation('error.gif')
            self.err_spr = pyglet.sprite.Sprite(
                    img=self.err_anm, batch=self.title_batch,
                    group=self.title_bg
                    )
            self.err_spr.scale_x = 4
            self.err_spr.scale_y = 3
            self.errors = pyglet.text.Label(
                    self.result, font_name='Minecraft',
                    font_size=18, x=0,
                    y=self.height, anchor_x='left',
                    anchor_y='top', batch=self.title_batch,
                    group=self.title_fg, multiline=True,
                    width=self.width-18
                    )
        else:
            # -------> No errors encountered -> Map scene creation
            self.in_map = True

            self.sprite.delete()
            if self.easy_map:
                self.map_bg_anim = pyglet.resource.animation(
                        'in_level_easy.gif'
                        )
            elif self.medium_map:
                self.map_bg_anim = pyglet.resource.animation(
                        'in_level_medium.gif'
                        )
            elif self.hard_map:
                self.map_bg_anim = pyglet.resource.animation(
                        'in_level_hard.gif'
                        )
            elif self.challenger_map:
                self.map_bg_anim = pyglet.resource.animation(
                        'in_level_challenger.gif'
                        )
            else:
                self.map_bg_anim = pyglet.resource.animation(
                        'in_level_custom.gif'
                        )
            self.map_spr = pyglet.sprite.Sprite(
                    img=self.map_bg_anim, batch=self.title_batch,
                    group=self.title_bg
                    )

            self.map_spr.scale_x = 4
            self.map_spr.scale_y = 3

            # -------> We use the SetupFactory class which is documented
            # -------> To create a list of Drone and Zone classes
            setup = SetupFactory(self.result)
            self.drones_list = setup.create_drones()
            self.zones_list = setup.create_zones()

            # -------> We then use the Pathfinder class to solve the map
            # -------> We also use it to determine the maximum turns used
            self.pathfinder = Pathfinder(self.drones_list, self.zones_list)
            self.pathfinder.solve()
            self.max_turns = self.pathfinder.benchmark

            # -------> Finally we create the graph and drones (graphically)
            # -------> As well as the overlay (turn counter and total drones)
            self.create_graph()
            self.create_drones()
            self.simulation_overlay()

    def create_graph(self) -> None:
        """
        This method is used to create
        the graph network in visual form.
        It will add zone, connection and drone
        visual representations into their Groups and Batches.
        """
        self.shapes = {}
        self.line_shapes = []
        self.outlines: list = []

        # --------> Make a simple circle for a zone and the outline
        for zone in self.zones_list:
            self.outlines.append(
                    pyglet.shapes.Circle(
                        x=20 + (zone.x) * (self.width / 24),
                        y=(self.height // 2) + (zone.y * self.height // 10),
                        radius=12.5, batch=self.graph, group=self.zones,
                    )
                )

            self.shapes[zone.name] = pyglet.shapes.Circle(
                        x=20 + (zone.x) * (self.width / 24),
                        y=(self.height // 2) + (zone.y * self.height // 10),
                        radius=10, batch=self.graph, group=self.zones,
                        color=self.colors[zone.color]
                    )

        # --------> Center the entire graph network
        # --------> Using simple math, we find the median point of the graph
        # --------> Assuming that the lowest x coordinate is start
        # --------> And highest is end (true for all provided maps)
        # --------> We then project the points into their centered position
        # --------> By shifting them in the x axis.
        start_x = self.shapes[self.zones_list[0].name].x
        end_x = self.shapes[self.zones_list[-1].name].x

        median = ((end_x - start_x) // 2) + start_x
        offset = self.width // 2 - median
        out_start_x = self.outlines[0].x
        out_end_x = self.outlines[-1].x
        out_median = ((out_end_x - out_start_x) // 2) + out_start_x
        out_offset = self.width // 2 - out_median

        for shape in self.shapes.values():
            shape.x += offset

        for outline in self.outlines:
            outline.x += out_offset

        # --------> Label each zone with a P, R, B or N depending on its type.
        for zone in self.zones_list:
            if zone.zone_type == 'priority':
                self.outlines.append(pyglet.text.Label(
                        'P',
                        x=self.shapes[zone.name].x - 2.5,
                        y=self.shapes[zone.name].y - 4,
                        font_name='Minecraft', font_size=9,
                        batch=self.graph, group=self.zones
                        )
                    )
            elif zone.zone_type == 'restricted':
                self.outlines.append(pyglet.text.Label(
                        'R',
                        x=self.shapes[zone.name].x - 3.5,
                        y=self.shapes[zone.name].y - 4,
                        font_name='Minecraft', font_size=9,
                        batch=self.graph, group=self.zones
                        )
                    )
            elif zone.zone_type == 'blocked':
                self.outlines.append(pyglet.text.Label(
                        'B',
                        x=self.shapes[zone.name].x - 3.5,
                        y=self.shapes[zone.name].y - 4,
                        font_name='Minecraft', font_size=9,
                        batch=self.graph, group=self.zones
                        )
                    )
            else:
                self.outlines.append(pyglet.text.Label(
                        'N',
                        x=self.shapes[zone.name].x - 3.5,
                        y=self.shapes[zone.name].y - 4,
                        font_name='Minecraft', font_size=9,
                        batch=self.graph, group=self.zones
                        )
                    )

            # -------> Render the connections
            for connection, capacity in zone.connected_to:
                self.line_shapes.append(
                        pyglet.shapes.Line(
                            x=self.shapes[zone.name].x,
                            y=self.shapes[zone.name].y,
                            x2=self.shapes[connection].x,
                            y2=self.shapes[connection].y, thickness=3,
                            batch=self.graph, group=self.lines,
                            color=(20, 40, 16)
                            )
                        )

            # -------> Specifically if there's a color=rainbow metadata tag
            for zone in self.zones_list:
                self.animate_rainbow(zone)

    def animate_rainbow(self, zone: Any) -> None:
        """
        This method simply renders a rainbow colored circle
        """
        step = list(reversed(range(1, 6)))
        colors = ['orange', 'yellow', 'green', 'blue', 'purple', 'violet']
        if zone.color == 'rainbow':
            for i in step:
                self.outlines.append(
                        pyglet.shapes.Circle(
                            x=self.shapes[zone.name].x,
                            y=self.shapes[zone.name].y,
                            radius=1.43 * i, batch=self.graph,
                            group=self.zones,
                            color=self.colors[colors[i - 1]]
                        )
                    )
        else:
            pass

    def create_drones(self) -> None:
        """
        This method simply renders the drones
        on the start zone.
        """
        self.aliens = {}
        alien = pyglet.resource.animation('drone.gif')
        for drone in self.drones_list:
            self.aliens[drone.d_id] = pyglet.sprite.Sprite(
                    alien, batch=self.graph, group=self.drones,
                    x=self.shapes[self.zones_list[0].name].x - 13,
                    y=self.shapes[self.zones_list[0].name].y - 9
                    )
            self.aliens[drone.d_id].scale_x = 1/14
            self.aliens[drone.d_id].scale_y = 1/14

    def simulation_overlay(self) -> None:
        """
        This method simply displays an overlay
        with a turn counter and the number of drones
        """
        self.simulation = {}
        self.turn_counter = 0
        self.simulation['turn'] = pyglet.text.Label(
                f'Turn {self.turn_counter}',
                x=self.width - 10, y=self.height,
                anchor_x='right', anchor_y='top',
                font_name='Minecraft', font_size=16,
                batch=self.graph, group=self.title_fg,
                color=self.colors['yellow']
                )

        total_drones = len(self.drones_list)
        self.simulation['nb_drones'] = pyglet.text.Label(
               f'Nb_drones: {total_drones}',
               x=10, y=self.height,
               anchor_x='left', anchor_y='top',
               font_name='Minecraft', font_size=16,
               batch=self.graph, group=self.title_fg,
               color=self.colors['yellow']
               )

        self.instruction = pyglet.text.Label(
                '- Space: Simulate | S: Showcase Mode -',
                font_name='Minecraft', font_size=14,
                anchor_x='center', anchor_y='bottom',
                y=30, x=self.width / 2,
                batch=self.graph, group=self.zones,
                color=self.colors['yellow']
                )

    def next_turn(self) -> None:
        """
        This method simply visually increases the turn counter by one
        """
        self.simulation['turn'].delete()
        self.turn_counter += 1
        self.simulation['turn'] = pyglet.text.Label(
                f'Turn {self.turn_counter}',
                x=self.width - 10, y=self.height,
                anchor_x='right', anchor_y='top',
                font_name='Minecraft', font_size=16,
                batch=self.graph, group=self.title_fg,
                color=self.colors['yellow']
                )

    def start_sim(self) -> None:
        """
        This method resets drone conditions and then
        calls the next turn processing.
        """
        for drone in self.drones_list:
            drone.i = 0
            drone.arrived = False
            if self.expansion_counter == 0:
                drone.expand_path(drone.path)
        if self.expansion_counter == 0:
            self.expansion_counter += 1

        self.process_next_turn()

    def process_next_turn(self) -> None:
        """
        This method checks pending animations
        if no pending animations remain and all drones
        have arrived we stop the simulation.
        Else we keep going until they arrive.
        """
        # ------> We make sure that pending animations are 0
        self.pending_animations = 0

        # ------> We check if each drone has arrived (by checking the next idx)
        # ------> Otherwise we schedule an animation towards the next zone
        for drone in self.drones_list:
            if drone.arrived:
                continue
            next_i = drone.i + 1
            if next_i >= len(drone.anim_path):
                drone.arrived = True
                continue
            self.pending_animations += 1
            target_zone = drone.anim_path[next_i]
            self.schedule_animation(drone, target_zone)

        # ------> Every time we have no pending animations
        # ------> We check if the drones arrived or not
        # ------> If they did we transition into the next state (sim_over)
        if self.pending_animations == 0:
            if all(drone.arrived for drone in self.drones_list):
                self.simulating = False
                self.sim_over = True
                self.simulation['done'] = pyglet.text.Label(
                        'Simulation over!',
                        x=self.width / 2, y=30,
                        font_name='Minecraft', font_size=16,
                        anchor_x='center', anchor_y='bottom',
                        batch=self.graph, group=self.zones,
                        color=self.colors['yellow']
                        )
                self.simulation['instruction'] = pyglet.text.Label(
                        '- Press Space to proceed! -',
                        x=self.width / 2, y=8,
                        font_name='Minecraft', font_size=14,
                        anchor_x='center', anchor_y='bottom',
                        batch=self.graph, group=self.zones,
                        color=self.colors['yellow']
                        )
                return
            else:
                pass

    def schedule_animation(self, drone: Any, target_zone: str) -> None:
        """
        This method schedules animations per drone
        to a target zone.
        """
        def animation_done() -> None:
            """
            This inner function serves as a callback func
            that signals an animation is over.
            It then calls the process_next_turn method and move_drone method
            to start the next sequence of animations recursively
            """
            drone.i += 1
            self.pending_animations -= 1
            if self.pending_animations == 0:
                self.next_turn()
                pyglet.clock.schedule_once(
                        lambda dt: self.process_next_turn(), 0.1
                        )

        self.move_drone(drone, target_zone, animation_done)

    def move_drone(
            self, drone: Any, target_zone: str, callback: Any = None
            ) -> None:
        """
        This method simply calculates the distance of a drone
        from the target_zone, once it does that it checks if the drone
        has arrived and calls the next sequence of animations for it.
        """
        start_x = self.aliens[drone.d_id].x
        start_y = self.aliens[drone.d_id].y

        # ------> Specifically for restricted zones
        if len(target_zone.split('-')) == 2:
            ex = (self.shapes[target_zone.split('-')[1]].x - 13)
            ey = (self.shapes[target_zone.split('-')[1]].y - 9)

            # ------> Basic mathematics to find the medium point coords
            mx = self.aliens[drone.d_id].x + ex
            mx /= 2
            my = self.aliens[drone.d_id].y + ey
            my /= 2

            end_x = mx
            end_y = my
        else:
            end_x = self.shapes[target_zone].x - 13
            end_y = self.shapes[target_zone].y - 9

        # -------> Directional unit vectors.
        dx = end_x - start_x
        dy = end_y - start_y

        # -------> Basic euclidian mathematics to find the dist between 2 pts.
        total_distance = math.sqrt(dx ** 2 + dy ** 2)
        if total_distance < 2:
            self.aliens[drone.d_id].x = end_x
            self.aliens[drone.d_id].y = end_y
            if callback:
                callback()
            return

        def update(dt: float) -> None:
            """
            This inner function uses the calculations
            from the outer function (move_drone) to
            actually animate the drone moving towards
            the destination.
            It does so at a static rate of 250 per time unit
            (in this case dt)
            """
            nonlocal dx, dy, total_distance
            pixels_per_dt = 250 * dt
            if pixels_per_dt >= total_distance:
                self.aliens[drone.d_id].x = end_x
                self.aliens[drone.d_id].y = end_y
                pyglet.clock.unschedule(update)
                if callback:
                    callback()
                return

            ratio = pixels_per_dt / total_distance

            self.aliens[drone.d_id].x += dx * ratio
            self.aliens[drone.d_id].y += dy * ratio

            dx = end_x - self.aliens[drone.d_id].x
            dy = end_y - self.aliens[drone.d_id].y

            total_distance = math.sqrt(dx ** 2 + dy ** 2)

        # ------> we schedule update to be called every 60th of a sec
        pyglet.clock.schedule_interval(update, 1/60)

    def start_overview(self) -> None:
        """
        This method simply renders the overview phase
        """
        # -------> Prepping the overview screen.
        self.overview_anim = pyglet.resource.animation('output.gif')
        self.overview_screen = pyglet.sprite.Sprite(
                self.overview_anim, group=self.title_bg,
                batch=self.title_batch
                )
        self.overview_screen.scale_x *= 4
        self.overview_screen.scale_y *= 3

        # --------> Deleting artifacts from last step
        self.map_spr.delete()
        for outline in self.outlines:
            outline.delete()
        for zone in self.zones_list:
            self.shapes[zone.name].delete()
        for line in self.line_shapes:
            line.delete()
        for drone in self.drones_list:
            self.aliens[drone.d_id].delete()
        self.simulation['turn'].delete()
        self.simulation['nb_drones'].delete()
        self.simulation['done'].delete()
        self.simulation['instruction'].delete()

        # --------> Setting up overview labels and stats
        self.overview_labels = []
        self.overview_labels.append(
                pyglet.text.Label(
                    'Map Cleared!', font_name='Minecraft',
                    font_size=24, x=20, y=self.height - 10,
                    anchor_x='left', anchor_y='top',
                    group=self.title_fg, batch=self.title_batch,
                    color=self.colors['yellow']
                    )
                )
        self.overview_labels.append(
                pyglet.text.Label(
                    'Overview:', font_name='Minecraft',
                    font_size=18, x=60, y=self.height - 54,
                    anchor_x='left', anchor_y='top',
                    group=self.title_fg, batch=self.title_batch,
                    color=self.colors['yellow']
                    )
                )
        self.overview += "\nTotal number of drones:"
        self.overview += f" {len(self.drones_list)}\n\n"
        self.overview += "Total number of zones:"
        self.overview += f" {len(self.zones_list)}\n\n"
        self.normals = [
                zone for zone in self.zones_list
                if zone.zone_type == 'normal'
                ]
        self.overview += "Total number of normal zones:"
        self.overview += f" {len(self.normals)}\n\n"
        self.prios = [
                zone for zone in self.zones_list
                if zone.zone_type == 'priority'
                ]
        self.overview += "Total number of priority zones:"
        self.overview += f" {len(self.prios)}\n\n"
        self.rests = [
                zone for zone in self.zones_list
                if zone.zone_type == 'restricted'
                ]
        self.overview += "Total number of restricted zones:"
        self.overview += f" {len(self.rests)}\n\n"
        self.blocks = [
                zone for zone in self.zones_list
                if zone.zone_type == 'blocked'
                ]
        self.overview += "Total number of blocked zones:"
        self.overview += f" {len(self.blocks)}\n\n"
        self.overview += f"Total number of turns: {self.max_turns}\n\n"
        self.overview_labels.append(
                pyglet.text.Label(
                    self.overview, font_name='Minecraft',
                    font_size=18, x=80, y=self.height - 82,
                    anchor_x='left', anchor_y='top',
                    group=self.title_fg, batch=self.title_batch,
                    multiline=True, width=640
                    )
                )
        self.overview_labels.append(
                pyglet.text.Label(
                    "- Escape: Exit | M: Map Selection | P: Print Paths-",
                    font_size=14, x=self.width / 2,
                    y=10, anchor_x='center', anchor_y='bottom',
                    font_name='Minecraft', group=self.title_fg,
                    batch=self.title_batch, color=self.colors['yellow']
                    )
                )

    def game_over(self) -> None:
        """
        This method is a simple game over screen
        that appears in case the map is unsolvable.
        """
        # -------> Changing simulation states.
        self.simulating = False
        self.unsolvable = True

        # -------> Setting up the game over scene
        self.overview_anim = pyglet.resource.animation('error.gif')
        self.overview_screen = pyglet.sprite.Sprite(
                self.overview_anim, group=self.title_bg,
                batch=self.title_batch
                )
        self.overview_screen.scale_x *= 4
        self.overview_screen.scale_y *= 3

        # ------> Deleting artifacts from last step
        self.map_spr.delete()
        for outline in self.outlines:
            outline.delete()
        for zone in self.zones_list:
            self.shapes[zone.name].delete()
        for line in self.line_shapes:
            line.delete()
        for drone in self.drones_list:
            self.aliens[drone.d_id].delete()
        self.simulation['turn'].delete()
        self.simulation['nb_drones'].delete()

        # -------> Setting up game over labels and stats.
        self.unsolvable_labels = []
        self.unsolvable_labels.append(
                pyglet.text.Label(
                    "Lost in space...",
                    font_name='Minecraft', font_size=24,
                    x=20, y=self.height - 10,
                    anchor_x='left', anchor_y='top',
                    group=self.title_fg, batch=self.title_batch,
                    color=self.colors['crimson']
                    )
                )
        self.unsolvable_labels.append(
                pyglet.text.Label(
                    "The map was unsolvable...",
                    font_name='Minecraft', font_size=18,
                    x=40, y=self.height - 54,
                    anchor_x='left', anchor_y='top',
                    group=self.title_fg, batch=self.title_batch,
                    color=self.colors['red']
                    )
                )

        self.overview += "\nTotal number of drones:"
        self.overview += f" {len(self.drones_list)}\n\n"
        self.overview += "Total number of zones:"
        self.overview += f" {len(self.zones_list)}\n\n"
        self.normals = [
                zone for zone in self.zones_list
                if zone.zone_type == 'normal'
                ]
        self.overview += "Total number of normal zones:"
        self.overview += f" {len(self.normals)}\n\n"
        self.prios = [
                zone for zone in self.zones_list
                if zone.zone_type == 'priority'
                ]
        self.overview += "Total number of priority zones:"
        self.overview += f" {len(self.prios)}\n\n"
        self.rests = [
                zone for zone in self.zones_list
                if zone.zone_type == 'restricted'
                ]
        self.overview += "Total number of restricted zones:"
        self.overview += f" {len(self.rests)}\n\n"
        self.blocks = [
                zone for zone in self.zones_list
                if zone.zone_type == 'blocked'
                ]
        self.overview += "Total number of blocked zones:"
        self.overview += f" {len(self.blocks)}\n\n"
        self.overview += "Total number of turns: Pathfinding failed...\n\n"
        self.unsolvable_labels.append(
                pyglet.text.Label(
                    self.overview, font_name='Minecraft',
                    font_size=18, x=80, y=self.height - 82,
                    anchor_x='left', anchor_y='top',
                    group=self.title_fg, batch=self.title_batch,
                    multiline=True, width=640
                    )
                )
        self.unsolvable_labels.append(
                pyglet.text.Label(
                    "- Escape: Exit | M: Map Selection -",
                    font_size=14, x=self.width / 2,
                    y=10, anchor_x='center', anchor_y='bottom',
                    font_name='Minecraft', group=self.title_fg,
                    batch=self.title_batch, color=self.colors['yellow']
                    )
                )

    def teleport_drone(
            self, drone: Any, target_zone: str, going_back: bool
            ) -> None:
        """
        A simple method that teleports a drone to a target zone.
        """
        if len(target_zone.split('-')) == 2:
            if going_back:
                ex = self.shapes[target_zone.split('-')[0]].x - 13
                ey = self.shapes[target_zone.split('-')[0]].y - 9
            else:
                ex = self.shapes[target_zone.split('-')[1]].x - 13
                ey = self.shapes[target_zone.split('-')[1]].y - 9

            end_x = (self.aliens[drone.d_id].x + ex) / 2
            end_y = (self.aliens[drone.d_id].y + ey) / 2
        else:
            end_x = self.shapes[target_zone].x - 13
            end_y = self.shapes[target_zone].y - 9

        self.aliens[drone.d_id].x = end_x
        self.aliens[drone.d_id].y = end_y

    def prev_turn(self) -> None:
        """
        This method simply visually increases the turn counter by one
        """
        self.simulation['turn'].delete()
        self.turn_counter -= 1
        self.simulation['turn'] = pyglet.text.Label(
                f'Turn {self.turn_counter}',
                x=self.width - 10, y=self.height,
                anchor_x='right', anchor_y='top',
                font_name='Minecraft', font_size=16,
                batch=self.graph, group=self.title_fg,
                color=self.colors['yellow']
                )

    def manual_path(self) -> None:
        """
        A simple method that sets up the manual showcase path.
        """
        for drone in self.drones_list:
            drone.man_anim_path = [entry for entry in drone.anim_path]
        last_d_len = len(self.drones_list[-1].man_anim_path)
        for drone in self.drones_list:
            while len(drone.man_anim_path) < last_d_len:
                drone.man_anim_path.append(self.zones_list[-1].name)

    def collect_info(self) -> None:
        for drone in self.drones_list:
            for move in drone.man_anim_path:
                self.info[move] = []
        for drone in self.drones_list:
            self.info[drone.man_anim_path[drone.i]] += [drone.d_id]

    def update_info(self, dt: float) -> None:
        """
        Wrapper method to schedule and unschedule
        collect_info() and display_info()
        """
        self.collect_info()
        self.display_info()

    def display_info(self, callback: bool = False) -> None:
        """
        This method renders current drone positions
        it checks if it was called and changes behaviours
        """
        if callback:
            self.info_display.clear()
        for position, drones in self.info.items():
            drones_str = " ".join(drones)
            if len(position.split('-')) != 2:
                self.info_display.append(
                        pyglet.text.Label(
                            drones_str, font_name='Minecraft', font_size=8,
                            x=self.shapes[position].x - 5,
                            y=self.shapes[position].y - 25, batch=self.graph,
                            group=self.info_group, multiline=True, width=2
                            )
                        )
            else:
                point1 = self.shapes[position.split('-')[0]]
                point2 = self.shapes[position.split('-')[1]]
                midpoint_x = ((point1.x + point2.x) / 2) - 3
                midpoint_y = ((point1.y + point2.y) / 2) - 5
                self.info_display.append(
                        pyglet.text.Label(
                            drones_str, font_name='Minecraft', font_size=8,
                            x=midpoint_x, y=midpoint_y, batch=self.graph,
                            group=self.info_group, multiline=True, width=5,
                            color=self.colors['orange']
                            )
                        )
        if not callback:
            callback = True
            self.display_info(callback)

    @staticmethod
    def run() -> None:
        """
        This method starts the main event handler and renders our window.
        """
        pyglet.app.run()
