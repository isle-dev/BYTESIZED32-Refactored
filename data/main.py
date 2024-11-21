import games.balance_scale_heaviest as game_heaviest
import games.balance_scale_weigh as game_weigh

def run_game(game_module):
    # Random seed
    randomSeed = 0

    # Create a new game instance from the chosen game module
    game_instance = game_module.TextGame(randomSeed=randomSeed)

    # Get a list of valid actions
    possibleActions = game_instance.generatePossibleActions()
    print("Task Description: " + game_instance.getTaskDescription())
    print("")
    print("Initial Observation: " + game_instance.observationStr)
    print("")

    # Main game loop
    while not game_instance.gameOver:
        # Get the player's action
        actionStr = input("> ")
        if actionStr in ["exit", "quit"]:
            return
        if actionStr == "help":
            print("Possible actions: " + str(possibleActions.keys()))
            continue

        # Perform the action
        observationStr, score, reward, gameOver, gameWon = game_instance.step(actionStr)
        possibleActions = game_instance.generatePossibleActions()

        # Print the current game state
        print(f"Observation: {observationStr}\nScore: {score}\nGame Over: {gameOver}\nGame Won: {gameWon}\n")

def main():
    while True:
        print("Choose a game to play:")
        print("1. Balance Scale - Heaviest")
        print("2. Balance Scale - Weigh")
        print("3. Exit")

        choice = input("Enter the number of the game you want to play: ")

        if choice == "1":
            print("Starting Balance Scale - Heaviest game...")
            run_game(game_heaviest)  # 运行第一个游戏
        elif choice == "2":
            print("Starting Balance Scale - Weigh game...")
            run_game(game_weigh)  # 运行第二个游戏
        elif choice == "3":
            print("Exiting the program.")
            break
        else:
            print("Invalid choice, please select a valid option.")

if __name__ == "__main__":
    main()