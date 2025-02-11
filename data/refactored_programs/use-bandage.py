# refactored use-bandage.py
# Process and problem of code


from data.library.GameBasic import *


# A box of bandages
class BandageBox(Container):
    def __init__(self):
        GameObject.__init__(self, "bandage box")
        Container.__init__(self, "bandage box")
        self.properties["isOpenable"] = True
        self.properties["isOpen"] = False

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a bandage box"
        if not self.properties["isOpen"]:
            outStr += " that is closed"
        else:
            outStr += " that is open"
            effectiveContents = [obj.makeDescriptionStr() for obj in self.contains]

            if effectiveContents:
                outStr += " and that looks to have " + ", ".join(effectiveContents[:-1])
                if len(effectiveContents) > 1:
                    outStr += " and " + effectiveContents[-1]
                outStr += " " + self.properties["containerPrefix"] + " it"
            else:
                outStr += " and appears to be empty"

        return outStr


# A bandage
class Bandage(GameObject):
    def __init__(self):
        GameObject.__init__(self, "bandage")

    def makeDescriptionStr(self, makeDetailed=False):
        return "a bandage"


# A person, that contains different body parts
class Person(Container):
    def __init__(self):
        Container.__init__(self, "person")
        self.properties["containerPrefix"] = "on"

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a " + self.name
        effectiveContents = [obj.makeDescriptionStr() for obj in self.contains]
        if effectiveContents:
            outStr += " that looks to have " + ", ".join(effectiveContents[:-1])
            if len(effectiveContents) > 1:
                outStr += " and " + effectiveContents[-1]
        else:
            outStr += " that appears to be empty"

        return outStr


# A body part with possible wound
class BodyPart(Container):
    def __init__(self, bodyPartName, hasWound=False):
        Container.__init__(self, bodyPartName)
        self.properties["containerPrefix"] = "on"
        self.properties["hasWound"] = hasWound

    def placeObjectInContainer(self, obj):

        # Check to see if the object is an instance of Clothing
        if isinstance(obj, Clothing):
            # If so, check to see if the clothing is appropriate for this body part
            if not (self.name in obj.properties["bodyPartItFits"]):
                return ("The " + obj.name + " is not appropriate for the " + self.name + ".", False)

        # Otherwise, call the base class method
        return Container.placeObjectInContainer(self, obj)

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "a " + self.name
        if self.properties["hasWound"]:
            outStr += " that has a wound"
        if len(self.containsItemWithName("bandage")) == 1:
            outStr += " with a bandage on it"
        elif len(self.containsItemWithName("bandage")) > 1:
            outStr += " with bandages on it"

        effectiveContents = [
            obj.makeDescriptionStr() for obj in self.contains if obj.name != "bandage"
        ]

        if effectiveContents:
            outStr += " that has " + ", ".join(effectiveContents[:-1])
            if len(effectiveContents) > 1:
                outStr += " and " + effectiveContents[-1]
            outStr += " " + self.properties["containerPrefix"] + " it"

        return outStr


# A sticker with a description
class Sticker(GameObject):
    def __init__(self, stickerDescription):
        GameObject.__init__(self, "sticker")
        self.properties["stickerDescription"] = stickerDescription

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a sticker{self.properties['stickerDescription']}"


# A piece of clothing fitting specific body parts
class Clothing(GameObject):
    def __init__(self, name, bodyPartItFits):
        GameObject.__init__(self, name)
        self.properties["bodyPartItFits"] = bodyPartItFits

    def makeDescriptionStr(self, makeDetailed=False):
        return "a " + self.name


# World Setup for bathroom
class BathroomWorld(World):
    def __init__(self):
        World.__init__(self, "bathroom")

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "You find yourself in a bathroom.  Around you, you see: \n"
        for obj in self.contains:
            outStr += "\t" + obj.makeDescriptionStr() + "\n"

        return outStr


# Game Implementation
class UseBandageGame(TextGame):
    def __init__(self, randomSeed):
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = BathroomWorld()

        world.addObject(self.agent)

        person = Person()
        world.addObject(person)

        bodyPartNames = ["left hand", "right hand", "left foot", "right foot", "head"]
        self.random.shuffle(bodyPartNames)
        for idx, bodyPartName in enumerate(bodyPartNames):
            hasWound = idx == 0
            bodyPart = BodyPart(bodyPartName, hasWound=hasWound)
            person.addObject(bodyPart)
        self.random.shuffle(person.contains)

        bandageBox = BandageBox()
        world.addObject(bandageBox)

        bandage = Bandage()
        bandageBox.addObject(bandage)

        stickerMessages = [
            " with a picture of a cat",
            " with a picture of a dog",
            " with a picture of a fish",
            " that is pink",
            " that says 'get well soon'",
            " that says 'I donated blood'"
        ]
        self.random.shuffle(stickerMessages)

        sticker = Sticker(stickerMessages[0])
        world.addObject(sticker)

        distractorClothing = [
            Clothing("blue glove", ["left hand", "right hand"]),
            Clothing("red glove", ["left hand", "right hand"]),
            Clothing("warm sock", ["left foot", "right foot"]),
            Clothing("pink hat", ["head"]),
            Clothing("baseball hat", ["head"]),
        ]
        self.random.shuffle(distractorClothing)
        world.addObject(distractorClothing[0])

        self.random.shuffle(world.contains)

        return world

    def getTaskDescription(self):
        return "Your task is to put bandages on any cuts."

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
                self.addAction("open " + objReferent, ["open", obj])
                self.addAction("close " + objReferent, ["close", obj])
                self.addAction("examine " + objReferent, ["examine", obj])

        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if (obj1 != obj2):
                            containerPrefix = "in"
                            if obj2.properties["isContainer"]:
                                containerPrefix = obj2.properties["containerPrefix"]
                            self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2,
                                           ["put", obj1, obj2])

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
            "look around": lambda: self.rootObject.makeDescriptionStr(),
            "inventory": lambda: self.actionInventory(),
            "examine": lambda: action[1].makeDescriptionStr(makeDetailed=True),
            "open": lambda: self.actionOpen(action[1]),
            "close": lambda: self.actionClose(action[1]),
            "take": lambda: self.actionTake(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
        }

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
        bodyPartsMissingBandages = 0
        for obj in allObjects:
            if isinstance(obj, BodyPart):
                if (obj.getProperty("hasWound") == True):
                    # Check if the body part has a bandage on it
                    if (len(obj.containsItemWithName("bandage")) > 0):
                        self.score += 1
                    else:
                        bodyPartsMissingBandages += 1

        if bodyPartsMissingBandages == 0:
            self.gameOver = True
            self.gameWon = True


if __name__ == "__main__":
    randomSeed = 1
    game = UseBandageGame(randomSeed=randomSeed)
    main(game)
