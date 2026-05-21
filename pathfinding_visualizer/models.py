"""Shared dataclasses and types for the pathfinding visualizer."""

from __future__ import annotations

from dataclasses import dataclass
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