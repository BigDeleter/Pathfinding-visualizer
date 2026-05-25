"""Shared dataclasses and types for the pathfinding visualizer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import pygame

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


@dataclass
class GameplayState:
    active: bool = False
    pending_generation: bool = False
    player_cell: Optional[Cell] = None
    moves: int = 0
    start_ticks: int = 0
    elapsed_seconds: float = 0.0
    won: bool = False
    used_generated_maze: bool = False


@dataclass
class SuccessDialogState:
    visible: bool = False
    moves: int = 0
    elapsed_seconds: float = 0.0


@dataclass
class GridSizeDialogState:
    visible: bool = False
    slider_value: int = 0
    width_text: str = ""
    height_text: str = ""
    active_field: Optional[str] = None
    advanced_open: bool = False
    dragging_slider: bool = False


@dataclass
class ModalState:
    kind: Optional[str] = None
    hovered_action: Optional[str] = None
    success: SuccessDialogState = field(default_factory=SuccessDialogState)
    grid_size: GridSizeDialogState = field(default_factory=GridSizeDialogState)