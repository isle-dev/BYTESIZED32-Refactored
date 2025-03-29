# Refactored volume-container.py using GameBasic templates
# Process and problem of code
# Success Haonan(2025.2)

# Task Description: Your task is to simulate an experiment that measures the volume of a container by measuring the water it can hold.
# Environment: room
# Task-critical Objects: Water, Sink, WaterContainer, GraduatedCylinder
# High-level object classes: Container (Sink, WaterContainer), WaterContainer (GraduatedCylinder)
# Critical properties: volume (WaterContainer), containedLiquidVolume (GraduatedCylinder)
# Actions: look, inventory, take/put objects, pour liquid, answer
# Distractor Items: WaterContainer
# Distractor Actions: None
# High-level solution procedure: put target water container into the sink, turn on sink, pour water in the target water container to the graduated cylinder, read graduated cylinder, answer

from data.library.GameBasic import *

# Water
class Water(GameObject):
    def __init__(self, volume):
        GameObject.__init__(self, "water")
        self.properties["isLiquid"] = True
        self.properties["volume"] = volume

    def getReferents(self):
        return [f"water in {self.parentContainer.name}"]

    def makeDescriptionStr(self, makeDetailed=False):
        return "water"

# A sink
class Sink(Container, Device):
    def __init__(self, isOn=False):
        GameObject.__init__(self, "sink")
        Container.__init__(self, "sink")
        self.properties["isActivatable"] = True  # a sink can be activated
        self.properties["isMoveable"] = False
        self.properties["isOn"] = isOn

    # On each step that the sink is on, add water to any object in the sink that doesn't have water on it
    def tick(self):
        # Get the objects contained in the sink
        containedObjects = self.getAllContainedObjectsRecursive()
        # Check if the sink is on
        if self.properties["isOn"]:
            # Check each container to make sure it contains water
            for obj in containedObjects:
                # Check if the object is a container
                if isinstance(obj, WaterContainer):
                    # Check if the container contains water
                    foundObjects = obj.containsItemWithName("water")
                    # If it doesn't contain any water, add some
                    if len(obj.containsItemWithName("water")) == 0:
                        water = Water(obj.getProperty("volume"))
                        obj.addObject(water)
                    # If it contains water, add water to the container's max volume
                    else:
                        foundObjects[0].properties["volume"] = obj.getProperty("volume")

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a sink"

        # Check if on
        if self.properties["isOn"]:
            outStr += " that is currently on"
        else:
            outStr += " that is currently off"

        # Check if open
        if len(self.contains) == 0:
            outStr += " and that is empty"
        else:
            if not makeDetailed:
                outStr += " and that contains one or more items."
            else:
                outStr += " and that contains the following items: \n"
                for obj in self.contains:
                    outStr += "\t" + obj.makeDescriptionStr() + "\n"

        return outStr

# Water Container
class WaterContainer(Container):
    def __init__(self, name, volume):
        GameObject.__init__(self, name)
        self.properties["isWaterContainer"] = True
        self.properties["volume"] = volume

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"a {self.name}"
        effectiveContents = [obj.makeDescriptionStr() for obj in self.contains]

        if effectiveContents:
            outStr += " containing " + ", ".join(effectiveContents[:-1]) + (
                " and " + effectiveContents[-1] if len(effectiveContents) > 1 else "")
        else:
            outStr += " that is empty"

        return outStr

# Graduated Cylinder for measuring liquid volume
class GraduatedCylinder(WaterContainer):
    def __init__(self, volume):
        WaterContainer.__init__(self, "graduated cylinder", volume)
        self.properties['containedLiquidVolume'] = 0

    # Add liquid to the graduated cylinder, remove it from its previous container, update contained liquid volume
    def addObject(self, obj):
        obj.removeSelfFromContainer()
        self.contains.append(obj)
        obj.parentContainer = self
        self.properties['containedLiquidVolume'] = obj.getProperty("volume")

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"a {self.name}"

        if self.properties['containedLiquidVolume'] > 0:
            outStr += f" containing {self.properties['containedLiquidVolume']} mL {self.contains[0].name}"
        else:
            outStr += " that is empty"

        return outStr


# The world is the root object of the game object tree.  In single room environments, it's where all the objects are located.
class RoomWorld(World):
    def __init__(self):
        World.__init__(self, "room")

class VolumeContainerGame(TextGame):
    def __init__(self, randomSeed):
        # Player answer volume
        self.answer_volume = None
        TextGame.__init__(self, randomSeed)

    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = RoomWorld()
        # Add the agent (the mother bird) into the world (nest)
        world.addObject(self.agent)
        # Add a sink
        sink = Sink()
        world.addObject(sink)
        # Add 2-5 water containers, one of them is the target
        possible_water_containers = ["cup", "glass", "mug", "bottle", "bowl"]
        self.random.shuffle(possible_water_containers)
        num_water_containers = self.random.randint(2, 5)
        water_containers = possible_water_containers[:num_water_containers]
        # select volumes for the containers randomly from 50 mL to 200 mL
        water_containers_volume = self.random.choices(range(50, 200), k=num_water_containers)
        target_id = self.random.randint(0, num_water_containers - 1)

        for i in range(num_water_containers):
            water_container = WaterContainer(water_containers[i], water_containers_volume[i])
            world.addObject(water_container)
            if i == target_id:
                self.target_water_container = water_containers[i]
                self.target_water_container_volume = water_containers_volume[i]

        # Add a 200 mL graduated cylinder
        graduated_cylinder = GraduatedCylinder(200)
        world.addObject(graduated_cylinder)

        # Return the world
        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return f"Your task is to figure out the volume of the {self.target_water_container}."

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
        # (1-arg) Take, urn on/Turn off device, Answer
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0], ["take", obj])
                self.addAction(f"turn on {objReferent}", ["turn on", obj])
                self.addAction(f"turn off {objReferent}", ["turn off", obj])
        for i in range(50, 200):
            self.addAction(f"answer {i} mL", ["answer", i])

        # Actions with two object arguments
        # (2-arg) Put, Pour
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            containerPrefix = "in"
                            if obj2.properties["isContainer"]:
                                containerPrefix = obj2.properties["containerPrefix"]
                            self.addAction(f"put {objReferent1} {containerPrefix} {objReferent2}", ["put", obj1, obj2])
                            self.addAction(f"pour {objReferent1} into {objReferent2}", ["pour", obj1, obj2])

        return self.possibleActions

    # Pour water
    def actionPour(self, water, target):
        if type(water) != Water:
            return f"Cannot pour {water.name}."
        if not target.getProperty("isWaterContainer"):
            referent = water.getReferents()[0]
            water.removeSelfFromContainer()
            del water
            return f"{referent} is poured on the ground."
        else:
            # if current container is bigger than the target, the target is filled and there are some water left in the current container
            if water.parentContainer.getProperty("volume") > target.getProperty("volume"):
                water.properties["volume"] = water.parentContainer.getProperty("volume") - target.getProperty("volume")
                extra_water = Water(target.getProperty("volume"))
                target.addObject(extra_water)
            # otherwise, the target container will take all water
            else:
                water.removeSelfFromContainer()
                target.addObject(water)

            return f"You pour {water.getReferents()[0]} into {target.name}"

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

    # Answer
    def actionAnswer(self, volume):
        self.answer_volume = volume
        return f"You believe the {self.target_water_container}'s volume is {volume} mL."

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

        # Dictionary to map verbs to methods
        action_map = {
            "look around": self.rootObject.makeDescriptionStr,  # Look around the environment -- i.e. show the description of the world.
            "inventory": self.actionInventory,  # Display the agent's inventory
            "take": lambda: self.actionTake(action[1]),  # Take an object from a container
            "turn on": lambda: self.actionTurnOn(action[1]),  # turn on a sink
            "turn off": lambda: self.actionTurnOff(action[1]),  # Turn off a sink
            "put": lambda: self.actionPut(action[1], action[2]),  # Turn off a sink
            "pour": lambda: self.actionPour(action[1], action[2]),  # Turn off a sink
            "answer": lambda: self.actionAnswer(action[1]),  # answer
        }

        # Catch-all
        self.observationStr = action_map.get(actionVerb, lambda action: "ERROR: Unknown action.")()

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
        if self.answer_volume is not None:
            if self.target_water_container_volume == self.answer_volume:
                self.score += 1
                self.gameOver, self.gameWon = True, True
            else:
                self.gameOver, self.gameWon = True, False

if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(VolumeContainerGame(randomSeed=0))