from __future__ import annotations

from collections import deque
import heapq
import math
import random
from dataclasses import dataclass
from typing import Callable, Generator, Optional

try:
    import pygame
except ImportError as exc:
    raise SystemExit(
        "pygame is required. Install dependencies with: pip install -r requirements.txt"
    ) from exc


DEFAULT_GRID_WIDTH = 100
DEFAULT_GRID_HEIGHT = 100
MIN_GRID_DIMENSION = 2
MAX_GRID_DIMENSION = 500
PANEL_WIDTH = 360
WINDOW_DEFAULT_WIDTH = 1180
WINDOW_DEFAULT_HEIGHT = 820
WINDOW_MIN_WIDTH = 900
WINDOW_MIN_HEIGHT = 820
WINDOW_SCREEN_MARGIN_X = 0
WINDOW_SCREEN_MARGIN_Y = 80
WINDOW_FLAGS = pygame.RESIZABLE
FPS = 60

GRID_PADDING = 16
GRID_LINE_THRESHOLD = 6.0

ALGORITHM_HEADER_Y = 44
ALGORITHM_BUTTON_ROWS = (72, 118)
EDIT_HEADER_Y = 168
EDIT_BUTTON_ROWS = (196, 240)
CONTROLS_HEADER_Y = 290
CONTROL_BUTTON_ROWS = (318, 360, 402)
SPEED_HEADER_Y = 446
SPEED_BUTTON_Y = 470

MAZE_ALGORITHMS = ("Recursive Division", "DFS Backtracker")

MOVE_STRAIGHT = 1.0
MOVE_DIAGONAL = math.sqrt(2.0)

BACKGROUND_COLOR = (243, 240, 233)
GRID_LINE_COLOR = (214, 209, 197)
EMPTY_COLOR = (250, 248, 242)
OBSTACLE_COLOR = (45, 55, 72)
START_COLOR = (47, 133, 90)
GOAL_COLOR = (192, 57, 43)
OPEN_COLOR = (255, 214, 102)
CLOSED_COLOR = (78, 140, 255)
CURRENT_COLOR = (255, 120, 90)
PATH_COLOR = (155, 89, 182)
PANEL_COLOR = (24, 34, 52)
PANEL_SECTION_COLOR = (58, 79, 110)
BUTTON_COLOR = (241, 196, 85)
BUTTON_HOVER_COLOR = (249, 211, 113)
BUTTON_ACTIVE_COLOR = (104, 190, 140)
BUTTON_TEXT_COLOR = (27, 31, 38)
TEXT_COLOR = (235, 239, 245)
MUTED_TEXT_COLOR = (180, 192, 210)

Cell = tuple[int, int]


@dataclass
class SearchFrame:
    open_cells: set[Cell]
    closed_cells: set[Cell]
    current_cell: Optional[Cell]
    path_cells: list[Cell]
    visited_count: int
    path_cost: Optional[float]
    done: bool
    found: bool
    message: str


@dataclass
class MazeFrame:
    obstacle_count: int
    done: bool
    message: str
    changed_cells: tuple[Cell, ...] = ()
    full_redraw: bool = False


@dataclass
class Button:
    label: str
    rect: pygame.Rect
    action: Callable[[], None]
    kind: str = ""
    value: object = None


class PathfinderApp:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Pathfinding Visualizer")

        self.grid_width = DEFAULT_GRID_WIDTH
        self.grid_height = DEFAULT_GRID_HEIGHT

        self.screen = pygame.display.set_mode(self.get_default_window_size(), WINDOW_FLAGS)
        self.window_size = self.screen.get_size()
        self.clock = pygame.time.Clock()

        self.title_font = pygame.font.SysFont("consolas", 28, bold=True)
        self.section_font = pygame.font.SysFont("consolas", 20, bold=True)
        self.text_font = pygame.font.SysFont("consolas", 16)
        self.small_font = pygame.font.SysFont("consolas", 14)

        self.selected_algorithm = "A*"
        self.selected_maze_algorithm = "DFS Backtracker"
        self.edit_mode = "obstacle"
        self.steps_per_frame = 4

        self.start_cell: Optional[Cell] = None
        self.goal_cell: Optional[Cell] = None
        self.obstacles: set[Cell] = set()

        self.open_cells: set[Cell] = set()
        self.closed_cells: set[Cell] = set()
        self.current_cell: Optional[Cell] = None
        self.path_cells: list[Cell] = []
        self.path_lookup: set[Cell] = set()
        self.visited_count = 0
        self.path_cost: Optional[float] = None

        self.search_generator: Optional[Generator[SearchFrame, None, None]] = None
        self.maze_generator: Optional[Generator[MazeFrame, None, None]] = None
        self.search_paused = False
        self.status_message = "Place start, goal, and obstacles. Then press Run."

        self.drag_button: Optional[int] = None
        self.last_drag_cell: Optional[Cell] = None

        self.grid_surface = pygame.Surface((1, 1)).convert()
        self.grid_surface_dirty = True
        self.grid_dirty_cells: set[Cell] = set()
        self.scaled_grid_surface: Optional[pygame.Surface] = None
        self.scaled_grid_size = (0, 0)
        self.rebuild_grid_surface()

        self.buttons: list[Button] = []
        self._build_buttons()

    def _build_buttons(self) -> None:
        panel_rect = self.get_panel_rect()
        panel_left = panel_rect.x + 20
        content_width = max(0, panel_rect.width - 40)

        two_col_gap = 18
        row_height = 38
        three_col_gap = 10
        two_col_width = max(0, (content_width - two_col_gap) // 2)
        three_col_width = max(0, (content_width - 2 * three_col_gap) // 3)

        def rect_2col(row_y: int, column: int) -> pygame.Rect:
            return pygame.Rect(
                panel_left + column * (two_col_width + two_col_gap),
                row_y,
                two_col_width,
                row_height,
            )

        def rect_3col(row_y: int, column: int) -> pygame.Rect:
            return pygame.Rect(
                panel_left + column * (three_col_width + three_col_gap),
                row_y,
                three_col_width,
                row_height,
            )

        def rect_full(row_y: int) -> pygame.Rect:
            return pygame.Rect(panel_left, row_y, content_width, row_height)

        self.buttons = [
            Button(
                "A*",
                rect_3col(ALGORITHM_BUTTON_ROWS[0], 0),
                lambda: self.set_algorithm("A*"),
                "algorithm",
                "A*",
            ),
            Button(
                "Dijkstra",
                rect_3col(ALGORITHM_BUTTON_ROWS[0], 1),
                lambda: self.set_algorithm("Dijkstra"),
                "algorithm",
                "Dijkstra",
            ),
            Button(
                "BFS",
                rect_3col(ALGORITHM_BUTTON_ROWS[0], 2),
                lambda: self.set_algorithm("BFS"),
                "algorithm",
                "BFS",
            ),
            Button(
                "Greedy",
                rect_3col(ALGORITHM_BUTTON_ROWS[1], 0),
                lambda: self.set_algorithm("Greedy"),
                "algorithm",
                "Greedy",
            ),
            Button(
                "Bi-A*",
                rect_3col(ALGORITHM_BUTTON_ROWS[1], 1),
                lambda: self.set_algorithm("Bidirectional A*"),
                "algorithm",
                "Bidirectional A*",
            ),
            Button(
                "Obstacle",
                rect_2col(EDIT_BUTTON_ROWS[0], 0),
                lambda: self.set_edit_mode("obstacle"),
                "mode",
                "obstacle",
            ),
            Button(
                "Set Start",
                rect_2col(EDIT_BUTTON_ROWS[0], 1),
                lambda: self.set_edit_mode("start"),
                "mode",
                "start",
            ),
            Button(
                "Set Goal",
                rect_2col(EDIT_BUTTON_ROWS[1], 0),
                lambda: self.set_edit_mode("goal"),
                "mode",
                "goal",
            ),
            Button(
                "Erase",
                rect_2col(EDIT_BUTTON_ROWS[1], 1),
                lambda: self.set_edit_mode("erase"),
                "mode",
                "erase",
            ),
            Button("Run", rect_3col(CONTROL_BUTTON_ROWS[0], 0), self.start_search),
            Button("Pause", rect_3col(CONTROL_BUTTON_ROWS[0], 1), self.toggle_pause),
            Button("Maze", rect_3col(CONTROL_BUTTON_ROWS[0], 2), self.start_maze_generation),
            Button("Clear Path", rect_3col(CONTROL_BUTTON_ROWS[1], 0), self.clear_search_state),
            Button("Clear Map", rect_3col(CONTROL_BUTTON_ROWS[1], 1), self.clear_map),
            Button("Maze Type", rect_3col(CONTROL_BUTTON_ROWS[1], 2), self.toggle_maze_algorithm),
            Button("Grid Size", rect_full(CONTROL_BUTTON_ROWS[2]), self.prompt_grid_size),
            Button("Slow", rect_3col(SPEED_BUTTON_Y, 0), lambda: self.set_speed(1), "speed", 1),
            Button("Medium", rect_3col(SPEED_BUTTON_Y, 1), lambda: self.set_speed(4), "speed", 4),
            Button("Fast", rect_3col(SPEED_BUTTON_Y, 2), lambda: self.set_speed(16), "speed", 16),
        ]

    def get_default_window_size(self) -> tuple[int, int]:
        min_width, min_height, max_width, max_height = self.get_window_limits()
        return (
            max(min_width, min(WINDOW_DEFAULT_WIDTH, max_width)),
            max(min_height, min(WINDOW_DEFAULT_HEIGHT, max_height)),
        )

    def get_window_limits(self) -> tuple[int, int, int, int]:
        desktop_sizes = pygame.display.get_desktop_sizes()
        if desktop_sizes:
            display_width, display_height = desktop_sizes[0]
        else:
            display_info = pygame.display.Info()
            display_width = max(display_info.current_w, WINDOW_DEFAULT_WIDTH)
            display_height = max(display_info.current_h, WINDOW_DEFAULT_HEIGHT)

        max_width = max(PANEL_WIDTH + GRID_PADDING * 2 + 120, display_width - WINDOW_SCREEN_MARGIN_X)
        max_height = max(560, display_height - WINDOW_SCREEN_MARGIN_Y)
        min_width = min(WINDOW_MIN_WIDTH, max_width)
        min_height = min(WINDOW_MIN_HEIGHT, max_height)
        return min_width, min_height, max_width, max_height

    def get_panel_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.window_size[0] - PANEL_WIDTH,
            0,
            PANEL_WIDTH,
            self.window_size[1],
        )

    def get_grid_rect(self) -> pygame.Rect:
        panel_rect = self.get_panel_rect()
        available_width = max(1, panel_rect.left - GRID_PADDING * 2)
        available_height = max(1, self.window_size[1] - GRID_PADDING * 2)
        aspect_ratio = self.grid_width / self.grid_height

        grid_width = available_width
        grid_height = max(1, int(round(grid_width / aspect_ratio)))
        if grid_height > available_height:
            grid_height = available_height
            grid_width = max(1, int(round(grid_height * aspect_ratio)))

        grid_x = GRID_PADDING + (available_width - grid_width) // 2
        grid_y = GRID_PADDING + (available_height - grid_height) // 2
        return pygame.Rect(grid_x, grid_y, grid_width, grid_height)

    def cell_in_bounds(self, cell: Cell) -> bool:
        x, y = cell
        return 0 <= x < self.grid_width and 0 <= y < self.grid_height

    def clamp_grid_size(self, width: int, height: int) -> tuple[int, int]:
        return (
            max(MIN_GRID_DIMENSION, min(MAX_GRID_DIMENSION, width)),
            max(MIN_GRID_DIMENSION, min(MAX_GRID_DIMENSION, height)),
        )

    def parse_grid_dimension_text(self, raw_value: str) -> Optional[int]:
        normalized = raw_value.strip()
        if not normalized:
            return None
        if not normalized.isdigit():
            return None
        return int(normalized)

    def prompt_grid_size(self) -> None:
        if self.search_generator is not None or self.maze_generator is not None:
            self.status_message = "Finish the active animation before changing grid size."
            return

        try:
            import tkinter as tk
            from tkinter import simpledialog
        except ImportError:
            self.status_message = "Grid size prompt is unavailable in this environment."
            return

        class GridSizeDialog(simpledialog.Dialog):
            def __init__(self, parent: tk.Misc, width_value: int, height_value: int) -> None:
                self.width_value = str(width_value)
                self.height_value = str(height_value)
                self.result: Optional[tuple[str, str]] = None
                super().__init__(parent, title="Grid Size")

            def body(self, master: tk.Misc):
                tk.Label(
                    master,
                    text=(
                        f"Enter width and height separately.\n"
                        f"Allowed range per dimension: {MIN_GRID_DIMENSION} to {MAX_GRID_DIMENSION}."
                    ),
                    justify="left",
                    anchor="w",
                ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 8), sticky="w")

                tk.Label(master, text="Width").grid(row=1, column=0, padx=(10, 6), pady=4, sticky="e")
                tk.Label(master, text="Height").grid(row=2, column=0, padx=(10, 6), pady=4, sticky="e")

                self.width_entry = tk.Entry(master, width=12)
                self.height_entry = tk.Entry(master, width=12)
                self.width_entry.grid(row=1, column=1, padx=(0, 10), pady=4, sticky="w")
                self.height_entry.grid(row=2, column=1, padx=(0, 10), pady=(4, 10), sticky="w")

                self.width_entry.insert(0, self.width_value)
                self.height_entry.insert(0, self.height_value)
                return self.width_entry

            def apply(self) -> None:
                self.result = (
                    self.width_entry.get(),
                    self.height_entry.get(),
                )

        root: Optional[tk.Tk] = None
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            dialog = GridSizeDialog(
                root,
                self.grid_width,
                self.grid_height,
            )
        except tk.TclError:
            self.status_message = "Grid size prompt is unavailable in this environment."
            return
        finally:
            if root is not None:
                root.destroy()

        if dialog.result is None:
            self.status_message = "Grid size change cancelled."
            return

        width_text, height_text = dialog.result
        width_value = self.parse_grid_dimension_text(width_text)
        height_value = self.parse_grid_dimension_text(height_text)
        if width_value is None or height_value is None:
            self.status_message = "Invalid grid size. Enter width and height as whole numbers."
            return

        self.apply_grid_size(
            width_value,
            height_value,
            requested=(width_value, height_value),
        )

    def apply_grid_size(
        self,
        width: int,
        height: int,
        *,
        requested: Optional[tuple[int, int]] = None,
    ) -> None:
        requested_width, requested_height = requested or (width, height)
        width, height = self.clamp_grid_size(width, height)

        if (width, height) == (self.grid_width, self.grid_height):
            if (requested_width, requested_height) != (width, height):
                self.status_message = (
                    f"Grid size clamped from {requested_width}x{requested_height} "
                    f"to {width}x{height}. Map size unchanged."
                )
            else:
                self.status_message = f"Grid size unchanged: {width}x{height}."
            return

        self.search_generator = None
        self.maze_generator = None
        self.search_paused = False
        self.start_cell = None
        self.goal_cell = None
        self.obstacles.clear()
        self.open_cells = set()
        self.closed_cells = set()
        self.current_cell = None
        self.path_cells = []
        self.path_lookup = set()
        self.visited_count = 0
        self.path_cost = None
        self.drag_button = None
        self.last_drag_cell = None

        self.grid_width = width
        self.grid_height = height
        self.rebuild_grid_surface()
        self._build_buttons()

        if (requested_width, requested_height) != (width, height):
            self.status_message = (
                f"Grid size clamped from {requested_width}x{requested_height} "
                f"to {width}x{height}. Map reset."
            )
        else:
            self.status_message = f"Grid resized to {width}x{height}. Map reset."

    def invalidate_scaled_grid(self) -> None:
        self.scaled_grid_surface = None
        self.scaled_grid_size = (0, 0)

    def mark_full_grid_dirty(self) -> None:
        self.grid_surface_dirty = True
        self.grid_dirty_cells.clear()
        self.invalidate_scaled_grid()

    def rebuild_grid_surface(self) -> None:
        self.grid_surface = pygame.Surface((self.grid_width, self.grid_height)).convert()
        self.mark_full_grid_dirty()

    def refresh_cells(self, cells: set[Cell] | list[Cell] | tuple[Cell, ...]) -> None:
        changed = False
        for cell in cells:
            if self.cell_in_bounds(cell):
                self.grid_dirty_cells.add(cell)
                changed = True
        if changed:
            self.invalidate_scaled_grid()

    def get_cell_color(self, cell: Cell) -> tuple[int, int, int]:
        if cell == self.start_cell:
            return START_COLOR
        if cell == self.goal_cell:
            return GOAL_COLOR
        if cell in self.obstacles:
            return OBSTACLE_COLOR
        if cell == self.current_cell:
            return CURRENT_COLOR
        if cell in self.path_lookup:
            return PATH_COLOR
        if cell in self.closed_cells:
            return CLOSED_COLOR
        if cell in self.open_cells:
            return OPEN_COLOR
        return EMPTY_COLOR

    def _refresh_grid_surface(self) -> None:
        if self.grid_surface_dirty:
            self.grid_surface.fill(EMPTY_COLOR)
            for cell in self.obstacles:
                self.grid_surface.set_at(cell, OBSTACLE_COLOR)
            for cell in self.open_cells:
                self.grid_surface.set_at(cell, OPEN_COLOR)
            for cell in self.closed_cells:
                self.grid_surface.set_at(cell, CLOSED_COLOR)
            for cell in self.path_lookup:
                self.grid_surface.set_at(cell, PATH_COLOR)
            if self.current_cell is not None:
                self.grid_surface.set_at(self.current_cell, CURRENT_COLOR)
            if self.start_cell is not None:
                self.grid_surface.set_at(self.start_cell, START_COLOR)
            if self.goal_cell is not None:
                self.grid_surface.set_at(self.goal_cell, GOAL_COLOR)
            self.grid_surface_dirty = False
            self.grid_dirty_cells.clear()
            self.invalidate_scaled_grid()
            return

        if not self.grid_dirty_cells:
            return

        for cell in self.grid_dirty_cells:
            self.grid_surface.set_at(cell, self.get_cell_color(cell))
        self.grid_dirty_cells.clear()
        self.invalidate_scaled_grid()

    def set_algorithm(self, algorithm: str) -> None:
        if algorithm == self.selected_algorithm:
            return
        self.selected_algorithm = algorithm
        self.clear_search_state(silent=True)
        self.status_message = f"Algorithm switched to {algorithm}."

    def set_edit_mode(self, mode: str) -> None:
        self.edit_mode = mode
        self.status_message = f"Edit mode: {mode}."

    def toggle_maze_algorithm(self) -> None:
        if self.maze_generator is not None:
            self.status_message = "Finish or clear the current maze generation before switching maze algorithms."
            return
        current_index = MAZE_ALGORITHMS.index(self.selected_maze_algorithm)
        self.selected_maze_algorithm = MAZE_ALGORITHMS[(current_index + 1) % len(MAZE_ALGORITHMS)]
        self.status_message = f"Maze algorithm switched to {self.selected_maze_algorithm}."

    def set_speed(self, steps_per_frame: int) -> None:
        self.steps_per_frame = steps_per_frame
        labels = {1: "slow", 4: "medium", 16: "fast"}
        self.status_message = f"Animation speed set to {labels.get(steps_per_frame, steps_per_frame)}."

    def clear_search_overlay(self) -> None:
        dirty_cells = set(self.open_cells)
        dirty_cells.update(self.closed_cells)
        dirty_cells.update(self.path_lookup)
        if self.current_cell is not None:
            dirty_cells.add(self.current_cell)

        self.open_cells = set()
        self.closed_cells = set()
        self.current_cell = None
        self.path_cells = []
        self.path_lookup = set()
        self.visited_count = 0
        self.path_cost = None

        self.refresh_cells(dirty_cells)

    def clear_search_state(self, silent: bool = False) -> None:
        self.search_generator = None
        self.maze_generator = None
        self.search_paused = False
        self.clear_search_overlay()
        if not silent:
            self.status_message = "Visualization state cleared."

    def clear_map(self) -> None:
        dirty_cells = set(self.obstacles)
        if self.start_cell is not None:
            dirty_cells.add(self.start_cell)
        if self.goal_cell is not None:
            dirty_cells.add(self.goal_cell)

        self.start_cell = None
        self.goal_cell = None
        self.obstacles.clear()
        self.clear_search_state(silent=True)
        self.refresh_cells(dirty_cells)
        self.status_message = "Map cleared."

    def toggle_pause(self) -> None:
        if self.search_generator is None and self.maze_generator is None:
            self.status_message = "No active animation to pause."
            return
        self.search_paused = not self.search_paused
        active_label = (
            f"{self.selected_maze_algorithm} maze generation"
            if self.maze_generator is not None
            else self.selected_algorithm
        )
        if self.search_paused:
            self.status_message = f"{active_label} paused."
        else:
            self.status_message = f"{active_label} resumed."

    def start_search(self) -> None:
        if self.maze_generator is not None:
            self.status_message = "Finish or clear the maze generation before starting a search."
            return
        if self.start_cell is None or self.goal_cell is None:
            self.status_message = "Set both a start cell and a goal cell before running."
            return
        if self.start_cell == self.goal_cell:
            self.status_message = "Start and goal must be different cells."
            return
        self.clear_search_state(silent=True)
        self.search_generator = self.search_steps(self.selected_algorithm)
        self.search_paused = False
        self.status_message = f"Running {self.selected_algorithm}..."

    def start_maze_generation(self) -> None:
        dirty_cells = set(self.obstacles)
        self.clear_search_state(silent=True)
        self.obstacles.clear()
        self.refresh_cells(dirty_cells)
        self.maze_generator = self.maze_steps(self.selected_maze_algorithm)
        self.search_paused = False
        self.status_message = f"Generating maze with {self.selected_maze_algorithm}..."

    def run(self) -> None:
        running = True
        window_size_changed_event = getattr(pygame, "WINDOWSIZECHANGED", None)
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif window_size_changed_event is not None and event.type == window_size_changed_event:
                    self.handle_resize(
                        getattr(event, "x", self.window_size[0]),
                        getattr(event, "y", self.window_size[1]),
                    )
                elif window_size_changed_event is None and event.type == pygame.VIDEORESIZE:
                    self.handle_resize(event.w, event.h)
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_down(event.pos, event.button)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.handle_mouse_up(event.button)
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos, event.buttons)

            self.advance_maze_generation()
            self.advance_search()
            self.draw()

        pygame.quit()

    def handle_resize(self, width: int, height: int) -> None:
        min_width, min_height, _, _ = self.get_window_limits()
        clamped_width = max(min_width, width)
        clamped_height = max(min_height, height)
        previous_size = self.window_size

        if (clamped_width, clamped_height) == (width, height):
            self.window_size = (clamped_width, clamped_height)
            current_surface = pygame.display.get_surface()
            if current_surface is not None:
                self.screen = current_surface
        else:
            if (clamped_width, clamped_height) == previous_size:
                return
            self.screen = pygame.display.set_mode((clamped_width, clamped_height), WINDOW_FLAGS)
            self.window_size = self.screen.get_size()

        if self.window_size == previous_size:
            return
        self.invalidate_scaled_grid()
        self._build_buttons()

    def handle_keydown(self, key: int) -> None:
        if key == pygame.K_a:
            self.set_algorithm("A*")
        elif key == pygame.K_b:
            self.set_algorithm("BFS")
        elif key == pygame.K_d:
            self.set_algorithm("Dijkstra")
        elif key == pygame.K_g:
            self.set_algorithm("Greedy")
        elif key == pygame.K_i:
            self.set_algorithm("Bidirectional A*")
        elif key == pygame.K_r:
            self.start_maze_generation()
        elif key == pygame.K_t:
            self.toggle_maze_algorithm()
        elif key == pygame.K_l:
            self.prompt_grid_size()
        elif key == pygame.K_1:
            self.set_edit_mode("obstacle")
        elif key == pygame.K_2:
            self.set_edit_mode("start")
        elif key == pygame.K_3:
            self.set_edit_mode("goal")
        elif key == pygame.K_4:
            self.set_edit_mode("erase")
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.start_search()
        elif key == pygame.K_SPACE:
            self.toggle_pause()
        elif key == pygame.K_c:
            self.clear_search_state()
        elif key == pygame.K_m:
            self.clear_map()
        elif key == pygame.K_ESCAPE:
            self.clear_search_state(silent=True)
            self.status_message = "Search interrupted."

    def handle_mouse_down(self, position: tuple[int, int], button: int) -> None:
        if button not in (1, 3):
            return
        for ui_button in self.buttons:
            if ui_button.rect.collidepoint(position):
                ui_button.action()
                self.drag_button = None
                self.last_drag_cell = None
                return
        cell = self.screen_to_cell(position)
        if cell is None:
            return
        self.drag_button = button
        self.last_drag_cell = None
        self.apply_edit(cell, button)

    def handle_mouse_up(self, button: int) -> None:
        if self.drag_button == button:
            self.drag_button = None
            self.last_drag_cell = None

    def handle_mouse_motion(
        self, position: tuple[int, int], button_states: tuple[int, int, int]
    ) -> None:
        if self.drag_button not in (1, 3):
            return
        pressed = button_states[0] if self.drag_button == 1 else button_states[2]
        if not pressed:
            return
        cell = self.screen_to_cell(position)
        if cell is None or cell == self.last_drag_cell:
            return
        self.apply_edit(cell, self.drag_button)

    def apply_edit(self, cell: Cell, button: int) -> None:
        if self.maze_generator is not None or self.search_generator is not None or self.path_cells or self.closed_cells or self.open_cells:
            self.clear_search_state(silent=True)
            self.status_message = "Map changed. Cleared the previous visualization state."

        self.last_drag_cell = cell
        dirty_cells = {cell}

        if button == 3 or self.edit_mode == "erase":
            self.erase_cell(cell)
            return

        if self.edit_mode == "obstacle":
            if cell == self.start_cell or cell == self.goal_cell:
                return
            self.obstacles.add(cell)
            self.refresh_cells(dirty_cells)
            return

        if self.edit_mode == "start":
            if self.start_cell is not None:
                dirty_cells.add(self.start_cell)
            self.obstacles.discard(cell)
            if cell == self.goal_cell:
                dirty_cells.add(self.goal_cell)
                self.goal_cell = None
            self.start_cell = cell
            self.refresh_cells(dirty_cells)
            return

        if self.edit_mode == "goal":
            if self.goal_cell is not None:
                dirty_cells.add(self.goal_cell)
            self.obstacles.discard(cell)
            if cell == self.start_cell:
                dirty_cells.add(self.start_cell)
                self.start_cell = None
            self.goal_cell = cell
            self.refresh_cells(dirty_cells)

    def erase_cell(self, cell: Cell) -> None:
        if cell == self.start_cell:
            self.start_cell = None
        elif cell == self.goal_cell:
            self.goal_cell = None
        else:
            self.obstacles.discard(cell)
        self.refresh_cells({cell})

    def advance_search(self) -> None:
        if self.search_generator is None or self.search_paused:
            return

        for _ in range(self.steps_per_frame):
            try:
                frame = next(self.search_generator)
            except StopIteration:
                self.search_generator = None
                break

            self.apply_frame(frame)
            if frame.done:
                self.search_generator = None
                self.search_paused = False
                break

    def advance_maze_generation(self) -> None:
        if self.maze_generator is None or self.search_paused:
            return

        for _ in range(self.steps_per_frame):
            try:
                frame = next(self.maze_generator)
            except StopIteration:
                self.maze_generator = None
                break

            self.apply_maze_frame(frame)
            if frame.done:
                self.maze_generator = None
                self.search_paused = False
                break

    def apply_frame(self, frame: SearchFrame) -> None:
        new_open_cells = set(frame.open_cells)
        new_closed_cells = set(frame.closed_cells)
        new_path_cells = list(frame.path_cells)
        new_path_lookup = set(new_path_cells)

        dirty_cells = self.open_cells.symmetric_difference(new_open_cells)
        dirty_cells.update(self.closed_cells.symmetric_difference(new_closed_cells))
        dirty_cells.update(self.path_lookup.symmetric_difference(new_path_lookup))
        if self.current_cell is not None:
            dirty_cells.add(self.current_cell)
        if frame.current_cell is not None:
            dirty_cells.add(frame.current_cell)

        self.open_cells = new_open_cells
        self.closed_cells = new_closed_cells
        self.current_cell = frame.current_cell
        self.path_cells = new_path_cells
        self.path_lookup = new_path_lookup
        self.visited_count = frame.visited_count
        self.path_cost = frame.path_cost

        self.refresh_cells(dirty_cells)

        if frame.done and frame.found and frame.path_cost is not None:
            self.status_message = f"{self.selected_algorithm} found a path with cost {frame.path_cost:.2f}."
        else:
            self.status_message = frame.message

    def apply_maze_frame(self, frame: MazeFrame) -> None:
        if frame.full_redraw:
            self.mark_full_grid_dirty()
        else:
            self.refresh_cells(frame.changed_cells)
        self.status_message = frame.message

    def search_steps(self, algorithm: str) -> Generator[SearchFrame, None, None]:
        if algorithm == "BFS":
            yield from self.breadth_first_steps()
            return
        if algorithm == "Bidirectional A*":
            yield from self.bidirectional_a_star_steps()
            return
        if algorithm in {"A*", "Dijkstra", "Greedy"}:
            yield from self.best_first_steps(algorithm)
            return
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    def maze_steps(self, algorithm: str) -> Generator[MazeFrame, None, None]:
        if algorithm == "Recursive Division":
            yield from self.recursive_division_steps()
            return
        if algorithm == "DFS Backtracker":
            yield from self.dfs_backtracker_steps()
            return
        raise ValueError(f"Unsupported maze algorithm: {algorithm}")

    def best_first_steps(self, algorithm: str) -> Generator[SearchFrame, None, None]:
        assert self.start_cell is not None
        assert self.goal_cell is not None

        start = self.start_cell
        goal = self.goal_cell
        frontier: list[tuple[float, int, Cell]] = []
        g_score: dict[Cell, float] = {start: 0.0}
        came_from: dict[Cell, Cell] = {}
        open_cells: set[Cell] = {start}
        closed_cells: set[Cell] = set()
        path_cells: list[Cell] = []
        counter = 0

        heapq.heappush(
            frontier,
            (self.priority_for(algorithm, 0.0, start, goal), counter, start),
        )

        yield SearchFrame(
            open_cells,
            closed_cells,
            None,
            path_cells,
            0,
            None,
            False,
            False,
            f"Exploring with {algorithm}...",
        )

        while frontier:
            _, _, current = heapq.heappop(frontier)
            if current in closed_cells:
                continue

            open_cells.discard(current)
            closed_cells.add(current)

            if current == goal:
                final_path = self.reconstruct_path(came_from, current)
                yield from self.trace_path_frames(
                    open_cells,
                    closed_cells,
                    final_path,
                    g_score[current],
                )
                return

            for neighbor, move_cost in self.iter_neighbors(current):
                if neighbor in closed_cells:
                    continue

                tentative_cost = g_score[current] + move_cost
                if tentative_cost >= g_score.get(neighbor, math.inf):
                    continue

                came_from[neighbor] = current
                g_score[neighbor] = tentative_cost
                counter += 1
                heapq.heappush(
                    frontier,
                    (
                        self.priority_for(algorithm, tentative_cost, neighbor, goal),
                        counter,
                        neighbor,
                    ),
                )
                open_cells.add(neighbor)

            yield SearchFrame(
                open_cells,
                closed_cells,
                current,
                path_cells,
                len(closed_cells),
                None,
                False,
                False,
                f"Exploring with {algorithm}...",
            )

        yield SearchFrame(
            set(),
            closed_cells,
            None,
            [],
            len(closed_cells),
            None,
            True,
            False,
            f"{algorithm} could not find a valid path.",
        )

    def breadth_first_steps(self) -> Generator[SearchFrame, None, None]:
        assert self.start_cell is not None
        assert self.goal_cell is not None

        start = self.start_cell
        goal = self.goal_cell
        frontier: deque[Cell] = deque([start])
        came_from: dict[Cell, Cell] = {}
        open_cells: set[Cell] = {start}
        closed_cells: set[Cell] = set()
        discovered: set[Cell] = {start}

        yield SearchFrame(
            open_cells,
            closed_cells,
            None,
            [],
            0,
            None,
            False,
            False,
            "Exploring with BFS...",
        )

        while frontier:
            current = frontier.popleft()
            open_cells.discard(current)
            closed_cells.add(current)

            if current == goal:
                final_path = self.reconstruct_path(came_from, current)
                yield from self.trace_path_frames(
                    open_cells,
                    closed_cells,
                    final_path,
                    self.calculate_path_cost(final_path),
                )
                return

            for neighbor, _ in self.iter_neighbors(current):
                if neighbor in discovered or neighbor in closed_cells:
                    continue
                discovered.add(neighbor)
                came_from[neighbor] = current
                frontier.append(neighbor)
                open_cells.add(neighbor)

            yield SearchFrame(
                open_cells,
                closed_cells,
                current,
                [],
                len(closed_cells),
                None,
                False,
                False,
                "Exploring with BFS...",
            )

        yield SearchFrame(
            set(),
            closed_cells,
            None,
            [],
            len(closed_cells),
            None,
            True,
            False,
            "BFS could not find a valid path.",
        )

    def bidirectional_a_star_steps(self) -> Generator[SearchFrame, None, None]:
        assert self.start_cell is not None
        assert self.goal_cell is not None

        start = self.start_cell
        goal = self.goal_cell
        forward_frontier: list[tuple[float, int, Cell]] = [(self.heuristic(start, goal), 0, start)]
        backward_frontier: list[tuple[float, int, Cell]] = [(self.heuristic(goal, start), 1, goal)]
        forward_g: dict[Cell, float] = {start: 0.0}
        backward_g: dict[Cell, float] = {goal: 0.0}
        forward_parent: dict[Cell, Cell] = {}
        backward_parent: dict[Cell, Cell] = {}
        forward_open: set[Cell] = {start}
        backward_open: set[Cell] = {goal}
        forward_closed: set[Cell] = set()
        backward_closed: set[Cell] = set()
        counter = 2
        expand_forward = True

        yield SearchFrame(
            forward_open | backward_open,
            set(),
            None,
            [],
            0,
            None,
            False,
            False,
            "Exploring from both ends with Bidirectional A*...",
        )

        while forward_frontier and backward_frontier:
            if expand_forward:
                current = self.pop_frontier(forward_frontier, forward_closed)
                if current is None:
                    expand_forward = False
                    continue
                forward_open.discard(current)
                forward_closed.add(current)

                if current in backward_open or current in backward_closed:
                    final_path = self.reconstruct_bidirectional_path(
                        forward_parent,
                        backward_parent,
                        current,
                    )
                    yield from self.trace_path_frames(
                        forward_open | backward_open,
                        forward_closed | backward_closed,
                        final_path,
                        self.calculate_path_cost(final_path),
                    )
                    return

                for neighbor, move_cost in self.iter_neighbors(current):
                    if neighbor in forward_closed:
                        continue

                    tentative_cost = forward_g[current] + move_cost
                    if tentative_cost >= forward_g.get(neighbor, math.inf):
                        continue

                    forward_parent[neighbor] = current
                    forward_g[neighbor] = tentative_cost
                    heapq.heappush(
                        forward_frontier,
                        (
                            tentative_cost + self.heuristic(neighbor, goal),
                            counter,
                            neighbor,
                        ),
                    )
                    counter += 1
                    forward_open.add(neighbor)

                    if neighbor in backward_open or neighbor in backward_closed:
                        final_path = self.reconstruct_bidirectional_path(
                            forward_parent,
                            backward_parent,
                            neighbor,
                        )
                        yield from self.trace_path_frames(
                            forward_open | backward_open,
                            forward_closed | backward_closed,
                            final_path,
                            self.calculate_path_cost(final_path),
                        )
                        return
            else:
                current = self.pop_frontier(backward_frontier, backward_closed)
                if current is None:
                    expand_forward = True
                    continue
                backward_open.discard(current)
                backward_closed.add(current)

                if current in forward_open or current in forward_closed:
                    final_path = self.reconstruct_bidirectional_path(
                        forward_parent,
                        backward_parent,
                        current,
                    )
                    yield from self.trace_path_frames(
                        forward_open | backward_open,
                        forward_closed | backward_closed,
                        final_path,
                        self.calculate_path_cost(final_path),
                    )
                    return

                for neighbor, move_cost in self.iter_neighbors(current):
                    if neighbor in backward_closed:
                        continue

                    tentative_cost = backward_g[current] + move_cost
                    if tentative_cost >= backward_g.get(neighbor, math.inf):
                        continue

                    backward_parent[neighbor] = current
                    backward_g[neighbor] = tentative_cost
                    heapq.heappush(
                        backward_frontier,
                        (
                            tentative_cost + self.heuristic(neighbor, start),
                            counter,
                            neighbor,
                        ),
                    )
                    counter += 1
                    backward_open.add(neighbor)

                    if neighbor in forward_open or neighbor in forward_closed:
                        final_path = self.reconstruct_bidirectional_path(
                            forward_parent,
                            backward_parent,
                            neighbor,
                        )
                        yield from self.trace_path_frames(
                            forward_open | backward_open,
                            forward_closed | backward_closed,
                            final_path,
                            self.calculate_path_cost(final_path),
                        )
                        return

            combined_open = forward_open | backward_open
            combined_closed = forward_closed | backward_closed
            yield SearchFrame(
                combined_open,
                combined_closed,
                current,
                [],
                len(combined_closed),
                None,
                False,
                False,
                "Exploring from both ends with Bidirectional A*...",
            )
            expand_forward = not expand_forward

        yield SearchFrame(
            set(),
            forward_closed | backward_closed,
            None,
            [],
            len(forward_closed | backward_closed),
            None,
            True,
            False,
            "Bidirectional A* could not find a valid path.",
        )

    def recursive_division_steps(self) -> Generator[MazeFrame, None, None]:
        regions: list[tuple[int, int, int, int]] = [
            (0, 0, self.grid_width - 1, self.grid_height - 1)
        ]
        reserved_cells = self.get_reserved_cells()

        yield MazeFrame(
            len(self.obstacles),
            False,
            f"Generating maze with {self.selected_maze_algorithm}...",
        )

        while regions:
            left, top, right, bottom = regions.pop()
            width = right - left + 1
            height = bottom - top + 1
            orientation = self.choose_division_orientation(width, height)
            if orientation is None:
                continue

            new_walls: set[Cell] = set()

            if orientation == "horizontal":
                wall_y = random.randint(top + 1, bottom - 1)
                gap_x = random.randint(left, right)
                for x in range(left, right + 1):
                    cell = (x, wall_y)
                    if x == gap_x or cell in reserved_cells:
                        continue
                    new_walls.add(cell)

                if wall_y - 1 >= top:
                    regions.append((left, top, right, wall_y - 1))
                if wall_y + 1 <= bottom:
                    regions.append((left, wall_y + 1, right, bottom))
            else:
                wall_x = random.randint(left + 1, right - 1)
                gap_y = random.randint(top, bottom)
                for y in range(top, bottom + 1):
                    cell = (wall_x, y)
                    if y == gap_y or cell in reserved_cells:
                        continue
                    new_walls.add(cell)

                if wall_x - 1 >= left:
                    regions.append((left, top, wall_x - 1, bottom))
                if wall_x + 1 <= right:
                    regions.append((wall_x + 1, top, right, bottom))

            self.obstacles.update(new_walls)

            if new_walls:
                yield MazeFrame(
                    len(self.obstacles),
                    False,
                    f"Generating maze with Recursive Division... {len(self.obstacles)} walls placed.",
                    tuple(new_walls),
                )

        before_repair = set(self.obstacles)
        self.ensure_reserved_connectivity()
        yield MazeFrame(
            len(self.obstacles),
            True,
            f"Recursive Division maze generated with {len(self.obstacles)} walls.",
            tuple(before_repair.symmetric_difference(self.obstacles)),
        )

    def dfs_backtracker_steps(self) -> Generator[MazeFrame, None, None]:
        reserved_cells = self.get_reserved_cells()
        self.obstacles = {
            (x, y)
            for x in range(self.grid_width)
            for y in range(self.grid_height)
            if (x, y) not in reserved_cells
        }

        maze_cells = [
            (x, y)
            for x in range(1, self.grid_width - 1, 2)
            for y in range(1, self.grid_height - 1, 2)
        ]
        if not maze_cells:
            before_repair = set(self.obstacles)
            self.ensure_reserved_connectivity()
            yield MazeFrame(
                len(self.obstacles),
                True,
                "DFS Backtracker maze generated.",
                tuple(before_repair.symmetric_difference(self.obstacles)),
                True,
            )
            return

        start_cell = random.choice(maze_cells)
        stack = [start_cell]
        visited = {start_cell}
        self.obstacles.discard(start_cell)

        yield MazeFrame(
            len(self.obstacles),
            False,
            f"Generating maze with DFS Backtracker... {len(visited)} passages carved.",
            full_redraw=True,
        )

        directions = ((2, 0), (-2, 0), (0, 2), (0, -2))

        while stack:
            current = stack[-1]
            neighbors: list[tuple[Cell, Cell]] = []
            for dx, dy in directions:
                nx = current[0] + dx
                ny = current[1] + dy
                next_cell = (nx, ny)
                if not (1 <= nx < self.grid_width - 1 and 1 <= ny < self.grid_height - 1):
                    continue
                if next_cell in visited:
                    continue
                wall_cell = (current[0] + dx // 2, current[1] + dy // 2)
                neighbors.append((next_cell, wall_cell))

            if neighbors:
                next_cell, wall_cell = random.choice(neighbors)
                visited.add(next_cell)
                stack.append(next_cell)
                self.obstacles.discard(wall_cell)
                self.obstacles.discard(next_cell)
                yield MazeFrame(
                    len(self.obstacles),
                    False,
                    f"Generating maze with DFS Backtracker... {len(visited)} passages carved.",
                    (wall_cell, next_cell),
                )
            else:
                stack.pop()

        before_repair = set(self.obstacles)
        self.ensure_reserved_connectivity()
        yield MazeFrame(
            len(self.obstacles),
            True,
            f"DFS Backtracker maze generated with {len(self.obstacles)} walls.",
            tuple(before_repair.symmetric_difference(self.obstacles)),
        )

    def choose_division_orientation(self, width: int, height: int) -> Optional[str]:
        can_split_horizontally = height >= 3
        can_split_vertically = width >= 3

        if not can_split_horizontally and not can_split_vertically:
            return None
        if not can_split_horizontally:
            return "vertical"
        if not can_split_vertically:
            return "horizontal"
        if width > height:
            return "vertical"
        if height > width:
            return "horizontal"
        return random.choice(("horizontal", "vertical"))

    def get_reserved_cells(self) -> set[Cell]:
        reserved_cells: set[Cell] = set()
        if self.start_cell is not None:
            reserved_cells.add(self.start_cell)
        if self.goal_cell is not None:
            reserved_cells.add(self.goal_cell)
        return reserved_cells

    def ensure_reserved_connectivity(self) -> None:
        reserved_cells = self.get_reserved_cells()
        for cell in reserved_cells:
            self.carve_reserved_area(cell)

        if self.start_cell is None or self.goal_cell is None:
            return

        if self.has_walkable_path(self.start_cell, self.goal_cell):
            return

        self.carve_direct_connection(self.start_cell, self.goal_cell)
        self.carve_reserved_area(self.start_cell)
        self.carve_reserved_area(self.goal_cell)

    def carve_reserved_area(self, cell: Cell) -> None:
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                nx = cell[0] + dx
                ny = cell[1] + dy
                if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                    self.obstacles.discard((nx, ny))

    def has_walkable_path(self, start: Cell, goal: Cell) -> bool:
        frontier: deque[Cell] = deque([start])
        visited: set[Cell] = {start}

        while frontier:
            current = frontier.popleft()
            if current == goal:
                return True

            for neighbor, _ in self.iter_neighbors(current):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                frontier.append(neighbor)

        return False

    def carve_direct_connection(self, start: Cell, goal: Cell) -> None:
        x, y = start
        self.obstacles.discard((x, y))

        while x != goal[0]:
            x += 1 if goal[0] > x else -1
            self.obstacles.discard((x, y))

        while y != goal[1]:
            y += 1 if goal[1] > y else -1
            self.obstacles.discard((x, y))

    def trace_path_frames(
        self,
        open_cells: set[Cell],
        closed_cells: set[Cell],
        final_path: list[Cell],
        path_cost: float,
    ) -> Generator[SearchFrame, None, None]:
        path_cells: list[Cell] = []
        stable_open = set(open_cells)
        stable_closed = set(closed_cells)
        for index, cell in enumerate(final_path, start=1):
            path_cells.append(cell)
            yield SearchFrame(
                stable_open,
                stable_closed,
                cell,
                list(path_cells),
                len(stable_closed),
                path_cost,
                index == len(final_path),
                True,
                "Tracing final path...",
            )

    def pop_frontier(
        self,
        frontier: list[tuple[float, int, Cell]],
        closed_cells: set[Cell],
    ) -> Optional[Cell]:
        while frontier:
            _, _, cell = heapq.heappop(frontier)
            if cell not in closed_cells:
                return cell
        return None

    def priority_for(self, algorithm: str, path_cost: float, cell: Cell, goal: Cell) -> float:
        if algorithm == "Dijkstra":
            return path_cost
        if algorithm == "Greedy":
            return self.heuristic(cell, goal)
        return path_cost + self.heuristic(cell, goal)

    def heuristic(self, cell: Cell, goal: Cell) -> float:
        dx = abs(cell[0] - goal[0])
        dy = abs(cell[1] - goal[1])
        diagonal_steps = min(dx, dy)
        straight_steps = max(dx, dy) - diagonal_steps
        return diagonal_steps * MOVE_DIAGONAL + straight_steps * MOVE_STRAIGHT

    def iter_neighbors(self, cell: Cell):
        x, y = cell
        directions = (
            (-1, 0, MOVE_STRAIGHT),
            (1, 0, MOVE_STRAIGHT),
            (0, -1, MOVE_STRAIGHT),
            (0, 1, MOVE_STRAIGHT),
            (-1, -1, MOVE_DIAGONAL),
            (-1, 1, MOVE_DIAGONAL),
            (1, -1, MOVE_DIAGONAL),
            (1, 1, MOVE_DIAGONAL),
        )

        for dx, dy, move_cost in directions:
            nx = x + dx
            ny = y + dy
            neighbor = (nx, ny)

            if not (0 <= nx < self.grid_width and 0 <= ny < self.grid_height):
                continue
            if neighbor in self.obstacles:
                continue
            if dx != 0 and dy != 0:
                side_a = (x + dx, y)
                side_b = (x, y + dy)
                if side_a in self.obstacles or side_b in self.obstacles:
                    continue
            yield neighbor, move_cost

    def reconstruct_path(self, came_from: dict[Cell, Cell], current: Cell) -> list[Cell]:
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def reconstruct_bidirectional_path(
        self,
        forward_parent: dict[Cell, Cell],
        backward_parent: dict[Cell, Cell],
        meeting_cell: Cell,
    ) -> list[Cell]:
        path = self.reconstruct_path(forward_parent, meeting_cell)
        current = meeting_cell
        while current in backward_parent:
            current = backward_parent[current]
            path.append(current)
        return path

    def calculate_path_cost(self, path: list[Cell]) -> float:
        total_cost = 0.0
        for previous, current in zip(path, path[1:]):
            step_dx = abs(previous[0] - current[0])
            step_dy = abs(previous[1] - current[1])
            if step_dx == 1 and step_dy == 1:
                total_cost += MOVE_DIAGONAL
            else:
                total_cost += MOVE_STRAIGHT
        return total_cost

    def screen_to_cell(self, position: tuple[int, int]) -> Optional[Cell]:
        grid_rect = self.get_grid_rect()
        if not grid_rect.collidepoint(position):
            return None

        relative_x = (position[0] - grid_rect.x) / max(1, grid_rect.width)
        relative_y = (position[1] - grid_rect.y) / max(1, grid_rect.height)
        cell_x = min(self.grid_width - 1, max(0, int(relative_x * self.grid_width)))
        cell_y = min(self.grid_height - 1, max(0, int(relative_y * self.grid_height)))
        return cell_x, cell_y

    def get_panel_layout(self) -> dict[str, pygame.Rect]:
        panel_rect = self.get_panel_rect()
        panel_left = panel_rect.x + 16
        panel_width = panel_rect.width - 32
        gap = 10
        bottom_margin = 16
        section_top = SPEED_BUTTON_Y + 38 + gap
        usable_height = max(0, self.window_size[1] - section_top - bottom_margin - gap * 2)

        default_heights = {
            "stats": 110,
            "legend": 92,
            "status": 54,
        }
        minimum_heights = {
            "stats": 48,
            "legend": 44,
            "status": 40,
        }
        total_default_height = sum(default_heights.values())
        total_minimum_height = sum(minimum_heights.values())

        if usable_height >= total_default_height:
            heights = dict(default_heights)
        elif usable_height >= total_minimum_height:
            heights = dict(minimum_heights)
            remaining_height = usable_height - total_minimum_height
            growth_order = sorted(
                default_heights,
                key=lambda key: default_heights[key] - minimum_heights[key],
                reverse=True,
            )
            while remaining_height > 0:
                advanced = False
                for key in growth_order:
                    if heights[key] >= default_heights[key]:
                        continue
                    heights[key] += 1
                    remaining_height -= 1
                    advanced = True
                    if remaining_height == 0:
                        break
                if not advanced:
                    break
        else:
            heights = {key: 0 for key in default_heights}
            if usable_height > 0:
                remaining_height = usable_height
                total_weight = total_default_height
                for key in ("stats", "legend", "status"):
                    allocated = (default_heights[key] * usable_height) // total_weight
                    heights[key] = allocated
                    remaining_height -= allocated
                for key in ("stats", "legend", "status"):
                    if remaining_height == 0:
                        break
                    heights[key] += 1
                    remaining_height -= 1

        stats_rect = pygame.Rect(panel_left, section_top, panel_width, heights["stats"])
        legend_rect = pygame.Rect(
            panel_left,
            stats_rect.bottom + gap,
            panel_width,
            heights["legend"],
        )
        status_rect = pygame.Rect(
            panel_left,
            legend_rect.bottom + gap,
            panel_width,
            heights["status"],
        )
        return {
            "stats": stats_rect,
            "legend": legend_rect,
            "status": status_rect,
        }

    def format_cell(self, cell: Optional[Cell]) -> str:
        return str(cell) if cell is not None else "--"

    def draw(self) -> None:
        current_surface = pygame.display.get_surface()
        if current_surface is not None:
            self.screen = current_surface
        self.screen.fill(BACKGROUND_COLOR)
        self.draw_grid()
        self.draw_panel()
        pygame.display.flip()

    def draw_grid(self) -> None:
        self._refresh_grid_surface()

        grid_rect = self.get_grid_rect()
        if self.scaled_grid_surface is None or self.scaled_grid_size != grid_rect.size:
            self.scaled_grid_surface = pygame.transform.scale(self.grid_surface, grid_rect.size)
            self.scaled_grid_size = grid_rect.size

        self.screen.blit(self.scaled_grid_surface, grid_rect.topleft)
        pygame.draw.rect(self.screen, PANEL_SECTION_COLOR, grid_rect, 2, border_radius=6)

        cell_width = grid_rect.width / self.grid_width
        cell_height = grid_rect.height / self.grid_height
        if min(cell_width, cell_height) >= GRID_LINE_THRESHOLD:
            for x in range(1, self.grid_width):
                line_x = round(grid_rect.x + x * cell_width)
                pygame.draw.line(
                    self.screen,
                    GRID_LINE_COLOR,
                    (line_x, grid_rect.y),
                    (line_x, grid_rect.bottom),
                    1,
                )
            for y in range(1, self.grid_height):
                line_y = round(grid_rect.y + y * cell_height)
                pygame.draw.line(
                    self.screen,
                    GRID_LINE_COLOR,
                    (grid_rect.x, line_y),
                    (grid_rect.right, line_y),
                    1,
                )

    def draw_panel(self) -> None:
        panel_rect = self.get_panel_rect()
        panel_height = panel_rect.height
        panel_left = panel_rect.x + 20
        pygame.draw.rect(self.screen, PANEL_COLOR, panel_rect)
        pygame.draw.line(
            self.screen,
            PANEL_SECTION_COLOR,
            (panel_rect.x, 0),
            (panel_rect.x, panel_height),
            2,
        )

        self.draw_text("Pathfinding Demo", self.title_font, TEXT_COLOR, (panel_left, 18))
        self.draw_text("Algorithm", self.section_font, TEXT_COLOR, (panel_left, ALGORITHM_HEADER_Y))
        self.draw_text("Edit Mode", self.section_font, TEXT_COLOR, (panel_left, EDIT_HEADER_Y))
        self.draw_text("Controls", self.section_font, TEXT_COLOR, (panel_left, CONTROLS_HEADER_Y))
        self.draw_text("Speed", self.section_font, TEXT_COLOR, (panel_left, SPEED_HEADER_Y))

        for button in self.buttons:
            self.draw_button(button)

        layout = self.get_panel_layout()
        stats_rect = layout["stats"]
        legend_rect = layout["legend"]
        status_rect = layout["status"]

        pygame.draw.rect(self.screen, PANEL_SECTION_COLOR, stats_rect, border_radius=10)
        pygame.draw.rect(self.screen, PANEL_SECTION_COLOR, legend_rect, border_radius=10)
        pygame.draw.rect(self.screen, PANEL_SECTION_COLOR, status_rect, border_radius=10)

        if stats_rect.height >= 24:
            self.draw_text("Stats", self.text_font, TEXT_COLOR, (stats_rect.x + 12, stats_rect.y + 8))
        if legend_rect.height >= 24:
            self.draw_text("Legend", self.text_font, TEXT_COLOR, (legend_rect.x + 12, legend_rect.y + 8))
        if status_rect.height >= 24:
            self.draw_text("Status", self.text_font, TEXT_COLOR, (status_rect.x + 12, status_rect.y + 8))

        speed_labels = {1: "Slow", 4: "Medium", 16: "Fast"}
        path_cost_text = f"{self.path_cost:.2f}" if self.path_cost is not None else "--"
        stats = [
            f"Search: {self.selected_algorithm}",
            f"Maze / Edit: {self.selected_maze_algorithm} / {self.edit_mode}",
            f"Grid / Obstacles: {self.grid_width}x{self.grid_height} / {len(self.obstacles)}",
            f"Visited / Cost: {self.visited_count} / {path_cost_text}",
            f"Speed: {speed_labels.get(self.steps_per_frame, self.steps_per_frame)}",
            f"Start -> Goal: {self.format_cell(self.start_cell)} -> {self.format_cell(self.goal_cell)}",
        ]
        text_y = stats_rect.y + 30
        max_stats_lines = max(0, (stats_rect.height - 32) // 14)
        for line in stats[:max_stats_lines]:
            self.draw_text(line, self.small_font, MUTED_TEXT_COLOR, (stats_rect.x + 12, text_y))
            text_y += 14

        legend_items = [
            (START_COLOR, "Start"),
            (GOAL_COLOR, "Goal"),
            (OBSTACLE_COLOR, "Obstacle"),
            (OPEN_COLOR, "Open set"),
            (CLOSED_COLOR, "Closed set"),
            (CURRENT_COLOR, "Current"),
            (PATH_COLOR, "Final path"),
        ]
        legend_column_width = (legend_rect.width - 24) // 2
        if legend_rect.height >= 44:
            max_legend_rows = ((legend_rect.height - 44) // 18) + 1
        else:
            max_legend_rows = 0
        max_legend_items = max(0, max_legend_rows * 2)
        for index, (color, label) in enumerate(legend_items[:max_legend_items]):
            column = index % 2
            row = index // 2
            swatch_x = legend_rect.x + 12 + column * legend_column_width
            swatch_y = legend_rect.y + 30 + row * 18
            swatch_rect = pygame.Rect(swatch_x, swatch_y, 14, 14)
            pygame.draw.rect(self.screen, color, swatch_rect, border_radius=3)
            self.draw_text(label, self.small_font, MUTED_TEXT_COLOR, (swatch_x + 22, swatch_y - 1))

        wrapped_status = self.wrap_text(self.status_message, self.small_font, status_rect.width - 24)
        max_status_lines = max(0, (status_rect.height - 26) // 14)
        for index, line in enumerate(wrapped_status[:max_status_lines]):
            self.draw_text(
                line,
                self.small_font,
                TEXT_COLOR,
                (status_rect.x + 12, status_rect.y + 28 + index * 14),
            )

    def draw_button(self, button: Button) -> None:
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = button.rect.collidepoint(mouse_pos)
        is_active = False

        if button.kind == "algorithm":
            is_active = button.value == self.selected_algorithm
        elif button.kind == "mode":
            is_active = button.value == self.edit_mode
        elif button.kind == "speed":
            is_active = button.value == self.steps_per_frame

        color = BUTTON_ACTIVE_COLOR if is_active else BUTTON_HOVER_COLOR if is_hovered else BUTTON_COLOR
        pygame.draw.rect(self.screen, color, button.rect, border_radius=10)
        pygame.draw.rect(self.screen, PANEL_SECTION_COLOR, button.rect, 2, border_radius=10)

        text_surface = self.text_font.render(button.label, True, BUTTON_TEXT_COLOR)
        text_rect = text_surface.get_rect(center=button.rect.center)
        self.screen.blit(text_surface, text_rect)

    def draw_text(
        self,
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int],
        position: tuple[int, int],
    ) -> None:
        surface = font.render(text, True, color)
        self.screen.blit(surface, position)

    def wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        words = text.split()
        if not words:
            return [""]

        lines: list[str] = []
        current_line = words[0]

        for word in words[1:]:
            candidate = f"{current_line} {word}"
            if font.size(candidate)[0] <= max_width:
                current_line = candidate
            else:
                lines.append(current_line)
                current_line = word

        lines.append(current_line)
        return lines


def main() -> None:
    PathfinderApp().run()


if __name__ == "__main__":
    main()