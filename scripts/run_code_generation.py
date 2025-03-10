import os
import re
import time
import datetime
import argparse
from os.path import join as pjoin


import pandas as pd
from termcolor import colored

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.. ')))

from bytes32.utils import count_tokens, stream_llm_gpt, extract_python_code, load_program


MAX_CONTEXT_LENGTH = 32000
MAX_PROGRAM_LENGTH = 16000


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_file", help="CSV file")
    parser.add_argument("--data", type=str, default="./data/")
    parser.add_argument("--output-folder", type=str, default=f"./results/{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}/generated_games/")
    parser.add_argument("--model", type=str, default="gpt-4o-mini")

    parser.add_argument("--strip-comments", action="store_true")
    parser.add_argument("--zero-shot", action="store_true", help="Perform zero-shot generation (no in-context example code).")

    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    os.makedirs(args.output_folder, exist_ok=True)

    experiment_name = args.experiment_file.split("/")[-1].split(".csv")[0]
    experiment_df = pd.read_csv(args.experiment_file, header=None)
    for n, row in experiment_df.iterrows():
        # The first prompt includes the desired feature, the second prompt does not
        ablation_games = {"p": row.values[0], "n": row.values[1]}

        for key in ablation_games:
            prompt_task = ablation_games[key]
            fileout_prefix = f"{experiment_name}_test_{n+1}_{key}_{args.model.split('/')[-1]}_{prompt_task[:-3]}"
            if os.path.exists(pjoin(args.output_folder, f'{fileout_prefix}_generation.py')):
                print(colored(f"Skipping: '{fileout_prefix}' already exists!", "yellow"))
                continue

            target_task = f"test_{n+1}.py"

            prompt_program = load_program(pjoin(args.data, "refactored_programs", prompt_task))
            if args.strip_comments:
                # Remove Python comments from generated_game.
                prompt_program = re.sub(r'#[^\n]*\n', '', prompt_program)

            print (f"Prompt program: {prompt_task}, total tokens: {count_tokens(prompt_program, args.model)}")

            target_spec = load_program(pjoin(args.data, "test_prompts", target_task))
            print (f"Prompt program: {target_spec}, total tokens: {count_tokens(target_spec, args.model)}")

            # 'DeveloperGPT' prompt from @skirano
            prompt = "You are DeveloperGPT, the most advanced AI developer tool on the planet.  You answer any coding question, and provide real useful example code using code blocks.  Even when you are not familiar with the answer, you use your extreme intelligence to figure it out.\n"

            #change prompt
            prompt_GameBasic = load_program(pjoin(args.data, "library", "GameBasic.py"))
            prompt += "Your task is to write a program that is a text-based simulation.\n"
            prompt += "The program should be written in Python. It should challenge the user by testing their common-sense knowledge and require multiple steps to complete. Where possible, include distractor objects and actions that do not help progress, so as to determine if the user truly understands the game mechanics. Use common-sense names for all target and distractor objects.\n"
            prompt += "```python GameBasic.py\n"
            prompt += '''
            import random

#
# Abstract class for all game objects
#
class GameObject():
    def __init__(self, name):
        # Prevent this constructor from running if it's already been run during multiple inheritance
        if hasattr(self, "constructorsRun"):
            return
        # Otherwise, keep a list of constructors that have already been run
        self.constructorsRun = ["GameObject"]

        self.name = name
        self.parentContainer = None
        self.contains = []
        self.properties = {}

        # Default properties
        self.properties["isContainer"] = False
        self.properties["isMoveable"] = True
        self.properties["isUsable"] = False
        self.properties["isActivatable"] =False

        # Initialize everything to have a starting temperature of 20 degrees C
        self.properties["temperature"] = 20.0

        # Properties for combustion
        self.properties["isCombustible"] = False  # By default, objects are not combustable
        self.properties["isCombusting"] = False  # By default, objects are not currently on fire
        self.properties["combustionTimeRemaining"] = 0  # By default, objects don't have a combustion time

    # Get a property of the object (safely), returning None if the property doesn't exist
    def getProperty(self, propertyName):
        if propertyName in self.properties:
            return self.properties[propertyName]
        else:
            return None

    # Add an object to this container, removing it from its previous container
    def addObject(self, obj):
        obj.removeSelfFromContainer()
        self.contains.append(obj)
        obj.parentContainer = self

    # Remove an object from this container
    def removeObject(self, obj):
        self.contains.remove(obj)
        obj.parentContainer = None

    # Remove the current object from whatever container it's currently in
    def removeSelfFromContainer(self):
        if self.parentContainer != None:
            self.parentContainer.removeObject(self)

    # Get all contained objects, recursively
    def getAllContainedObjectsRecursive(self):
        outList = []
        for obj in self.contains:
            # Add self
            outList.append(obj)
            # Add all contained objects
            outList.extend(obj.getAllContainedObjectsRecursive())
        return outList


    # Get all contained objects that have a specific name (not recursively)
    def containsItemWithName(self, name):
        foundObjects = []
        for obj in self.contains:
            if obj.name == name:
                foundObjects.append(obj)
        return foundObjects

    # Game tick: Perform any internal updates that need to be performed at each step of the game.
    def tick(self):
        pass

    # Get a list of referents (i.e. names that this object can be called by)
    def getReferents(self):
        return [self.name]

    # Make a human-readable string that describes this object
    def makeDescriptionStr(self, makeDetailed=False):
        return self.name

#
#   Abstract Game-object Classes
#

# Abstract class for things that can be considered 'containers' (e.g. a drawer, a box, a table, a shelf, etc.)
class Container(GameObject):
    def __init__(self, name):
        # Prevent this constructor from running if it's already been run during multiple inheritance
        if hasattr(self, "constructorsRun"):
            if "Container" in self.constructorsRun:
                return

        GameObject.__init__(self, name)
        # Otherwise, mark this constructor as having been run
        self.constructorsRun.append("Container")

        self.properties["isContainer"] = True
        self.properties["isOpenable"] = False  # Can the container be opened (e.g. a drawer, a door, a box, etc.), or is it always 'open' (e.g. a table, a shelf, etc.)
        self.properties["isOpen"] = True  # Is the container open or closed (if it is openable)
        self.properties["containerPrefix"] = "in" # The prefix to use when referring to the container (e.g. "in the drawer", "on the table", etc.)

    # Try to open the container
    # Returns an observation string, and a success flag (boolean)
    def openContainer(self):
        # First, check to see if this object is openable
        if not self.getProperty("isOpenable"):
            # If not, then it can't be opened
            return ("The " + self.name + " can't be opened.", False)

        # If this object is openable, then check to see if it is already open
        if self.getProperty("isOpen"):
            # If so, then it can't be opened
            return ("The " + self.name + " is already open.", False)

        # If this object is openable and it is closed, then open it
        self.properties["isOpen"] = True
        return ("The " + self.name + " is now open.", True)

    # Try to close the container
    # Returns an observation string, and a success flag (boolean)
    def closeContainer(self):
        # First, check to see if this object is openable
        if not (self.getProperty("isOpenable") == True):
            # If not, then it can't be closed
            return ("The " + self.name + " can't be closed.", False)

        # If this object is openable, then check to see if it is already closed
        if not (self.getProperty("isOpen") == True):
            # If so, then it can't be closed
            return ("The " + self.name + " is already closed.", False)

        # If this object is openable and it is open, then close it
        self.properties["isOpen"] = False
        return ("The " + self.name + " is now closed.", True)

    # Try to place the object in a container.
    # Returns an observation string, and a success flag (boolean)
    def placeObjectInContainer(self, obj):
        # First, check to see if this object is a container
        if not self.getProperty("isContainer"):
            # If not, then it can't be placed in a container
            return ("The " + self.name + " is not a container, so things can't be placed there.", False)

        # Check to see if the object is moveable
        if not obj.getProperty("isMoveable"):
            # If not, then it can't be removed from a container
            return ("The " + obj.name + " is not moveable.", None, False)

        # If this object is a container, then check to see if it is open
        if not self.getProperty("isOpen"):
            # If not, then it can't be placed in a container
            return ("The " + self.name + " is closed, so things can't be placed there.", False)

        # If this object is a container and it is open, then place the object in the container
        self.addObject(obj)
        return ("The " + obj.getReferents()[0] + " is placed in the " + self.name + ".", True)

    # Try to remove the object from a container.
    # Returns an observation string, a reference to the object being taken, and a success flag (boolean)
    def takeObjectFromContainer(self, obj):
        # First, check to see if this object is a container
        if not self.getProperty("isContainer"):
            # If not, then it can't be removed from a container
            return ("The " + self.name + " is not a container, so things can't be removed from it.", None, False)

        # Check to see if the object is moveable
        if not obj.getProperty("isMoveable"):
            # If not, then it can't be removed from a container
            return ("The " + obj.name + " is not moveable.", None, False)

        # If this object is a container, then check to see if it is open
        if not self.getProperty("isOpen"):
            # If not, then it can't be removed from a container
            return ("The " + self.name + " is closed, so things can't be removed from it.", None, False)

        # Check to make sure that the object is contained in this container
        if obj not in self.contains:
            return ("The " + obj.name + " is not contained in the " + self.name + ".", None, False)

        # If this object is a container and it is open, then remove the object from the container
        obj.removeSelfFromContainer()
        return ("The " + obj.getReferents()[0] + " is removed from the " + self.name + ".", obj, True)

    # Make a human-readable string that describes this object
    def makeDescriptionStr(self, makeDetailed=False):
        return "the " + self.name + "."



# Abstract class for anything that can be considered a device that turns on or off (e.g. a light, a fan, a TV, etc.)
class Device(GameObject):
    def __init__(self, name):
        # Prevent this constructor from running if it's already been run during multiple inheritance
        if hasattr(self, "constructorsRun"):
            if "Device" in self.constructorsRun:
                return
        GameObject.__init__(self, name)
        # Otherwise, mark this constructor as having been run
        self.constructorsRun.append("Device")

        self.properties["isDevice"] = True
        self.properties["isActivatable"] = True # Can this device be turned on or off?
        self.properties["isOn"] = False         # Is the device currently on or off?

    # Try to turn on the device.
    # Returns an observation string, and a success flag (boolean)
    def turnOn(self):
        # If the device isn't activatable, then return an error
        if (self.getProperty("isActivatable") == False):
            return ("It's not clear how the " + self.getReferents()[0] + " could be turned on.", False)

        # If the device is already on, then return an error
        if self.properties["isOn"]:
            return ("The " + self.getReferents()[0] + " is already on.", False)
        else:
            self.properties["isOn"] = True
            return ("The " + self.getReferents()[0] + " is now turned on.", True)

    # Try to turn off the device.
    # Returns an observation string, and a success flag (boolean)
    def turnOff(self):
        # If the device isn't activatable, then return an error
        if (self.getProperty("isActivatable") == False):
            return ("It's not clear how the " + self.getReferents()[0] + " could be turned off.", False)

        # If the device is already off, then return an error
        if not self.properties["isOn"]:
            return ("The " + self.getReferents()[0] + " is already off.", False)
        else:
            self.properties["isOn"] = False
            return ("The " + self.getReferents()[0] + " is now turned off.", True)

    # Try to use the device with a patient object (e.g. a light with a person, a fan with a person, etc.)
    # Returns an observation string, and a success flag (boolean)
    def useWithObject(self, patientObject):
        return ("You're not sure how to use the " + self.getReferents()[0] + " with the " + patientObject.name + ".", False)

    # Make a human-readable string that describes this object
    def makeDescriptionStr(self, makeDetailed=False):
        outStr = "The " + self.name + ", which is currently "
        if self.properties["isOn"]:
            outStr += "on."
        else:
            outStr += "off."
        return outStr


# A substance (like water), with specific physical properties
class Substance(GameObject):
    def __init__(self, solidName, liquidName, gasName, boilingPoint, meltingPoint, currentTemperatureCelsius):
        GameObject.__init__(self, "substance")
        # Set critical properties
        self.properties["solidName"] = solidName
        self.properties["liquidName"] = liquidName
        self.properties["gasName"] = gasName
        self.properties["boilingPoint"] = boilingPoint
        self.properties["meltingPoint"] = meltingPoint
        self.properties["temperature"] = currentTemperatureCelsius

    # Change the state of matter of the substance (and it's name) based on the current temperature
    def tick(self):
        # Check if the substance is a solid
        if self.properties["temperature"] <= self.properties["meltingPoint"]:
            self.properties["stateOfMatter"] = "solid"
            self.name = self.properties["solidName"]
        # Check if the substance is a liquid
        elif self.properties["temperature"] <= self.properties["boilingPoint"]:
            self.properties["stateOfMatter"] = "liquid"
            self.name = self.properties["liquidName"]
        # Check if the substance is a gas
        else:
            self.properties["stateOfMatter"] = "gas"
            self.name = self.properties["gasName"]

    def makeDescriptionStr(self, makeDetailed=False):
        return "some " + self.name


# The world is the root object of the game object tree.  In single room environments, it's where all the objects are located.
class World(Container):
    def __init__(self, room):
        Container.__init__(self, room)
        self.room = room

    def makeDescriptionStr(self, makeDetailed=False):
        outStr = f"You find yourself in a {self.room}.  In the {self.room}, you see: \n"
        for obj in self.contains:
            outStr += "\t" + obj.makeDescriptionStr() + "\n"

        return outStr


# The agent (just a placeholder for a container for the inventory)
class Agent(Container):
    def __init__(self, name):
        GameObject.__init__(self, name)
        Container.__init__(self, name)
        self.name = name

    def getReferents(self):
        return ["yourself"]

    def makeDescriptionStr(self, makeDetailed=False):
        return "yourself"


class TextGame:

    def __init__(self, randomSeed):
        # Random number generator, initialized with a seed passed as an argument
        self.random = random.Random(randomSeed)
        # The agent/player
        self.agent = Agent("agent")
        # Game Object Tree
        self.rootObject = self.initializeWorld()
        # Game score
        self.score = 0
        self.numSteps = 0
        # Game over flag
        self.gameOver = False
        self.gameWon = False
        # Last game observation
        self.observationStr = self.rootObject.makeDescriptionStr()
        # Register actions
        self.actions = []
        self.registerActions()
        # Do calculate initial scoring
        self.calculateScore()


    # Creating/initializing the world/environment for this game
    def initializeWorld(self):
        ...

    # Get the task description for this game
    def getTaskDescription(self):
        ...
    def registerActions(self):
        ...
    # Make a dictionary whose keys are object names (strings), and whose values are lists of object references with those names.
    # This is useful for generating valid actions, and parsing user input.
    def makeNameToObjectDict(self):
        # Get a list of all game objects
        allObjects = self.rootObject.getAllContainedObjectsRecursive()

        # Make a dictionary whose keys are object names (strings), and whose values are lists of object references with those names.
        nameToObjectDict = {}
        for obj in allObjects:
            for name in obj.getReferents():
                # print("Object referent: " + name)
                if name in nameToObjectDict:
                    nameToObjectDict[name].append(obj)
                else:
                    nameToObjectDict[name] = [obj]

        return nameToObjectDict

    #
    #   Action generation
    #

    def addAction(self, actionStr, actionArgs):
        # Check whether the action string key already exists -- if not, add a blank list
        if not (actionStr in self.possibleActions):
            self.possibleActions[actionStr] = []
        # Add the action arguments to the list
        self.possibleActions[actionStr].append(actionArgs)

    # Returns a list of valid actions at the current time step
    def generatePossibleActions(self):
        ...

    #
    #   Interpret actions
    #

    # Take an object from a container
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
        return obsStr + " You put the " + obj.getReferents()[0] + " in your inventory."

    # Put an object in a container
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
        return obsStr1 + "\n" + obsStr2

    # Display agent inventory
    def actionInventory(self):
        # Get the inventory
        inventory = self.agent.contains
        # If the inventory is empty, return a message
        if (len(inventory) == 0):
            return "Your inventory is empty."
        # Otherwise, return a list of the inventory items
        else:
            obsStr = "You have the following items in your inventory:\n"
            for obj in inventory:
                obsStr += "\t" + obj.makeDescriptionStr() + "\n"
            return obsStr

    # More actions
    ...

    # Performs an action in the environment, returns the result (a string observation, the reward, and whether the game is completed).
    def step(self, actionStr):
        ...

    # Call the object update for each object in the environment
    def doWorldTick(self):
        # Get a list of all objects in the environment
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        # Loop through all objects, and call their tick()
        for obj in allObjects:
            obj.tick()

    # Calculate the game score
    def calculateScore(self):
        ...

# Main Program
def main(game):

    # Get a list of valid actions
    possibleActions = game.generatePossibleActions()
    # print("Possible actions: " + str(possibleActions.keys()))
    print("Task Description: " + game.getTaskDescription())
    print("")
    print("Initial Observation: " + game.observationStr)
    print("")
    print("Type 'help' for a list of possible actions.")
    print("")


    # Main game loop
    # while not game.gameOver:
    while True:

        # Get the player's action
        actionStr = ""
        while ((len(actionStr) == 0) or (actionStr == "help")):
            actionStr = input("> ")
            if (actionStr == "help"):
                print("Possible actions: " + str(possibleActions.keys()))
                print("")
                actionStr = ""
            elif (actionStr == "exit") or (actionStr == "quit"):
                return

        # Perform the action
        observationStr, score, reward, gameOver, gameWon = game.step(actionStr)

        # Get a list of valid actions
        possibleActions = game.generatePossibleActions()

        # Print the current game state
        print("Observation: " + observationStr)
        print("")
        print("Current step: " + str(game.numSteps))
        print("Score: " + str(score))
        print("Reward: " + str(reward))
        print("Game Over: " + str(gameOver))
        print("Game Won: " + str(gameWon))
        print("")
        print("----------------------------------------")


# Run the main program
if __name__ == "__main__":
    # Random seed
    randomSeed = 0

    # Create a new game
    game = TextGame(randomSeed=randomSeed)
    main(game)


            '''
            prompt += "```\n"
            prompt += "GameBasic.py includes the classes GameObject, Container, Device, Substance, World, Agent, and a base implementation of TextGame. In your game code, you must derive new classes from these basic classes to implement your game logic.\n"
            prompt += "Your code must include a derived class of TextGame that implements the following member functions: __init__(self, randomSeed), getTaskDescription(self), generatePossibleActions(self), step(self, actionStr), and calculateScore(self).\n"


            if not args.zero_shot:
                prompt += "\nHere is an example of a text-based simulation on a different topic that you can use as a template:\n"
                prompt += "```python\n"
                prompt += prompt_program
                prompt += "```\n"

            prompt += "\nProduce the Python code for the following task specification:\n"
            prompt += "```python\n"
            prompt += target_spec + "\n\n"

            prompt_out_file = pjoin(args.output_folder, f'{fileout_prefix}_prompt_out.txt')
            print(f"Writing prompt to file {prompt_out_file})")
            with open(prompt_out_file, 'w') as f:
                f.write(prompt)

            print(colored(f"Prompting {args.model} for 1-shot generation...", "yellow"))
            context_length = count_tokens(prompt, args.model)
            print(colored(f"  Context length {context_length} tokens.", "yellow"))

            max_new_tokens = min(max(0, MAX_CONTEXT_LENGTH-context_length), MAX_PROGRAM_LENGTH)
            start = time.time()
            response = stream_llm_gpt(prompt, args.model, max_tokens=max_new_tokens)
            print(colored(f"  Response time: {time.time()-start} secs.", "yellow"))

            print(colored(f"  Responded with {count_tokens(response, args.model)} tokens.", "yellow"))
            programOut = extract_python_code(response)

            generation_txt_file = pjoin(args.output_folder,f"{fileout_prefix}_generation.txt")
            print (f"  Saving response to: {generation_txt_file}")
            with open(generation_txt_file, 'w') as f:
                f.write(response)

            generation_py_file = pjoin(args.output_folder,f"{fileout_prefix}_generation.py")
            print (f"  Saving postprocessed program to: {generation_py_file}")
            with open(generation_py_file, 'w') as f:
                f.write(programOut)


if __name__ == "__main__":
    main()
