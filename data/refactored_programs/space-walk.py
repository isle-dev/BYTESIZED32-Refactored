# refactored space-walk.py
# Success Haonan Wang and Ziang Xiao(Nov 2024)

from data.library.GameBasic import *

# A room
class Room(Container):
    def __init__(self, name, isOuterSpace=False):
        Container.__init__(self, name)
        self.properties["isMoveable"] = False
        self.properties["isOuterSpace"] = isOuterSpace
        self.connects = {}  # other rooms that this room connects to, {room: door}

    def connect(self, room):
        if room not in self.connects:
            self.connects[room] = None
            room.connects[self] = None

    def connectsToOuterSpace(self, visited):
        visited.append(self)
        if self.properties["isOuterSpace"]:
            return True
        connected = False
        for r in self.connects:
            if r in visited:
                continue
            elif self.connects[r] is not None and not self.connects[r].getProperty("is_open"):
                continue
            elif r.getProperty("isOuterSpace"):
                connected = True
                break
            else:
                connected = r.connectsToOuterSpace(visited)
                if connected:
                    break
        return connected

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"You find yourself in a {self.name}.  In the {self.name}, you see: \n"
        for obj in self.contains:
            outStr += "\t" + obj.makeDescriptionStr() + "\n"

        return outStr


# A door
class Door(GameObject):
    def __init__(self, name, room1, room2, is_open=False):
        GameObject.__init__(self, name)
        self.properties["is_open"] = is_open
        self.properties["isMoveable"] = False
        self.connects = {room1: room2, room2: room1}
        room1.connects[room2] = self
        room2.connects[room1] = self

    def open(self, curr_room):
        if curr_room not in self.connects:
            return "You can't open a door that is not in the current room."
        elif self.properties["is_open"]:
            return f"The door to the {self.connects[curr_room].name} is already open."
        else:
            self.properties["is_open"] = True
            return f"You open the door to the {self.connects[curr_room].name}."

    def close(self, curr_room):
        if curr_room not in self.connects:
            return "You can't close a door that is not in the current room."
        elif not self.properties["is_open"]:
            return f"The door to the {self.connects[curr_room].name} is already closed."
        else:
            self.properties["is_open"] = False
            return f"You close the door to the {self.connects[curr_room].name}."

    def getReferents(self, curr_room):
        return [f"door to {self.connects[curr_room].name}"]

    def makeDescriptionStr(self, curr_room, makeDetailed=False):
        status = "open" if self.properties["is_open"] else "closed"
        return f"a door to the {self.connects[curr_room].name} that is {status}"


# Space suit
class SpaceSuit(GameObject):
    def __init__(self, name):
        GameObject.__init__(self, name)


# World Setup
class SpaceWorld(World):
    def __init__(self):
        World.__init__(self, "world")

    def makeDescriptionStr(self, room, makeDetailed=False):
        outStr = f"You find yourself in a {room.name}.  In the {room.name}, you see: \n"
        for obj in room.contains:
            outStr += "\t" + obj.makeDescriptionStr() + "\n"
        # describe room connection information
        outStr += "You also see:\n"
        for _, door in room.connects.items():
            outStr += f"\t {door.makeDescriptionStr(room)}\n"

        return outStr



# The agent
class SpaceAgent(Agent):
    def __init__(self):
        Agent.__init__(self)
        self.properties["wearSpaceSuit"] = False
        self.properties["die"] = False

    def tick(self):
        if self.parentContainer.connectsToOuterSpace([]) and not self.getProperty("wearSpaceSuit"):
            self.properties["die"] = True


# Game Implementation
class SpaceWalkGame(TextGame):
    def __init__(self, randomSeed):
        # Random number generator, initialized with a seed passed as an argument
        self.random = random.Random(randomSeed)
        # The agent/player
        self.agent = SpaceAgent()
        # Game Object Tree
        self.rootObject = self.initializeWorld()
        # Game score
        self.score = 0
        self.numSteps = 0
        # Game over flag
        self.gameOver = False
        self.gameWon = False
        # Last game observation
        self.observationStr = self.rootObject.makeDescriptionStr(self.current_room)
        # Do calculate initial scoring
        self.calculateScore()

    def initializeWorld(self):
        world = SpaceWorld()

        spaceship, airlock, outer_space = Room("spaceship"), Room("airlock"), Room("outer space", isOuterSpace=True)
        world.addObject(spaceship)
        world.addObject(airlock)
        world.addObject(outer_space)
        spaceship.connect(airlock)
        airlock.connect(outer_space)

        inner_door, outer_door = Door("inner door", spaceship, airlock), Door("outer door", airlock, outer_space)
        world.addObject(inner_door)
        world.addObject(outer_door)

        spaceship.addObject(self.agent)
        self.current_room = spaceship

        world.addObject(SpaceSuit("space suit"))

        return world

    def getTaskDescription(self):
        return "Your task is to conduct a space walk."

    def makeNameToObjectDict(self):
        allObjects = self.current_room.getAllContainedObjectsRecursive()

        nameToObjectDict = {}
        for obj in allObjects:
            for name in obj.getReferents():
                if name in nameToObjectDict:
                    nameToObjectDict[name].append(obj)
                else:
                    nameToObjectDict[name] = [obj]

        for _, door in self.current_room.connects.items():
            for referent in door.getReferents(self.current_room):
                if referent in nameToObjectDict:
                    nameToObjectDict[referent].append(door)
                else:
                    nameToObjectDict[referent] = [door]

        return nameToObjectDict

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
                self.addAction("open " + objReferent, ["open", obj])
                self.addAction("close " + objReferent, ["close", obj])
                self.addAction("put on " + objReferent, ["wear", obj])

        for room in self.current_room.connects:
            for room_ref in room.getReferents():
                self.addAction("move to " + room_ref, ["move", room])

        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if (obj1 != obj2):
                            containerPrefix = "in"
                            if obj2.properties["isContainer"]:
                                containerPrefix = obj2.properties["containerPrefix"]
                            self.addAction("put " + objReferent1 + " " + containerPrefix + " " + objReferent2, ["put", obj1, obj2])


        return self.possibleActions

    def actionPut(self, objToMove, newContainer):
        # Check that the destination container is a container
        if (newContainer.getProperty("isContainer") == False):
            if type(newContainer) == Door:
                curr_room = self.agent.parentContainer
                obj_ref = newContainer.getReferents(curr_room)[0]
            else:
                obj_ref = newContainer.getReferents()[0]
            return "You can't put things in the " + obj_ref + "."

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
        return obsStr1 + "\n" + obsStr2

    def actionOpen(self, obj):
        if isinstance(obj, Door):
            return obj.open(self.current_room)
        else:
            return "You can't open that."

    def actionClose(self, obj):
        if isinstance(obj, Door):
            return obj.close(self.current_room)
        else:
            return "You can't close that."

    def actionPutOn(self, obj):
        if not isinstance(obj, SpaceSuit):
            return f"You can't put on {obj.name}"

        self.agent.properties["wearSpaceSuit"] = True
        obsStr, objRef, success = obj.parentContainer.takeObjectFromContainer(obj)
        if not success:
            return obsStr
        self.agent.addObject(obj)
        return obsStr + f" You put on the {obj.name}."

    def actionMove(self, room):
        if not isinstance(room, Room):
            return f"Cannot move to the {room.name}"
        elif room not in self.agent.parentContainer.connects:
            return f"There is no way from {self.agent.parentContainer.name} to {room.name}."
        elif not self.agent.parentContainer.connects[room].getProperty("is_open"):
            return f"The door to the {room.name} is closed."
        else:
            current_location = self.agent.parentContainer.name
            self.agent.removeSelfFromContainer()
            room.addObject(self.agent)
            self.current_room = room
            return f"You move from {current_location} to {room.name}."

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
            "look around": lambda: self.rootObject.makeDescriptionStr(self.agent.parentContainer),
            "inventory": lambda: self.actionInventory(),
            "take": lambda: self.actionTake(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "open": lambda: self.actionOpen(action[1]),
            "close": lambda: self.actionClose(action[1]),
            "wear": lambda: self.actionPutOn(action[1]),
            "move": lambda: self.actionMove(action[1])
        }

        self.observationStr = actions.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):
        if self.agent.properties["die"]:
            self.score = 0
            self.gameOver = True
            self.gameWon = False
            return
            # Lose if the spaceship directly connects to the outerspace
        else:
            allObjects = self.rootObject.getAllContainedObjectsRecursive()
            for obj in allObjects:
                if obj.name == "spaceship":
                    if obj.connectsToOuterSpace([]):
                        self.score = 0
                        self.gameOver = True
                        self.gameWon = False
                        return

        if self.agent.parentContainer.name == "outer space":
            self.score = 1
            self.gameOver = True
            self.gameWon = True


if __name__ == "__main__":
    randomSeed = 0
    game = SpaceWalkGame(randomSeed=randomSeed)
    main(game)