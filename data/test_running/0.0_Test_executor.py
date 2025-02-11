import argparse
import subprocess

def get_commands(file_path: str):
    commands = []
    with open(file_path, "r") as file:
        for line in file:
            if line.startswith(">") and line[2:].strip():
                commands.append(line[2:].strip())
    return commands

def execute_commands(commands, script_name, status):
    # 将所有命令合并为一个字符串，并用换行符分隔
    commands_str = "\n".join(command.strip() for command in commands)
    print(f"--------------Executing combined command--------------\n{commands_str}")
    subprocess.run(["python", script_name, commands_str, status], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute commands from a playthrough file for a specified script.")
    parser.add_argument("game_name", help="The Python script to run (e.g., 'bath-tub-water-temperature.py').")
    parser.add_argument("status", default=0, help="Select the TextGame execution status(e.g., 0 or 1)")
    args = parser.parse_args()
    file_path = f"../playthroughs/{args.game_name}-playthrough.txt"
    # 从指定的文件路径加载命令
    commands = get_commands(file_path)
    # 执行指定的脚本并传入命令
    execute_commands(commands, args.game_name+".py", args.status)


# python 0.0_Test_executor.py bath-tub-water-temperature 1