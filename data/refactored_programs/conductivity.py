# refactor conductivity.py
# Process and problem of scoring results
# success Haonan(2025.2)

# Task Description: Create a micro-simulation that simulates an experiment which tests the conductivity of a fork by putting the fork into a circuit.
# Environment: room
# Task-critical Objects: Battery, LightBulb, Wire, ElectricalObject, Container
# High-level object classes: ElectricalObject (battery, light bulb, wire)
# Critical properties: connects (ElectricalObject), on (LightBulb), conductivity (ElectricalObject)
# Actions: look, inventory, take/put objects, connect X terminal A to Y terminal B
# Distractor Items: None
# Distractor Actions: None
# High-level solution procedure: connect the light bulb, the fork, and battery into a circuit with wires, observe the light bulb, if the light bulb is on, put the fork into the red box, otherwise, put it into the black box

from data.library.GameBasic import *

# A game object with electrical terminals
class ElectricalObject(GameObject):
    def __init__(self, name, conductive=True):
        GameObject.__init__(self, name)
        self.properties["is_electrical_object"] = True
        self.properties["conductive"] = conductive
        self.connects = {"terminal1": (None, None), "terminal2": (None, None)}

    def disconnect(self, terminal):
        if self.connects[terminal][0] is not None:
            obj_connects_to, connected_terminal = self.connects[terminal]
            obj_connects_to.connects[connected_terminal] = (None, None)
        self.connects[terminal] = (None, None)

    def makeDescriptionStr(self, makeDetailed=False):
        terminal1, terminal2 = self.connects.keys()
        if self.connects[terminal1][0] is None and self.connects[terminal2][0] is None:
            return f"a {self.name}"
        elif self.connects[terminal1][0] is None and self.connects[terminal2][0]:
            return f"a {self.name} connecting to {self.connects[terminal2][0].name} {self.connects[terminal2][1]}"
        elif self.connects[terminal1][0] and self.connects[terminal2][0] is None:
            return f"a {self.name} connecting to {self.connects[terminal1][0].name} {self.connects[terminal1][1]}"
        else:
            return f"a {self.name} connecting to {self.connects[terminal1][0].name} {self.connects[terminal1][1]} and {self.connects[terminal2][0].name} {self.connects[terminal2][1]}"

# A battery
class Battery(ElectricalObject):
    def __init__(self, name):
        ElectricalObject.__init__(self, name, True)
        self.connects = {"cathode": (None, None), "anode": (None, None)}

# A lightbulb
class LightBulb(ElectricalObject):
    def __init__(self, name):
        ElectricalObject.__init__(self, name, True)
        self.properties['on'] = False

    def connectsToBattery(self):
        # check if the bulb is in a conductive circuit with at least one battery in it
        found_battery = False
        is_good_circuit = True
        current_obj = self
        current_terminal = 'terminal1'
        while True:
            next_obj, next_terminal = current_obj.connects[current_terminal]
            # ends if the connected object is not conductive
            # ends if does not connect to anything
            if next_obj is None:
                is_good_circuit = False
                break
            elif not next_obj.getProperty("conductive"):
                is_good_circuit = False
                break
            # ends when find the bulb itself in a loop
            elif next_obj == self:
                break
            else:
                if type(next_obj) == Battery:
                    found_battery = True
                for key in next_obj.connects:
                    if key != next_terminal:
                        next_terminal = key
                        break
                # update current objects and terminal name
                current_obj = next_obj
                current_terminal = next_terminal

        if found_battery and is_good_circuit:
            return True
        else:
            return False

    def tick(self):
        self.properties['on'] = True if self.connectsToBattery() else False

    def makeDescriptionStr(self, makeDetailed=False):
        state_desc = f"a {self.name} which is {'on' if self.properties['on'] else 'off'}"
        terminal1, terminal2 = self.connects.keys()
        if self.connects[terminal1][0] is None and self.connects[terminal2][0] is None:
            return state_desc
        elif self.connects[terminal1][0] is None and self.connects[terminal2][0]:
            return f"{state_desc} and connects to {self.connects[terminal2][0].name} {self.connects[terminal2][1]}"
        elif self.connects[terminal1][0] and self.connects[terminal2][0] is None:
            return f"{state_desc} and connects to {self.connects[terminal1][0].name} {self.connects[terminal1][1]}"
        else:
            return f"{state_desc} and connects to {self.connects[terminal1][0].name} {self.connects[terminal1][1]} and {self.connects[terminal2][0].name} {self.connects[terminal2][1]}"

# wires that can connect electrical devices
class Wire(ElectricalObject):
    def __init__(self, name):
        super().__init__(name, True)
        self.properties["is_wire"] = True

# The world is the root object of the game object tree.  In single room environments, it's where all the objects are located.
class Room(World):
    def __init__(self):
        World.__init__(self, "room")

class ConductivityGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = Room()

        # Add the agent
        world.addObject(self.agent)

        # Add a light bulb
        bulb = LightBulb("light bulb")
        world.addObject(bulb)

        # Add three wires
        wires = ["red wire", "black wire", "blue wire"]
        for wire in wires:
            world.addObject(Wire(wire))

        # Add a battery
        battery = Battery("battery")
        world.addObject(battery)
        #
        # Add a fork to test
        #
        # randomly generate if the fork is conductive or not
        self.conductive = self.random.choice([True, False])
        fork = ElectricalObject("fork", conductive=self.conductive)
        world.addObject(fork)

        # Add two answer boxes
        world.addObject(Container("red box"))
        world.addObject(Container("black box"))

        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to figure out if the fork is conductive or not. If the fork is conductive, put it in the red box. Otherwise, put it in the black box."

    # Returns a list of valid actions at the current time step
    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Actions with zero arguments
        # (0-arg) Look around the environment and Look at the agent's current inventory
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # Actions with one object argument
        # (1-arg) Take
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction(f"take {objReferent}", ["take", obj])
                self.addAction(f"take {objReferent} from {obj.parentContainer.getReferents()[0]}", ["take", obj])

        # Actions with two object arguments
        # (2-arg) Put
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            containerPrefix = "in"
                            if obj2.properties["isContainer"]:
                                containerPrefix = obj2.properties["containerPrefix"]
                            self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2,
                                           ["put", obj1, obj2])

        # Actions with four object arguments
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if (obj1 != obj2 and obj1.getProperty("is_electrical_object") and obj2.getProperty(
                                "is_electrical_object")):
                            for terminal_1 in obj1.connects:
                                for terminal_2 in obj2.connects:
                                    self.addAction(
                                        f"connect {objReferent1} {terminal_1} to {objReferent2} {terminal_2}",
                                        ["connect", obj1, terminal_1, obj2, terminal_2])

        return self.possibleActions

    # Connects two electrical objects
    def actionConnect(self, obj1, terminal_1, obj2, terminal_2):
        # at least one of the two objects should be a wire
        if not (obj1.getProperty("is_wire") or obj2.getProperty("is_wire")):
            return "You cannot connect two devices directly without a wire."
        # disconnect the terminal if the terminal is already connected to other objects
        if obj1.connects[terminal_1]:
            obj1.disconnect(terminal_1)
        if obj2.connects[terminal_2]:
            obj2.disconnect(terminal_2)

        obj1.connects[terminal_1] = (obj2, terminal_2)
        obj2.connects[terminal_2] = (obj1, terminal_1)
        return f"Successfully connected {obj1.name} {terminal_1} to {obj2.name} {terminal_2}"

    # Performs an action in the environment, returns the result (a string observation, the reward, and whether the game is completed).
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

        action_map = {
            "look around": self.rootObject.makeDescriptionStr,  # Look around the environment -- i.e. show the description of the world.
            "inventory": self.actionInventory,  # Display the agent's inventory
            "take": lambda: self.actionTake(action[1]),  # Take an object from a container
            "put": lambda: self.actionPut(action[1], action[2]),  # Put an object in a container
            "connect": lambda: self.actionConnect(*action[1:])
        }

        # Catch-all
        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    # Calculate the game score
    def calculateScore(self):
        # Baseline score
        self.score = 0
        # Check if the folk is put into the correct box.
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        for obj in allObjects:
            if obj.name == "fork":
                if (obj.parentContainer.name == 'red box' and self.conductive) or (obj.parentContainer.name == 'black box' and not self.conductive):
                    self.score += 1
                    self.gameOver,self.gameWon = True, True

                elif (obj.parentContainer.name == 'red box' and not self.conductive) or (obj.parentContainer.name == 'black box' and self.conductive):
                    self.score, self.gameOver,self.gameWon = 0, True, False

# Run the main program
if __name__ == "__main__":
    # Set random seed 1 and Create a new game
    main(ConductivityGame(randomSeed=1))