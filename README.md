*This project has been created as part of the 42 curriculum by ayafit*

![A funny take on my multi-agent pathfinding](https://preview.redd.it/the-worst-pathfinding-ive-ever-seen-v0-4s5kw2r4adwe1.jpeg?width=585&format=pjpg&auto=webp&s=fe5a30cc8ed6e715d9f1524e4f2a7f775ffde1fd)

## Description & Project Overview

`Fly-in` is 42's spin on the classic Multi-Agent Path Finding (hereby referred to as MAPF) problem.

How can we automate routing a bunch of agents (drones) through a graph of varied zones (vertices) and connections (edges)?

My insights towards that question will be explored in this document and my application of `Fly-in`.

## Instructions

Here's the list of make instructions available in my project.

- `install`: Installs the required python modules, in this case it's only `pyglet`

- `run`: Runs the main script of the program.

- `debug`: Runs the main script of the program in debug mode.

- `clean`: Removes python artifacts.

- `lint`: Checks flake8 and mypy compliance.

The first step would be to make a virtual environment to isolate dependencies.

Use the command: `python3 -m venv .venv; source .venv/bin/activate`

After that use the command: `make install`

Followed by: `make run`

The program will launch and you'll need to follow the on-screen instructions.

Once done you can use the command: `deactivate; rm -rf .venv`

## Resources

- CBS for EMPF by Justin Kottinger, Shaull Almagor, Morteza Lahijanian: https://arxiv.org/pdf/2202.09930

- Pyglet documentation: https://pyglet.readthedocs.io/en/latest/index.html

No AI was used in the making of this project

## Algorithmic choice

While researching pathfinding methods I came across multiple viable options such as `Dijkstra's Algorithm`, `Bellman Ford's Algorithm`, `A* Algorithm` and `Conflict Based Search`.

All of these algorithms proved to be efficient at what they do but not quite what I was looking for:

- The `Bellman Ford's Algorithm` can handle negative weights but is otherwise has more overheads than `Dijkstra's Algorithm`.

- The `Dijkstra's Algorithm` explores evenly in all directions meaning it's a greedy algorithm so it ends up being very slow in large graphs.

- The `A* Algorithm` uses an heuristic as a compass to guide itself towards the correct path so it's fast and efficient however it has no way of planning for multiple drones.

- `Conflict Based Search` is a complex algorithm that uses a low level planner to calculate paths and a high level planner to manage drones. Given enough time it will find the most optimal path for each and every map, but it's slow speed makes it challenging to adapt for `Fly-in`.

After reading the paper by Justin Kottinger, Shaull Almagor and Morteza Lahijanian I came to a solution.

Making my own complex algorithm that uses A* as a low level planner and makes space-time reservations as a high level planner to avoid conflicts.

The implementation wasn't particularly challenging. I use Dijkstra's to calculate A*'s heuristic instead of using Manhattan or Euclidean heuristics. We then check if the next proposed move is valid (as in it will not create any conflicts). Afterwich we reserve the path for a drone and repeat until all drones are planned.

This algorithm managed to solve all maps and passes the challenger map with a score of 43.

## Visualization

The visual representation was made using `pyglet` which has no external dependencies and makes use of advanced batching and GPU rendering for excellent performance.

The representation features a game like experience with a space theme. This allows users to see drone paths on the fly (pun intended) and also gives users a final overview on the map state, turns taken, and also supports printing drone movements into the terminal for enhanced user experience.