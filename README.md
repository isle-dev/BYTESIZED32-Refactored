# Refactored_BYTESIZED32
Byte-sized text games for code generation tasks on virtual environments,and In this refactoring process, the aim was to optimize the code for a collection of 32 games with similar structures and mechanics. The key focus areas were modularity, readability, reusability, extensibility, and performance. Each game followed a common pattern with variations in game-specific rules, objects, and actions, which provided an excellent opportunity to abstract shared logic and create a reusable framework.
## Key Optimization Highlights

### 1. Modular Design
Before Refactoring:
Each game contained a large amount of duplicated code, including classes like `GameObject`, `Container`, and `TextGame`.
Game-specific logic was intertwined with shared logic, making it difficult to isolate reusable components.
After Refactoring:
 Shared Module (`GameBasic`): Abstracted common classes (`GameObject`, `Container`, `TextGame`, etc.) into a shared library, reducing redundancy.
Game-Specific Classes: Individual games inherit from `TextGame`, focusing only on game-specific logic such as tasks, objects, and scoring.
Benefits:
Code reuse across all games.
We simplified game-specific implementation.
Centralized management of core functionalities, reducing maintenance effort.

—
### 2. Streamlined Action Handling
Before Refactoring:
Actions like `look around`, `take`, `put`, and game-specific commands were handled using repetitive `if-elif` blocks, leading to bloated code.
After Refactoring:
Introduced a **dictionary-based `action_map`** to handle actions dynamically. Each action is mapped to a corresponding method or lambda function:
    ```python
    action_map = {
        "look around": self.rootObject.makeDescriptionStr,
        "inventory": self.actionInventory,
        "take": lambda: self.actionTake(action[1]),
        "put": lambda: self.actionPut(action[1], action[2]),
        "answer": lambda: self.actionAnswer(action[1])
    }
    ```
Benefits:
Eliminated redundant `if-elif` statements.
Easy to add or modify actions for individual games by updating the `action_map`.
Improved readability and reduced code complexity.

---

### 3. Recursive Logic Optimization
Before Refactoring:
Recursive operations, such as retrieving all contained objects or calculating masses, used explicit loops with redundant code.
After Refactoring:
Used **list comprehensions** and **combined recursive calls**:
    ```python
    def getAllContainedObjectsRecursive(self):
        return self.left.getAllContainedObjectsRecursive() + self.right.getAllContainedObjectsRecursive() + [self.left, self.right]
    ```

    ```python
    def get_mass(self, contains):
        return sum(obj.getProperty("weight") for obj in contains.contains)
    ```

Benefits:
Cleaner, more concise implementations.Improved efficiency and maintainability.

---

### 4. Enhanced Object Description
Before Refactoring:
Descriptions for containers and their contents relied on verbose string concatenations and nested loops.
After Refactoring:
Simplified descriptions with list comprehensions:
    ```python
    def makeOneSideDescription(contains):
        effectiveContents = [obj.makeDescriptionStr() for obj in contains.contains]
        if effectiveContents:
            return "contains " + ", ".join(effectiveContents[:-1]) + (
                ", and " if len(effectiveContents) > 1 else "") + effectiveContents[-1]
        return "is empty"
    ```

Benefits:
Reduced verbosity and improved readability.
Consistent and elegant handling of object descriptions across games.

---

### 5. Unified Game Logic
Before Refactoring:
Game-specific logic (e.g., tasks, scoring) was mixed into a single monolithic class, making it hard to isolate and extend.
After Refactoring:
Game Logic Isolation: Each game is implemented as a subclass of `TextGame`, with methods overridden for tasks, scoring, and object initialization.
    ```python
    class BalanceScaleWeighGame(TextGame):
        def getTaskDescription(self):
            return "Your task is to figure out the weight of the cube."
        def calculateScore(self):
            self.score = 1 if self.cube_weight == self.answer_mass else 0
            self.gameOver = True
            self.gameWon = self.score > 0
    ```

Benefits:
Clear separation of shared and game-specific responsibilities. Easier to implement new games with minimal duplication.



### 6. Extended Features
Before Refactoring:
Limited gameplay mechanics with predefined actions and rigid rules.
After Refactoring:
Added dynamic action generation based on game state:
Actions like `answer` (specific to certain games) can be dynamically included.
generatePossibleActions build action sets tailored to the game environment:
      ```python
      for i in range(1, self.max_mass + 1):
          self.addAction(f"answer {i}g", ["answer", i])
      ```
  - Expanded scoring and feedback logic, allowing for more interactive and engaging gameplay.

Benefits:
Increased flexibility to define unique game rules and mechanics.
Enhanced player experience with dynamic interactions.

—
### 7. Centralized Testing and Execution
Before Refactoring:
Each game had its own main loop, often with duplicate logic for handling input, generating actions, and updating states.
After Refactoring:
Unified the main game loop in the shared `TextGame` class.
Games are instantiated and executed using the same `main(game)` function.
Benefits:
Standardized game execution. Simplified testing across multiple games.

---

### **Overall Impact**

| **Aspect**            | **Before Refactoring**                           | **After Refactoring**                            | **Improvement**                                                          |
|------------------------|-------------------------------------------------|-------------------------------------------------|--------------------------------------------------------------------------|
| **Modularity**         | Monolithic scripts with duplicated logic        | Shared modules with reusable components         | Easier to manage, reuse, and extend functionalities.                     |
| **Readability**        | Verbose and repetitive logic                    | Streamlined with comprehensions and mappings    | Improved clarity and reduced cognitive load for developers.              |
| **Extensibility**      | Hard to add new features or games               | Game-specific logic isolated in subclasses      | New games or features require minimal effort to implement.               |
| **Performance**        | Explicit loops and redundant operations         | Optimized recursive calls and calculations      | Improved efficiency for recursive and state-dependent operations.        |
| **Action Handling**    | Repetitive `if-elif` structures                 | Dynamic action mapping                          | Reduced boilerplate and easier action management.                        |
| **Testing and Execution**| Separate, inconsistent main loops              | Unified main execution function                 | Standardized testing and execution across all games.                     |

The refactoring effort successfully optimized the framework for 32 similar games by focusing on modularity, reusability, and maintainability. Key achievements include:
- A **reusable core library** that supports future game development.
- Simplified and extensible game-specific implementations.
- Improved performance and developer experience.
This approach significantly reduces technical debt, making the codebase more adaptable for evolving project needs. The same framework can now efficiently support additional games with minimal effort, ensuring scalability and consistency across the board.
---
## Intro to main code
### 1.library-GameBasic.py
This code is a general-purpose text-based game engine framework designed to provide a foundation for creating text adventure games. Using abstract classes and object-oriented programming, the framework modularly implements game objects' fundamental behaviors and logic (e.g., items, containers, devices). Developers can extend the framework to build specific game scenarios and logic.
Modules and Functionalities
#### 1. GameObject (Base Game Object)
- **Description**: GameObject is the abstract base class for all game objects, defining fundamental attributes and operational logic such as container relationships, movability, and recursive object management.
- **Key Features:**
Dynamic property management, e.g., isMoveable (movable), temperature (temperature), etc.
Container relationship management, supporting object addition, removal, and recursive traversal.
Provides a mapping between object names and references, facilitating player interactions.
#### 2. Container (Container)
- **Description:**
Inherits from GameObject and represents objects that can contain other items (e.g., drawers, boxes, tables).
- **Key Features:**
Supports container opening and closing operations.
Implements logic for storing and retrieving items, including validating the target container's availability and state.
#### 3. Device (Device)
- **Description:**
Inherits from GameObject and represents devices that can be activated or deactivated (e.g., lights, fans).
- **Key Features:**
Provides operations for turning devices on (turnOn) and off (turnOff).
Supports an interface for interacting with other objects.
#### 4. Substance (Substance)
- **Description:**
Defines substances with physical properties (e.g., melting point, boiling point) and dynamically adjusts their states (solid, liquid, or gas) based on temperature.
- **Key Features:**
Automatically switches the substance's physical state based on its temperature.
Provides descriptive information about the current state.
#### 5. World (World)
- **Description:**
Inherits from Container and represents the game scene or environment, serving as the root container for all game objects.
- **Key Features:**
Manages all objects within the scene and their states.
Generates natural language descriptions of the current scene.
#### 6. Agent (Agent)
- **Description:**
Represents the player’s in-game proxy, responsible for managing the player’s items (e.g., inventory).
- **Key Features:**
Implements logic for managing player items.
Provides readable descriptions of player items.
#### 7. TextGame (Text Game Logic)
- **Description:**
Provides a general game logic framework, including world initialization, action registration, score calculation, and player interaction.
- **Key Features:**
Defines abstract methods like initializeWorld() and getTaskDescription() for specific game logic implementation.
Supports parsing and executing player actions, such as picking up and placing items.
Manages game states, including game over and victory conditions.

### 2. Test_running-0.0_Test_executor.py

This code serves as a universal command executor designed to run specified game scripts via the command line and execute corresponding game commands. It loads commands from predefined text files, passes them to the game script, and simulates player input. This simplifies testing processes and is suitable for batch execution and debugging of text-based adventure games.

---

#### Code Structure and Functionality

##### 1. `get_commands` Function
- **Purpose**: 
  - Loads commands from a specified file path.
- **Explanation**: 
  - Reads a command file located in the `playthroughs` directory (e.g., `bath-tub-water-temperature-playthrough.txt`) using the `get_commands` function from the `command_runner` module and returns a list of commands.


##### 2. `execute_commands` Function
- **Purpose**: 
  - Combines a list of commands into a single string and executes them using `subprocess`.
- **Explanation**: 
  - Runs the specified game script (e.g., `bath-tub-water-temperature.py`) with the combined commands passed as arguments via `subprocess.run`.


##### 3. Command-Line Argument Parsing
- **Uses `argparse` to parse command-line arguments**:
  - `game_name`: Specifies the name of the game script to be executed (e.g., `bath-tub-water-temperature`).
  - Automatically locates the corresponding command file (`../playthroughs/{game_name}-playthrough.txt`) and loads the commands.


#### Execution Flow

##### Input
- The user specifies the name of the game script via the command line.

##### Processing
1. The code locates the command file corresponding to the specified game.
2. It loads the commands from the file using `get_commands`.
3. It invokes `execute_commands` to combine and execute the commands via `subprocess`.

##### Output
- Displays the executed commands.
- Runs the specified game script, simulating player interactions.


#### Usage Example

- **Assuming the game script is `bath-tub-water-temperature.py` and the corresponding command file is `bath-tub-water-temperature-playthrough.txt`**:
  - **Command**:
    ```bash
    python 0.0_Test_executor.py bath-tub-water-temperature
    ```
  - **Execution**:
    1. Loads commands from `../playthroughs/bath-tub-water-temperature-playthrough.txt`.
    2. Executes `bath-tub-water-temperature.py` with the loaded commands.

---

#### Code Logic Summary

##### 1. Modular Design
- The `get_commands` function abstracts command-loading logic, enhancing reusability.
- The `execute_commands` function encapsulates execution logic, improving code readability and maintainability.

---

##### 2. Flexibility and Extensibility
- Command-line argument parsing supports testing and running different game scripts.
- Automatically maps game scripts to their corresponding command files, reducing manual effort.

---

##### 3. Ease of Debugging
- Prints detailed information about executed commands for easier debugging.
- Uses `subprocess.run` to ensure safe and reliable command execution.

---

##### 4. Adaptability
- Supports cross-platform execution as long as the Python environment and file paths are correctly configured.
### 3.Test_running-command_runner.py
The main function of this code is to extract valid game commands from a specified `playthrough` file and return them as a list. By parsing the file content, it filters out commands that start with `>` and prepares them for batch testing or game debugging.

---

#### Code Structure and Functionality

1. **`get_commands` Function**  
   - **Purpose**:  
     Load commands from a specified file path and filter valid command lines.
   - **Logic**:  
     - Opens the file at the specified path and reads it line by line.
     - Extracts lines starting with `>`, removing the `>` symbol and surrounding whitespace.
     - Stores the filtered commands in a list and returns them.

   **Example Input File**:
   ```text
   > take apple
   > put apple in basket
   look around
   ```
   **Output**:
   ```python
   ["take apple", "put apple in basket"]
   ```

2. **Command-Line Execution**  
   - **Purpose**:  
     Allows specifying the file path from the command line to load commands.
   - **Logic**:  
     - Uses `argparse` to accept the `file_path` parameter from the command line.
     - Calls the `get_commands` function to read commands from the specified file path.
     - Prints the loaded commands (for debugging purposes).

3. **Usage**  
   Run the following command to load a command file:  
   ```bash
   python command_runner.py ../playthroughs/bath-tub-water-temperature-playthrough.txt
   ```
   **Example Output**:  
   ```
   Loaded commands: ['take apple', 'put apple in basket']
   ```

---

#### Code Logic Summary

1. **Simplicity and Efficiency**  
   - Encapsulates the command extraction logic into a single function for reusability.
   - Filters valid commands to ensure correct input format.

2. **High Extensibility**  
   - Can be used for different game test scripts by specifying various command file paths.
   - The `get_commands` function can be integrated into more complex execution frameworks.

3. **Debugging-Friendly**  
   - Prints the loaded commands to verify the correctness of the command extraction process.

This utility provides a reliable and reusable method for extracting game commands, simplifying the workflow for text-based game testing and debugging.

## How to run this code?
## Demo Video
[![How to run this code?](https://img.youtu.be/MHR61h1qEzs/0.jpg)](https://youtu.be/MHR61h1qEzs)


## **Instructions for Running the Test**

Below are detailed instructions on how to use `Test_running-0.0_Test_executor.py` to run tests and switch between different games.

---

### **Step 1: Open the Test File**
1. Locate the `Test_running-0.0_Test_executor.py` file in your project directory.
2. Confirm that the file exists and is accessible, or right-click the file to find its relative path.

---

### **Step 2: Navigate to the File Directory**
1. Open a terminal.
2. Enter the following command to navigate to the directory containing the test file:
   ```bash
   cd <test_running_file_relative_path>
   ```
   Replace `<test_running_file_relative_path>` with the relative path of `Test_running-0.0_Test_executor.py`.

---

### **Step 3: Run the Test File**
1. To execute the test file and launch a specific game, use the following command:
   ```bash
   python 0.0_Test_executor.py balance-scale-heaviest
   ```
   - `balance-scale-heaviest` is the name of the game. You can replace it with the name of another game to run a different one.
   - Example game names can be found in the `../playthroughs` folder, such as:
     - `bath-tub-water-temperature`
     - `cube-weight-guess`

2. Press **Enter**, and the game will start. The program will load the corresponding command file and execute the game logic.

---

### **Step 4: Switch Between Games**
1. To run another game, repeat Step 3 and replace the game name with a new one. For example:
   ```bash
   python 0.0_Test_executor.py bath-tub-water-temperature
   ```

2. Each time you run a new game, the program will load the respective commands and simulate the game process.

---

### **Usage Example**

Here is an example of running multiple games:

1. Navigate to the test file directory:
   ```bash
   cd /path/to/test/running/directory
   ```

2. Run the first game (e.g., `balance-scale-heaviest`):
   ```bash
   python 0.0_Test_executor.py balance-scale-heaviest
   ```

3. Switch and run the next game (e.g., `bath-tub-water-temperature`):
   ```bash
   python 0.0_Test_executor.py bath-tub-water-temperature
   ```

---

### **Important Notes**
1. Ensure Python is installed on your system and the `python` command works in your terminal.
2. Verify that the `Test_running-0.0_Test_executor.py` file path is correct and that all dependent command files exist in the `../playthroughs` directory.
3. To avoid path errors, consider right-clicking and copying the relative path to the file.
4. The game name must match the command file name in the `playthroughs` folder; otherwise, the program will fail to load the game.

---

By following these steps, you can efficiently run specific games and switch between different test games to validate the logic or enjoy the game content!



