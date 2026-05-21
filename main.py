from __future__ import annotations

from collections import deque
import heapq
import math
from dataclasses import dataclass
from typing import Callable, Generator, Optional

try:
    import pygame
except ImportError as exc:
    raise SystemExit(
        "pygame is required. Install dependencies with: pip install -r requirements.txt"
    ) from exc


GRID_SIZE = 100
CELL_SIZE = 8
GRID_PIXELS = GRID_SIZE * CELL_SIZE
PANEL_WIDTH = 360
WINDOW_WIDTH = GRID_PIXELS + PANEL_WIDTH
WINDOW_HEIGHT = GRID_PIXELS
WINDOW_FLAGS = pygame.RESIZABLE
FPS = 60

ALGORITHM_HEADER_Y = 44
ALGORITHM_BUTTON_ROWS = (72, 118)
EDIT_HEADER_Y = 168
EDIT_BUTTON_ROWS = (196, 240)
CONTROLS_HEADER_Y = 290
CONTROL_BUTTON_ROWS = (318, 362)
SPEED_HEADER_Y = 412
SPEED_BUTTON_Y = 440

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
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), WINDOW_FLAGS)
        self.clock = pygame.time.Clock()
        self.grid_surface = pygame.Surface((GRID_PIXELS, GRID_PIXELS)).convert()

        self.title_font = pygame.font.SysFont("consolas", 28, bold=True)
        self.section_font = pygame.font.SysFont("consolas", 20, bold=True)
        self.text_font = pygame.font.SysFont("consolas", 16)
        self.small_font = pygame.font.SysFont("consolas", 14)

        self.selected_algorithm = "A*"
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
        self.search_paused = False
        self.status_message = "Place start, goal, and obstacles. Then press Run."

        self.drag_button: Optional[int] = None
        self.last_drag_cell: Optional[Cell] = None

        self.buttons: list[Button] = []
        self._build_buttons()

    def _build_buttons(self) -> None:
        panel_left = GRID_PIXELS + 20
        two_col_width = 150
        two_col_gap = 18
        row_height = 38
        three_col_width = 96
        three_col_gap = 10

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
            Button("Run", rect_2col(CONTROL_BUTTON_ROWS[0], 0), self.start_search),
            Button("Pause", rect_2col(CONTROL_BUTTON_ROWS[0], 1), self.toggle_pause),
            Button("Clear Path", rect_2col(CONTROL_BUTTON_ROWS[1], 0), self.clear_search_state),
            Button("Clear Map", rect_2col(CONTROL_BUTTON_ROWS[1], 1), self.clear_map),
            Button("Slow", rect_3col(SPEED_BUTTON_Y, 0), lambda: self.set_speed(1), "speed", 1),
            Button("Medium", rect_3col(SPEED_BUTTON_Y, 1), lambda: self.set_speed(4), "speed", 4),
            Button("Fast", rect_3col(SPEED_BUTTON_Y, 2), lambda: self.set_speed(16), "speed", 16),
        ]

    def set_algorithm(self, algorithm: str) -> None:
        if algorithm == self.selected_algorithm:
            return
        self.selected_algorithm = algorithm
        self.clear_search_state(silent=True)
        self.status_message = f"Algorithm switched to {algorithm}."

    def set_edit_mode(self, mode: str) -> None:
        self.edit_mode = mode
        self.status_message = f"Edit mode: {mode}."

    def set_speed(self, steps_per_frame: int) -> None:
        self.steps_per_frame = steps_per_frame
        labels = {1: "slow", 4: "medium", 16: "fast"}
        self.status_message = f"Animation speed set to {labels.get(steps_per_frame, steps_per_frame)}."

    def clear_search_overlay(self) -> None:
        self.open_cells = set()
        self.closed_cells = set()
        self.current_cell = None
        self.path_cells = []
        self.path_lookup = set()
        self.visited_count = 0
        self.path_cost = None

    def clear_search_state(self, silent: bool = False) -> None:
        self.search_generator = None
        self.search_paused = False
        self.clear_search_overlay()
        if not silent:
            self.status_message = "Search state cleared."

    def clear_map(self) -> None:
        self.start_cell = None
        self.goal_cell = None
        self.obstacles.clear()
        self.clear_search_state(silent=True)
        self.status_message = "Map cleared."

    def toggle_pause(self) -> None:
        if self.search_generator is None:
            self.status_message = "No active search to pause."
            return
        self.search_paused = not self.search_paused
        if self.search_paused:
            self.status_message = f"{self.selected_algorithm} paused."
        else:
            self.status_message = f"{self.selected_algorithm} resumed."

    def start_search(self) -> None:
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

    def run(self) -> None:
        running = True
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.handle_resize(event.w, event.h)
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_down(event.pos, event.button)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.handle_mouse_up(event.button)
                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos, event.buttons)

            self.advance_search()
            self.draw()

        pygame.quit()

    def handle_resize(self, width: int, height: int) -> None:
        min_width = GRID_PIXELS + 220
        min_height = 560
        clamped_width = max(width, min_width)
        clamped_height = max(height, min_height)
        if (clamped_width, clamped_height) == self.screen.get_size():
            return
        self.screen = pygame.display.set_mode((clamped_width, clamped_height), WINDOW_FLAGS)

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
        if self.search_generator is not None or self.path_cells or self.closed_cells or self.open_cells:
            self.clear_search_state(silent=True)
            self.status_message = "Map changed. Cleared the previous search state."

        self.last_drag_cell = cell

        if button == 3 or self.edit_mode == "erase":
            self.erase_cell(cell)
            return

        if self.edit_mode == "obstacle":
            if cell == self.start_cell or cell == self.goal_cell:
                return
            self.obstacles.add(cell)
            return

        if self.edit_mode == "start":
            self.obstacles.discard(cell)
            if cell == self.goal_cell:
                self.goal_cell = None
            self.start_cell = cell
            return

        if self.edit_mode == "goal":
            self.obstacles.discard(cell)
            if cell == self.start_cell:
                self.start_cell = None
            self.goal_cell = cell

    def erase_cell(self, cell: Cell) -> None:
        if cell == self.start_cell:
            self.start_cell = None
        elif cell == self.goal_cell:
            self.goal_cell = None
        else:
            self.obstacles.discard(cell)

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

    def apply_frame(self, frame: SearchFrame) -> None:
        self.open_cells = frame.open_cells
        self.closed_cells = frame.closed_cells
        self.current_cell = frame.current_cell
        self.path_cells = frame.path_cells
        self.path_lookup = set(frame.path_cells)
        self.visited_count = frame.visited_count
        self.path_cost = frame.path_cost

        if frame.done and frame.found and frame.path_cost is not None:
            self.status_message = f"{self.selected_algorithm} found a path with cost {frame.path_cost:.2f}."
        else:
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

            if not (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE):
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
        x, y = position
        if not (0 <= x < GRID_PIXELS and 0 <= y < GRID_PIXELS):
            return None
        return x // CELL_SIZE, y // CELL_SIZE

    def get_panel_layout(self) -> dict[str, pygame.Rect]:
        panel_left = GRID_PIXELS + 16
        panel_width = self.screen.get_width() - GRID_PIXELS - 32
        gap = 10
        bottom_margin = 16
        stats_height = 96
        legend_height = 92
        status_height = 54

        status_rect = pygame.Rect(
            panel_left,
            self.screen.get_height() - bottom_margin - status_height,
            panel_width,
            status_height,
        )
        legend_rect = pygame.Rect(
            panel_left,
            status_rect.top - gap - legend_height,
            panel_width,
            legend_height,
        )
        stats_rect = pygame.Rect(
            panel_left,
            legend_rect.top - gap - stats_height,
            panel_width,
            stats_height,
        )
        return {
            "stats": stats_rect,
            "legend": legend_rect,
            "status": status_rect,
        }

    def format_cell(self, cell: Optional[Cell]) -> str:
        return str(cell) if cell is not None else "--"

    def draw(self) -> None:
        self.screen.fill(BACKGROUND_COLOR)
        self.draw_grid()
        self.draw_panel()
        pygame.display.flip()

    def draw_grid(self) -> None:
        self.grid_surface.fill(GRID_LINE_COLOR)

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                cell = (x, y)
                color = EMPTY_COLOR

                if cell == self.start_cell:
                    color = START_COLOR
                elif cell == self.goal_cell:
                    color = GOAL_COLOR
                elif cell in self.obstacles:
                    color = OBSTACLE_COLOR
                elif cell == self.current_cell:
                    color = CURRENT_COLOR
                elif cell in self.path_lookup:
                    color = PATH_COLOR
                elif cell in self.closed_cells:
                    color = CLOSED_COLOR
                elif cell in self.open_cells:
                    color = OPEN_COLOR

                rect = pygame.Rect(
                    x * CELL_SIZE + 1,
                    y * CELL_SIZE + 1,
                    CELL_SIZE - 1,
                    CELL_SIZE - 1,
                )
                pygame.draw.rect(self.grid_surface, color, rect)

        visible_rect = pygame.Rect(
            0,
            0,
            min(GRID_PIXELS, self.screen.get_width()),
            min(GRID_PIXELS, self.screen.get_height()),
        )
        self.screen.blit(self.grid_surface, (0, 0), visible_rect)

    def draw_panel(self) -> None:
        panel_width = self.screen.get_width() - GRID_PIXELS
        panel_height = self.screen.get_height()
        panel_left = GRID_PIXELS + 20
        panel_rect = pygame.Rect(GRID_PIXELS, 0, panel_width, panel_height)
        pygame.draw.rect(self.screen, PANEL_COLOR, panel_rect)
        pygame.draw.line(
            self.screen,
            PANEL_SECTION_COLOR,
            (GRID_PIXELS, 0),
            (GRID_PIXELS, panel_height),
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

        self.draw_text("Stats", self.text_font, TEXT_COLOR, (stats_rect.x + 12, stats_rect.y + 8))
        self.draw_text("Legend", self.text_font, TEXT_COLOR, (legend_rect.x + 12, legend_rect.y + 8))
        self.draw_text("Status", self.text_font, TEXT_COLOR, (status_rect.x + 12, status_rect.y + 8))

        speed_labels = {1: "Slow", 4: "Medium", 16: "Fast"}
        path_cost_text = f"{self.path_cost:.2f}" if self.path_cost is not None else "--"
        stats = [
            f"Algorithm: {self.selected_algorithm}",
            f"Edit mode: {self.edit_mode}",
            f"Visited / Cost: {self.visited_count} / {path_cost_text}",
            f"Obstacles / Speed: {len(self.obstacles)} / {speed_labels.get(self.steps_per_frame, self.steps_per_frame)}",
            f"Start -> Goal: {self.format_cell(self.start_cell)} -> {self.format_cell(self.goal_cell)}",
        ]
        text_y = stats_rect.y + 30
        for line in stats:
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
        for index, (color, label) in enumerate(legend_items):
            column = index % 2
            row = index // 2
            swatch_x = legend_rect.x + 12 + column * legend_column_width
            swatch_y = legend_rect.y + 30 + row * 18
            swatch_rect = pygame.Rect(swatch_x, swatch_y, 14, 14)
            pygame.draw.rect(self.screen, color, swatch_rect, border_radius=3)
            self.draw_text(label, self.small_font, MUTED_TEXT_COLOR, (swatch_x + 22, swatch_y - 1))

        wrapped_status = self.wrap_text(self.status_message, self.small_font, status_rect.width - 24)
        for index, line in enumerate(wrapped_status[:2]):
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