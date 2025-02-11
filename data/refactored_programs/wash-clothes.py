# refactored wash-clothes.py
# Process and problem of code
# Success Haonan(2025.2)

# Task: Create a micro-simulation that models how to wash clothes with a washing machine and dry clothes with a dryer.
# Environment: room
# Task-critical Objects: WashingMachine, Dryer, Clothes, DetergentBottle, Detergent, Container, Basket
# High-level object classes: Device (WashingMachine, Dryer, DetergentBottle), Container (WashingMachine, Dryer, Basket)
# Critical properties: isDirty (Clothes), isWet (Clothes), cycleStage(WashingMachine, Dryer)
# Actions: look, inventory, wait, examine, take/put objects, open/close containers, turn on/off devices, use X on Y
# Distractor Items: None
# Distractor Actions: None
# High-level solution procedure: put dirty clothes into the washing machine, add detergent, turn on washing machine, wait for cycle to finish, put wet clothes into the dryer, turn on dryer, wait for cycle to finish, put all clothes into the basket

from data.library.GameBasic import *

# A washing machine, which is a device that can hold clothes.  When it's turned on, it washes the clothes (changes them from dirty to clean)
# as long as it has detergent in it.  If it doesn't have detergent in it, then it doesn't change them from dirty to clean.
class WashingMachine(Container, Device):
    def __init__(self):
        GameObject.__init__(self, "washing machine")
        Container.__init__(self, "washing machine")
        Device.__init__(self, "washing machine")

        # Set the properties of this object
        self.properties["isOpenable"] = True  # A washing machine is openable
        self.properties["isOpen"] = False     # A washing machine is closed by default
        self.properties["isMoveable"] = False # A washing machine is too heavy to move (and doesn't really need to be moved for this simulation)

        self.properties["cycleStage"] = 0  # The current stage of the washing machine's cycle.
        self.properties["finishedCycle"] = False  # Set to True when the washing machine has finished washing the dishes.  Reset when it's open.

    # Try to turn on the washing machine.
    def turnOn(self):
        if self.properties["isOpen"]:
            return ("The " + self.name + " is opened, so it can't be turned on.", False)
        return super().turnOn()

    def tick(self):
        # If the washing machine is opened, turn it off and reset
        if self.properties["isOpen"]:
            self.properties.update({"isOn": False, "finishedCycle": False, "cycleStage": 0})

        # If the washing machine is on, wash the clothes
        if self.properties["isOn"]:
            if self.properties["cycleStage"] < 3:
                self.properties["cycleStage"] += 1

            # Stage 1: Check for detergent and wash clothes
            if self.properties["cycleStage"] == 2:
                containsDetergent = any(obj.name == "detergent" for obj in self.getAllContainedObjectsRecursive())
                if containsDetergent:
                    for obj in self.getAllContainedObjectsRecursive():
                        if isinstance(obj, Clothes):
                            obj.properties['isDirty'] = False

                # Mark clothes wet
                for obj in self.getAllContainedObjectsRecursive():
                    if isinstance(obj, Clothes):
                        obj.properties['isWet'] = True

            # Stage 2: Finish the cycle and turn off
            elif self.properties["cycleStage"] == 3:
                self.properties["finishedCycle"] = True
                self.properties["cycleStage"] = 0
                self.turnOff()

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a washing machine"
        if self.properties["finishedCycle"]:
            outStr += " with a blinking green light"

        if self.properties["isOn"]:
            outStr += " that is currently on"
        else:
            if self.properties["isOpen"]:
                outStr += " that is currently open"
                if len(self.contains) == 0:
                    outStr += " and empty"
                else:
                    if not makeDetailed:
                        outStr += " and contains one or more items."
                    else:
                        outStr += " and contains the following items: \n"
                        for obj in self.contains:
                            outStr += "\t" + obj.makeDescriptionStr() + "\n"
            else:
                outStr += " that is currently closed"
        return outStr

# A dryer, which is a device that can hold clothes. When it's turned on, it dries the clothes (changes them from wet to dry)
class Dryer(Container, Device):
    def __init__(self):
        GameObject.__init__(self, "dryer")
        Container.__init__(self, "dryer")
        Device.__init__(self, "dryer")

        # Set the properties of this object
        self.properties["isOpenable"] = True  # A dryer is openable
        self.properties["isOpen"] = False     # A dryer is closed by default
        self.properties["isMoveable"] = False  # A dryer is too heavy to move (and doesn't really need to be moved for this simulation)

        self.properties["cycleStage"] = 0  # The current stage of the dryer's cycle.  0 = not running, 1 = drying, 2 = finished
        self.properties["finishedCycle"] = False  # Set to True when the dryer has finished drying the clothes.  Reset when it's open.

    # Try to turn on the dryer.
    # Returns an observation string, and a success flag (boolean)
    def turnOn(self):
        # The dryer can't be turned on if it's opened
        if self.properties["isOpen"]:
            return ("The " + self.name + " is opened, so it can't be turned on.", False)
        return super().turnOn()

    def tick(self):
        # If the dryer is opened, then it automatically turns off and resets
        if (self.properties["isOpen"] == True):
            self.properties["isOn"] = False
            self.properties["finishedCycle"] = False
            self.properties["cycleStage"] = 0

        # If the dryer is on, then dry the clothes
        if (self.properties["isOn"] == True):
            # Increment the cycle stage
            if (self.properties["cycleStage"] < 3):
                self.properties["cycleStage"] += 1

            # Check for stage 1
            if self.properties["cycleStage"] == 2:
                # Clothes become dry
                for obj in self.getAllContainedObjectsRecursive():
                    if (type(obj) == Clothes):
                        obj.properties['isWet'] = False

            # Check for stage 2
            elif self.properties["cycleStage"] == 3:
                # Set the dryer to finished
                self.properties["finishedCycle"] = True
                self.properties["cycleStage"] = 0
                # Turn off the dryer
                self.turnOff()
        else:
            # If the dryer is off, then don't dry the clothes
            pass

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a dryer"
        # Check if finished a cycle
        if self.properties["finishedCycle"]:
            outStr += " with a blinking green light"

        if self.properties["isOn"]:
            outStr += " that is currently on"
        else:
            if self.properties["isOpen"]:
                outStr += " that is currently open"
                if len(self.contains) == 0:
                    outStr += " and empty"
                else:
                    if not makeDetailed:
                        outStr += " and contains one or more items."
                    else:
                        outStr += " and contains the following items: \n"
                        for obj in self.contains:
                            outStr += "\t" + obj.makeDescriptionStr() + "\n"
            else:
                outStr += " that is currently closed"
        return outStr

class Clothes(GameObject):
    # Constructor.
    # isClean is a boolean that indicates whether the dish is initialized as clean or dirty
    def __init__(self, name, isDirty=True, isWet=False):
        GameObject.__init__(self, name)

        self.properties["isDirty"] = isDirty
        self.properties["isWet"] = isWet

    # Get a list of referents (i.e. names that this object can be called by)
    def getReferents(self):
        is_dirty = "dirty " if self.properties["isDirty"] else "clean "
        is_wet = "wet " if self.properties["isWet"] else "dry "

        # Allow reference by either the clothes name, or optionally saying its dirty/clean or wet/dry
        return [self.name, f"{is_dirty}{self.name}", f"{is_wet}{self.name}", f"{is_dirty}{is_wet}{self.name}"]

    def makeDescriptionStr(self, makeDetailed=False):
        is_dirty = "dirty " if self.properties["isDirty"] else "clean "
        is_wet = "wet " if self.properties["isWet"] else "dry "
        return f"a {is_dirty}{is_wet}{self.name}"

# A bottle of dish soap
class DetergentBottle(Device):
    def __init__(self):
        Device.__init__(self, "bottle of detergent")

    # Try to use the device with a patient object (e.g. a light with a person, a fan with a person, etc.)
    # Returns an observation string, and a success flag (boolean)
    def useWithObject(self, patientObject):
        # If the patient object is a washing machine, then add detergent in it
        if (patientObject.name == "washing machine"):
            # Add a squirt of soap to the dishwasher
            patientObject.addObject(Detergent())
            return ("You add some detergent into the washing machine.", True)
        return ("You're not sure how to use the " + self.name + " with the " + patientObject.name + ".", False)

    def makeDescriptionStr(self, makeDetailed=False):
        return "a bottle of detergent"

# Detergent
class Detergent(GameObject):
    def __init__(self):
        GameObject.__init__(self, "detergent")

# A basket used as an answer box
class Basket(Container):
    def __init__(self):
        GameObject.__init__(self, "basket")
        Container.__init__(self, "basket")
        self.properties["isMoveable"] = False
        self.properties["isOpenable"] = False

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a {self.name}"

# The world is the root object of the game object tree.  In single room environments, it's where all the objects are located.
class RoomWorld(World):
    def __init__(self):
        World.__init__(self, "room")

# Game Implementation
class WashClothesGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = RoomWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add a washing machine
        washing_machine = WashingMachine()
        world.addObject(washing_machine)

        # Add a dryer
        dryer = Dryer()
        world.addObject(dryer)

        # Add dish soap
        detergent_bottle = DetergentBottle()
        world.addObject(detergent_bottle)

        # Add some clothes names and shuffle them
        clothes_names = ["shirt", "coat", "jacket", "dress", "skirt", "vest", "sweater"]
        self.random.shuffle(clothes_names)

        # Add some random number of dirty clothes to the world (minimum 3, maximum 5)
        self.num_dirty_clothes = self.random.randint(3, 5)

        for i in range(self.num_dirty_clothes):
            # create a Clothes object
            clothes = Clothes(clothes_names[i])
            # Add the clothes to the environment
            world.addObject(clothes)

        # Also add a few clean dishes
        for i in range(self.num_dirty_clothes, len(clothes_names)):
            # create a Clothes object
            clothes = Clothes(clothes_names[i], isDirty=False)
            # Add the clothes to the environment
            world.addObject(clothes)

        # Add a basket as an answer box
        basket = Basket()
        world.addObject(basket)

        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to wash the dirty clothes and dry them."

    # Returns a list of valid actions at the current time step
    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}
        # Actions with zero arguments
        # (0-arg) Look around the environment and Look at the agent's current inventory
        # (0-arg) Wait. Do nothing, just wait 1 tick
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory"),
                       ("wait", "wait")]:
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

    # Open a container
    def actionOpen(self, obj):
        # Check if the object is a container
        if (obj.getProperty("isContainer") == True):
            # This is handled by the object itself
            obsStr, success = obj.openContainer()
            return obsStr
        else:
            return "You can't open that."

    # Close a container
    def actionClose(self, obj):
        # Check if the object is a container
        if (obj.getProperty("isContainer") == True):
            # This is handled by the object itself
            obsStr, success = obj.closeContainer()
            return obsStr
        else:
            return "You can't close that."

    def actionTurnOn(self, obj):
        # Check if the object is a device
        if (obj.getProperty("isDevice") == True):
            # This is handled by the object itself
            obsStr, success = obj.turnOn()
            return obsStr
        else:
            return "You can't turn on that."

    def actionTurnOff(self, obj):
        # Check if the object is a device
        if (obj.getProperty("isDevice") == True):
            # This is handled by the object itself
            obsStr, success = obj.turnOff()
            return obsStr
        else:
            return "You can't turn off that."

    def actionUse(self, deviceObj, patientObject):
        # Check if the object is a device
        if (deviceObj.getProperty("isDevice") == True):
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

        # Dictionary of actions mapped to their corresponding methods
        action_map = {
            "look around": lambda: self.rootObject.makeDescriptionStr(),  # Look around the environment -- i.e. show the description of the world.
            "inventory": lambda: self.actionInventory(),  # Display the agent's inventory
            "wait": lambda: "You wait.",  # wait one tick
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

    # Calculate the game score
    def calculateScore(self):
        self.score = 0
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        all_complete = all((not obj.getProperty("isDirty") and not obj.getProperty("isWet") and obj.parentContainer.name == 'basket') for obj in allObjects if isinstance(obj, Clothes))

        if all_complete:
            self.score, self.gameOver, self.gameWon = 1, True, True

if __name__ == "__main__":
    # Set random seed 0 and Create a new game
    main(WashClothesGame(randomSeed=0))