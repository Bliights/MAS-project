# MAS project



## Table of Contents
1. [Overview](#overview)
2. [Development](#development)
3. [Project Scope](#project-scope)
4. [Architecture](#architecture)
5. [Protocols](#protocols)
6. [Strategies](#strategies)
7. [Simulation Preview](#simulation-preview)
8. [Contributors](#contributors)

## Overview


## Development
This project follows the best practices we currently rely on for building maintainable Python projects. We use:

- **`uv`** for dependency management  
- **`pre-commit`** for automated code quality checks  
- **`Ruff`** for linting and formatting (a VS Code configuration is included)  
- **`Makefile`** to run common commands consistently

### Requirements
- **Python 3.12**
- [**`uv`**](https://docs.astral.sh/uv/) (recommended) for dependency management and editable installs (alternatively, you can manage dependencies via the `requirements.txt` generated with `uv`).
- **`make`** (recommended) to use the provided Makefile commands (alternatively, you can execute the underlying commands manually).

### Environment setup
Install dependencies and set up `pre-commit` hooks:
```bash
make install
```

### Code quality
Run linting/formatting checks via `pre-commit`:
```bash
make pre-commit
```

## Project Scope
This project focuses on a multi-agent simulation in which robots operate within a hostile environment divided into three distinct radioactivity zones. The environment is modeled as a grid where three different types of robots are deployed, each following its own movement constraints.

Within this setting, a waste transformation process takes place. As the simulation progresses, waste is gradually transformed from green to yellow, and then from yellow to red. At the same time, a dedicated disposal area is positioned on the right edge of the grid, serving as the final destination for all processed waste.

Given this setup, the main objective of the simulation is to maximize waste compaction while ensuring that all waste is efficiently transported to the disposal area.

However, the robots do not operate with complete information. Each robot only has partial knowledge of the system, it is aware of the names of other robots of the same type, and its perception of the environment is limited to the four adjacent tiles (excluding diagonals) and what he has seen.

To tackle these constraints, two different strategies are explored. On the one hand, a basic approach without communication is implemented, where robots act independently using simple behaviors. On the other hand, a more advanced strategy introduces a communication protocol, enabling robots to coordinate their actions and achieve more efficient and optimized waste compaction and transportation.


## Architecture
### Logic
The code is organized around a clear separation between the model, the agents, the objects placed in the environment, and the support classes used for decision making. The `RobotMission` class in [`model.py`](./src/model.py) is the central controller of the simulation. It creates the grid, assigns the radioactivity zones, places wastes and robots, executes actions, generates percepts, and collects the data used for visualization. The robot classes are defined in [`agents.py`](./src/agents.py). `BaseRobot` provides the common structure shared by all robots, including an inventory, a local knowledge base, the generic simulation step, position validation, and random movement. `GreenRobot`, `YellowRobot`, and `RedRobot` then specialize this base class by fixing the accessible zones, the handled waste type, and the decision rules associated with their role in the processing chain.

Several object-oriented support classes were added to make the implementation more modular than a minimal reading of the subject would require. The `Waste`, `Radioactivity`, and `DisposalZone` classes in [`objects.py`](./src/objects.py) explicitly model the entities present on the grid. The `Action` class in [`core/actions.py`](./src/core/actions.py) formalizes what a robot asks the environment to do. The `Inventory` class in [`core/inventory.py`](./src/core/inventory.py) isolates waste storage and manipulation inside each robot. The `Knowledge` class in [`core/knowledge.py`](./src/core/knowledge.py) stores the robot's current position, its percept history, and its local map memory. The `Percepts` and `TileContent` data structures in [`core/percepts.py`](./src/core/percepts.py) standardize what a robot can observe at each step. The zone system is also encapsulated in dedicated classes in [`core/zones.py`](./src/core/zones.py), with `Z1`, `Z2`, and `Z3` representing the three radioactivity intervals and `Zones` grouping the global configuration. We have also the [`core/enums.py`](./src/core/enums.py) that centralizes the enumerations for colors, action types, and waste types, which keeps the rest of the code simpler and more consistent. Finally we have the communication part that use a `MessageService` in [`communication/service.py`](./src/communication/service.py) to deliver the message, the `Message` class in [`communication/enums.py`](./src/communication/enums.py) to formalize the content of the messages sent between robots and finally the `Mailbox` class in [`communication/mailbox.py`](./src/communication/mailbox.py) to store the messages received by each robot and the future message to send.

Here is a quick class diagram to illustrate our architecture (each link mean "has an instance of" or "uses an instance of"):

![Class Diagram](./assets/class_diagram.png)


### Visualization
The visualization layer is separated from the simulation logic. The [`server.py`](./src/server.py) file defines the Solara interface, the graphical rendering of the grid, and the plots that track the number of green, yellow, and red wastes over time. The [`run.py`](./src/run.py) file only exposes this page as the application entry point. This organization keeps the interface code distinct from the environment rules and the decision logic.

Here is a quick overview of simulation displays:

![Display_1](./assets/display_example_1.png)
![Display_2](./assets/display_example_2.png)


## Protocols
In our project, communication between agents is only triggered in specific situations rather than being used continuously. More precisely, an agent initiates communication when it is carrying a piece of waste and no other waste remains available on the ground. In this context, collaboration becomes necessary to continue optimizing the process.

To achieve this, the agent starts a first communication protocol by reaching out to other agents of the same type and asks whether they are also carrying waste and if they are available to engage in communication. If another agent responds positively, a communication link is established between the two. 

The diagram below illustrates this initial communication phase:

![Communication_protocol](./assets/communication_protocol.png)

Once communication is established, the two agents must coordinate their actions to safely exchange waste. The first step is to reserve a tile in the environment to ensures that no other agent can interfere during the process, for example by picking up the waste involved in the exchange.

After reserving the tile, both agents move toward this shared location and when they confirm that they are on the same tile, they proceed with the exchange of waste. Finally, once the exchange is completed, they communicate one last time to release the tile, making it available again for the rest of the system. 

The following diagram presents this second phase of the protocol:

![Transfer_protocol](./assets/transfer_protocol.png)


## Strategies
### Random
***
For the random strategy without communication, each robot simply follows a set of basic rules based on its current state and the local information it has. The robots move randomly until they find two pieces of waste they can transform and once the transformation is done, they drop the resulting waste as far to the right as possible within the part of the grid they can access. Then, they continue moving randomly until they find more waste, and repeat this process.

Here are the main behaviors for each type of robot, in order of priority:

**Green Robots:**
- If the robots has a yellow waste in inventory, it tries to drop it as far right as possible within its accessible area
- If it can transform 2 green wastes into a yellow waste, it does it
- If there is a green waste on the ground, it picks it up
- Otherwise, it moves randomly, but if it sees a green waste nearby, it moves toward it

**Yellow Robots:**
- If the robot has a red waste in its inventory, it tries to drop it as far right as possible within its accessible area
- If it can transform 2 yellow wastes into a red waste, it does it
- If there is a yellow waste on the ground, it picks it up
- Otherwise, it moves randomly, but if it sees a yellow waste nearby, it moves toward it

**Red Robots:**
- If the robot has a red waste in its inventory, it tries to drop it in the disposal area (right side of the grid)
- If it is not in the disposal zone and there is a red waste on the ground, it picks it up
- Otherwise, it moves randomly, but if it sees a red waste nearby, it moves toward it (except if it is close to the disposal zone)


### Communication
***
For the communication strategy, the behavior is quite different. Here, robots can exchange waste between each other, which allows a more optimal compaction strategy and a better organization of waste positions.

- Green robots still move randomly, but they now drop all waste at a specific target position. Moreover, when they are blocked (for example, when they cannot transform waste alone) they initiate a communication to exchange waste with another robot in order to proceed with the transformation and if it is the last waste, it is directly placed at the target position.
- Yellow robots start from the target position of the green robots which allows them to immediately collect the transformed waste produced by the green robots. Similarly, if they are blocked, they can communicate to exchange waste and continue the process.
- Finally, red robots start from the target position of the yellow robots and they collect all the waste dropped by the yellow robots and transport it to the disposal zone.

Here are the main behaviors for each type of robot, in order of priority:

**Green Robots:**
- If the robot has a communication action to perform (read message, send message, etc.), it does it first
- If the robot has a green waste and it is the last green waste, it drops it on the target zone
- If the robot has a green waste and there is no other green waste on the ground, it tries to start a communication with another robot to merge them
- If it has a yellow waste in its inventory, it drops it on the target zone
- If it can transform 2 green wastes into a yellow waste, it does it
- If there is a green waste on the ground, it picks it up (except if it is the last one already in the target position)
- Otherwise, it moves randomly, but if it sees a green waste nearby, it moves toward it

**Yellow Robots:**
- If the robot has a communication action to perform, it does it first
- If the robot has a yellow waste and it is the last yellow waste, it drops it in the target zone
- If the robot has a yellow waste and there is no other yellow waste on the ground, it tries to start a communication to merge them
- If it has a yellow or green waste in its inventory, it moves it toward the target zone
- If it can transform 2 yellow wastes into a red waste, it does it
- If there is a yellow waste on the ground, it picks it up (except if it is the last one already in the target position)
- If there is only one green waste left on the ground, it picks it up
- If it is at its start position, it waits
- Otherwise, it moves toward its start position

**Red Robots:**
- If the robot has a communication action to perform, it does it first
- If the robot has a waste, it drops it in the disposal zone
- If there is a waste on the ground outside the first zone, it picks it up
- If it is at its start position, it waits
- Otherwise, it moves toward its start position


### Results
***



## Simulation Preview
launch the simulation with:
```bash
make solara-server
```

## Contributors

|            Name            |                Email                  |
| :------------------------: | :-----------------------------------: |
|    MOLLY-MITTON Clément    |    clement.mollymitton@gmail.com      |
|       VERBECQ DIANE        |        diane.verbecq@gmail.com        |
