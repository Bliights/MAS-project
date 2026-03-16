"""
Groupe 10
16/03/2026
Clément MOLLY-MITTON
Diane VERBECQ
"""

import solara
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from mesa.visualization import SolaraViz
from mesa.visualization.utils import update_counter

from model import RobotMission, RobotAgent, WasteAgent


def get_cell_background(x, model):
    if x < model.z1_limit:
        return "#e8f5e9"   # vert pastel
    elif x < model.z2_limit:
        return "#fff9c4"   # jaune pastel
    else:
        return "#ffebee"   # rouge pastel


def waste_color(waste_type):
    if waste_type == "green":
        return "limegreen"
    if waste_type == "yellow":
        return "gold"
    return "darkred"


def robot_color(robot_type):
    if robot_type == "green":
        return "green"
    if robot_type == "yellow":
        return "gold"
    return "red"


@solara.component
def GridView(model):
    update_counter.get()

    fig = Figure(figsize=(9, 6))
    ax = fig.subplots()

    for x in range(model.width):
        for y in range(model.height):
            rect = Rectangle(
                (x, y),
                1,
                1,
                facecolor=get_cell_background(x, model),
                edgecolor="lightgray",
                linewidth=0.8,
            )
            ax.add_patch(rect)

            cell_agents = model.grid.get_cell_list_contents([(x, y)])
            robots = [a for a in cell_agents if isinstance(a, RobotAgent)]
            wastes = [a for a in cell_agents if isinstance(a, WasteAgent)]

            # 1) Déchets au sol
            # petits carrés placés en haut à droite de la case
            for i, waste in enumerate(wastes):
                ax.scatter(
                    x + 0.78,
                    y + 0.78 - 0.16 * i,
                    s=80,
                    marker="s",
                    c=waste_color(waste.waste_type),
                    edgecolors="black",
                    linewidths=0.5,
                    zorder=2,
                )

            # 2) Robots
            # cercle au centre/bas de la case
            for i, robot in enumerate(robots):
                rx = x + 0.35 + 0.18 * i
                ry = y + 0.35

                ax.scatter(
                    rx,
                    ry,
                    s=220,
                    marker="o",
                    c=robot_color(robot.robot_type),
                    edgecolors="black",
                    linewidths=0.8,
                    zorder=3,
                )

                # 3) Déchet porté
                # mini-carré collé au robot, pour montrer qu'il se déplace avec lui
                if robot.carrying is not None:
                    ax.scatter(
                        rx + 0.16,
                        ry + 0.16,
                        s=45,
                        marker="s",
                        c=waste_color(robot.carrying),
                        edgecolors="black",
                        linewidths=0.5,
                        zorder=4,
                    )

    # lignes de séparation de zones plus visibles
    ax.axvline(model.z1_limit, color="gray", linewidth=2)
    ax.axvline(model.z2_limit, color="gray", linewidth=2)

    ax.set_xlim(0, model.width)
    ax.set_ylim(0, model.height)
    ax.set_aspect("equal")
    ax.set_xticks(range(model.width + 1))
    ax.set_yticks(range(model.height + 1))
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.tick_params(length=0)
    ax.set_title("Environment grid")

    solara.FigureMatplotlib(fig)

@solara.component
def WasteCountHistogram(model):
    update_counter.get()

    green_total = model.count_total_waste("green")
    yellow_total = model.count_total_waste("yellow")
    red_total = model.count_total_waste("red")

    fig = Figure(figsize=(6, 4))
    ax = fig.subplots()

    labels = ["green", "yellow", "red"]
    values = [green_total, yellow_total, red_total]
    colors = ["limegreen", "gold", "darkred"]

    ax.bar(labels, values, color=colors, edgecolor="black")
    ax.set_ylabel("Number of wastes")
    ax.set_title("Total waste counts")

    for i, value in enumerate(values):
        ax.text(i, value + 0.1, str(value), ha="center")

    solara.FigureMatplotlib(fig)



@solara.component
def StepCounter(model):
    update_counter.get()

    solara.Markdown(
        f"""
## Simulation time

# Step {model.current_step}
"""
    )
    

@solara.component
def WasteEvolutionPlot(model):
    update_counter.get()

    fig = Figure(figsize=(7, 4.5))
    ax = fig.subplots()

    x = list(range(len(model.green_history)))

    ax.plot(x, model.green_history, label="Green waste", color="green", linewidth=2)
    ax.plot(x, model.yellow_history, label="Yellow waste", color="gold", linewidth=2)
    ax.plot(x, model.red_history, label="Red waste", color="red", linewidth=2)

    ax.set_xlabel("Step")
    ax.set_ylabel("Number of wastes")
    ax.set_title("Waste evolution over time")
    ax.legend()
    ax.grid(True, alpha=0.3)

    solara.FigureMatplotlib(fig)

@solara.component
def Legend(model):
    update_counter.get()

    fig = Figure(figsize=(8, 1.8))
    ax = fig.subplots()

    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2)
    ax.axis("off")

    # 1) Robot
    ax.scatter(
        1.0, 1.0,
        s=220,
        marker="o",
        c="green",
        edgecolors="black",
        linewidths=0.8,
        zorder=3,
    )
    ax.text(1.5, 1.0, "Robot", va="center", fontsize=10)

    # 2) Déchet au sol
    ax.scatter(
        4.0, 1.0,
        s=80,
        marker="s",
        c="limegreen",
        edgecolors="black",
        linewidths=0.5,
        zorder=2,
    )
    ax.text(4.5, 1.0, "Waste on ground", va="center", fontsize=10)

    # 3) Robot portant un déchet
    ax.scatter(
        7.0, 1.0,
        s=220,
        marker="o",
        c="green",
        edgecolors="black",
        linewidths=0.8,
        zorder=3,
    )
    ax.scatter(
        7.18, 1.16,
        s=45,
        marker="s",
        c="limegreen",
        edgecolors="black",
        linewidths=0.5,
        zorder=4,
    )
    ax.text(7.5, 1.0, "Robot carrying waste", va="center", fontsize=10)

    solara.FigureMatplotlib(fig)


model_params = {
    "width": 15,
    "height": 10,
    "n_green_robots": {
        "type": "SliderInt",
        "value": 4,
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
    "n_green_waste": {
        "type": "SliderInt",
        "value": 12,
        "label": "Initial green waste",
        "min": 1,
        "max": 30,
        "step": 1,
    },
}

model = RobotMission()

page = SolaraViz(
    model,
    components=[GridView, Legend, WasteEvolutionPlot, StepCounter],
    model_params=model_params,
    name="Robot Mission - Simple Init",
)

page