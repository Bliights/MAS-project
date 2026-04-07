"""
Groupe 10
16/03/2026
Clément MOLLY-MITTON
Diane VERBECQ
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import solara
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from mesa.visualization import SolaraViz
from mesa.visualization.utils import update_counter

from src.agents import BaseRobot
from src.core.enums import Colour, Strategy, WasteType
from src.model import RobotMission
from src.objects import DisposalZone, Waste

if TYPE_CHECKING:
    from mesa import Model

    from src.communication.enums import Message


def get_cell_background(x: int, y: int, model: Model) -> str:
    """
    Determine the background color of a grid cell based on its zone

    Parameters
    ----------
    x : int
        The x-coordinate of the cell
    y : int
        The y-coordinate of the cell
    model : Model
        The simulation model containing zone configuration

    Returns
    -------
    str
        A color string representing the zone (hex format)
    """
    tile = model.grid.get_cell_list_contents([(x, y)])

    for obj in tile:
        if isinstance(obj, DisposalZone):
            return "#4b0082"  # Purple

    if x < model.zone_width:
        return "#e8f5e9"  # Light green
    if x < 2 * model.zone_width:
        return "#fff9c4"  # Light yellow
    return "#ffebee"  # Light red


def waste_color(waste_type: WasteType) -> str:
    """
    Map a waste type to its display color

    Parameters
    ----------
    waste_type : WasteType
        The type of waste

    Returns
    -------
    str
        A color string used for visualization
    """
    if waste_type == WasteType.GREEN:
        return "limegreen"
    if waste_type == WasteType.YELLOW:
        return "gold"
    return "darkred"


def robot_color(robot: BaseRobot) -> str:
    """
    Map a robot to its display color based on its type

    Parameters
    ----------
    robot : BaseRobot
        The robot instance

    Returns
    -------
    str
        A color string representing the robot type
    """
    if robot.colour == Colour.GREEN:
        return "green"
    if robot.colour == Colour.YELLOW:
        return "gold"
    return "red"


@solara.component
def grid_view(model: Model) -> None:
    """
    Render the main environment grid

    This visualization displays:
        - the grid structure with zone-based background colors,
        - wastes present on each cell,
        - robots and their carried wastes,
        - a legend explaining the visual encoding

    Parameters
    ----------
    model : Model
        The simulation model containing agents and grid state
    """
    update_counter.get()

    fig = Figure(figsize=(8, 4))
    ax = fig.subplots()

    # Grid
    for x in range(model.width):
        for y in range(model.height):
            rect = Rectangle(
                (x, y),
                1,
                1,
                facecolor=get_cell_background(x, y, model),
                edgecolor="lightgray",
                linewidth=0.8,
            )
            ax.add_patch(rect)

            cell_agents = model.grid.get_cell_list_contents([(x, y)])
            robots = [a for a in cell_agents if isinstance(a, BaseRobot)]
            wastes = [a for a in cell_agents if isinstance(a, Waste)]

            # Wastes
            for i, waste in enumerate(wastes):
                ax.scatter(
                    x + 0.78,
                    y + 0.78 - 0.16 * i,
                    s=80,
                    marker="s",
                    c=waste_color(waste.type),
                    edgecolors="black",
                    linewidths=0.5,
                    zorder=2,
                )

            # Robots
            for i, robot in enumerate(robots):
                rx = x + 0.35 + 0.18 * i
                ry = y + 0.35

                ax.scatter(
                    rx,
                    ry,
                    s=220,
                    marker="o",
                    c=robot_color(robot),
                    edgecolors="black",
                    linewidths=0.8,
                    zorder=3,
                )

                # robots + wastes
                if robot.inventory.wastes:
                    ax.scatter(
                        rx + 0.16,
                        ry + 0.16,
                        s=45,
                        marker="s",
                        c=waste_color(robot.inventory.wastes[0].type),
                        edgecolors="black",
                        linewidths=0.5,
                        zorder=4,
                    )
                    ax.text(
                        rx + 0.16,
                        ry + 0.16,
                        str(len(robot.inventory.wastes)),
                        fontsize=6,
                        color="black",
                        ha="center",
                        va="center",
                        zorder=5,
                        fontweight="bold",
                    )

    ax.axvline(model.zone_width, color="gray", linewidth=2)
    ax.axvline(model.zone_width * 2, color="gray", linewidth=2)

    ax.set_xlim(0, model.width)
    ax.set_ylim(0, model.height)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.tick_params(length=0)
    ax.set_title("Environment grid")

    # Legend
    ly = -0.8
    lx = 2
    step = 3

    # Robot
    ax.scatter(
        lx,
        ly,
        s=220,
        marker="o",
        c="green",
        edgecolors="black",
        linewidths=0.8,
        zorder=3,
        clip_on=False,
    )
    ax.text(lx + 0.5, ly, "Robot", va="center", fontsize=10, clip_on=False)

    # Waste
    ax.scatter(
        lx + step,
        ly,
        s=80,
        marker="s",
        c="limegreen",
        edgecolors="black",
        linewidths=0.5,
        zorder=2,
        clip_on=False,
    )
    ax.text(lx + step + 0.4, ly, "Waste on ground", va="center", fontsize=10, clip_on=False)

    # Robot with waste
    ax.scatter(
        lx + 2.7 * step,
        ly,
        s=220,
        marker="o",
        c="green",
        edgecolors="black",
        linewidths=0.8,
        zorder=3,
        clip_on=False,
    )
    ax.scatter(
        lx + 2.7 * step + 0.16,
        ly + 0.16,
        s=45,
        marker="s",
        c="limegreen",
        edgecolors="black",
        linewidths=0.5,
        zorder=4,
        clip_on=False,
    )
    ax.text(
        lx + 2.7 * step + 0.16,
        ly + 0.16,
        "1",
        fontsize=6,
        color="black",
        ha="center",
        va="center",
        zorder=5,
        fontweight="bold",
        clip_on=False,
    )
    ax.text(
        lx + 2.7 * step + 0.5,
        ly,
        "Robot carrying waste",
        va="center",
        fontsize=10,
        clip_on=False,
    )

    solara.FigureMatplotlib(fig)


@solara.component
def waste_count_histogram(model: Model) -> None:
    """
    Display a histogram of current waste counts

    Parameters
    ----------
    model : Model
        The simulation model with collected data
    """
    update_counter.get()

    data = model.datacollector.get_model_vars_dataframe()

    last = data.iloc[-1]

    fig = Figure(figsize=(8, 4))
    ax = fig.subplots()

    labels = ["green", "yellow", "red"]
    values = [last["green_waste"], last["yellow_waste"], last["red_waste"]]
    colors = ["limegreen", "gold", "darkred"]

    ax.bar(labels, values, color=colors, edgecolor="black")
    ax.set_ylabel("Number of wastes")
    ax.set_title("Total waste counts")

    for i, value in enumerate(values):
        ax.text(i, value + 0.1, str(value), ha="center")

    solara.FigureMatplotlib(fig)


@solara.component
def waste_evolution_plot(model: Model) -> None:
    """
    Plot the evolution of waste quantities over time

    Parameters
    ----------
    model : Model
        The simulation model with recorded time-series data
    """
    update_counter.get()

    data = model.datacollector.get_model_vars_dataframe()

    fig = Figure(figsize=(8, 4))
    ax = fig.subplots()

    x = data.index

    ax.plot(x, data["green_waste"], label="Green waste", color="green", linewidth=2)
    ax.plot(x, data["yellow_waste"], label="Yellow waste", color="gold", linewidth=2)
    ax.plot(x, data["red_waste"], label="Red waste", color="red", linewidth=2)

    ax.set_xlabel("Step")
    ax.set_ylabel("Number of wastes")
    ax.set_title("Waste evolution over time")
    ax.legend()
    ax.grid(True, alpha=0.3)

    solara.FigureMatplotlib(fig)


def format_messages(messages: list[Message]) -> str:
    """
    Convert a list of messages into a readable one-line string

    Parameters
    ----------
    messages : list[Message]
        The messages to format

    Returns
    -------
    str
        A formatted string containing all messages, or "-" if the list is empty
    """
    if not messages:
        return "-"
    return " | ".join(
        f"{m.sender}->{m.receiver}:{m.performative.name}/{m.type.name}" for m in messages
    )


def format_wastes(wastes: list[Waste]) -> str:
    """
    Convert a list of carried wastes into a readable string

    Parameters
    ----------
    wastes : list[Waste]
        The wastes to format

    Returns
    -------
    str
        A formatted string of waste types, or "-" if the list is empty
    """
    if not wastes:
        return "-"
    return ", ".join(w.type.name for w in wastes)


@solara.component
def agents_debug_table(model: Model) -> None:
    """
    Display a debug table showing the last recorded state of all robots before the execution of the action

    Parameters
    ----------
    model : Model
        The simulation model
    """
    update_counter.get()

    robots = [agent for agent in model.agents if isinstance(agent, BaseRobot)]
    robots = sorted(robots, key=lambda robot: robot.name)

    rows = [
        {
            "Agent": robot.last_infos.get("agent", robot.name),
            "Pos": str(robot.last_infos.get("pos", "-")),
            "Last action": (
                f"{robot.last_infos.get('action', '-')}"
                + (
                    f" | payload={robot.last_infos.get('payload')}"
                    if robot.last_infos.get("payload") is not None
                    else ""
                )
            ),
            "Status": robot.last_infos.get("status", "-"),
            "Available": (
                "-"
                if robot.last_infos.get("available", -1) < model.current_step
                else robot.last_infos.get("available")
            ),
            "Reserved": str(robot.last_infos.get("reserved", "-")),
            "Partner": robot.last_infos.get("current_partner", "-") or "-",
            "Meeting point": str(robot.last_infos.get("meeting_point", "-")),
            "Wastes": format_wastes(robot.last_infos.get("wastes", [])),
            "Unread": format_messages(robot.last_infos.get("message_receive", [])),
            "Outbox": format_messages(robot.last_infos.get("message_outbox", [])),
        }
        for robot in robots
    ]

    df = pd.DataFrame(rows)

    with solara.Column():
        solara.Markdown(f"### Agents state — step {model.current_step}")
        solara.DataFrame(df, items_per_page=10, scrollable=True)


@solara.component
def distance_plot(model: Model) -> None:
    """
    Plot the evolution of total waste distance to disposal zone

    Parameters
    ----------
    model : Model
        The simulation model
    """
    update_counter.get()

    data = model.datacollector.get_model_vars_dataframe()

    fig = Figure(figsize=(8, 4))
    ax = fig.subplots()

    x = data.index

    ax.plot(x, data["total_distance"], linewidth=2)

    ax.set_xlabel("Step")
    ax.set_ylabel("Total distance")
    ax.set_title("Total waste distance to disposal zone")
    ax.grid(True, alpha=0.3)

    solara.FigureMatplotlib(fig)


model_params = {
    "width": 15,
    "height": 10,
    "strategy": {
        "type": "Select",
        "value": Strategy.COMMUNICATION,
        "label": "Strategy",
        "values": list(Strategy),
    },
    "n_green_waste": {
        "type": "SliderInt",
        "value": 12,
        "label": "Initial green waste",
        "min": 1,
        "max": 30,
        "step": 1,
    },
    "n_green_robots": {
        "type": "SliderInt",
        "value": 5,
        "label": "Green robots",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "n_yellow_robots": {
        "type": "SliderInt",
        "value": 3,
        "label": "Yellow robots",
        "min": 1,
        "max": 10,
        "step": 1,
    },
    "n_red_robots": {
        "type": "SliderInt",
        "value": 2,
        "label": "Red robots",
        "min": 1,
        "max": 10,
        "step": 1,
    },
}

model = RobotMission(
    model_params["width"],
    model_params["height"],
    model_params["strategy"]["value"],
    model_params["n_green_waste"]["value"],
    model_params["n_green_robots"]["value"],
    model_params["n_yellow_robots"]["value"],
    model_params["n_red_robots"]["value"],
)

page = SolaraViz(
    model,
    components=[
        grid_view,
        agents_debug_table,
        waste_count_histogram,
        waste_evolution_plot,
        distance_plot,
    ],
    model_params=model_params,
    name="Robot Mission - Simple Init",
)
