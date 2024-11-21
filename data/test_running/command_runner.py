import argparse

# 用于提取playthroughs命令，引用这个函数，
def get_commands(file_path: str):
    commands = []
    with open(file_path, "r") as file:
        for line in file:
            if line.startswith(">") and line[2:].strip():
                commands.append(line[2:].strip())
    return commands

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load commands from a specified playthrough file.")
    parser.add_argument("file_path", help="The path to the playthrough file")
    args = parser.parse_args()

    commands = get_commands(args.file_path)
    print("Loaded commands:", commands)  # 可以用于调试，确认是否正确加载命令
