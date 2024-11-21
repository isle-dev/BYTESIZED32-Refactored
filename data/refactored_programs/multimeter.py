# refactored multimeter.py
# Success Haonan Wang and Ziang Xiao(Nov 2024)

from data.library.GameBasic import *


# A game object with electrical terminals
class ElectricalObject(GameObject):
    def __init__(self, name, conductive=True, resistance=0):
        super().__init__(name)
        self.properties["is_electrical_object"] = True
        self.properties["conductive"] = conductive
        self.properties["resistance"] = resistance
        self.connects = {"terminal1": None, "terminal2": None}

    def disconnect(self, terminal):
        if self.connects[terminal] is not None:
            obj_connects_to, connected_terminal = self.connects[terminal]
            obj_connects_to.connects[connected_terminal] = None
        self.connects[terminal] = None

    def makeDescriptionStr(self, makeDetailed=False):
        terminal1, terminal2 = self.connects.keys()
        if self.connects[terminal1] is None and self.connects[terminal2] is None:
            return f"a {self.name}"
        elif self.connects[terminal1] is None and self.connects[terminal2]:
            return f"a {self.name} connecting to {self.connects[terminal2][0].name} {self.connects[terminal2][1]}"
        elif self.connects[terminal1] and self.connects[terminal2] is None:
            return f"a {self.name} connecting to {self.connects[terminal1][0].name} {self.connects[terminal1][1]}"
        else:
            return f"a {self.name} connecting to {self.connects[terminal1][0].name} {self.connects[terminal1][1]} and {self.connects[terminal2][0].name} {self.connects[terminal2][1]}"


# a multimeter with three modes: voltage, current, and resistance
class Multimeter(ElectricalObject):
    def __init__(self, mode='voltage'):
        conductive = True if mode in ['current', 'resistance'] else False
        resistance = 0 if mode in ['current', 'resistance'] else float('inf')
        ElectricalObject.__init__(self, "multimeter", conductive, resistance)
        self.mode = mode

    # measure the voltage/current/resistance
    def measure(self):
        # voltage mode
        if self.mode == "voltage":
            return 0, "V"
        elif self.mode == "current":
            return 0, "A"
        elif self.mode == "resistance":
            total_resistance = 0
            current_obj = self
            current_terminal = 'terminal1'
            while True:
                if current_obj.connects.get(current_terminal) is None or not (
                next_obj := current_obj.connects[current_terminal][0]).getProperty("conductive"):
                    total_resistance = "inf"
                    break

                next_terminal = next((key for key in next_obj.connects if key != current_terminal), current_terminal)

                if next_obj == self:
                    break

                resistance = next_obj.getProperty("resistance")
                total_resistance = 'inf' if total_resistance == 'inf' or resistance == 'inf' else total_resistance + resistance

                current_obj, current_terminal = next_obj, next_terminal

            return total_resistance, "ohm"

    def makeDescriptionStr(self, makeDetailed=False):
        number, unit = self.measure()
        number_str = "INF" if number == float('inf') else str(number)
        return f"a multimeter, which is in {self.mode} mode and reads {number_str} {unit}"


# wires that can connects electrical devices
class Wire(ElectricalObject):
    def __init__(self, name):
        ElectricalObject.__init__(self, name, True)
        self.properties["is_wire"] = True


# World Setup
class RoomWorld(World):
    def __init__(self):
        super().__init__("room")


# Game Implementation
class MultimeterGame(TextGame):
    def __init__(self, randomSeed):
        # User answer
        self.answer_resistance = None
        super().__init__(randomSeed)

    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = RoomWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add a multimeter
        multimeter = Multimeter(mode=self.random.choice(["voltage", "current", "resistance"]))
        world.addObject(multimeter)

        # Add 2-5 resistors, one resistor is the target while others are distractors
        num_resistors = self.random.randint(2,5)
        resistance = self.random.choices(range(50), k=num_resistors)
        resistor_ids = list(range(num_resistors))
        self.random.shuffle(resistor_ids)
        self.target_resistor_id = resistor_ids[0]
        self.target_resistance = resistance[0]
        for i in range(num_resistors):
            resistor = ElectricalObject(f"resistor {resistor_ids[i]}", resistance=resistance[i])
            world.addObject(resistor)

        # Add three wires
        wire1 = Wire("red wire")
        wire2 = Wire("black wire")
        wire3 = Wire("blue wire")
        world.addObject(wire1)
        world.addObject(wire2)
        world.addObject(wire3)

        # Return the world
        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return f"Your task is to figure out the resistance of the resistor {self.target_resistor_id}."

    # Returns a list of valid actions at the current time step
    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Zero-argument actions
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0], ["take", obj])

        # (1-arg) Answer
        for i in range(1, 200):
            self.addAction(f"answer {i} ohm", ["answer", i])

        # Actions with two object arguments
        # (2-arg) Set
        for objReferent1, objs1 in allObjects.items():
            for obj1 in objs1:
                for mode in ["voltage", "current", "resistance"]:
                    self.addAction(f"set {objReferent1} to {mode} mode", ["set", obj1, mode])

        # Actions with four object arguments
        # (4-arg) Connect
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if (obj1 != obj2 and obj1.getProperty("is_electrical_object") and obj2.getProperty("is_electrical_object")):
                            for terminal_1 in obj1.connects:
                                for terminal_2 in obj2.connects:
                                    containerPrefix = "in"
                                    if obj2.properties["isContainer"]:
                                        containerPrefix = obj2.properties["containerPrefix"]
                                    self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2,
                                                   ["put", obj1, obj2])

                                    self.addAction(f"connect {objReferent1} {terminal_1} to {objReferent2} {terminal_2}", ["connect", obj1, terminal_1, obj2, terminal_2])

        return self.possibleActions

    #
    #   Interpret actions
    #

    # Connects two electrical objects
    def actionConnect(self, obj1, terminal_1, obj2, terminal_2):
        if not (obj1.getProperty("is_wire") or obj2.getProperty("is_wire") or isinstance(obj1, Multimeter) or isinstance(obj2, Multimeter)):
            return "You cannot connect two devices directly."
        # disconnect the terminal if the terminal is already connected to other objects
        if obj1.connects[terminal_1]:
            obj1.disconnect(terminal_1)
        if obj2.connects[terminal_2]:
            obj2.disconnect(terminal_2)
        obj1.connects[terminal_1] = (obj2, terminal_2)
        obj2.connects[terminal_2] = (obj1, terminal_1)
        return f"Successfully connect {obj1.name} {terminal_1} to {obj2.name} {terminal_2}"

    # Answer
    def actionAnswer(self, resistance):
        self.answer_resistance = resistance
        return f"You believe the resistance of the resistor {self.target_resistor_id} is {resistance} ohms."

    # Set the multimeter to a new mode
    def actionSet(self, multimeter, mode):
        if not isinstance(multimeter, Multimeter):
            return "You cannot set that."
        elif mode not in ["voltage", "current", "resistance"]:
            return "Unknown mode."
        multimeter.mode = mode
        return f"You set the multimeter to the {mode} mode."

    def step(self, actionStr):
        self.observationStr = ""
        reward = 0

        # Check to make sure the action is in the possible actions dictionary
        if actionStr not in self.possibleActions:
            self.observationStr = "I don't understand that."
            return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

        self.numSteps += 1

        # Find the action in the possible actions dictionary
        actions = self.possibleActions[actionStr]
        action = None

        # Check for an ambiguous action (i.e. one that has multiple possible arguments)
        if (len(actions) > 1):
            # If there are multiple possible arguments, for now just choose the first one
            action = actions[0]
        else:
            # Otherwise, also just take the first action in the list of possible actions
            action = actions[0]

        # Interpret the action
        actionVerb = action[0]

        actions = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": lambda: self.actionInventory(),
            "take": lambda: self.actionTake(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "connect": lambda: self.actionConnect(action[1], action[2], action[3], action[4]),
            "answer": lambda: self.actionAnswer(action[1]),
            "set": lambda: self.actionSet(action[1], action[2])
        }

        # Check if actionVerb is in predefined actions, otherwise return error
        self.observationStr = actions.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)


    def calculateScore(self):
        self.score = 0
        if self.answer_resistance is not None:
            if self.target_resistance == self.answer_resistance:
                self.score += 1
                self.gameOver = True
                self.gameWon = True
            else:
                self.score = 0
                self.gameOver = True
                self.gameWon = False


if __name__ == "__main__":
    randomSeed = 1
    game = MultimeterGame(randomSeed=randomSeed)
    main(game)