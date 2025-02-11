# refactored blood-type.py
# Process but problem of doubting the playthroughs
# Success junf
from GameBasic import *


# A patient with specific blood type who needs a blood transfusion
class Patient(GameObject):
    def __init__(self, blood_type, Rh):
        GameObject.__init__(self, "patient")
        # The blood type here is modeled as a basic type plus Rh-positive or Rh-negative
        self.properties["blood_type"] = (blood_type, Rh)
        self.given_blood = None

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a {self.name} whose blood type is Type {self.properties['blood_type'][0]} {self.properties['blood_type'][1]}"


# Blood with a certain type
class Blood(GameObject):
    def __init__(self, blood_type, Rh):
        GameObject.__init__(self, "blood")
        # The blood type here is modeled as a basic type plus Rh-positive or Rh-negative
        self.properties["blood_type"] = (blood_type, Rh)

    def getReferents(self):
        return [f"Type {self.properties['blood_type'][0]} {self.properties['blood_type'][1]} {self.name}"]

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a bag of Type {self.properties['blood_type'][0]} {self.properties['blood_type'][1]} {self.name}"


# World Setup
class EmergencyRoom(World):
    def __init__(self):
        World.__init__(self, "emergency room")


# Game Implementation
class BloodTypeGame(TextGame):

    def __init__(self, randomSeed):
        # A lookup table to decide the blood types accepted for each type
        self.blood_type_lut = {
            'A': ['A', 'O'],
            'B': ['B', 'O'],
            'AB': ['A', 'B', 'AB', 'O'],
            'O': ['O']
        }
        self.blood_type_rh_lut = {
            'positive': ['positive', 'negative'],
            'negative': ['negative']
        }
        TextGame.__init__(self, randomSeed)

    # Create/initialize the world/environment for this game
    def initializeWorld(self):
        world = EmergencyRoom()

        # Add the agent
        world.addObject(self.agent)

        # Add a patient with a randomly chosen blood type
        blood_types = ['A', 'B', 'AB', 'O']
        Rh = ['positive', 'negative']
        patient_blood_type = self.random.choice(blood_types)
        patient_rh = self.random.choice(Rh)
        patient = Patient(patient_blood_type, patient_rh)
        world.addObject(patient)

        # Available blood configurations
        matched_types = []
        unmatched_types = []
        for blood_type in blood_types:
            for rh in Rh:
                if blood_type in self.blood_type_lut[patient_blood_type] \
                        and rh in self.blood_type_rh_lut[patient_rh]:
                    matched_types.append((blood_type, rh))
                else:
                    unmatched_types.append((blood_type, rh))

        # Randomly selects blood types available
        num_avail_accepted_types = self.random.randint(1, len(matched_types))
        num_avail_unaccepted_types = self.random.randint(0, len(unmatched_types))
        available_accepted_types = self.random.sample(matched_types, k=num_avail_accepted_types)
        available_unaccepted_types = self.random.sample(unmatched_types, k=num_avail_unaccepted_types)

        # Add available matching blood
        for blood_type, rh in available_accepted_types:
            world.addObject(Blood(blood_type, rh))

        # Add available unmatching blood
        for blood_type, rh in available_unaccepted_types:
            world.addObject(Blood(blood_type, rh))

        # Return the world
        return world

    # Get the task description for this game
    def getTaskDescription(self):
        return "Your task is to give a correct type of blood to the patient."

    # Returns a list of valid actions at the current time step
    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Zero-argument actions
        for action in ["look around", "look", "inventory"]:
            self.addAction(action, [action])

        # One-object actions (Take)
        for objReferent, objs in allObjects.items():
            for obj in objs:
                self.addAction(f"take {objReferent}", ["take", obj])
                self.addAction(f"take {objReferent} from {obj.parentContainer.getReferents()[0]}", ["take", obj])

        # Two-object actions (Put and Give)
        for objReferent1, objs1 in allObjects.items():
            for objReferent2, objs2 in allObjects.items():
                for obj1 in objs1:
                    for obj2 in objs2:
                        if obj1 != obj2:
                            # Put action with containerPrefix
                            containerPrefix = obj2.properties.get("containerPrefix", "in") if obj2.properties.get(
                                "isContainer") else "in"
                            self.addAction(f"put {objReferent1} {containerPrefix} {objReferent2}", ["put", obj1, obj2])
                            # Give action
                            self.addAction(f"give {objReferent1} to {objReferent2}", ["give", obj1, obj2])

        return self.possibleActions

    #
    #   Interpret actions
    #

    def actionGive(self, blood, patient):
        # Check the type of the blood
        if not isinstance(blood, Blood):
            return f"You cannot give {blood.name}."
        # Check the type of the patient
        elif not isinstance(patient, Patient):
            return f"You cannot give blood to {patient.name}."
        # Check if the agent has the blood
        elif blood.parentContainer.name != 'agent':
            return f"You need to take the blood first."
        else:
            patient.given_blood = blood.properties['blood_type']
            return f"You give {blood.makeDescriptionStr()} to {patient.name}"
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
            "take": lambda action: self.actionTake(action[1]),
            "put": lambda action: self.actionPut(action[1], action[2]),
            "give": lambda action: self.actionGive(action[1], action[2])
        }

        self.observationStr = action_map.get(actionVerb, lambda action: "ERROR: Unknown action.")(action)

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

        # If blood transfusion is done and the blood given is correct, the player wins
        # Otherwise, game is over and the player loses
        allObjects = self.rootObject.getAllContainedObjectsRecursive()
        for obj in allObjects:
            if isinstance(obj, Patient) and obj.given_blood is not None:
                given_blood_type, given_blood_Rh = obj.given_blood
                if given_blood_type in self.blood_type_lut[obj.getProperty("blood_type")[0]] \
                        and given_blood_Rh in self.blood_type_rh_lut[obj.getProperty("blood_type")[1]]:
                    self.score += 1
                    self.gameOver, self.gameWon  = True, True
                else:
                    self.gameOver, self.gameWon  = True, False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Execute a game command.")
    parser.add_argument("commands", help="The command to execute in the game")
    args = parser.parse_args()

    print("Command received")
    # Random seed
    randomSeed = 0
    # Create a new game
    game = BloodTypeGame(randomSeed=randomSeed)
    main(game, args.commands)