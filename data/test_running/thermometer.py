# Refactor thermometer.py

# success
from GameBasic import *

# Liquid
class Liquid(GameObject):
    def __init__(self, name, temperature):
        GameObject.__init__(self, name)
        self.properties["temperature"] = temperature


# A thermometer that can measure the temperature of objects
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


# World
class EmergencyRoomWorld(World):
    def __init__(self):
        World.__init__(self, "emergency room")



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

        # Zero-argument actions
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0], ["take", obj])
                self.addAction("examine " + objReferent, ["examine", obj])

        # Add actions that are not provided in the default actions in the super class
        # (1-arg) Answer
        for i in range(1, 100):
            self.addAction(f"answer {i} Celsius degree", ["answer", i])

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

    # Use an object with another object
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

        # Create a dictionary to map action verbs to corresponding methods
        actions = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": lambda: self.actionInventory(),
            "examine": lambda: self.actionExamine(action[1]),  # Assuming 'action[1]' is the object to examine
            "take": lambda: self.actionTake(action[1]),  # Assuming 'action[1]' is the thing to take
            "put": lambda: self.actionPut(action[1], action[2]),
            # Assuming 'action[1]' is the item to put, 'action[2]' is the container
            "use": lambda: self.actionUse(action[1], action[2]),
            # Assuming 'action[1]' is the device, 'action[2]' is the object
            "answer": lambda: self.actionAnswer(action[1])  # Assuming 'action[1]' is the answer
        }

        # Execute the corresponding action based on the verb, default to "ERROR: Unknown action."
        self.observationStr = actions.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):
        # Baseline score
        self.score = 0

        if self.answer_temperature is not None:
            if self.water_temperature == self.answer_temperature:
                self.score = 1
                self.gameOver = True
                self.gameWon = True
            else:
                self.score = 0
                self.gameOver = True
                self.gameWon = False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Execute a game command.")
    parser.add_argument("commands", help="The command to execute in the game")
    args = parser.parse_args()

    print("Command received")
    # Random seed
    randomSeed = 0
    # Create a new game
    game = ThermometerGame(randomSeed=randomSeed)
    main(game, args.commands)
