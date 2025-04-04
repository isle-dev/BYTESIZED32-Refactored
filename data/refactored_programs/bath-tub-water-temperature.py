# Refactored bath-tub-water-temperature.py
# Process
# Success Haonan(2025.2)

# Task: Create a micro-simulation that models how to make the water temperature suitable for bath (35-40 Ceilsius degree) by adding hot/cold water to a bath tub.
# Environment: bathroom
# Task-critical Objects: Tap, Thermometer, Water, BathTub
# High-level object classes: Container (BathTub)
# Critical properties: temperature (GameObject), water_temperature (Tap)
# Actions: look, inventory, take/put objects, turn on/off devices, use device on objects, bath
# Distractor Items: None
# Distractor Actions: None
# High-level solution procedure: Take the thermometer and measure the water temperature. If the water is too hot, add cold water. If it is too cold, add hot water. Keep measuring water temperature till the temperature is suitable for a bath. Take a bath.


from data.library.GameBasic import *

# A tap of the bath tub
class Tap(Device):
    def __init__(self, name, water_temperature, is_on=False):
        GameObject.__init__(self, name)

        self.properties["isActivatable"] = True  # Can this device be turned on or off?
        self.properties["isOn"] = is_on  # Is the device currently on or off?
        self.properties["isMoveable"] = False  # A tap is not moveable
        self.properties["water_temperature"] = water_temperature  # The temperature of the water coming out from the tap

    def tick(self):
        if self.properties["isOn"] and self.parentContainer is not None and type(self.parentContainer) == BathTub:
            water_list = self.parentContainer.containsItemWithName("water")
            # If there is no water in the bath tub now, add water
            if len(water_list) == 0:
                water = Water(self.properties["water_temperature"])
                self.parentContainer.addObject(water)
            else:
                water = water_list[0]
                # If the water in the bath tub is hotter than the water from the tap, decrease the temperature of the water in the bath tub
                water.properties["temperature"] = max(water.properties["temperature"] - 5, self.properties["water_temperature"]) if self.properties["water_temperature"] < water.properties["temperature"] else min(water.properties["temperature"] + 5, self.properties["water_temperature"])

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a {self.name}, which is currently {'on' if self.properties['isOn'] else 'off'}."

# A thermometer
class Thermometer(GameObject):
    def __init__(self):
        GameObject.__init__(self, "thermometer")
        self.properties["isMoveable"] = True
        self.properties["isUsable"] = True

    # When using the thermometer on an object, the temperature of the object can be read by the thermometer.
    def useWithObject(self, obj):
        if isinstance(obj, (Agent, Thermometer)):
            return "You cannot use a thermometer on that.", False
        return f"The thermometer reads {obj.getProperty('temperature')} Celsius degree.", True

    def makeDescriptionStr(self, makeDetailed=False):
        return "a thermometer"

# An instance of a substance (here, water)
class Water(GameObject):
    def __init__(self, temperature):
        GameObject.__init__(self, "water")
        self.properties["isMoveable"] = False  # Water is liquid so we don't allow it to be moved
        self.properties["temperature"] = temperature

# A bath tub
class BathTub(Container):
    def __init__(self):
        GameObject.__init__(self, "bath tub")
        Container.__init__(self, "bath tub")

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a bath tub"
        # Check if open
        outStr += " that is empty" if len(self.contains) == 0 else " that contains the following items: \n" + ''.join(
            f"\t{desc}\n" for obj in self.contains for desc in obj.makeDescriptionStr().strip().split('\n'))
        return outStr


# The world is the root object of the game object tree.  In single room environments, it's where all the objects are located.
class BathroomWorld(World):
    def __init__(self):
        Container.__init__(self, "bathroom")

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "You find yourself in a bathroom.  In the kitchen, you see: \n"
        outStr += ''.join(
            f"\t{desc}\n" for obj in self.contains for desc in obj.makeDescriptionStr().strip().split('\n'))
        return outStr

# Game Implementation
class BathTubTemperatureGame(TextGame):
    def __init__(self, randomSeed):
        self.bath = False
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = BathroomWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add a bath tub
        bath_tub = BathTub()
        world.addObject(bath_tub)

        # Add some water to the bath tub
        water = Water(self.random.randint(20, 60))
        bath_tub.addObject(water)

        # Add two taps
        hot_tap = Tap("hot tap", 60)
        bath_tub.addObject(hot_tap)
        cold_tap = Tap("cold tap", 20)
        bath_tub.addObject(cold_tap)

        # Add a thermometer to measure the water temperature
        thermometer = Thermometer()
        world.addObject(thermometer)

        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return 'Your task is to make the temperature of the water in the bath tub suitable for a bath (35 - 40 Celsius degree). When you are done, take the action "bath".'

    #
    #   Action generation
    #

    # Returns a list of valid actions at the current time step
    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Actions with zero arguments
        # (0-arg) Look around the environment and Look at the agent's current inventory
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory"),
                       ("bath", "bath")]:
            self.addAction(action[0], [action[1]])

        # Actions with one object argument
        # (1-arg) Take, Turn on/Turn off device
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction(f"take {objReferent}", ["take", obj])
                self.addAction(f"take {objReferent} from {obj.parentContainer.getReferents()[0]}", ["take", obj])
                self.addAction(f"turn on {objReferent}", ["turn on", obj])
                self.addAction(f"turn off {objReferent}", ["turn off", obj])

        # Actions with two object arguments
        # (2-arg) Put, Use
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            containerPrefix = obj2.properties.get("containerPrefix", "in") if obj2.properties[
                                "isContainer"] else "in"
                            self.addAction(f"put {objReferent1} {containerPrefix} {objReferent2}", ["put", obj1, obj2])
                            self.addAction(f"use {objReferent1} on {objReferent2}", ["use", obj1, obj2])

        return self.possibleActions

    #
    #   Interpret actions
    #

    def actionTurnOn(self, obj):
        # Check if the object is activatable
        if obj.getProperty("isActivatable"):
            # This is handled by the object itself
            obsStr, success = obj.turnOn()
            return obsStr
        else:
            return "You can't turn on that."

    def actionTurnOff(self, obj):
        # Check if the object is activatable
        if obj.getProperty("isActivatable"):
            # This is handled by the object itself
            obsStr, success = obj.turnOff()
            return obsStr
        else:
            return "You can't turn off that."

    def actionUse(self, deviceObj, patientObject):
        # Check if the object is usable
        if deviceObj.getProperty("isUsable"):
            # This is handled by the object itself
            obsStr, _ = deviceObj.useWithObject(patientObject)
            return obsStr
        else:
            return "You can't use that."

    def actionBath(self):
        self.bath = True
        return "You take a bath."

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
            "look around": self.rootObject.makeDescriptionStr(),  # Look around the environment -- i.e. show the description of the world.
            "inventory": self.actionInventory,  # Display the agent's inventory
            "bath": self.actionBath,  # Take a bath
            "take": lambda: self.actionTake(action[1]),  # Take an object from a container
            "turn on": lambda: self.actionTurnOn(action[1]),  # Turn on a device
            "turn off": lambda: self.actionTurnOff(action[1]),  # Turn off a device
            "put": lambda: self.actionPut(action[1], action[2]),  # Put an object in a container
            "use": lambda: self.actionUse(action[1], action[2])  # Use a device on an object
        }

        # Catch-all
        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action")()

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

        # Check the water temperature when the agent takes a bath
        if self.bath:
            allObjects = self.rootObject.getAllContainedObjectsRecursive()
            for obj in allObjects:
                if obj.name == "water" and obj.parentContainer.name == "bath tub":
                    self.score, self.gameOver, self.gameWon = (1, True, True) if 35 <= obj.getProperty("temperature") <= 40 else (0, True, False)

if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(BathTubTemperatureGame(randomSeed=0))