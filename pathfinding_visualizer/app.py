"""Desktop pygame application for pathfinding and maze visualization."""

from __future__ import annotations

from collections import deque
import heapq
import math
import random
from typing import Generator, Optional

try:
    import pygame
except ImportError as exc:
    raise SystemExit(
        "pygame is required. Install dependencies with: pip install -r requirements.txt"
    ) from exc

try:
    from .constants import (
        ALGORITHM_BUTTON_ROWS,
        ALGORITHM_HEADER_Y,
        BACKGROUND_COLOR,
        BUTTON_ACTIVE_COLOR,
        BUTTON_COLOR,
        BUTTON_HOVER_COLOR,
        BUTTON_TEXT_COLOR,
        CLOSED_COLOR,
        CONTROL_BUTTON_ROWS,
        CONTROLS_HEADER_Y,
        CURRENT_COLOR,
        DEFAULT_GRID_HEIGHT,
        DEFAULT_GRID_WIDTH,
        EDIT_BUTTON_ROWS,
        EDIT_HEADER_Y,
        EMPTY_COLOR,
        FPS,
        GAMEPLAY_MOVE_INITIAL_DELAY_MS,
        GAMEPLAY_MOVE_REPEAT_MS,
        GOAL_COLOR,
        GRID_LINE_COLOR,
        GRID_LINE_THRESHOLD,
        GRID_PADDING,
        MAX_GRID_DIMENSION,
        MAZE_ALGORITHMS,
        MIN_GRID_DIMENSION,
        MODAL_ACCENT_COLOR,
        MODAL_BUTTON_HEIGHT,
        MODAL_CARD_BORDER_COLOR,
        MODAL_CARD_COLOR,
        MODAL_CLOSE_COLOR,
        MODAL_INPUT_ACTIVE_COLOR,
        MODAL_INPUT_COLOR,
        MODAL_MUTED_TEXT_COLOR,
        MODAL_OVERLAY_COLOR,
        MODAL_SUCCESS_COLOR,
        MODAL_TEXT_COLOR,
        MOVE_DIAGONAL,
        MOVE_STRAIGHT,
        MUTED_TEXT_COLOR,
        OBSTACLE_COLOR,
        OPEN_COLOR,
        PANEL_COLOR,
        PANEL_SECTION_COLOR,
        PANEL_WIDTH,
        PATH_COLOR,
        PLAYER_COLOR,
        SLIDER_THUMB_RADIUS,
        SLIDER_TRACK_HEIGHT,
        SPEED_BUTTON_Y,
        SPEED_HEADER_Y,
        START_COLOR,
        SUCCESS_DIALOG_HEIGHT,
        SUCCESS_DIALOG_WIDTH,
        TEXT_COLOR,
        WINDOW_DEFAULT_HEIGHT,
        WINDOW_DEFAULT_WIDTH,
        WINDOW_FLAGS,
        WINDOW_MIN_HEIGHT,
        WINDOW_MIN_WIDTH,
        WINDOW_SCREEN_MARGIN_X,
        WINDOW_SCREEN_MARGIN_Y,
        GRID_DIALOG_ADVANCED_HEIGHT,
        GRID_DIALOG_HEIGHT,
        GRID_DIALOG_WIDTH,
    )
    from .models import Button, Cell, GameplayState, GridSizeDialogState, MazeFrame, ModalState, SearchFrame, SuccessDialogState
except ImportError:
    import sys
    from pathlib import Path

    module_dir = Path(__file__).resolve().parent
    if str(module_dir) not in sys.path:
        sys.path.insert(0, str(module_dir))

    from constants import (
        ALGORITHM_BUTTON_ROWS,
        ALGORITHM_HEADER_Y,
        BACKGROUND_COLOR,
        BUTTON_ACTIVE_COLOR,
        BUTTON_COLOR,
        BUTTON_HOVER_COLOR,
        BUTTON_TEXT_COLOR,
        CLOSED_COLOR,
        CONTROL_BUTTON_ROWS,
        CONTROLS_HEADER_Y,
        CURRENT_COLOR,
        DEFAULT_GRID_HEIGHT,
        DEFAULT_GRID_WIDTH,
        EDIT_BUTTON_ROWS,
        EDIT_HEADER_Y,
        EMPTY_COLOR,
        FPS,
        GAMEPLAY_MOVE_INITIAL_DELAY_MS,
        GAMEPLAY_MOVE_REPEAT_MS,
        GOAL_COLOR,
        GRID_LINE_COLOR,
        GRID_LINE_THRESHOLD,
        GRID_PADDING,
        MAX_GRID_DIMENSION,
        MAZE_ALGORITHMS,
        MIN_GRID_DIMENSION,
        MODAL_ACCENT_COLOR,
        MODAL_BUTTON_HEIGHT,
        MODAL_CARD_BORDER_COLOR,
        MODAL_CARD_COLOR,
        MODAL_CLOSE_COLOR,
        MODAL_INPUT_ACTIVE_COLOR,
        MODAL_INPUT_COLOR,
        MODAL_MUTED_TEXT_COLOR,
        MODAL_OVERLAY_COLOR,
        MODAL_SUCCESS_COLOR,
        MODAL_TEXT_COLOR,
        MOVE_DIAGONAL,
        MOVE_STRAIGHT,
        MUTED_TEXT_COLOR,
        OBSTACLE_COLOR,
        OPEN_COLOR,
        PANEL_COLOR,
        PANEL_SECTION_COLOR,
        PANEL_WIDTH,
        PATH_COLOR,
        PLAYER_COLOR,
        SLIDER_THUMB_RADIUS,
        SLIDER_TRACK_HEIGHT,
        SPEED_BUTTON_Y,
        SPEED_HEADER_Y,
        START_COLOR,
        SUCCESS_DIALOG_HEIGHT,
        SUCCESS_DIALOG_WIDTH,
        TEXT_COLOR,
        WINDOW_DEFAULT_HEIGHT,
        WINDOW_DEFAULT_WIDTH,
        WINDOW_FLAGS,
        WINDOW_MIN_HEIGHT,
        WINDOW_MIN_WIDTH,
        WINDOW_SCREEN_MARGIN_X,
        WINDOW_SCREEN_MARGIN_Y,
        GRID_DIALOG_ADVANCED_HEIGHT,
        GRID_DIALOG_HEIGHT,
        GRID_DIALOG_WIDTH,
    )
    from models import Button, Cell, GameplayState, GridSizeDialogState, MazeFrame, ModalState, SearchFrame, SuccessDialogState


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
        self.gameplay_state = GameplayState()
        self.modal_state = ModalState()
        self.gameplay_hold_direction: Optional[Cell] = None
        self.gameplay_next_move_ticks = 0
        self.gameplay_drag_cell: Optional[Cell] = None

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
            Button("Grid Size", rect_2col(CONTROL_BUTTON_ROWS[2], 0), self.prompt_grid_size),
            Button("Play", rect_2col(CONTROL_BUTTON_ROWS[2], 1), self.toggle_gameplay_mode, "gameplay", True),
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
        if self.is_gameplay_engaged():
            self.status_message = "Exit gameplay mode before changing grid size."
            return
        if self.search_generator is not None or self.maze_generator is not None:
            self.status_message = "Finish the active animation before changing grid size."
            return

        self.open_grid_size_dialog()

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
        self.clear_gameplay_input_state()
        self.gameplay_state = GameplayState()
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
        if cell == self.gameplay_state.player_cell:
            return PLAYER_COLOR
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

    def is_gameplay_engaged(self) -> bool:
        return self.gameplay_state.active or self.gameplay_state.pending_generation

    def has_active_modal(self) -> bool:
        return self.modal_state.kind is not None

    def dismiss_modal(self, status_message: Optional[str] = None) -> None:
        self.modal_state = ModalState()
        if status_message is not None:
            self.status_message = status_message

    def open_success_dialog(self) -> None:
        self.modal_state = ModalState(
            kind="success",
            success=SuccessDialogState(
                visible=True,
                moves=self.gameplay_state.moves,
                elapsed_seconds=self.gameplay_state.elapsed_seconds,
            ),
        )

    def open_grid_size_dialog(self) -> None:
        linked_size = self.grid_width if self.grid_width == self.grid_height else min(
            self.grid_width,
            self.grid_height,
        )
        linked_size, _ = self.clamp_grid_size(linked_size, linked_size)
        self.modal_state = ModalState(
            kind="grid_size",
            grid_size=GridSizeDialogState(
                visible=True,
                slider_value=linked_size,
                width_text=str(self.grid_width),
                height_text=str(self.grid_height),
                advanced_open=self.grid_width != self.grid_height,
            ),
        )
        self.status_message = "Adjust the grid size and click Apply to confirm."

    def close_grid_size_dialog(self) -> None:
        self.dismiss_modal("Grid size change cancelled.")

    def get_grid_dialog_dimensions(self) -> tuple[int, int]:
        state = self.modal_state.grid_size
        width_value = self.parse_grid_dimension_text(state.width_text)
        height_value = self.parse_grid_dimension_text(state.height_text)
        if width_value is None or height_value is None:
            return self.clamp_grid_size(self.grid_width, self.grid_height)
        return self.clamp_grid_size(width_value, height_value)

    def set_grid_dialog_linked_size(self, value: int) -> None:
        clamped_value, _ = self.clamp_grid_size(value, value)
        self.modal_state.grid_size.slider_value = clamped_value
        self.modal_state.grid_size.width_text = str(clamped_value)
        self.modal_state.grid_size.height_text = str(clamped_value)

    def adjust_grid_dialog_axis(self, axis: str, delta: int) -> None:
        width, height = self.get_grid_dialog_dimensions()
        if axis == "width":
            width += delta
        else:
            height += delta

        width, height = self.clamp_grid_size(width, height)
        self.modal_state.grid_size.width_text = str(width)
        self.modal_state.grid_size.height_text = str(height)
        if width == height:
            self.modal_state.grid_size.slider_value = width

    def apply_grid_size_from_dialog(self) -> None:
        requested_width = self.parse_grid_dimension_text(self.modal_state.grid_size.width_text)
        requested_height = self.parse_grid_dimension_text(self.modal_state.grid_size.height_text)
        width, height = self.get_grid_dialog_dimensions()
        self.dismiss_modal()
        self.apply_grid_size(
            width,
            height,
            requested=(requested_width or width, requested_height or height),
        )

    def clear_gameplay_hold(self) -> None:
        self.gameplay_hold_direction = None
        self.gameplay_next_move_ticks = 0

    def clear_gameplay_drag(self) -> None:
        self.gameplay_drag_cell = None

    def clear_gameplay_input_state(self) -> None:
        self.clear_gameplay_hold()
        self.clear_gameplay_drag()

    def iter_gameplay_drag_cells(self, start_cell: Cell, end_cell: Cell) -> list[Cell]:
        if start_cell == end_cell:
            return []

        x0, y0 = start_cell
        x1, y1 = end_cell
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        step_x = 1 if x1 > x0 else -1 if x1 < x0 else 0
        step_y = 1 if y1 > y0 else -1 if y1 < y0 else 0
        error = dx - dy
        traversed_cells: list[Cell] = []

        while (x0, y0) != (x1, y1):
            doubled_error = error * 2
            next_x = x0
            next_y = y0
            if doubled_error > -dy:
                error -= dy
                next_x += step_x
            if doubled_error < dx:
                error += dx
                next_y += step_y
            x0, y0 = next_x, next_y
            traversed_cells.append((x0, y0))

        return traversed_cells

    def advance_gameplay_drag(self, cell: Cell) -> None:
        if (
            self.gameplay_drag_cell is None
            or self.gameplay_state.pending_generation
            or not self.gameplay_state.active
            or self.gameplay_state.player_cell is None
            or self.gameplay_state.won
        ):
            return
        if cell == self.gameplay_drag_cell:
            return

        traversed_cells = self.iter_gameplay_drag_cells(self.gameplay_drag_cell, cell)
        self.gameplay_drag_cell = cell

        for traversed_cell in traversed_cells:
            player_cell = self.gameplay_state.player_cell
            if player_cell is None or self.gameplay_state.won:
                self.clear_gameplay_drag()
                return

            dx = traversed_cell[0] - player_cell[0]
            dy = traversed_cell[1] - player_cell[1]
            if max(abs(dx), abs(dy)) != 1:
                continue

            self.try_move_player(dx, dy)
            if self.gameplay_state.won:
                self.clear_gameplay_drag()
                return

    def get_gameplay_direction_for_key(self, key: int) -> Optional[Cell]:
        if key in (pygame.K_UP, pygame.K_w):
            return (0, -1)
        if key in (pygame.K_DOWN, pygame.K_s):
            return (0, 1)
        if key in (pygame.K_LEFT, pygame.K_a):
            return (-1, 0)
        if key in (pygame.K_RIGHT, pygame.K_d):
            return (1, 0)
        return None

    def is_gameplay_direction_pressed(self, direction: Cell, pressed_keys) -> bool:
        if direction == (0, -1):
            return bool(pressed_keys[pygame.K_UP] or pressed_keys[pygame.K_w])
        if direction == (0, 1):
            return bool(pressed_keys[pygame.K_DOWN] or pressed_keys[pygame.K_s])
        if direction == (-1, 0):
            return bool(pressed_keys[pygame.K_LEFT] or pressed_keys[pygame.K_a])
        if direction == (1, 0):
            return bool(pressed_keys[pygame.K_RIGHT] or pressed_keys[pygame.K_d])
        return False

    def handle_gameplay_direction_keydown(self, direction: Cell) -> None:
        if self.gameplay_state.pending_generation:
            self.try_move_player(*direction)
            return
        if not self.gameplay_state.active:
            return

        self.clear_gameplay_drag()
        self.gameplay_hold_direction = direction
        self.gameplay_next_move_ticks = pygame.time.get_ticks() + GAMEPLAY_MOVE_INITIAL_DELAY_MS
        self.try_move_player(*direction)
        if self.gameplay_state.won:
            self.clear_gameplay_hold()

    def advance_gameplay_hold(self) -> None:
        if self.gameplay_hold_direction is None:
            return

        pressed_keys = pygame.key.get_pressed()
        if not self.is_gameplay_direction_pressed(self.gameplay_hold_direction, pressed_keys):
            self.clear_gameplay_hold()
            return

        now_ticks = pygame.time.get_ticks()
        if now_ticks < self.gameplay_next_move_ticks:
            return

        self.try_move_player(*self.gameplay_hold_direction)
        self.gameplay_next_move_ticks = now_ticks + GAMEPLAY_MOVE_REPEAT_MS
        if self.gameplay_state.won:
            self.clear_gameplay_hold()

    def toggle_gameplay_mode(self) -> None:
        if self.is_gameplay_engaged():
            self.exit_gameplay_mode("Gameplay mode exited.")
            return
        self.start_gameplay_mode()

    def start_gameplay_mode(self) -> None:
        self.clear_gameplay_input_state()
        self.clear_search_state(silent=True)
        if self.can_use_current_map_for_gameplay():
            self.activate_gameplay_level(auto_generated=False)
            return

        self.ensure_gameplay_start_goal()
        self.gameplay_state = GameplayState(pending_generation=True)
        self.start_maze_generation()
        self.gameplay_state.pending_generation = True
        self.status_message = f"Generating a {self.selected_maze_algorithm} maze for gameplay..."

    def exit_gameplay_mode(self, message: str) -> None:
        dirty_cells: set[Cell] = set()
        if self.gameplay_state.player_cell is not None:
            dirty_cells.add(self.gameplay_state.player_cell)
        if self.gameplay_state.pending_generation:
            self.clear_search_state(silent=True)
        self.clear_gameplay_input_state()
        self.modal_state = ModalState()
        self.gameplay_state = GameplayState()
        self.refresh_cells(dirty_cells)
        self.status_message = message

    def restart_gameplay(self) -> None:
        if self.gameplay_state.pending_generation:
            self.status_message = "Wait for the gameplay maze to finish generating."
            return
        if not self.gameplay_state.active or self.start_cell is None:
            self.status_message = "Gameplay mode is not active."
            return

        dirty_cells = {self.start_cell}
        if self.gameplay_state.player_cell is not None:
            dirty_cells.add(self.gameplay_state.player_cell)

        self.clear_gameplay_input_state()
        self.gameplay_state.player_cell = self.start_cell
        self.gameplay_state.moves = 0
        self.gameplay_state.start_ticks = pygame.time.get_ticks()
        self.gameplay_state.elapsed_seconds = 0.0
        self.gameplay_state.won = False
        self.refresh_cells(dirty_cells)
        self.status_message = "Gameplay restarted. Reach the goal with arrows/WASD or left-drag."

    def start_new_gameplay_round(self) -> None:
        dirty_cells: set[Cell] = set()
        if self.gameplay_state.player_cell is not None:
            dirty_cells.add(self.gameplay_state.player_cell)
        if self.start_cell is not None:
            dirty_cells.add(self.start_cell)
        if self.goal_cell is not None:
            dirty_cells.add(self.goal_cell)

        self.dismiss_modal()
        self.clear_gameplay_input_state()
        self.gameplay_state = GameplayState()
        self.refresh_cells(dirty_cells)
        self.clear_search_state(silent=True)
        self.start_cell = None
        self.goal_cell = None
        self.ensure_gameplay_start_goal()
        self.gameplay_state = GameplayState(pending_generation=True)
        self.start_maze_generation()
        self.gameplay_state.pending_generation = True
        self.status_message = f"Generating a {self.selected_maze_algorithm} maze for gameplay..."

    def advance_gameplay(self) -> None:
        if not self.gameplay_state.active or self.gameplay_state.pending_generation:
            return
        if self.gameplay_state.won or self.gameplay_state.start_ticks <= 0:
            return
        self.update_gameplay_elapsed_time()
        self.advance_gameplay_hold()

    def update_gameplay_elapsed_time(self) -> None:
        if not self.gameplay_state.active or self.gameplay_state.start_ticks <= 0:
            return
        self.gameplay_state.elapsed_seconds = (
            pygame.time.get_ticks() - self.gameplay_state.start_ticks
        ) / 1000.0

    def can_use_current_map_for_gameplay(self) -> bool:
        if self.start_cell is None or self.goal_cell is None:
            return False
        if self.start_cell == self.goal_cell:
            return False
        if self.start_cell in self.obstacles or self.goal_cell in self.obstacles:
            return False
        return self.has_walkable_path(self.start_cell, self.goal_cell)

    def get_gameplay_axis_order(self, size: int, toward_end: bool) -> list[int]:
        target = size - 1 if toward_end else 0
        scored_indices: list[tuple[tuple[int, int, int, int], int]] = []

        for index in range(size):
            margin = min(index, size - 1 - index)
            score = (
                1 if margin >= 3 else 0,
                -abs(index - target),
                1 if index % 2 == 1 else 0,
                margin,
            )
            scored_indices.append((score, index))

        scored_indices.sort(reverse=True)
        return [index for _, index in scored_indices]

    def iter_gameplay_corner_candidates(
        self,
        toward_right: bool,
        toward_bottom: bool,
    ):
        x_order = self.get_gameplay_axis_order(self.grid_width, toward_right)
        y_order = self.get_gameplay_axis_order(self.grid_height, toward_bottom)

        for y in y_order:
            for x in x_order:
                yield (x, y)

    def get_default_gameplay_start_goal(self) -> tuple[Cell, Cell]:
        start_cell = next(self.iter_gameplay_corner_candidates(False, False))

        goal_cell = next(
            (
                cell
                for cell in self.iter_gameplay_corner_candidates(True, True)
                if cell != start_cell
            ),
            start_cell,
        )
        if goal_cell != start_cell:
            return start_cell, goal_cell

        for y in range(self.grid_height):
            for x in range(self.grid_width):
                fallback = (x, y)
                if fallback != start_cell:
                    return start_cell, fallback

        return start_cell, start_cell

    def ensure_gameplay_start_goal(self) -> None:
        new_start, new_goal = self.get_default_gameplay_start_goal()

        dirty_cells: set[Cell] = set()
        if self.start_cell is not None:
            dirty_cells.add(self.start_cell)
        if self.goal_cell is not None:
            dirty_cells.add(self.goal_cell)

        self.start_cell = new_start
        self.goal_cell = new_goal
        self.obstacles.discard(self.start_cell)
        self.obstacles.discard(self.goal_cell)
        dirty_cells.update({self.start_cell, self.goal_cell})
        self.refresh_cells(dirty_cells)

    def activate_gameplay_level(self, auto_generated: bool) -> None:
        if not self.can_use_current_map_for_gameplay() or self.start_cell is None:
            self.exit_gameplay_mode("Unable to start gameplay: no valid path exists.")
            return

        dirty_cells: set[Cell] = set()
        if self.gameplay_state.player_cell is not None:
            dirty_cells.add(self.gameplay_state.player_cell)

        self.gameplay_state = GameplayState(
            active=True,
            player_cell=self.start_cell,
            start_ticks=pygame.time.get_ticks(),
            used_generated_maze=auto_generated,
        )
        self.clear_gameplay_input_state()
        dirty_cells.add(self.start_cell)
        self.refresh_cells(dirty_cells)

        source_label = "generated maze" if auto_generated else "current map"
        self.status_message = (
            f"Gameplay started on the {source_label}. "
            "Use arrows/WASD or left-drag on the grid. Press N to restart, P or Esc to exit."
        )

    def try_move_player(self, dx: int, dy: int) -> None:
        if self.gameplay_state.pending_generation:
            self.status_message = "Wait for the gameplay maze to finish generating."
            return
        if not self.gameplay_state.active or self.gameplay_state.player_cell is None:
            return
        if self.gameplay_state.won:
            self.status_message = "Goal already reached. Press N to restart or P to exit."
            return

        current_cell = self.gameplay_state.player_cell
        target_cell = (current_cell[0] + dx, current_cell[1] + dy)
        valid_neighbors = {neighbor for neighbor, _ in self.iter_neighbors(current_cell)}
        if target_cell not in valid_neighbors:
            self.status_message = "Blocked by a wall."
            return

        self.gameplay_state.player_cell = target_cell
        self.gameplay_state.moves += 1
        self.update_gameplay_elapsed_time()
        self.refresh_cells({current_cell, target_cell})

        if target_cell == self.goal_cell:
            self.finish_gameplay()
            return

        self.status_message = (
            f"Moves: {self.gameplay_state.moves}. Reach the goal with arrows/WASD or left-drag."
        )

    def finish_gameplay(self) -> None:
        self.update_gameplay_elapsed_time()
        self.clear_gameplay_input_state()
        self.gameplay_state.won = True
        self.status_message = (
            f"Goal reached in {self.gameplay_state.moves} moves and "
            f"{self.format_elapsed_time(self.gameplay_state.elapsed_seconds)}. "
            "Choose Play Again or close the popup."
        )
        self.open_success_dialog()

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
        if self.gameplay_state.player_cell is not None:
            dirty_cells.add(self.gameplay_state.player_cell)

        self.clear_gameplay_input_state()
        self.gameplay_state = GameplayState()
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
                elif event.type == pygame.KEYUP:
                    self.handle_keyup(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_down(event.pos, event.button)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.handle_mouse_up(event.button)
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos, event.buttons)

            self.advance_gameplay()
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

    def get_modal_card_rect(self, width: int, height: int) -> pygame.Rect:
        card_width = max(260, min(width, self.window_size[0] - 48))
        card_height = max(180, min(height, self.window_size[1] - 48))
        return pygame.Rect(
            (self.window_size[0] - card_width) // 2,
            (self.window_size[1] - card_height) // 2,
            card_width,
            card_height,
        )

    def get_success_dialog_layout(self) -> dict[str, pygame.Rect]:
        card = self.get_modal_card_rect(SUCCESS_DIALOG_WIDTH, SUCCESS_DIALOG_HEIGHT)
        content_left = card.x + 28
        content_width = card.width - 56
        close_icon = pygame.Rect(card.right - 50, card.y + 18, 30, 30)
        action_y = card.bottom - 66
        play_again_button = pygame.Rect(content_left, action_y, content_width, MODAL_BUTTON_HEIGHT)

        return {
            "card": card,
            "close_icon": close_icon,
            "play_again": play_again_button,
        }

    def get_grid_size_dialog_layout(self) -> dict[str, pygame.Rect]:
        dialog_height = (
            GRID_DIALOG_ADVANCED_HEIGHT
            if self.modal_state.grid_size.advanced_open
            else GRID_DIALOG_HEIGHT
        )
        card = self.get_modal_card_rect(GRID_DIALOG_WIDTH, dialog_height)
        content_left = card.x + 32
        content_width = card.width - 64
        close_icon = pygame.Rect(card.right - 50, card.y + 18, 30, 30)
        slider_track = pygame.Rect(
            content_left,
            card.y + 122,
            content_width,
            SLIDER_TRACK_HEIGHT,
        )
        advanced_toggle = pygame.Rect(content_left, card.y + 170, content_width, 36)
        footer_y = card.bottom - 60
        footer_width = (content_width - 16) // 2
        cancel_button = pygame.Rect(content_left, footer_y, footer_width, MODAL_BUTTON_HEIGHT)
        apply_button = pygame.Rect(
            cancel_button.right + 16,
            footer_y,
            footer_width,
            MODAL_BUTTON_HEIGHT,
        )

        field_y = card.y + 222
        field_width = (content_width - 20) // 2
        width_card = pygame.Rect(content_left, field_y, field_width, 104)
        height_card = pygame.Rect(width_card.right + 20, field_y, field_width, 104)

        def build_stepper(rect: pygame.Rect) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
            minus_rect = pygame.Rect(rect.x + 12, rect.bottom - 44, 32, 32)
            plus_rect = pygame.Rect(rect.right - 44, rect.bottom - 44, 32, 32)
            value_rect = pygame.Rect(
                minus_rect.right + 8,
                minus_rect.y,
                max(40, rect.width - 104),
                32,
            )
            return minus_rect, value_rect, plus_rect

        width_minus, width_value, width_plus = build_stepper(width_card)
        height_minus, height_value, height_plus = build_stepper(height_card)

        return {
            "card": card,
            "close_icon": close_icon,
            "slider_track": slider_track,
            "advanced_toggle": advanced_toggle,
            "cancel": cancel_button,
            "apply": apply_button,
            "width_card": width_card,
            "height_card": height_card,
            "width_minus": width_minus,
            "width_value": width_value,
            "width_plus": width_plus,
            "height_minus": height_minus,
            "height_value": height_value,
            "height_plus": height_plus,
        }

    def get_slider_thumb_rect(self, track_rect: pygame.Rect, value: int) -> pygame.Rect:
        if MAX_GRID_DIMENSION == MIN_GRID_DIMENSION:
            ratio = 0.0
        else:
            ratio = (value - MIN_GRID_DIMENSION) / (MAX_GRID_DIMENSION - MIN_GRID_DIMENSION)
        thumb_center_x = round(track_rect.x + ratio * track_rect.width)
        thumb_center_y = track_rect.centery
        return pygame.Rect(
            thumb_center_x - SLIDER_THUMB_RADIUS,
            thumb_center_y - SLIDER_THUMB_RADIUS,
            SLIDER_THUMB_RADIUS * 2,
            SLIDER_THUMB_RADIUS * 2,
        )

    def update_grid_dialog_slider_from_position(self, x_position: int) -> None:
        track_rect = self.get_grid_size_dialog_layout()["slider_track"]
        if track_rect.width <= 0:
            return
        ratio = (x_position - track_rect.x) / track_rect.width
        ratio = max(0.0, min(1.0, ratio))
        value = round(MIN_GRID_DIMENSION + ratio * (MAX_GRID_DIMENSION - MIN_GRID_DIMENSION))
        self.set_grid_dialog_linked_size(value)

    def get_success_dialog_action_at(self, position: tuple[int, int]) -> Optional[str]:
        layout = self.get_success_dialog_layout()
        if layout["close_icon"].collidepoint(position):
            return "close"
        if layout["play_again"].collidepoint(position):
            return "play_again"
        return None

    def get_grid_dialog_action_at(self, position: tuple[int, int]) -> Optional[str]:
        layout = self.get_grid_size_dialog_layout()
        if layout["close_icon"].collidepoint(position):
            return "close"
        if layout["cancel"].collidepoint(position):
            return "cancel"
        if layout["apply"].collidepoint(position):
            return "apply"
        if layout["advanced_toggle"].collidepoint(position):
            return "toggle_advanced"
        if layout["slider_track"].inflate(0, 28).collidepoint(position):
            return "slider"
        if not self.modal_state.grid_size.advanced_open:
            return None
        if layout["width_minus"].collidepoint(position):
            return "width_minus"
        if layout["width_plus"].collidepoint(position):
            return "width_plus"
        if layout["height_minus"].collidepoint(position):
            return "height_minus"
        if layout["height_plus"].collidepoint(position):
            return "height_plus"
        return None

    def update_modal_hover(self, position: tuple[int, int]) -> None:
        if self.modal_state.kind == "success":
            self.modal_state.hovered_action = self.get_success_dialog_action_at(position)
        elif self.modal_state.kind == "grid_size":
            self.modal_state.hovered_action = self.get_grid_dialog_action_at(position)
        else:
            self.modal_state.hovered_action = None

    def handle_modal_keydown(self, key: int) -> None:
        if self.modal_state.kind == "success":
            if key == pygame.K_ESCAPE:
                self.dismiss_modal()
            return

        if self.modal_state.kind != "grid_size":
            return

        if key == pygame.K_ESCAPE:
            self.close_grid_size_dialog()
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.apply_grid_size_from_dialog()
        elif key in (pygame.K_LEFT, pygame.K_DOWN):
            self.set_grid_dialog_linked_size(self.modal_state.grid_size.slider_value - 1)
        elif key in (pygame.K_RIGHT, pygame.K_UP):
            self.set_grid_dialog_linked_size(self.modal_state.grid_size.slider_value + 1)

    def handle_modal_mouse_down(self, position: tuple[int, int], button: int) -> None:
        if button != 1:
            return

        if self.modal_state.kind == "success":
            action = self.get_success_dialog_action_at(position)
            if action == "play_again":
                self.start_new_gameplay_round()
            elif action == "close":
                self.dismiss_modal()
            return

        if self.modal_state.kind != "grid_size":
            return

        action = self.get_grid_dialog_action_at(position)
        if action in {"close", "cancel"}:
            self.close_grid_size_dialog()
            return
        if action == "apply":
            self.apply_grid_size_from_dialog()
            return
        if action == "toggle_advanced":
            self.modal_state.grid_size.advanced_open = not self.modal_state.grid_size.advanced_open
            return
        if action == "slider":
            self.modal_state.grid_size.dragging_slider = True
            self.update_grid_dialog_slider_from_position(position[0])
            return
        if action == "width_minus":
            self.adjust_grid_dialog_axis("width", -1)
            return
        if action == "width_plus":
            self.adjust_grid_dialog_axis("width", 1)
            return
        if action == "height_minus":
            self.adjust_grid_dialog_axis("height", -1)
            return
        if action == "height_plus":
            self.adjust_grid_dialog_axis("height", 1)

    def handle_modal_mouse_up(self, button: int) -> None:
        if button == 1 and self.modal_state.kind == "grid_size":
            self.modal_state.grid_size.dragging_slider = False

    def handle_modal_mouse_motion(
        self,
        position: tuple[int, int],
        button_states: tuple[int, int, int],
    ) -> None:
        self.update_modal_hover(position)
        if (
            self.modal_state.kind == "grid_size"
            and self.modal_state.grid_size.dragging_slider
            and button_states[0]
        ):
            self.update_grid_dialog_slider_from_position(position[0])
        elif self.modal_state.kind == "grid_size" and not button_states[0]:
            self.modal_state.grid_size.dragging_slider = False

    def handle_keydown(self, key: int) -> None:
        if self.has_active_modal():
            self.handle_modal_keydown(key)
            return

        if self.is_gameplay_engaged():
            if key in (pygame.K_p, pygame.K_ESCAPE):
                self.exit_gameplay_mode("Gameplay mode exited.")
            elif key == pygame.K_n:
                self.restart_gameplay()
            else:
                direction = self.get_gameplay_direction_for_key(key)
                if direction is not None:
                    self.handle_gameplay_direction_keydown(direction)
            return

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

    def handle_keyup(self, key: int) -> None:
        if self.has_active_modal():
            return
        if not self.is_gameplay_engaged() or self.gameplay_hold_direction is None:
            return

        direction = self.get_gameplay_direction_for_key(key)
        if direction == self.gameplay_hold_direction:
            self.clear_gameplay_hold()

    def handle_mouse_down(self, position: tuple[int, int], button: int) -> None:
        if self.has_active_modal():
            self.handle_modal_mouse_down(position, button)
            return
        if button not in (1, 3):
            return
        for ui_button in self.buttons:
            if ui_button.rect.collidepoint(position):
                if self.is_gameplay_engaged() and ui_button.kind != "gameplay":
                    self.status_message = (
                        "Exit gameplay mode before using visualizer controls. "
                        "Press N to restart, P or Esc to exit."
                    )
                    self.drag_button = None
                    self.last_drag_cell = None
                    return
                ui_button.action()
                self.drag_button = None
                self.last_drag_cell = None
                return
        if self.is_gameplay_engaged():
            if self.gameplay_state.pending_generation:
                self.status_message = "Wait for the gameplay maze to finish generating."
                self.clear_gameplay_drag()
                return
            if self.gameplay_state.won:
                self.status_message = "Goal already reached. Press N to restart or P to exit."
                self.clear_gameplay_drag()
                return
            if button != 1:
                self.status_message = "Gameplay uses arrows/WASD or left-drag on the grid."
                self.clear_gameplay_drag()
                return
            cell = self.screen_to_cell(position)
            if cell is None:
                self.clear_gameplay_drag()
                return
            self.clear_gameplay_hold()
            self.gameplay_drag_cell = cell
            return
        cell = self.screen_to_cell(position)
        if cell is None:
            return
        self.drag_button = button
        self.last_drag_cell = None
        self.apply_edit(cell, button)

    def handle_mouse_up(self, button: int) -> None:
        if self.has_active_modal():
            self.handle_modal_mouse_up(button)
            return
        if button == 1:
            self.clear_gameplay_drag()
        if self.drag_button == button:
            self.drag_button = None
            self.last_drag_cell = None

    def handle_mouse_motion(
        self, position: tuple[int, int], button_states: tuple[int, int, int]
    ) -> None:
        if self.has_active_modal():
            self.handle_modal_mouse_motion(position, button_states)
            return
        if self.gameplay_drag_cell is not None:
            if not button_states[0]:
                self.clear_gameplay_drag()
                return
            cell = self.screen_to_cell(position)
            if cell is None:
                return
            self.advance_gameplay_drag(cell)
            return
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
        if self.gameplay_state.active or self.search_generator is None or self.search_paused:
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
                if self.gameplay_state.pending_generation:
                    self.activate_gameplay_level(auto_generated=True)
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

    def format_elapsed_time(self, elapsed_seconds: float) -> str:
        total_seconds = max(0, int(elapsed_seconds))
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"

    def lighten_color(self, color: tuple[int, int, int], amount: int = 12) -> tuple[int, int, int]:
        return tuple(min(255, channel + amount) for channel in color)

    def draw_modal_button(
        self,
        rect: pygame.Rect,
        label: str,
        base_color: tuple[int, int, int],
        *,
        text_color: tuple[int, int, int] = MODAL_TEXT_COLOR,
    ) -> None:
        is_hovered = rect.collidepoint(pygame.mouse.get_pos())
        fill_color = self.lighten_color(base_color) if is_hovered else base_color
        pygame.draw.rect(self.screen, fill_color, rect, border_radius=12)
        pygame.draw.rect(self.screen, MODAL_CARD_BORDER_COLOR, rect, 2, border_radius=12)
        text_surface = self.text_font.render(label, True, text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)

    def draw_modal_close_icon(self, rect: pygame.Rect) -> None:
        is_hovered = rect.collidepoint(pygame.mouse.get_pos())
        fill_color = self.lighten_color(MODAL_CLOSE_COLOR, 8) if is_hovered else MODAL_CLOSE_COLOR
        pygame.draw.rect(self.screen, fill_color, rect, border_radius=10)
        pygame.draw.rect(self.screen, MODAL_CARD_BORDER_COLOR, rect, 2, border_radius=10)
        text_surface = self.text_font.render("X", True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)

    def draw_modal_card(self, rect: pygame.Rect) -> None:
        shadow_surface = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surface,
            (8, 14, 24, 46),
            shadow_surface.get_rect(),
            border_radius=22,
        )
        self.screen.blit(shadow_surface, (rect.x - 10, rect.y - 4))
        pygame.draw.rect(self.screen, MODAL_CARD_COLOR, rect, border_radius=20)
        pygame.draw.rect(self.screen, MODAL_CARD_BORDER_COLOR, rect, 2, border_radius=20)

    def draw_success_dialog(self) -> None:
        layout = self.get_success_dialog_layout()
        rect = layout["card"]
        content_left = rect.x + 28
        content_width = rect.width - 56

        self.draw_modal_card(rect)
        self.draw_modal_close_icon(layout["close_icon"])

        self.draw_text("Success", self.section_font, MODAL_TEXT_COLOR, (content_left, rect.y + 28))
        self.draw_text(
            "You reached the goal in Play mode.",
            self.small_font,
            MODAL_MUTED_TEXT_COLOR,
            (content_left, rect.y + 58),
        )
        self.draw_text(
            "Choose what to do next.",
            self.small_font,
            MODAL_MUTED_TEXT_COLOR,
            (content_left, rect.y + 78),
        )

        highlight_box = pygame.Rect(content_left, rect.y + 108, content_width, 62)
        pygame.draw.rect(self.screen, MODAL_INPUT_COLOR, highlight_box, border_radius=14)
        pygame.draw.rect(self.screen, MODAL_CARD_BORDER_COLOR, highlight_box, 2, border_radius=14)
        self.draw_text(
            f"Time: {self.format_elapsed_time(self.modal_state.success.elapsed_seconds)}",
            self.text_font,
            MODAL_TEXT_COLOR,
            (highlight_box.x + 18, highlight_box.y + 16),
        )
        self.draw_text(
            f"Moves: {self.modal_state.success.moves}",
            self.text_font,
            MODAL_TEXT_COLOR,
            (highlight_box.x + 18, highlight_box.y + 38),
        )

        self.draw_modal_button(layout["play_again"], "Play Again", MODAL_SUCCESS_COLOR)

    def draw_grid_size_dialog(self) -> None:
        layout = self.get_grid_size_dialog_layout()
        rect = layout["card"]
        content_left = rect.x + 32
        width_value, height_value = self.get_grid_dialog_dimensions()

        self.draw_modal_card(rect)
        self.draw_modal_close_icon(layout["close_icon"])

        self.draw_text("Grid Size", self.section_font, MODAL_TEXT_COLOR, (content_left, rect.y + 28))
        self.draw_text(
            "Use the quick slider for square grids or open advanced sizing.",
            self.small_font,
            MODAL_MUTED_TEXT_COLOR,
            (content_left, rect.y + 58),
        )
        self.draw_text(
            f"Range: {MIN_GRID_DIMENSION} to {MAX_GRID_DIMENSION} per dimension",
            self.small_font,
            MODAL_MUTED_TEXT_COLOR,
            (content_left, rect.y + 78),
        )

        slider_label = (
            f"Quick Square Slider: {self.modal_state.grid_size.slider_value} x "
            f"{self.modal_state.grid_size.slider_value}"
        )
        self.draw_text(slider_label, self.text_font, MODAL_TEXT_COLOR, (content_left, rect.y + 102))

        track_rect = layout["slider_track"]
        pygame.draw.rect(self.screen, MODAL_INPUT_COLOR, track_rect, border_radius=5)
        thumb_rect = self.get_slider_thumb_rect(track_rect, self.modal_state.grid_size.slider_value)
        filled_track = pygame.Rect(
            track_rect.x,
            track_rect.y,
            max(0, thumb_rect.centerx - track_rect.x),
            track_rect.height,
        )
        pygame.draw.rect(self.screen, MODAL_ACCENT_COLOR, filled_track, border_radius=5)
        pygame.draw.rect(self.screen, MODAL_CARD_BORDER_COLOR, track_rect, 2, border_radius=5)
        pygame.draw.ellipse(self.screen, MODAL_ACCENT_COLOR, thumb_rect)
        pygame.draw.ellipse(self.screen, MODAL_CARD_BORDER_COLOR, thumb_rect, 2)

        self.draw_text(
            f"Selected Size: {width_value} x {height_value}",
            self.text_font,
            MODAL_TEXT_COLOR,
            (content_left, rect.y + 140),
        )

        advanced_label = (
            "Hide Advanced Controls" if self.modal_state.grid_size.advanced_open else "Show Advanced Controls"
        )
        self.draw_modal_button(layout["advanced_toggle"], advanced_label, MODAL_INPUT_ACTIVE_COLOR)

        if self.modal_state.grid_size.advanced_open:
            for field_name, label in (("width", "Width"), ("height", "Height")):
                field_rect = layout[f"{field_name}_card"]
                value_rect = layout[f"{field_name}_value"]
                minus_rect = layout[f"{field_name}_minus"]
                plus_rect = layout[f"{field_name}_plus"]
                value_text = self.modal_state.grid_size.width_text if field_name == "width" else self.modal_state.grid_size.height_text

                pygame.draw.rect(self.screen, MODAL_INPUT_COLOR, field_rect, border_radius=16)
                pygame.draw.rect(self.screen, MODAL_CARD_BORDER_COLOR, field_rect, 2, border_radius=16)
                self.draw_text(label, self.text_font, MODAL_TEXT_COLOR, (field_rect.x + 14, field_rect.y + 16))
                self.draw_modal_button(minus_rect, "-", MODAL_INPUT_ACTIVE_COLOR)
                self.draw_modal_button(plus_rect, "+", MODAL_INPUT_ACTIVE_COLOR)
                pygame.draw.rect(self.screen, MODAL_CARD_COLOR, value_rect, border_radius=10)
                pygame.draw.rect(self.screen, MODAL_CARD_BORDER_COLOR, value_rect, 2, border_radius=10)
                value_surface = self.text_font.render(value_text, True, MODAL_TEXT_COLOR)
                value_text_rect = value_surface.get_rect(center=value_rect.center)
                self.screen.blit(value_surface, value_text_rect)

        self.draw_modal_button(layout["cancel"], "Cancel", MODAL_INPUT_ACTIVE_COLOR)
        self.draw_modal_button(layout["apply"], "Apply", MODAL_SUCCESS_COLOR)

    def draw_active_modal(self) -> None:
        if not self.has_active_modal():
            return

        overlay_surface = pygame.Surface(self.window_size, pygame.SRCALPHA)
        overlay_surface.fill(MODAL_OVERLAY_COLOR)
        self.screen.blit(overlay_surface, (0, 0))

        if self.modal_state.kind == "success":
            self.draw_success_dialog()
        elif self.modal_state.kind == "grid_size":
            self.draw_grid_size_dialog()

    def draw(self) -> None:
        current_surface = pygame.display.get_surface()
        if current_surface is not None:
            self.screen = current_surface
        self.screen.fill(BACKGROUND_COLOR)
        self.draw_grid()
        self.draw_panel()
        self.draw_active_modal()
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
        if self.is_gameplay_engaged():
            gameplay_state = "Preparing" if self.gameplay_state.pending_generation else "Won" if self.gameplay_state.won else "Playing"
            source_label = "Generated Maze" if self.gameplay_state.used_generated_maze else "Current Map"
            stats = [
                f"Mode / State: Gameplay / {gameplay_state}",
                f"Source / Grid: {source_label} / {self.grid_width}x{self.grid_height}",
                f"Moves / Time: {self.gameplay_state.moves} / {self.format_elapsed_time(self.gameplay_state.elapsed_seconds)}",
                f"Player -> Goal: {self.format_cell(self.gameplay_state.player_cell)} -> {self.format_cell(self.goal_cell)}",
                f"Obstacles: {len(self.obstacles)}",
                "Controls: Arrows/WASD, left-drag, N restart, P/Esc exit",
            ]
        else:
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
            (PLAYER_COLOR, "Player"),
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
        elif button.kind == "gameplay":
            is_active = self.is_gameplay_engaged()

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