# Refactor thermometer.py
# Process and problem of code
# Success Haonan(2025.2)

# Task: Create a micro-simulation that models how to measure the water temperature with a thermometer.
# Environment: emergency room
# Task-critical Objects: LiquidContainer, Liquid, Thermometer
# High-level object classes: Container (LiquidContainer)
# Critical properties: temperature (GameObject)
# Actions: look, inventory, examine, take/put object, use, answer
# Distractor Items: Liquid, LiquidContainer
# Distractor Actions: None
# High-level solution procedure: take the thermometer, use the thermometer on water, answer the temperature

from data.library.GameBasic import *

# Abstract class for things that can be considered 'containers' (e.g. a drawer, a box, a table, a shelf, etc.)
class Liquid(GameObject):
    def __init__(self, name, temperature):
        GameObject.__init__(self, name)
        self.properties["temperature"] = temperature


# A thermometer
class Thermometer(GameObject):
    def __init__(self):
        GameObject.__init__(self, "thermometer")

    # When using the thermometer on an object, the temperature of the object can be read by the thermometer.
    def useWithObject(self, obj):
        # cannot use the thermometer on the agent or itself
        if isinstance(obj, (Agent, Thermometer)):
            return "You cannot use a thermometer on that.", False
        else:
            return f"The thermometer reads {obj.getProperty('temperature')} Celsius degree.", True

    def makeDescriptionStr(self, makeDetailed=False):
        return "a thermometer"


# A container that can hold liquid
class LiquidContainer(Container):
    def __init__(self, name):
        GameObject.__init__(self, name)
        Container.__init__(self, name)
        self.properties["containerPrefix"] = "in"
        # Set the properties of this object
        self.properties["isOpenable"] = False  # A pot is not openable

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"a {self.name}"
        contents = [obj.makeDescriptionStr() for obj in self.contains]

        if contents:
            outStr += " that has "
            for i in range(len(contents)):
                if (i == len(contents) - 1) and (len(contents) > 1):
                    outStr += "and "
                outStr += contents[i] + ", "
            outStr = outStr[:-2] + " " + self.properties["containerPrefix"] + " it"
        else:
            outStr += " that is empty"

        return outStr


# The world is the root object of the game object tree.  In single room environments, it's where all the objects are located.
class EmergencyRoomWorld(World):
    def __init__(self):
        World.__init__(self, "emergency room")

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "You find yourself in a kitchen. In the kitchen, you see: \n"
        for obj in self.contains:
            outStr += "\t" + obj.makeDescriptionStr() + "\n"

        return outStr

# Game Implementation
class ThermometerGame(TextGame):
    def __init__(self, randomSeed):
        self.answer_temperature = None
        TextGame.__init__(self, randomSeed)

    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = EmergencyRoomWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add a pot
        pot = LiquidContainer("pot")
        world.addObject(pot)

        # Randomly choose the temperature of the water and the temperature of 2-5 distractors
        num_distractors = self.random.randint(2, 5)
        temperatures = self.random.choices(range(1, 100), k=num_distractors + 1)
        self.water_temperature = temperatures[0]
        water = Liquid("water", self.water_temperature)
        pot.addObject(water)

        # Add a thermometer
        thermometer = Thermometer()
        world.addObject(thermometer)

        # Add some distractors
        distractors = ["milk", "olive oil", "vinegar", "soy sauce", "orange juice"]
        containers = ["cup", "bottle", "bowl", "glass", "mug"]
        self.random.shuffle(distractors)
        self.random.shuffle(containers)
        for i in range(num_distractors):
            container = LiquidContainer(containers[i])
            distractor = Liquid(distractors[i], temperatures[i + 1])
            container.addObject(distractor)
            world.addObject(container)

        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to figure out the temperature of the water in the pot."

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

        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0], ["take", obj])
                self.addAction("examine " + objReferent, ["examine", obj])

        # Actions with one object argument
        # (1-arg) Take, Detailed look/examine, Answer
        for i in range(1, 100):
            self.addAction(f"answer {i} Celsius degree", ["answer", i])

        # Actions with two object arguments
        # (2-arg) Put, Use
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if (obj1 != obj2):
                            containerPrefix = "in"
                            if obj2.properties["isContainer"]:
                                containerPrefix = obj2.properties["containerPrefix"]
                            self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2, ["put", obj1, obj2])
                            self.addAction("use " + objReferent1 + " on " + objReferent2, ["use", obj1, obj2])

        return self.possibleActions

    #
    #   Interpret actions
    #

    # Answer the temperature
    def actionAnswer(self, temperature):
        self.answer_temperature = temperature
        return f"You believe the temperature of the water is {temperature} Celsius degree."

    # use a thermometer
    def actionUse(self, deviceObj, patientObject):
        if isinstance(deviceObj, Thermometer):
            if deviceObj.parentContainer == self.agent:
                obsStr, _ = deviceObj.useWithObject(patientObject)
                return obsStr
            else:
                return "You need to take the thermometer first."
        return "You can't use that."

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

        actions = {
            "look around": lambda: self.rootObject.makeDescriptionStr(), # Look around the environment -- i.e. show the description of the world.
            "inventory": lambda: self.actionInventory(),  # Display the agent's inventory
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed = True),  # Examine an object
            "take": lambda: self.actionTake(action[1]),  # Take an object from a container
            "put": lambda: self.actionPut(action[1], action[2]),  # Put an object in a container
            "use": lambda: self.actionUse(action[1], action[2]),  # Use a device on an object
            "answer": lambda: self.actionAnswer(action[1])  # Answer the temperature
        }

        # Catch-all
        self.observationStr = actions.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):
        # Calculate the game score
        self.score = 0

        if self.answer_temperature is not None:
            if self.water_temperature == self.answer_temperature:
                self.score = 1
                self.gameOver, self.gameWon = True, True

            else:
                self.score, self.gameOver, self.gameWon = 0, True, False

if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(game = ThermometerGame(randomSeed=0))