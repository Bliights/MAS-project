"""
Groupe 10
16/03/2026
Clément MOLLY-MITTON
Diane VERBECQ
"""

import random
import mesa


class RobotAgent(mesa.Agent):
    def __init__(self, model, robot_type="green"):
        super().__init__(model)

        # ============================================================
        # Attribut lu par server.py pour colorer le robot sur la grille
        # Valeurs attendues côté affichage :
        # - "green"
        # - "yellow"
        # - "red"
        # ============================================================
        self.robot_type = robot_type

        # ============================================================
        # Attribut lu par server.py pour savoir si le robot porte un déchet
        # Si None       -> le robot est affiché seul
        # Si "green"    -> le robot est affiché avec un petit carré vert
        # Si "yellow"   -> petit carré jaune
        # Si "red"      -> petit carré rouge
        #
        # C'est CET attribut qui permet dans l'affichage de distinguer :
        # - un déchet posé au sol
        # - un déchet porté par un robot
        # ============================================================
        self.carrying = None

    def pick_green_waste_if_possible(self):
        # ============================================================
        # LOGIQUE TEMPORAIRE DE TEST
        # Ici on a juste codé un comportement très simple :
        # un robot green ramasse un déchet green s'il est sur la même case.
        #
        # Cette partie n'est pas directement liée à l'affichage,
        # mais elle modifie self.carrying, donc elle impacte l'affichage.
        # ============================================================

        if self.robot_type != "green":
            return

        if self.carrying is not None:
            return

        cell_agents = self.model.grid.get_cell_list_contents([self.pos])

        for agent in cell_agents:
            if isinstance(agent, WasteAgent) and agent.waste_type == "green":
                # ====================================================
                # IMPORTANT POUR L'AFFICHAGE :
                # dès qu'on met self.carrying = "green",
                # server.py affichera le robot avec un mini-déchet porté.
                # ====================================================
                self.carrying = "green"

                # ====================================================
                # Le déchet n'est plus affiché au sol sur la grille,
                # car on l'enlève de la case.
                # ====================================================
                self.model.grid.remove_agent(agent)
                break

    def step(self):
        # ============================================================
        # 1) Avant de bouger, le robot tente de ramasser un déchet
        # s'il est déjà sur la même case.
        #
        # Effet visuel possible :
        # le déchet disparaît de la case et devient "porté".
        # ============================================================
        self.pick_green_waste_if_possible()

        # ============================================================
        # 2) Détermination des cases voisines accessibles
        # Cette partie sert à la logique de déplacement.
        #
        # Elle impacte indirectement l'affichage car la position du robot
        # sur la grille dépend de ce mouvement.
        # ============================================================
        neighbors = self.model.grid.get_neighborhood(
            self.pos,
            moore=False,
            include_center=False,
        )

        allowed_positions = []
        for pos in neighbors:
            x, y = pos

            # ========================================================
            # Ces conditions utilisent z1_limit et z2_limit.
            # Ces attributs sont aussi utilisés dans server.py
            # pour colorer les zones de la grille.
            # ========================================================
            if self.robot_type == "green" and x < self.model.z1_limit:
                allowed_positions.append(pos)
            elif self.robot_type == "yellow" and x < self.model.z2_limit:
                allowed_positions.append(pos)
            elif self.robot_type == "red":
                allowed_positions.append(pos)

        # ============================================================
        # 3) Déplacement du robot
        # C'est la position self.pos mise à jour par la grille
        # qui permet à server.py de dessiner le robot à la bonne case.
        # ============================================================
        if allowed_positions:
            new_pos = random.choice(allowed_positions)
            self.model.grid.move_agent(self, new_pos)

        # ============================================================
        # 4) Après déplacement, le robot retente de ramasser
        # un déchet s'il arrive sur une case qui en contient.
        # ============================================================
        self.pick_green_waste_if_possible()


class WasteAgent(mesa.Agent):
    def __init__(self, model, waste_type="green"):
        super().__init__(model)

        # ============================================================
        # Attribut lu par server.py pour colorer les déchets sur la grille
        # Valeurs attendues côté affichage :
        # - "green"
        # - "yellow"
        # - "red"
        # ============================================================
        self.waste_type = waste_type

    def step(self):
        # ============================================================
        # Les déchets n'ont pas de comportement propre.
        # Ils existent juste comme objets visibles sur la grille.
        # ============================================================
        pass


class RobotMission(mesa.Model):
    def __init__(
        self,
        width=15,
        height=10,
        n_green_robots=4,
        n_yellow_robots=3,
        n_red_robots=2,
        n_green_waste=12,
        seed=None,
    ):
        super().__init__(seed=seed)

        # ============================================================
        # Attributs généraux du modèle
        # width / height sont utilisés :
        # - par la logique du modèle
        # - par server.py pour dessiner la grille complète
        # ============================================================
        self.width = width
        self.height = height

        # ============================================================
        # Attribut CRUCIAL pour l'affichage de la grille dans server.py
        # server.py parcourt self.grid pour dessiner :
        # - les robots
        # - les déchets
        # case par case
        # ============================================================
        self.grid = mesa.space.MultiGrid(width, height, torus=False)

        # ============================================================
        # Attributs CRUCIAUX pour l'affichage des zones dans server.py
        #
        # server.py colorie les colonnes selon :
        # - x < z1_limit          -> zone verte pastel
        # - z1_limit <= x < z2_limit -> zone jaune pastel
        # - x >= z2_limit         -> zone rouge pastel
        # ============================================================
        self.z1_limit = width // 3
        self.z2_limit = 2 * width // 3

        # ============================================================
        # SOURCE DE VÉRITÉ POUR LE GRAPHE DES DÉCHETS
        #
        # Ces variables ne servent PAS à dessiner la grille.
        # Elles servent au graphique de server.py.
        #
        # count_total_waste("green") lit self.green_waste_total
        # count_total_waste("yellow") lit self.yellow_waste_total
        # count_total_waste("red") lit self.red_waste_total
        #
        # Donc si plus tard ton vrai modèle transforme :
        # green -> yellow
        # alors il faudra faire par ex. :
        # self.green_waste_total -= 2
        # self.yellow_waste_total += 1
        # ============================================================
        self.green_waste_total = n_green_waste
        self.yellow_waste_total = 0
        self.red_waste_total = 0

        # ============================================================
        # CRÉATION DES ROBOTS GREEN
        # Ils seront visibles sur la grille car placés dans self.grid.
        # ============================================================
        for _ in range(n_green_robots):
            agent = RobotAgent(self, "green")
            self.grid.place_agent(
                agent,
                (self.random.randrange(0, self.z1_limit), self.random.randrange(height)),
            )

        # ============================================================
        # CRÉATION DES ROBOTS YELLOW
        # ============================================================
        for _ in range(n_yellow_robots):
            agent = RobotAgent(self, "yellow")
            self.grid.place_agent(
                agent,
                (self.random.randrange(0, self.z2_limit), self.random.randrange(height)),
            )

        # ============================================================
        # CRÉATION DES ROBOTS RED
        # ============================================================
        for _ in range(n_red_robots):
            agent = RobotAgent(self, "red")
            self.grid.place_agent(
                agent,
                (self.random.randrange(0, width), self.random.randrange(height)),
            )

        # ============================================================
        # CRÉATION DES DÉCHETS GREEN INITIAUX
        #
        # Important pour l'affichage :
        # - chaque WasteAgent placé dans la grille sera dessiné dans server.py
        # - ici on impose au plus un déchet par case
        # ============================================================
        for _ in range(n_green_waste):
            possible_positions = [
                (x, y)
                for x in range(0, self.z1_limit)
                for y in range(height)
                if not self.cell_has_waste((x, y))
            ]

            if possible_positions:
                pos = self.random.choice(possible_positions)
                waste = WasteAgent(self, "green")
                self.grid.place_agent(waste, pos)

        # ============================================================
        # ======== PARTIE SPÉCIFIQUE AU GRAPHE DES 3 COURBES ==========
        #
        # current_step est lu par server.py pour afficher
        # le compteur de temps / step.
        #
        # green_history, yellow_history, red_history sont lus par server.py
        # pour tracer les 3 courbes dans le temps.
        #
        # Donc si tu veux garder le même server.py plus tard,
        # ton vrai modèle devra fournir ces attributs
        # ou des équivalents compatibles.
        # ============================================================
        self.current_step = 0

        self.green_history = [self.count_total_waste("green")]
        self.yellow_history = [self.count_total_waste("yellow")]
        self.red_history = [self.count_total_waste("red")]

    def cell_has_waste(self, pos):
        # ============================================================
        # Fonction utilitaire pour la logique du modèle
        # Sert ici à éviter de placer 2 déchets sur la même case.
        #
        # Pas directement utilisée par server.py.
        # ============================================================
        cell_agents = self.grid.get_cell_list_contents([pos])
        return any(isinstance(a, WasteAgent) for a in cell_agents)

    def cell_has_robot(self, pos):
        # ============================================================
        # Fonction utilitaire de logique
        # Pas directement utilisée par server.py actuellement.
        # ============================================================
        cell_agents = self.grid.get_cell_list_contents([pos])
        return any(isinstance(a, RobotAgent) for a in cell_agents)

    def count_waste_on_ground(self, waste_type):
        # ============================================================
        # Fonction utile si tu veux afficher / calculer
        # combien de déchets sont encore sur la grille.
        #
        # Cette fonction peut servir à des composants d'affichage
        # du type "waste currently on ground".
        # ============================================================
        count = 0
        for x in range(self.width):
            for y in range(self.height):
                cell_agents = self.grid.get_cell_list_contents([(x, y)])
                for agent in cell_agents:
                    if isinstance(agent, WasteAgent) and agent.waste_type == waste_type:
                        count += 1
        return count

    def count_waste_carried(self, waste_type):
        # ============================================================
        # Fonction utile si tu veux afficher / calculer
        # combien de déchets sont actuellement portés par les robots.
        #
        # Cette fonction repose sur robot.carrying.
        # ============================================================
        count = 0
        for agent in self.agents:
            if isinstance(agent, RobotAgent) and agent.carrying == waste_type:
                count += 1
        return count

    def count_total_waste(self, waste_type):
        # ============================================================
        # FONCTION CRUCIALE POUR LE GRAPHE
        #
        # server.py peut appeler cette fonction pour récupérer
        # le nombre total de déchets d'une couleur.
        #
        # Cette fonction ne regarde PAS la grille.
        # Elle lit la "source de vérité" :
        # - self.green_waste_total
        # - self.yellow_waste_total
        # - self.red_waste_total
        #
        # Donc si ton vrai modèle change la quantité totale de déchets
        # par transformation, il faudra mettre à jour ces compteurs.
        # ============================================================
        if waste_type == "green":
            return self.green_waste_total
        if waste_type == "yellow":
            return self.yellow_waste_total
        if waste_type == "red":
            return self.red_waste_total
        return 0

    def step(self):
        # ============================================================
        # BOUCLE PRINCIPALE DU MODÈLE
        # À chaque pas de simulation :
        # 1) on fait agir les agents
        # 2) on met à jour les variables utilisées par l'affichage
        #    du temps et du graphe
        # ============================================================

        for agent in list(self.agents):
            agent.step()

        # ============================================================
        # ======== PARTIE SPÉCIFIQUE À L'AFFICHAGE DU TEMPS ==========
        #
        # current_step est affiché dans server.py comme compteur de temps.
        # Si tu enlèves cette ligne, le compteur n'avancera plus.
        # ============================================================
        self.current_step += 1

        # ============================================================
        # ======== PARTIE SPÉCIFIQUE AU GRAPHE DES 3 COURBES ==========
        #
        # À chaque step, on ajoute la valeur courante dans l'historique.
        # server.py relit ces listes pour tracer :
        # - la courbe verte
        # - la courbe jaune
        # - la courbe rouge
        #
        # Si tu veux garder le même affichage plus tard,
        # il faut continuer à remplir ces listes.
        # ============================================================
        self.green_history.append(self.count_total_waste("green"))
        self.yellow_history.append(self.count_total_waste("yellow"))
        self.red_history.append(self.count_total_waste("red"))