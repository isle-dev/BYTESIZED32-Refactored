# refactored cooking.py
# Success Haonan Wang and Ziang Xiao(Oct)

from GameBasic import *


# A cook book
class CookBook(GameObject):
    def __init__(self, receipt):
        GameObject.__init__(self, "cook book")
        # receipt = {ingredients:[(cut methods, cook methods)]}
        self.properties["receipt"] = receipt

    def read(self):
        instruction = "Gather all following ingredients and follow the directions to prepare this tasty meal.\n\n"

        instruction += "Ingredients:\n"
        for ingredient in self.properties["receipt"]:
            instruction += f"\t{ingredient.name}\n"

        instruction += "\nDirections:\n"
        for ingredient in self.properties["receipt"]:
            for prepare_method in self.properties["receipt"][ingredient]:
                if prepare_method is not None:
                    instruction += f"\t{prepare_method} the {ingredient.name}\n"
        instruction += "\tprepare meal\n"

        return instruction

# Ingredient with properties of cut and cook
class Ingredient(GameObject):
    def __init__(self, name):
        GameObject.__init__(self, name)
        self.properties["cut"] = None  # how the ingredient is cut
        self.properties["cook"] = None  # how the ingredient is cooked

    def makeDescriptionStr(self, makeDetailed=False):
        cut = self.properties["cut"][1] + ' ' if self.properties["cut"] else ""
        cook = self.properties["cook"][1] + ' ' if self.properties["cook"] else ""
        return f"the {cut}{cook}{self.name}"

# A device to cook (stove or oven)
class CookingDevice(Device):
    def __init__(self, name, cook_method):
        Device.__init__(self, name)
        self.properties["cook_method"] = cook_method  # e.g., ("roast", "roasted")

    def cook(self, ingredient):
        if ingredient.properties["cook"]:
            return f"The {ingredient.name} has already been cooked."
        else:
            ingredient.properties["cook"] = self.properties["cook_method"]
            return f"You {self.properties['cook_method'][0]} the {ingredient.name} in the {self.name}."

# A knife
class Knife(GameObject):
    def __init__(self, name):
        GameObject.__init__(self, name)

    def cut(self, ingredient, cut_method):
        if ingredient.properties["cut"]:
            return f"The {ingredient.name} has already been {ingredient.properties['cut'][1]}."
        else:
            ingredient.properties["cut"] = cut_method
            return f"You {cut_method[0]} the {ingredient.name}."

# World setup specific to the cooking game
class KitchenWorld(World):
    def __init__(self):
        super().__init__("kitchen")

# Game Implementation
class CookingGame(TextGame):
    def __init__(self, randomSeed):
        # Additional attributes of the game
        #   - Number of actions that can earn a reward
        self.full_mark = 0
        #   - Additional Game Score
        self.prepare_meal = False
        TextGame.__init__(self, randomSeed)

    # Initialize the world/environment for this game
    def initializeWorld(self):
        world = KitchenWorld()

        # Add the agent
        world.addObject(self.agent)

        # cutting and cooking methods
        possible_cutting = ["slice", "dice", "chop", None]
        possible_cooking = ["fry", "roast", None]

        # randomly add some ingredients
        possible_ingredients = ["green hot pepper", "onion", "patato", "cucumber", "carrot"]
        num_ingredients = self.random.randint(2, 4)
        self.random.shuffle(possible_ingredients)

        # random generate the receipt
        self.receipt = {}
        for i in range(len(possible_ingredients)):
            ingredient = Ingredient(possible_ingredients[i])
            world.addObject(ingredient)
            if i < num_ingredients:
                # earn a reward when an ingredient on the receipt is taken
                self.full_mark += 1
                cut = self.random.choice(possible_cutting)
                cook = self.random.choice(possible_cooking)
                # earn a reward each time an ingredient is correctly prepared
                if cut is not None:
                    self.full_mark += 1
                if cook is not None:
                    self.full_mark += 1
                self.receipt[ingredient] = (cut, cook)

        # Add a cook book
        cook_book = CookBook(self.receipt)
        world.addObject(cook_book)

        # Add a knife
        knife = Knife("knife")
        world.addObject(knife)

        # Add a stove
        stove = CookingDevice("stove", ("fry", "fried"))
        oven = CookingDevice("oven", ("roast", "roasted"))
        world.addObject(stove)
        world.addObject(oven)

        # Return the world
        return world


    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to prepare a meal following the instructions of the cook book."

    # Returns a list of valid actions at the current time step
    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Actions with zero arguments
        for action in [("look around", "look around"), ("look", "look around"), ("inventory", "inventory"),
                       ("prepare meal", "prepare meal")]:
            self.addAction(action[0], [action[1]])
            # Actions with one object argument

        # Actions with one arguments
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction("take " + objReferent, ["take", obj])
                self.addAction("take " + objReferent + " from " + obj.parentContainer.getReferents()[0],
                               ["take", obj])
                self.addAction("read " + objReferent, ["read", obj])

        # Actions with two object arguments
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
                            if (obj1 != obj2):
                                self.addAction("slice " + objReferent1 + " with " + objReferent2, ["slice", obj1, obj2])
                                self.addAction("dice " + objReferent1 + " with " + objReferent2, ["dice", obj1, obj2])
                                self.addAction("chop " + objReferent1 + " with " + objReferent2, ["chop", obj1, obj2])
                                self.addAction("cook " + objReferent1 + " in " + objReferent2, ["cook", obj1, obj2])

        return self.possibleActions

    #
    # Interpret actions
    #
    # Utility function to cut actions
    def actionCut(self, cut_method, ingredient, knife):
        # Check if the object is an ingredient
        if not isinstance(ingredient, Ingredient):
            return f"You can't {cut_method} the {ingredient.name}."
        # Check if the tool is a knife
        if not isinstance(knife, Knife):
            return f"You can't {cut_method} with {knife.name}."

        # The agent must have the ingredient in inventory
        if not isinstance(ingredient.parentContainer, Agent):
            return f"You should take the {ingredient.name} first."

        # The agent must have the knife in inventory
        if not isinstance(knife.parentContainer, Agent):
            return f"You should take the {knife.name} first."

        # Define cut methods
        cut_methods = {"slice": "sliced", "dice": "diced", "chop": "chopped"}
        if cut_method in cut_methods:
            cut = (cut_method, cut_methods[cut_method])
        else:
            return f"I don't know how to {cut_method}."
        return knife.cut(ingredient, cut)

    # Utility function to cook actions
    def actionCook(self, ingredient, device):
        # Check if the object is an ingredient
        if not isinstance(ingredient, Ingredient):
            return f"You can't cook the {ingredient.name}."
        # Check if the tool is a device
        if not isinstance(device, Device):
            return f"You can't cook in {device.name}."

        # The agent must have the ingredient in inventory
        if not isinstance(ingredient.parentContainer, Agent):
            return f"You should take the {ingredient.name} first."

        # Cook the ingredient using the device
        return device.cook(ingredient)

    # Utility function to read cookbook
    def actionRead(self, cook_book):
        # Check the type of the cook book
        if not isinstance(cook_book, CookBook):
            return f"You can't read the {cook_book.name}."

        # Check if the agent has the cook book
        if not isinstance(cook_book.parentContainer, Agent):
            return f"You should take the {cook_book.name} first."

        # Read the cook book
        return cook_book.read()

    # Interpret prepare meal action
    def actionPrepareMeal(self):
        self.prepare_meal = True
        return "You prepare the meal."

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
            "slice": lambda: self.actionCut("slice", action[1], action[2]),
            "dice": lambda: self.actionCut("dice", action[1], action[2]),
            "chop": lambda: self.actionCut("chop", action[1], action[2]),
            "cook": lambda: self.actionCook(action[1], action[2]),
            "read": lambda: self.actionRead(action[1]),
            "prepare meal": self.actionPrepareMeal
        }

        # Execute the mapped function or return an error if action is unknown
        self.observationStr = action_map.get(actionVerb, lambda: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = round(self.score - lastScore, 2)

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    # Calculate the game score
    def calculateScore(self):
        # Baseline score
        self.score = 0

        for ingredient in self.receipt:
            # check if the agent has all ingredients in inventory
            if type(ingredient.parentContainer) == Agent:
                self.score += 1

            # check if all ingredients are prepared properly
            # The player loses the game if they wrongly prepare any ingredients
            if ingredient.properties['cut'] is not None:
                if ingredient.properties['cut'][0] == self.receipt[ingredient][0]:
                    self.score += 1
                else:
                    self.gameOver, self.gameWon= True, False

            if ingredient.properties['cook'] is not None:
                if ingredient.properties['cook'][0] == self.receipt[ingredient][1]:
                    self.score += 1
                else:
                    self.gameOver, self.gameWon = True, False

        if self.prepare_meal and self.score == self.full_mark:
            self.gameOver, self.gameWon = True, True
            self.score += 1

        self.score /= self.full_mark + 1
        self.score = round(self.score, 2)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Execute a game command.")
    parser.add_argument("commands", help="The command to execute in the game")
    args = parser.parse_args()

    print("Command received")
    # Random seed
    randomSeed = 10
    # Create a new game
    game = CookingGame(randomSeed=randomSeed)
    main(game, args.commands)