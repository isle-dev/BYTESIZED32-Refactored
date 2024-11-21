import argparse
import subprocess
from command_runner import get_commands  #  Import the function that gets the command
#
# The playthroughs command is uploaded to the game files and runs directly in Terminal
# start to train
def execute_commands(commands, script_name):
    # Combine all commands into a single string, separated by a newline
    commands_str = "\n".join(command.strip() for command in commands)
    print(f"--------------Executing combined command--------------\n{commands_str}")
    subprocess.run(["python", script_name, commands_str], check=True)
#  Enter the game name directly
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute commands from a playthrough file for a specified script.")
    parser.add_argument("game_name", help="The Python script to run (e.g., 'bath-tub-water-temperature.py').")
#
    # Add control parameters, python is used for command line control running, as path becomes more and more numerous
    args = parser.parse_args()
    file_path = f"../playthroughs/{args.game_name}-playthrough.txt"
    #  Load the command from the specified file path
    commands = get_commands(file_path)
    #  Execute the specified script and pass the command Execute the specified script and pass the command
    execute_commands(commands, args.game_name+".py")


# python 0.0_Test_executor.py balance-scale-heaviest