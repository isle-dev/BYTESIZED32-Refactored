# refactored plant-tree.py
# Process and problem of conde generation
# success junf
from GameBasic import *


# A hole to plant a tree
class Hole(Container):
    def __init__(self, name):
        Container.__init__(self, name)
        self.properties["isMoveable"] = False

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"a {self.name}"

        effectiveContents = [obj.makeDescriptionStr() for obj in self.contains]

        if effectiveContents:
            outStr += " containing " + ", ".join(effectiveContents[:-1]) + (
                " and " + effectiveContents[-1] if len(effectiveContents) > 1 else "")
        else:
            outStr += " that is empty"

        return outStr

# Water class
class Water(GameObject):
    def __init__(self):
        GameObject.__init__(self, "water")

    def getReferents(self):
        return [f"water in {self.parentContainer.name}"]

    def makeDescriptionStr(self, makeDetailed=False):
        return "water"


# A sink
class Sink(Container, Device):
    def __init__(self, isOn=False):
        Container.__init__(self, "sink")
        Device.__init__(self, "sink")

        self.properties["containerPrefix"] = "in"
        self.properties["isActivatable"] = True  # a sink can be activated
        self.properties["isMoveable"] = False
        self.properties["isOn"] = isOn


    def tick(self):
        # Get the objects contained in the sink
        containedObjects = self.getAllContainedObjectsRecursive()
        # Check if the sink is on
        if self.properties["isOn"]:
            # Check each container to make sure it contains water
            for obj in containedObjects:
                # If the object is a container and doesn't contain water, add some
                if isinstance(obj, Container) and len(obj.containsItemWithName("water"))==0:
                    obj.addObject(Water())

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a sink"
        outStr += " that is currently " + ("on" if self.properties["isOn"] else "off")

        if not self.contains:
            outStr += " and that is empty"
        else:
            if not makeDetailed:
                outStr += " and that contains one or more items."
            else:
                outStr += " and that contains the following items: \n"
                for obj in self.contains:
                    outStr += "\t" + obj.makeDescriptionStr() + "\n"


        return outStr

# Tool class
class Tool(GameObject):
    def __init__(self, name, type):
        GameObject.__init__(self, name)
        self.properties["type"] = type


    def makeDescriptionStr(self, makeDetailed=False):
        det = 'an' if self.name[0].lower() in ['a', 'e', 'i', 'o', 'u'] else 'a'
        return f"{det} {self.name}"

# Tree class
class Tree(GameObject):
    def __init__(self, name):
        GameObject.__init__(self, name)

    def makeDescriptionStr(self, makeDetailed=False):
        det = 'an' if self.name[0].lower() in ['a', 'e', 'i', 'o', 'u'] else 'a'
        return f"{det} {self.name}"

# Soil class
class Soil(GameObject):
    def __init__(self, wet=False):
        GameObject.__init__(self, 'soil')
        self.properties["wet"] = wet

    def makeDescriptionStr(self, makeDetailed=False):
        return "wet soil" if self.properties['wet'] else "dry soil"

# WaterContainer class
class WaterContainer(Container):
    def __init__(self, name):
        GameObject.__init__(self, name)
        self.properties["isWaterContainer"] = True

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"a {self.name}"

        effectiveContents = [obj.makeDescriptionStr() for obj in self.contains]

        if effectiveContents:
            outStr += " containing " + ", ".join(effectiveContents[:-1]) + (
                " and " + effectiveContents[-1] if len(effectiveContents) > 1 else "")
        else:
            outStr += " that is empty"

        return outStr




# Game world specific to planting trees
class GardenWorld(World):
    def __init__(self):
        World.__init__(self, "garden")


# Game class for planting trees
class PlantTreeGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = GardenWorld()

        # Add the agent to the world
        world.addObject(self.agent)

        # Add some tools (shovel and distractors)
        tools = ["shovel", "hammer", "screwer"]
        for toolName in tools:
            tool = Tool(toolName, toolName)
            world.addObject(tool)

        # Add a sink
        sink = Sink()
        world.addObject(sink)

        # Add some water containers
        containerNames = ["bucket", "jug"]
        for name in containerNames:
            container = WaterContainer(name)
            world.addObject(container)

        # Add a tree
        tree = Tree("tree")
        world.addObject(tree)

        return world

    def getTaskDescription(self):
        return "Your task is to plant the tree and water it."

    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Zero-argument actions
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])

        # Additional actions specific to this game
        # (1-arg) Dig
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                # self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0], ["take", obj])
                self.addAction("turn on " + objReferent, ["turn on", obj])
                self.addAction("turn off " + objReferent, ["turn off", obj])
                self.addAction("dig with " + objReferent, ["dig", obj])

        # (2-arg) Pour
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            containerPrefix = "in"
                            if obj2.properties["isContainer"]:
                                containerPrefix = obj2.properties["containerPrefix"]
                            self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2, ["put", obj1, obj2])
                            self.addAction("pour " + objReferent1 + " into " + objReferent2, ["pour", obj1, obj2])

        return self.possibleActions

    def actionTake(self, obj):
        # If the object doesn't have a parent container, then it's dangling and something has gone wrong
        if (obj.parentContainer == None):
            return "Something has gone wrong -- that object is dangling in the void.  You can't take that."

        # Take the object from the parent container, and put it in the inventory
        obsStr, objRef, success = obj.parentContainer.takeObjectFromContainer(obj)
        if (success == False):
            return obsStr

        # Add the object to the inventory
        self.agent.addObject(obj)
        return " You put the " + obj.getReferents()[0] + " in your inventory."

    def actionPut(self, objToMove, newContainer):
        # Check that the destination container is a container
        if (newContainer.getProperty("isContainer") == False):
            return "You can't put things in the " + newContainer.getReferents()[0] + "."

        # Enforce that the object must be in the inventory to do anything with it
        if (objToMove.parentContainer != self.agent):
            return "You don't currently have the " + objToMove.getReferents()[0] + " in your inventory."

        # Take the object from it's current container, and put it in the new container.
        # Deep copy the reference to the original parent container, because the object's parent container will be changed when it's taken from the original container
        originalContainer = objToMove.parentContainer
        obsStr1, objRef, success = objToMove.parentContainer.takeObjectFromContainer(objToMove)
        if (success == False):
            return obsStr1

        # Put the object in the new container
        obsStr2, success = newContainer.placeObjectInContainer(objToMove)
        if (success == False):
            # For whatever reason, the object can't be moved into the new container. Put the object back into the original container
            originalContainer.addObject(objToMove)
            return obsStr2

        # Success -- show both take and put observations
        return "\n" + obsStr2

    def actionDig(self, tool):
        if tool.parentContainer != self.agent:
            return f"To use {tool.name}, you need to have it in your inventory first."
        if tool.getProperty("type") != "shovel":
            return f"You can't dig with {tool.name}."
        hole = Hole("hole")
        self.rootObject.addObject(hole)
        self.agent.addObject(Soil())
        return f"You dig a hole on the ground. You get some soil."

    def actionPour(self, water, target):
        if water.name != "water":
            return f"Cannot pour {water.name}."
        water.removeSelfFromContainer()
        if target.getProperty("isWaterContainer"):
            target.addObject(water)
        elif target.name == 'soil':
            target.properties['wet'] = True
            del water
        else:
            del water

        return f"You pour water into {target.name}"

    def actionTurnOn(self, obj):
        # Check if the object is a device
        if (obj.getProperty("isActivatable") == True):
            # This is handled by the object itself
            obsStr, success = obj.turnOn()
            return obsStr
        else:
            return "You can't turn on that."

    def actionTurnOff(self, obj):
        # Check if the object is a device
        if (obj.getProperty("isActivatable") == True):
            # This is handled by the object itself
            obsStr, success = obj.turnOff()
            return obsStr
        else:
            return "You can't turn off that."

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
            "look around": self.rootObject.makeDescriptionStr,
            "inventory": self.actionInventory,
            "take": lambda: self.actionTake(action[1]),
            "turn on": lambda: self.actionTurnOn(action[1]),
            "turn off": lambda: self.actionTurnOff(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "dig": lambda: self.actionDig(action[1]),
            "pour": lambda: self.actionPour(action[1], action[2]),
        }

        # Check if the action verb exists in the map
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

        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        for obj in allObjects:
            if obj.name == "hole":
                tree_planted = any(isinstance(obj_hole, Tree) for obj_hole in obj.contains)
                soil_added = any(obj_hole.name == "soil" for obj_hole in obj.contains)
                watered = any(obj_hole.getProperty("wet") for obj_hole in obj.contains if obj_hole.name == "soil")
                if tree_planted and soil_added and watered:
                    self.score = 1
                    self.gameOver = True
                    self.gameWon = True


if __name__ == "__main__":
    args = parser_commands()
    main(PlantTreeGame(randomSeed=0), args.commands, args.status)