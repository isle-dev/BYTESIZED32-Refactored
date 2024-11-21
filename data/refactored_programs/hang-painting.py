# refactored hang-painting.py
# Success Haonan Wang and Ziang Xiao(Nov 2024)

from data.library.GameBasic import *


# Specific Game Objects

# A nail
class Nail(Container):
    def __init__(self):
        Container.__init__(self, "nail")

    # Hang a picture on the nail
    def hang(self, picture):
        if not isinstance(picture, Picture):
            return f"The {picture.name} is not a picture."
        if not isinstance(self.parentContainer, Wall):
            return f"You can't hang the {picture.name} on the nail because it is not hammered on a wall."
        if self.contains:
            return f"Another picture already hangs on the nail."

        self.addObject(picture)
        return f"You hang the {picture.name} on the {self.name}."

    def makeDescriptionStr(self, makeDetailed=False):
        if not self.contains:
            return "a nail"
        return f"a nail, which has a {self.contains[0]} hanging on it"


# A wall
class Wall(Container):
    def __init__(self, name):
        Container.__init__(self, name)
        self.properties["isMoveable"] = False

    # Override the method to prevent placing objects on wall
    def placeObjectInContainer(self, obj):
        return f"You can't place the {obj.name} on the {self.name}.", False

    # Override the method to prevent taking nails off the wall
    def takeObjectFromContainer(self, obj):
        return f"You can't get the {obj.name} off the wall.", None, False

    # Nails can be hammered on the wall
    def hammer(self, nail):
        if isinstance(nail, Nail):
            self.addObject(nail)

    def makeDescriptionStr(self, makeDetailed=False):
        if not self.contains:
            return f"a {self.name}"
        return f"a {self.name}, which has {len(self.contains)} nail(s)"


# A picture
class Picture(GameObject):
    def __init__(self, name):
        GameObject.__init__(self, name)


# A hammer
class Hammer(GameObject):
    def __init__(self, name):
        GameObject.__init__(self, name)


# World Setup
class LivingRoomWorld(World):
    def __init__(self):
        World.__init__(self, "living room")


# Game Implementation
class HangPaintingGame(TextGame):
    def __init__(self, randomSeed):
        # Target picture
        self.target_picture = None
        # Target wall
        self.target_wall = None
        super().__init__(randomSeed)

    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = LivingRoomWorld()

        # Add the agent
        world.addObject(self.agent)

        # Add four walls
        walls = ["left", "right", "front", "back"]
        self.target_wall = f"{self.random.choice(walls)} wall"
        for wall_name in walls:
            wall = Wall(f"{wall_name} wall")
            world.addObject(wall)

        # Add a hammer
        hammer = Hammer("hammer")
        world.addObject(hammer)

        # Add a nail
        nail = Nail()
        world.addObject(nail)

        # Add several pictures
        possible_pictures = ["picture of a mountain", "picture of a dog", "picture of a girl", "picture of a palace", "picture of a car"]
        num_pictures = self.random.randint(2, 5)
        self.random.shuffle(possible_pictures)
        all_pictures = possible_pictures[:num_pictures]
        self.target_picture = self.random.choice(all_pictures)

        for picture_name in all_pictures:
            picture = Picture(picture_name)
            world.addObject(picture)

        # Return the world
        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return f'Your task is to hang the {self.target_picture} on the {self.target_wall}.'

    # Generate possible actions
    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Zero-argument actions
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory")]:
            self.addAction(action[0], [action[1]])
        # Actions with one object argument
        # (1-arg) Take
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0],
                                 ["take", obj])

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
                            self.addAction("hang " + objReferent1 + " on " + objReferent2, ["hang", obj1, obj2])

        # Actions with three object arguments
        # (3-arg) Hammer
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for objReferent3, objs3 in allObjects.items():
                    for obj1 in objs1:
                        for obj2 in objs2:
                            for obj3 in objs3:
                                if obj1 != obj2 and obj2 != obj3 and obj3 != obj1 and isinstance(obj1, Nail) and isinstance(obj2, Wall) and isinstance(obj3, Hammer):
                                    self.addAction(f"hammer {objReferent1} on {objReferent2} with {objReferent3}", ["hammer", obj1, obj2, obj3])

        return self.possibleActions

    def actionHammer(self, nail, wall, hammer):
        # check nail
        if not isinstance(nail, Nail):
            return f"You can't hammer {nail.name}."
        # check wall
        if not isinstance(wall, Wall):
            return f"You can't hammer {nail.name} on {wall.name}."
        # check hammer
        if not isinstance(hammer, Hammer):
            return f"You can't hammer with {hammer.name}."

        # check if the agent has the nail
        if nail.parentContainer != self.agent:
            return f"You need to take the {nail.name} first."

        # check if the agent has the hammer
        if hammer.parentContainer != self.agent:
            return f"You don't have the {hammer.name}."

        wall.hammer(nail)
        return f"The {nail.name} is hammered on the {wall.name}."

    def actionHang(self, picture, nail):
        # check nail
        if not isinstance(nail, Nail):
            return f"You can't hang the {picture.name} on the {nail.name}."

        # check if the agent has the picture
        if picture.parentContainer != self.agent:
            return f"You need to take the {picture.name} first."

        observationStr = nail.hang(picture)
        return observationStr

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

        # Mapping action verbs to corresponding functions
        action_map = {
            "look around": self.rootObject.makeDescriptionStr,
            "inventory": self.actionInventory,
            "take": lambda: self.actionTake(action[1]),
            "put": lambda: self.actionPut(action[1], action[2]),
            "hammer": lambda: self.actionHammer(action[1], action[2], action[3]),
            "hang": lambda: self.actionHang(action[1], action[2])
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
        # Calculate the game score
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        for obj in allObjects:
            # Fail if the nail is hammered on a wrong wall
            if type(obj) == Nail:
                if obj.parentContainer.name != self.target_wall and type(obj.parentContainer) == Wall:
                    self.score, self.gameOver, self.gameWon  = 0, True, False

                elif obj.parentContainer.name == self.target_wall and obj.containsItemWithName(self.target_picture):
                    self.score, self.gameOver, self.gameWon  = 1, True, True


if __name__ == "__main__":
    # Random seed
    randomSeed = 0

    # Create a new game
    game = HangPaintingGame(randomSeed=randomSeed)
    main(game)