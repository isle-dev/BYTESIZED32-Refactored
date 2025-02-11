# refactored clean-energy.py
# Process and problem
from GameBasic import *

# A region, has a renewable resource and a power station
class Region(Container):
    def __init__(self, name, resource):
        Container.__init__(self, name)
        self.properties["resource"] = resource

    def makeDescriptionStr(self, makeDetailed=False):
        resource_map = {
            "sun": "has enough sunshine all year round.",
            "water": "is near a large river.",
            "wind": "has steady wind."
        }
        resource_desc = resource_map.get(self.properties["resource"], None)
        assert resource_desc is not None, f"Unknown resource {self.properties['resource']}"

        return f"{self.name} {resource_desc} It has {self.contains[0].makeDescriptionStr()}."


# A power plant
class PowerPlant(GameObject):
    def __init__(self, name, efficiency, capacity):
        GameObject.__init__(self, name)
        self.properties["running_efficiency"] = efficiency
        self.properties["capacityKW"] = capacity

    def makeDescriptionStr(self, makeDetailed=False):
        return f"a {self.name}, whose current generation capacity is {self.properties['capacityKW']}kW and is at {self.properties['running_efficiency']*100}% efficiency"


# World Setup
class EnergyWorld(World):
    def __init__(self):
        World.__init__(self, "world")

    def makeDescriptionStr(self, makeDetailed=False):
        num_regions = len(self.contains)
        outStr = f"You are in charge of {num_regions} regions. Modify power plants in the regions to use clean energy.\n"
        for obj in self.contains:
            outStr += "\t" + obj.makeDescriptionStr() + "\n"
        return outStr


class CleanEnergyGame(TextGame):
    def __init__(self, randomSeed):
        self.capacity_per_plant = 1000
        TextGame.__init__(self, randomSeed)

    def initializeWorld(self):
        world = EnergyWorld()

        # Generate 3-5 regions
        num_regions = self.random.choice([3, 4, 5])
        self.capacity_requirement = num_regions * self.capacity_per_plant
        self.CO2_threshold = 16  # If there are 5 regions, the agent can take one wrong action

        num_fire_power_stations = self.random.choice(range(1, num_regions + 1))
        clean_power = [("solar farm", "sun"), ("wind farm", "wind"), ("hydroelectric power station", "water")]
        fire_power = ["fossil-fuel power station"] * num_fire_power_stations
        fire_power_resource = self.random.choices(["sun", "wind", "water"], k=num_fire_power_stations)
        fire_power = list(zip(fire_power, fire_power_resource))

        power_stations = fire_power + self.random.choices(clean_power, k=num_regions - num_fire_power_stations)
        self.random.shuffle(power_stations)

        for n, (station_name, resource) in enumerate(power_stations):
            region = Region(f"region {n}", resource)
            if (station_name == 'solar farm' and resource != 'sun') or \
                    (station_name == 'wind farm' and resource != 'wind') or \
                    (station_name == 'hydroelectric power station' and resource != 'water'):
                efficiency = 0.1
            else:
                efficiency = 1

            power_station = PowerPlant(station_name, efficiency, self.capacity_per_plant)
            region.addObject(power_station)
            world.addObject(region)

        return world

    def getTaskDescription(self):
        return ("Your task is to change all fossil-fuel power stations to use renewable "
                "energy while keeping the same capacity.")

    def generatePossibleActions(self):
        # Get a list of all game objects that could serve as arguments to actions
        allObjects = self.makeNameToObjectDict()

        # Make a dictionary whose keys are possible action strings, and whose values are lists that contain the arguments.
        self.possibleActions = {}

        # Zero-argument actions
        for action in ["look around", "look"]:
            self.addAction(action, [action])

        # Two-object actions (Change)
        for objReferent1, objs1 in allObjects.items():
            for power_station in ['solar farm', 'wind farm', 'hydroelectric power station', 'fossil-fuel power station']:
                for obj1 in objs1:
                    self.addAction("change " + objReferent1 + " to " + power_station, ["change", obj1, power_station])

        return self.possibleActions

    def actionChange(self, region, power_station):
        if power_station not in ['solar farm', 'wind farm', 'hydroelectric power station', 'fossil-fuel power station']:
            return "Unknown power station."
        elif not isinstance(region, Region):
            return f"{region.name} is not a region."
        else:
            if (power_station == 'solar farm' and region.properties['resource'] != 'sun') or \
                    (power_station == 'wind farm' and region.properties['resource'] != 'wind') or \
                    (power_station == 'hydroelectric power station' and region.properties['resource'] != 'water'):
                efficiency = 0.1
            else:
                efficiency = 1

            new_power_station = PowerPlant(power_station, efficiency, self.capacity_per_plant)
            region.contains[0] = new_power_station
            return f"{region.name} now has a {power_station}.".capitalize()

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
            "change": lambda: self.actionChange(action[1], action[2])
        }

        self.observationStr = action_map.get(actionVerb, lambda action: "ERROR: Unknown action.")()

        # Do one tick of the environment
        self.doWorldTick()

        # Calculate the score
        lastScore = self.score
        self.calculateScore()
        reward = self.score - lastScore

        return (self.observationStr, self.score, reward, self.gameOver, self.gameWon)

    def calculateScore(self):
        self.score = 0
        allObjects = self.rootObject.contains
        all_clean = True
        total_capacity = 0
        for obj in allObjects:
            power_plant = obj.contains[0]
            if power_plant.name == 'fossil-fuel power station':
                all_clean = False
                break
            capacity = power_plant.properties["running_efficiency"] * power_plant.properties["capacityKW"]
            total_capacity += capacity

        if all_clean and total_capacity >= self.capacity_requirement:
            self.score += 1
            self.gameOver, self.gameWon = True, True



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Execute a game command.")
    parser.add_argument("commands", help="The command to execute in the game")
    args = parser.parse_args()

    print("Command received")
    # Random seed
    randomSeed = 0
    # Create a new game
    game = CleanEnergyGame(randomSeed=randomSeed)
    main(game, args.commands)