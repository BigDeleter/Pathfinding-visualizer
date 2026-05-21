# Pathfinding Visualizer

English | [中文](#中文说明)

An interactive `pygame` desktop visualizer for grid-based path planning on a `100 x 100` map. Users can place the start point, goal point, and obstacles, then watch different algorithms explore the grid and build the final path in real time.

## Features

- Fixed `100 x 100` grid map
- Interactive editing for start, goal, obstacles, and erasing cells
- Dynamic visualization of:
  - A*
  - Dijkstra
  - BFS
  - Greedy Best-First Search
  - Bidirectional A*
- Real-time display of explored nodes, current node, open set, closed set, and final path
- Adjustable animation speed
- Resizable window
- 8-direction movement with no corner cutting

## Requirements

- Python `3.13` recommended
- `pygame >= 2.5`

Install dependencies with:

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Controls

### Mouse

- Left click: apply the current edit mode
- Right click: erase the selected cell

### Edit Modes

- `Obstacle`: place obstacles
- `Set Start`: place the start point
- `Set Goal`: place the goal point
- `Erase`: clear a cell

### Keyboard Shortcuts

- `A`: switch to A*
- `D`: switch to Dijkstra
- `B`: switch to BFS
- `G`: switch to Greedy Best-First Search
- `I`: switch to Bidirectional A*
- `1`: obstacle mode
- `2`: set start mode
- `3`: set goal mode
- `4`: erase mode
- `Enter`: start search
- `Space`: pause or resume
- `C`: clear current path
- `M`: clear the map
- `Esc`: interrupt the current search

## Path Planning Rules

- 8-direction movement is enabled
- Straight moves cost `1`
- Diagonal moves cost `sqrt(2)`
- Diagonal corner cutting through blocked cells is not allowed

## Algorithm Notes

### A*

Uses both the traveled cost and the heuristic distance. It usually finds the optimal path with fewer explored nodes than Dijkstra.

### Dijkstra

Uses only the traveled cost. It guarantees an optimal path but often explores a larger area.

### BFS

Useful as a baseline search on an unweighted grid. It expands layer by layer.

### Greedy Best-First Search

Uses only the heuristic distance to the goal. It often appears very fast, but it does not guarantee the shortest path.

### Bidirectional A*

Searches from both the start and goal sides. It can reduce search effort on many maps.

## Project Files

- [main.py](main.py): application entry point, UI, interaction logic, and pathfinding algorithms
- [requirements.txt](requirements.txt): project dependency list

## Notes

- The current implementation is intentionally kept in a single Python file for easier demonstration and sharing.
- If the window height becomes smaller than the full grid, the visible area is clipped safely instead of crashing.

---

## 中文说明

这是一个基于 `pygame` 的交互式桌面路径规划演示程序，地图固定为 `100 x 100` 网格。用户可以手动设置起点、终点和障碍物，并动态查看不同算法的搜索过程与最终路径。

### 功能特点

- 固定 `100 x 100` 网格地图
- 支持交互设置起点、终点、障碍物和擦除格子
- 支持以下算法的动态演示：
  - A*
  - Dijkstra
  - BFS
  - Greedy Best-First Search
  - Bidirectional A*
- 支持显示开放集、关闭集、当前扩展节点和最终路径
- 支持调节动画速度
- 支持窗口缩放
- 支持 8 方向移动，且禁止穿角

### 运行环境

- 推荐 Python `3.13`
- 依赖：`pygame >= 2.5`

安装依赖：

```bash
python -m pip install -r requirements.txt
```

运行程序：

```bash
python main.py
```

### 快捷键

- `A`：切换到 A*
- `D`：切换到 Dijkstra
- `B`：切换到 BFS
- `G`：切换到 Greedy
- `I`：切换到 Bidirectional A*
- `1`：障碍物模式
- `2`：设置起点
- `3`：设置终点
- `4`：擦除模式
- `Enter`：开始搜索
- `Space`：暂停或继续
- `C`：清除当前路径
- `M`：清空地图
- `Esc`：中断当前搜索

### 规则说明

- 允许 8 方向移动
- 直线移动代价为 `1`
- 对角线移动代价为 `sqrt(2)`
- 不允许从两个障碍物夹角处斜向穿过

### 说明

- 当前项目使用单文件结构，便于演示、运行和上传。
- 当窗口高度小于完整网格时，程序会安全裁剪可见区域，而不会报错退出。