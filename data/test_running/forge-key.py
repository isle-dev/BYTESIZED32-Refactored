# refactored forge-key.py
# # Success Haonan Wang and Ziang Xiao(Oct 2024)
# success junf
from GameBasic import *


# A heat source, which is a heating device. It holds things on its surface. When turned on, it progressively heats things up to some temperature.
class HeatSource(Container, Device):
    def __init__(self, name, maxTemperature, tempIncreasePerTick, containerPrefix, isLiquidContainer=False):
        GameObject.__init__(self, name)
        Container.__init__(self, name)
        Device.__init__(self, name)

        self.properties["containerPrefix"] = containerPrefix

        # Set the properties of this object
        self.properties["isMoveable"] = False
        self.properties["isOn"] = False
        self.properties["isLiquidContainer"] = isLiquidContainer

        # Set critical properties
        self.properties["maxTemperature"] = maxTemperature
        self.properties["tempIncreasePerTick"] = tempIncreasePerTick

    # If the heat source is on, increase the temperature of anything on the heat source, up to the maximum temperature.
    def tick(self):
        # If the heat source is on, then increase the temperature of anything on the heat source
        if self.properties["isOn"]:
            # Get a list of all objects on the heat source
            containedObjects = self.getAllContainedObjectsRecursive()

            # Change the temperature of each object on/in the heat source
            for obj in containedObjects:
                if obj.properties["temperature"] > self.properties["maxTemperature"]:
                    newTemperature = max(obj.properties["temperature"] - self.properties["tempIncreasePerTick"], self.properties["maxTemperature"])
                else:
                    newTemperature = min(obj.properties["temperature"] + self.properties["tempIncreasePerTick"], self.properties["maxTemperature"])
                # Set the object's new temperature
                obj.properties["temperature"] = newTemperature

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"a {self.name}"

        # Check if on/off
        if self.properties["isOn"]:
            outStr += " that is currently on"
        else:
            outStr += " that is currently off"

        # Check if empty
        if len(self.contains) == 0:
            outStr += " and has nothing " + self.properties["containerPrefix"] + " it."
        else:
            outStr += " and has the following items " + self.properties["containerPrefix"] + " it: "
            outStr += ', '.join([obj.makeDescriptionStr() for obj in self.contains])

        return outStr


# A mold with specific shape
class Mold(Container):
    def __init__(self, mold_shape, temperature=20, temperature_change_per_tick=200):
        GameObject.__init__(self, f"{mold_shape} mold")
        Container.__init__(self, f"{mold_shape} mold")

        self.properties["containerPrefix"] = "in"
        self.properties["mold_shape"] = mold_shape
        self.properties["temperature"] = temperature
        self.properties["tempIncreasePerTick"] = temperature_change_per_tick
        self.properties["isLiquidContainer"] = True

    def addObject(self, obj):
        Container.addObject(self, obj)
        if obj.getProperty("stateOfMatter") == "liquid":
            obj.properties["solidShapeName"] = self.properties["mold_shape"]

    # Everything in the mold will gradually cools down (or heat up) to the room temperature
    def tick(self):
        # Get a list of all objects in the mold
        containedObjects = self.getAllContainedObjectsRecursive()

        # Change the temperature of each object in the mold
        for obj in containedObjects:
            if obj.properties["temperature"] > self.properties["temperature"]:
                newTemperature = max(obj.properties["temperature"] - self.properties["tempIncreasePerTick"], self.properties["temperature"])
            else:
                newTemperature = min(obj.properties["temperature"] + self.properties["tempIncreasePerTick"], self.properties["temperature"])
            # Set the object's new temperature
            obj.properties["temperature"] = newTemperature

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"the {self.properties['mold_shape']} mold"

        effectiveContents = [obj.makeDescriptionStr() for obj in self.contains]

        if effectiveContents:
            outStr += " that looks to have " + ", ".join(effectiveContents) + f" {self.properties['containerPrefix']} it"
        else:
            outStr += " that is empty"

        return outStr


# A substance with specific physical properties
class KeySubstance(Substance):
    def __init__(self, solidName, liquidName, gasName, solid_shape_name, boilingPoint, meltingPoint, currentTemperatureCelsius):
        Substance.__init__(self, solidName, liquidName, gasName, boilingPoint, meltingPoint, currentTemperatureCelsius)
        self.properties["solidShapeName"] = solid_shape_name
        self.tick()

    def tick(self):
        Substance.tick(self)  # Call the parent tick method

        # Check if the substance is a solid
        if self.properties["stateOfMatter"] == "solid":
            self.name = f'{self.properties["solidName"]} {self.properties["solidShapeName"]}'


# A door
class Door(GameObject):
    def __init__(self, name, is_locked=True, is_open=False):
        GameObject.__init__(self, name)
        self.properties["is_locked"] = is_locked
        self.properties["is_open"] = is_open

    def open(self, key=None):
        # The door is already opened
        if self.properties["is_open"]:
            return f"The {self.name} is already opened."
        else:
            # The door is closed, but not locked
            if not self.properties["is_locked"]:
                self.properties["is_open"] = True
                return f"You open the {self.name}."
            else:
                # The door is locked but a key is not available
                if key is None:
                    return f"The {self.name} is locked."
                # Unlock the door and open it
                else:
                    self.properties["is_open"] = True
                    self.properties["is_locked"] = False
                    return f"You unlock the {self.name} and open it."

    def close(self):
        # The door is already closed
        if not self.properties["is_open"]:
            return f"The {self.name} is already closed."
        # close the door
        else:
            return f"You close the {self.name}."

    def makeDescriptionStr(self, makeDetailed=False):
        if self.properties["is_open"]:
            outStr = f"a {self.name} that is open"
        elif self.properties["is_locked"]:
            outStr = f"a locked {self.name}"
        else:
            outStr = f"a door that is closed"
        return outStr


# World Setup
class WorkshopWorld(World):
    def __init__(self):
        World.__init__(self, "workshop")


# Game Implementation
class ForgeKeyGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = WorkshopWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add a stove as a distractor
        stove = HeatSource("stove", 500, 50, "on")
        world.addObject(stove)

        # Add a foundry
        foundry = HeatSource("foundry", 1500, 200, "in", isLiquidContainer=True)
        world.addObject(foundry)

        # Add a copper ingot
        copper = KeySubstance("copper", "copper (liquid)", "copper (steam)", "ingot", 2562, 1085, 20)
        world.addObject(copper)

        # Add a door
        door = Door("door")
        world.addObject(door)

        # Add a mold
        mold_key = Mold("key")
        world.addObject(mold_key)

        # Add a distractor mold
        mold_ingot = Mold("ingot")
        world.addObject(mold_ingot)

        # Return the world
        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to forge a key to open the door."

    # Returns a list of valid actions at the current time step
    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Zero-argument actions
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])
        # Add actions that are not provided in the default actions in the super class
        # Actions with one object argument
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0], ["take", obj])
                self.addAction("open " + objReferent, ["open", obj])
                self.addAction("close " + objReferent, ["close", obj])
                self.addAction("turn on " + objReferent, ["turn on", obj])
                self.addAction("turn off " + objReferent, ["turn off", obj])

        # Actions with two object arguments
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
                            self.addAction("pour " + objReferent1 + " into " + objReferent2, ["pour", obj1, obj2])
                            self.addAction("open " + objReferent1 + " with " + objReferent2, ["open", obj1, obj2])

        return self.possibleActions

    #
    #   Interpret actions
    #

    # Open a container/door
    def actionOpen(self, obj):
        # Check if the object is a container
        if obj.getProperty("isContainer"):
            # This is handled by the object itself
            obsStr, success = obj.openContainer()
            return obsStr
        # Check if the object is a door
        elif isinstance(obj, Door):
            return obj.open()
        else:
            return "You can't open that."

    # Open a door with a key
    def actionOpenWith(self, door, key):
        # Check the type of the door
        if not isinstance(door, Door):
            return f"You can't open the {door.name} with the {key.name}."

        # Check the key
        if not isinstance(key, KeySubstance) or key.getProperty("solidShapeName") != "key" or key.getProperty("stateOfMatter") != "solid":
            return f"The {key.name} is not a valid key."

        # open the door with the key
        return door.open(key)

    # Close a container
    def actionClose(self, obj):
        # Check if the object is a container
        if obj.getProperty("isContainer"):
            # This is handled by the object itself
            obsStr, success = obj.closeContainer()
            return obsStr
        elif isinstance(obj, Door):
            return obj.close()
        else:
            return "You can't close that."

    # Turn on
    def actionTurnOn(self, obj):
        # Check if the object is a HeatSource
        if isinstance(obj, HeatSource):
            # This is handled by the object itself
            obsStr, success = obj.turnOn()
            return obsStr
        return "You can't turn on that."

    # Turn off
    def actionTurnOff(self, obj):
        # Check if the object is a HeatSource
        if isinstance(obj, HeatSource):
            # This is handled by the object itself
            obsStr, success = obj.turnOff()
            return obsStr
        return "You can't turn off that."

    # Pour action
    def actionPour(self, liquid, container):
        # Check the type and state of liquid
        if not isinstance(liquid, Substance) or liquid.getProperty("stateOfMatter") != "liquid":
            return f"You can't pour the {liquid.name}."

        # Check if the container can hold liquid
        if not container.getProperty("isLiquidContainer"):
            return f"You can't pour the {liquid.name} into the {container.name}."

        # move the liquid to the new container
        container.addObject(liquid)
        return f"You pour the {liquid.name} into the {container.name}."

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

        # Mapping action verbs to corresponding functions
        action_map = {
            "look around": self.rootObject.makeDescriptionStr,
            "inventory": self.actionInventory,
            "open": lambda: self.actionOpen(action[1]) if len(action) == 2 else self.actionOpenWith(action[1],
                                                                                                    action[2]),
            "close": lambda: self.actionClose(action[1]),
            "take": lambda: self.actionTake(action[1]),
            "turn on": lambda: self.actionTurnOn(action[1]),
            "turn off": lambda: self.actionTurnOff(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "pour": lambda: self.actionPour(action[1], action[2])
        }

        # Execute the mapped function or return an error if action is unknown
        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action.")()

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

        # If the door is open, then add a point.
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        for obj in allObjects:
            if isinstance(obj, Door) and obj.getProperty("is_open"):
                self.score, self.gameOver,self.gameWon = 1, True, True

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Execute a game command.")
    parser.add_argument("commands", help="The command to execute in the game")
    args = parser.parse_args()

    print("Command received")
    # Random seed
    randomSeed = 0
    # Create a new game
    game = ForgeKeyGame(randomSeed=randomSeed)
    main(game, args.commands)