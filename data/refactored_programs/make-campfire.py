# refactored make-camp-fire.py
# Process and ploblem of code generation
# success Haonan(2025.2)

# Task: Create a micro-simulation that models how to make campfire.
# Environment: forest
# Task-critical Objects: FirePit, Match, Axe, Tree
# High-level object classes: Container (FirePit), Device (Match, Axe)
# Critical properties: isCombustible (Axe, Tree), isChoppable (Tree)
# Actions: look, inventory, examine, take/put object, open/close container, turn on/off device, use device on object
# Distractor Items: None
# Distractor Actions: open, turn on/off
# High-level solution procedure: take the axe, use the axe on the tree, use the axe on the chopped down tree, take the firewood, put the firewood in the fire pit, take the match, use the match on the fire pit

from data.library.GameBasic import *


# A fire pit, which is a container that typically holds logs/firewood that will be lit on fire. It's not openable.
class FirePit(Container):
    def __init__(self):
        Container.__init__(self, "fire pit")
        self.properties["containerPrefix"] = "in"
        # Set the properties of this object
        self.properties["isOpenable"] = False  # A fire pit is always open

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a fire pit"

        effectiveContents = [obj.makeDescriptionStr() for obj in self.contains]
        if effectiveContents:
            outStr += " that looks to have " + ", ".join(effectiveContents[:-1]) + (
                " and " if len(effectiveContents) > 1 else "") + effectiveContents[-1] + " " + self.properties[
                          "containerPrefix"] + " it"
        else:
            outStr += " that is empty"

        return outStr


# A match, which is a device that can be used to light things on fire. It is single-use, and is removed from the simulation when used.
class Match(Device):
    def __init__(self):
        Device.__init__(self, "match")

    # Try to use the device with a patient object
    # Returns an observation string, and a success flag (boolean)
    def useWithObject(self, patientObject):
        # Remove the match from the simulation, because it's only single-use.
        self.removeSelfFromContainer()
        # If the object is not combustible, then do nothing
        if not patientObject.properties["isCombustible"]:
            return f"You try to use the match on the {patientObject.name}, but it is not combustible. The match is used up.", False
        # If the patient object is already combusting, then do nothing
        if patientObject.properties["isCombusting"]:
            return f"You try to use the match on the {patientObject.name}, but it is already on fire. The match is used up.", False
        # If the patient object has already combusted, then do nothing
        if patientObject.properties["combustionTimeRemaining"] < 0:
            return f"You try to use the match on the {patientObject.name}, but it has already combusted. The match is used up.", False
        # If we reach here, then the patient object is combustible, and is not currently on fire, and has not combusted yet
        # If the patient object is combustible, then light it on fire
        patientObject.properties["isCombusting"] = True
        return f"You use the match to light the {patientObject.name} on fire. The match is used up.", True

    def makeDescriptionStr(self, makeDetailed=False):
        return "a match"


# An axe, which is a device that can be used to chop down trees.
class Axe(Device):
    def __init__(self):
        Device.__init__(self, "axe")

        # An axe (at least, it's handle) is combustable and burns for 5 ticks
        self.properties["isCombustible"] = True
        self.properties["combustionTimeRemaining"] = 5

    # Try to use the device with a patient object
    # Returns an observation string, and a success flag (boolean)
    def useWithObject(self, patientObject):
        # Can't use the axe if it's on fire
        if self.properties["isCombusting"]:
            return "You can't use the axe because it is on fire.", False
        # If the axe has been burned, then can't use it anymore
        if self.properties["combustionTimeRemaining"] < 0:
            return "You can't use the axe because it has combusted and no longer has a handle.", False
        # If the patient object is choppable, then call it's Chop method.
        if patientObject.getProperty("isChoppable"):
            preChoppedName = patientObject.name
            if patientObject.chop():
                return f"You use the axe to chop the {preChoppedName}.", True

        return f"You're not sure how to use the axe on the {patientObject.name}.", False

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "an axe"

        # If on fire, note it
        if self.properties.get("isCombusting"):
            outStr += " that is on fire"
        elif self.properties.get("combustionTimeRemaining", 0) < 0:
            outStr += " that has combusted"
        return outStr


# A tree, which can be chopped down. It is used to make firewood. It's also combustible.
class Tree(GameObject):
    def __init__(self):
        GameObject.__init__(self, "tree")
        self.properties.update({
            "prefix": "a",
            "isMoveable": False,  # A tree is too heavy to move
            "isChoppable": True,  # A tree can be chopped down
            "isCombustible": True,  # A tree is combustable and burns for 5 ticks
            "combustionTimeRemaining": 5
        })

    def chop(self):
        if self.name == "tree":
            self.name = "chopped down tree"
            return True
        if self.name == "chopped down tree":
            self.name = "firewood"
            self.properties.update({
                "prefix": "some",  # Change prefix to "some"
                "isMoveable": True,  # Make the firewood movable
                "isChoppable": False  # No longer choppable -- it's in its smallest form
            })
            return True
        return False

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"{self.properties['prefix']} {self.name}"
        # If on fire, note it
        if self.properties["isCombusting"]:
            outStr += " that is on fire"
        elif self.properties["combustionTimeRemaining"] < 0:
            outStr += " that has combusted"
        return outStr


# The world is the root object of the game object tree.  In single room environments, it's where all the objects are located.
class ForestWorld(World):
    def __init__(self):
        World.__init__(self, "forest")

class MakeCampfireGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = ForestWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add fire pit, match, axe, and tree
        for obj_class in [FirePit, Match, Axe, Tree]:
            world.addObject(obj_class())

        return world

    def getTaskDescription(self):
        return "Your task is to make a fire in the fire pit."

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
        # (1-arg) Take, Open/Close, Detailed look/examine, Turn on/Turn off device
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0], ["take", obj])
                self.addAction("open " + objReferent, ["open", obj])
                self.addAction("close " + objReferent, ["close", obj])
                self.addAction("examine " + objReferent, ["examine", obj])
                self.addAction("turn on " + objReferent, ["turn on", obj])
                self.addAction("turn off " + objReferent, ["turn off", obj])

        # Actions with two object arguments
        # (2-arg) Use, Put
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
                            self.addAction("use " + objReferent1 + " on " + objReferent2, ["use", obj1, obj2])

        return self.possibleActions

    def actionOpen(self, obj):
        # Check if the object is a container
        if (obj.getProperty("isContainer") == True):
            # This is handled by the object itself
            obsStr, success = obj.openContainer()
            return obsStr
        else:
            return "You can't open that."

    # Close a container
    ## (OMIT, UNUSED HERE, make-campfire)
    def actionClose(self, obj):
        # Check if the object is a container
        if (obj.getProperty("isContainer") == True):
            # This is handled by the object itself
            obsStr, success = obj.closeContainer()
            return obsStr
        else:
            return "You can't close that."

        ## (OMIT, UNUSED HERE, make-campfire)

    def actionTurnOn(self, obj):
        # Check if the object is a device
        if (obj.getProperty("isDevice") == True):
            # This is handled by the object itself
            obsStr, success = obj.turnOn()
            return obsStr
        else:
            return "You can't turn on that."

        ## (OMIT, UNUSED HERE, make-campfire)

    def actionTurnOff(self, obj):
        # Check if the object is a device
        if (obj.getProperty("isDevice") == True):
            # This is handled by the object itself
            obsStr, success = obj.turnOff()
            return obsStr
        else:
            return "You can't turn off that."

        ## OMIT, UNUSED (make ice cubes)

    def actionUse(self, deviceObj, patientObject):
        # Check if the object is a device
        if (deviceObj.getProperty("isDevice") == True):

            # Enforce that the object must be in the inventory to do anything with it
            if (deviceObj.parentContainer != self.agent):
                return "You don't currently have the " + deviceObj.getReferents()[0] + " in your inventory."

            # This is handled by the object itself
            obsStr, success = deviceObj.useWithObject(patientObject)
            return obsStr
        else:
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

        action_map = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),  # Look around the environment
            "inventory": lambda: self.actionInventory(),  # Display the agent's inventory
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),  # Examine an object
            "open": lambda: self.actionOpen(action[1]),  # Open a container
            "close": lambda: self.actionClose(action[1]),  # Close a container
            "take": lambda: self.actionTake(action[1]),  # Take an object from a container
            "turn on": lambda: self.actionTurnOn(action[1]),  # Turn on a device
            "turn off": lambda: self.actionTurnOff(action[1]),  # Turn off a device
            "put": lambda: self.actionPut(action[1], action[2]),  # Put an object in a container
            "use": lambda: self.actionUse(action[1], action[2]),  # Use a device on an object
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

    def calculateScore(self):
        self.score = 0

        # Check for game-winning condition
        firepit = next((obj for obj in self.rootObject.contains if isinstance(obj, FirePit)), None)
        firewood = next((obj for obj in firepit.contains if obj.name == "firewood"), None)
        if firewood and firewood.getProperty("isCombusting"):
            self.score += 1
            self.gameOver = True
            self.gameWon = True

        # Check for game-losing condition
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        for obj in allObjects:
            if isinstance(obj, Tree) and obj.getProperty(
                    "combustionTimeRemaining") < 0 and obj.parentContainer.name != "fire pit":
                self.score = -1
                self.gameOver = True
                self.gameWon = False


if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(MakeCampfireGame(randomSeed=0))
