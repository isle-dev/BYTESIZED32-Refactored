import os
import re
import json
import time
import shutil
import argparse
import traceback
import signal
import multiprocessing
from contextlib import contextmanager
from multiprocessing import Pool, Lock

from glob import glob
from os.path import join as pjoin

from tqdm import tqdm
from termcolor import colored
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bytes32 import check_winnability
from bytes32 import check_compliance
from bytes32 import check_alignment
from bytes32 import check_validity
from bytes32.utils import stream_llm_gpt, count_tokens, extract_python_code, get_empty_metrics


class TimeoutError(Exception):
    """Custom exception for timeout handling"""
    pass


@contextmanager
def timeout_handler(seconds):
    """Context manager for handling timeouts"""
    def timeout_signal_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Set the signal handler and alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_signal_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Reset the alarm and handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def automatic_evaluation(gamefile, args):
    """ Automatically evaluate one game """

    metrics = get_empty_metrics()

    # Compare new code with the one from the previous iteration.
    # Find the lastest code revision.
    version = int(re.search(r"_v(\d+)\.py", gamefile).group(1))
    if version > 0:
        old_gamefile = gamefile.replace(f"v{version}.py", f"v{version-1}.py")

        with open(old_gamefile) as f:
            old_code = f.read()

        with open(gamefile) as f:
            new_code = f.read()

        if new_code == old_code:
            metrics["validity"]["error_msg"] = "STOP: Code is the same as previous iteration."
            return metrics

        if len(new_code) / len(old_code) < 0.5:
            metrics["validity"]["error_msg"] = "STOP: Code has 50% less lines than previous iteration."
            return metrics

    # Run validity check with timeout
    print(colored("Running validity check...", "yellow"))
    try:
        with timeout_handler(args.validity_timeout):
            metrics["validity"] = check_validity(gamefile, args)
    except TimeoutError as e:
        print(colored(f"Validity check timed out: {e}", "red"))
        metrics["validity"]["error_msg"] = f"TIMEOUT: Validity check exceeded {args.validity_timeout} seconds. This likely indicates an infinite loop or extremely long-running operation."
        metrics["validity"]["runnable"] = False
        return metrics
    
    if metrics["validity"]["error_msg"]:
        return metrics

    # Run GPT evaluation for compliance.
    if args.reflect_compliance:
        metrics["compliance"] = check_compliance(gamefile, args)
        if not metrics["compliance"]["passed"]:
            return metrics

    # Run GPT evaluation for alignment.
    if args.reflect_alignment:
        metrics["alignment"] = check_alignment(gamefile, args)
        if not metrics["alignment"]["aligned"]:
            return metrics

    # Run GPT agent for winnability.
    if args.reflect_winnability:
        try:
            print(colored("Running winnability check...", "yellow"))
            metrics["winnability"] = check_winnability(gamefile, args.agent_model_name, args.game_random_seed, args.env_step_limit)
        except Exception as e:
            stacktrace = [frame.replace(os.getcwd(), "").strip() for frame in traceback.format_tb(e.__traceback__) if gamefile in frame or "language_agent.py" in frame]
            metrics["validity"]["error_msg"] = "\n".join(stacktrace) + "\n" + str(e)

    return metrics


def reflect(gamefile, metrics, args):
    with open(gamefile, 'r') as f:
        generated_game = f.read()

        if args.strip_comments:
            # Remove Python comments from generated_game.
            generated_game = re.sub(r'#[^\n]*', '', generated_game)

    # 'DeveloperGPT' prompt from @skirano
    prompt = "You are DeveloperGPT, the most advanced AI developer tool on the planet.  You answer any coding question, and provide real useful example code using code blocks.  Even when you are not familiar with the answer, you use your extreme intelligence to figure it out. \n"

    prompt += "Your task is to correct a buggy program that represents a text-based simulation.\n"

    if args.reflect_with_reference_game:
        # Load reference game
        reference_name = os.path.basename(gamefile).rsplit("_", 1)[0] + ".py"
        with open(pjoin(args.game_folder, "..", "gold-games", "program", reference_name)) as f:
            reference_game = f.read()

        if args.strip_comments:
            # Remove Python comments from reference_game.
            reference_game = re.sub(r'#[^\n]*', '', reference_game)

        prompt += "Here is the example code the buggy program was based on \n"
        prompt += "```"
        prompt += reference_game
        prompt += "```\n"

    prompt += "Here is the code of the buggy program \n"
    prompt += "```"
    prompt += generated_game
    prompt += "```\n"

    if metrics["validity"]["error_msg"] and metrics["winnability"]["transcript"]:
        prompt_ = "Here is the error message from a Python interpretor\n."
        prompt_ += metrics["validity"]["error_msg"]
        prompt_ += "\n"
        prompt_ += "Here's the transcript of someone playing the game when that error happened:\n"
        prompt_ += "```"
        prompt_ += metrics["winnability"]["transcript"]
        prompt_ += "```\n"
        prompt_ += "Based on this transcript and the Python error raised while playing the game, identify the problems and fix the code accordingly.\n"
    elif metrics["validity"]["error_msg"]:
        prompt_ = "Here is the error message from a Python interpretor.\n"
        prompt_ += metrics["validity"]["error_msg"]
        prompt_ += "\n"
    elif args.reflect_compliance and not metrics["compliance"]["passed"] and metrics["compliance"]["response_msg"]:
        prompt_ = f"While there were no errors from the Python interpretor, the game misses a required {metrics['compliance']['experiment']}. Here's the evaluation comments of the game:\n"
        prompt_ += "```"
        prompt_ += metrics["compliance"]["response_msg"]
        prompt_ += "```\n"
        prompt_ += "Based on this comments, identify the problems and fix the code accordingly.\n"
    elif args.reflect_alignment and not metrics["alignment"]["aligned"] and metrics["alignment"]["response_msg"]:
        prompt_ = f"While there were no errors from the Python interpretor, the game does not correctly model the physical world. Here's the evaluation comments of the game:\n"
        prompt_ += "```"
        prompt_ += metrics["alignment"]["response_msg"]
        prompt_ += "```\n"
        prompt_ += "Based on this comments, identify the problems and fix the code accordingly.\n"
    elif args.reflect_winnability and metrics["winnability"]["gpt_bug"]:
        prompt_ = "While there were no errors from the Python interpretor, the game was not working as intended. Here's the transcript of the broken game:\n"
        prompt_ += "```"
        prompt_ += metrics["winnability"]["transcript"]
        prompt_ += "```\n"
        prompt_ += "Based on this transcript, identify the problems and fix the code accordingly.\n"
    elif args.reflect_winnability and metrics["winnability"]["gpt_done"] and not metrics["winnability"]["done"]:
        prompt_ = "While there were no errors from the Python interpretor, the game couldn't be completed as expected. Here's the transcript of the broken game:\n"
        prompt_ += "```"
        prompt_ += metrics["winnability"]["transcript"]
        prompt_ += "```\n"
        prompt_ += "Based on this transcript, identify the problems and fix the code accordingly.\n"
    elif args.reflect_winnability and metrics["winnability"]["step"] >= metrics["winnability"]["max_steps"]:
        prompt_ = f"While there were no errors from the Python interpretor, the game couldn't be completed as expected within {args.env_step_limit*2} steps. Here's the transcript of the broken game:\n"
        prompt_ += "```"
        prompt_ += metrics["winnability"]["transcript"]
        prompt_ += "```\n"
        prompt_ += "Based on this transcript, identify the problems and fix the code accordingly.\n"
    else:
        # No reflection criteria met - skip this game
        print(colored(f"No reflection criteria met for this game. Skipping reflection.", "yellow"))
        return None, "", ""

    print(colored(prompt_, "cyan"))
    prompt += prompt_

    prompt += "You must provide the *full working code* that includes the fix. Do not respond with partial code or say anything else."

    print(colored(f"Prompting {args.reflect_model_name} for reflection...", "yellow"))
    response = stream_llm_gpt(prompt, model=args.reflect_model_name)
    print(colored(f"Responded with {count_tokens(response)} tokens.", "yellow"))
    generated_game = extract_python_code(response)

    return generated_game, prompt, response


def find_latest_revision(source, args):
    game_name = os.path.basename(source)[:-3]

    # Find the lastest code revision.
    for i in range(args.max_reflection_steps + 1)[::-1]:
        gamefile = pjoin(args.revision_folder, f"{game_name}_v{i}.py")
        if os.path.exists(gamefile):
            return i, gamefile

    return 0, source


def stop_reflection(metrics, args):
    if metrics["validity"]["error_msg"].startswith("STOP:"):
        return True

    return (
        # The game has no error and is runnable, and the GPT agent has finished the game without reporting a bug.
        metrics["validity"]["error_msg"] == "" and
        metrics["validity"]["runnable"] and
        (not args.reflect_compliance or metrics["compliance"]["passed"]) and
        (not args.reflect_winnability or not metrics["winnability"]["gpt_bug"]) and
        (not args.reflect_winnability or metrics["winnability"]["done"])
    )


def perform_code_reflection(source, args):
    game_name = os.path.basename(source)[:-3]
    last_revision, gamefile = find_latest_revision(source, args)
    if last_revision == 0:
        gamefile = pjoin(args.revision_folder, f"{game_name}_v0.py")
        shutil.copyfile(source, gamefile)

    # Add overall timeout for the entire reflection process per game
    try:
        with timeout_handler(args.game_timeout):
            metrics = automatic_evaluation(gamefile, args)
            yield gamefile, {"metrics": metrics, "reflection_prompt": "", "reflection_response": ""}

            # Prompt GPT for code revision until automatic evaluation yields success or we reach max reflection steps.
            for i in range(last_revision, args.max_reflection_steps):
                if stop_reflection(metrics, args):
                    # The new code is the same as the old code, or has 50% less lines of code.
                    # The game has no error and is runnable, and the GPT agent has finished the game without reporting a bug.
                    break

                reflection_game, reflection_prompt, reflection_response = reflect(gamefile, metrics, args)

                if reflection_game is None:
                    # No reflection criteria met, skip this iteration
                    break

                gamefile = pjoin(args.revision_folder, f"{game_name}_v{i+1}.py")
                with open(gamefile, 'w') as f:
                    f.write(reflection_game)

                metrics = automatic_evaluation(gamefile, args)
                yield gamefile, {"metrics": metrics, "reflection_prompt": reflection_prompt, "reflection_response": reflection_response}
    
    except TimeoutError as e:
        print(colored(f"Game reflection timed out for {game_name}: {e}", "red"))
        # Return the original code as final output when reflection fails due to timeout
        final_gamefile = pjoin(args.revision_folder, f"{game_name}_timeout_fallback.py")
        shutil.copyfile(source, final_gamefile)
        
        timeout_metrics = get_empty_metrics()
        timeout_metrics["validity"]["error_msg"] = f"TIMEOUT: Entire reflection process exceeded {args.game_timeout} seconds. Returning original code."
        timeout_metrics["validity"]["runnable"] = False
        
        yield final_gamefile, {
            "metrics": timeout_metrics, 
            "reflection_prompt": "", 
            "reflection_response": f"Process timed out after {args.game_timeout} seconds. Original code returned as fallback."
        }


def parse_args():
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--game-folder")
    group.add_argument("--games", nargs="+")

    parser.add_argument("--results-file", default="results.json")
    parser.add_argument("--revision-folder", default="revised_games/",
                        help="Where to save the revised games. Default: %(default)s")
    parser.add_argument("--final-folder", default="final_games/",
                        help="Where to save the final revised games. Default: %(default)s")
    parser.add_argument("--num-workers", type=int, default=1,
                        help="Number of parallel worker processes. Default: %(default)s")

    parser.add_argument("--reflect-model-name", default="gpt-4-32k")
    parser.add_argument("--max-reflection-steps", type=int, default=3)
    parser.add_argument("--game-timeout", type=int, default=2700,
                        help="Timeout in seconds for each game reflection process (default: 2700 = 45 minutes)")
    parser.add_argument("--validity-timeout", type=int, default=1800,
                        help="Timeout in seconds for validity check per iteration (default: 1800 = 30 minutes)")
    parser.add_argument("--strip-comments", action="store_true",
                        help="Remove Python comments from generated_game to save context space.")
    parser.add_argument("--reflect-with-reference-game", action="store_true",
                        help="Also, provide the original reference game during reflection (NB: requires very large context size).")

    parser.add_argument("--reflect-alignment", action="store_true",
                        help="Also, reflect on physical reality alignment.")
    parser.add_argument("--reflect-compliance", action="store_true",
                        help="Also, reflect on specification compliance.")
    parser.add_argument("--reflect-winnability", action="store_true",
                        help="Also, reflect on game winnability.")

    validity_group = parser.add_argument_group("Technical Validity")
    validity_group.add_argument("--max-steps", type=int, default=3)
    validity_group.add_argument("--random-seed", type=int, default=0)
    validity_group.add_argument("--max-num-actions", type=int, default=100)

    compliance_group = parser.add_argument_group("Specification Compliance")
    compliance_group.add_argument("--compliance-model-name", default="gpt-4")
    compliance_group.add_argument("--evaluation-form", type=str, default="data/test_eval.csv")
    compliance_group.add_argument("--test-prompt-input-folder", type=str, default="data/test_prompts")
    compliance_group.add_argument("--compliance-majority-vote", type=int, default=31)

    alignment_group = parser.add_argument_group("Physical Reality Alignment")
    alignment_group.add_argument("--alignment-model-name", default="gpt-4")
    alignment_group.add_argument("--shuffle-random-seed", type=int, default=0)
    alignment_group.add_argument("--max-depth", type=int, default=2)
    alignment_group.add_argument("--max-paths", type=int, default=25000)
    alignment_group.add_argument("--error-strategy", type=str, default="fail")
    alignment_group.add_argument("--num-samples-per-game", type=int, default=100)
    alignment_group.add_argument("--sample-strategy", type=str, default="action_even")
    alignment_group.add_argument("--alignment-batch-size", type=int, default=1)

    winnability_group = parser.add_argument_group("Game Winnability")
    winnability_group.add_argument("--agent-model-name", default="gpt-4")
    winnability_group.add_argument("--env-step-limit", type=int, default=30)
    winnability_group.add_argument("--game-random-seed", type=int, default=20230614)

    args = parser.parse_args()
    return args


def process_single_game(gamefile_and_args):
    """Process a single game file - designed to be used with multiprocessing"""
    gamefile, args = gamefile_and_args
    
    try:
        game_results = {}
        
        latest_revision, revised_gamefile = find_latest_revision(gamefile, args)
        if latest_revision >= args.max_reflection_steps:
            return None  # Skip this game
        
        # Check if already processed and completed
        if os.path.exists(args.results_file):
            try:
                with open(args.results_file) as f:
                    existing_results = json.load(f)
                    if os.path.basename(revised_gamefile) in existing_results:
                        if stop_reflection(existing_results[os.path.basename(revised_gamefile)]["metrics"], args):
                            return None  # Skip this game
            except (json.JSONDecodeError, IOError):
                # If we can't read the file, proceed with processing
                pass
        
        # Process the game
        final_revised_gamefile = None
        for revised_gamefile, stats in perform_code_reflection(gamefile, args):
            game_results[os.path.basename(revised_gamefile)] = stats
            final_revised_gamefile = revised_gamefile
        
        # Copy the final revised game to a separate folder
        if final_revised_gamefile:
            final_gamefile = pjoin(args.final_folder, os.path.basename(final_revised_gamefile).replace(".py", "_final.py"))
            shutil.copyfile(final_revised_gamefile, final_gamefile)
        
        return game_results
        
    except Exception as e:
        # Log the error and return error results
        print(colored(f"Error processing {os.path.basename(gamefile)}: {e}", "red"))
        traceback.print_exc()
        
        # Record the error in results
        game_name = os.path.basename(gamefile)[:-3]
        error_gamefile = f"{game_name}_error.py"
        error_results = {
            error_gamefile: {
                "metrics": {
                    "validity": {
                        "error_msg": f"ERROR: Exception during processing: {str(e)}",
                        "runnable": False
                    }
                },
                "reflection_prompt": "",
                "reflection_response": f"Processing failed with exception: {str(e)}"
            }
        }
        
        return error_results


def update_results_file_safe(results_file, new_results):
    """Safely update the results file with new results using file locking"""
    if not new_results:
        return
    
    # Use a lock file to prevent race conditions
    lock_file = f"{results_file}.lock"
    
    # Simple file-based locking mechanism
    max_wait_time = 30  # Maximum wait time in seconds
    wait_time = 0
    while os.path.exists(lock_file) and wait_time < max_wait_time:
        time.sleep(0.1)
        wait_time += 0.1
    
    # If we couldn't get the lock, try anyway but with a warning
    if os.path.exists(lock_file):
        print(colored(f"Warning: Couldn't acquire lock for {results_file}, proceeding anyway", "yellow"))
    
    try:
        # Create lock
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        
        # Read existing results
        reflection_results = {}
        if os.path.exists(results_file):
            try:
                with open(results_file) as f:
                    reflection_results = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(colored(f"Warning: Could not read existing results file: {e}", "yellow"))
                reflection_results = {}
        
        # Update with new results
        reflection_results.update(new_results)
        
        # Write back to file atomically
        temp_file = f"{results_file}.tmp"
        with open(temp_file, 'w') as f:
            json.dump(reflection_results, f, indent=2, sort_keys=True)
        
        # Atomic move (as atomic as possible on the filesystem)
        shutil.move(temp_file, results_file)
            
    except Exception as e:
        print(colored(f"Error updating results file: {e}", "red"))
        # Clean up temp file if it exists
        temp_file = f"{results_file}.tmp"
        if os.path.exists(temp_file):
            os.remove(temp_file)
    finally:
        # Remove lock
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
            except OSError:
                pass  # Lock file might have been removed by another process


def main():
    args = parse_args()

    # Create a folder to store revised and final games.
    os.makedirs(args.revision_folder, exist_ok=True)
    os.makedirs(args.final_folder, exist_ok=True)

    reflection_results = {}
    if os.path.exists(args.results_file):
        input(colored(f"WARNING: {args.results_file} already exists, data will be appended to it.\nPress Enter to continue...", "red", attrs={'bold': True}))
        with open(args.results_file) as f:
            reflection_results = json.load(f)

    gamefiles = args.games or glob(pjoin(args.game_folder, "*.py"))
    
    if args.num_workers == 1:
        # Sequential processing (original behavior)
        pbar = tqdm(sorted(gamefiles))
        for gamefile in pbar:
            time.sleep(0.1)
            pbar.set_description(os.path.basename(gamefile))

            try:
                latest_revision, revised_gamefile = find_latest_revision(gamefile, args)
                if latest_revision >= args.max_reflection_steps:
                    continue

                if os.path.basename(revised_gamefile) in reflection_results:
                    if stop_reflection(reflection_results[os.path.basename(revised_gamefile)]["metrics"], args):
                        # The new code is the same as the old code, or has 50% less lines of code.
                        # The game has no error and is runnable, and the GPT agent has finished the game without reporting a bug.
                        continue

                for revised_gamefile, stats in perform_code_reflection(gamefile, args):
                    reflection_results[os.path.basename(revised_gamefile)] = stats
                    with open(args.results_file, 'w') as f:
                        json.dump(reflection_results, f, indent=2, sort_keys=True)

                # Copy the final revised game to a separate folder.
                final_gamefile = pjoin(args.final_folder, os.path.basename(revised_gamefile).replace(".py", "_final.py"))
                shutil.copyfile(revised_gamefile, final_gamefile)
                
            except Exception as e:
                # Log the error and continue with the next game
                print(colored(f"Error processing {os.path.basename(gamefile)}: {e}", "red"))
                traceback.print_exc()
                
                # Record the error in results
                game_name = os.path.basename(gamefile)[:-3]
                error_gamefile = f"{game_name}_error.py"
                reflection_results[error_gamefile] = {
                    "metrics": {
                        "validity": {
                            "error_msg": f"ERROR: Exception during processing: {str(e)}",
                            "runnable": False
                        }
                    },
                    "reflection_prompt": "",
                    "reflection_response": f"Processing failed with exception: {str(e)}"
                }
                
                # Save results even when there's an error
                with open(args.results_file, 'w') as f:
                    json.dump(reflection_results, f, indent=2, sort_keys=True)
                    
                continue
    else:
        # Parallel processing
        print(colored(f"Using {args.num_workers} worker processes for parallel processing", "green"))
        
        # Prepare arguments for each game (sorted to maintain deterministic order)
        sorted_gamefiles = sorted(gamefiles)
        game_args = [(gamefile, args) for gamefile in sorted_gamefiles]
        
        # Use multiprocessing Pool
        with Pool(processes=args.num_workers) as pool:
            # Use imap for progress tracking while preserving order
            pbar = tqdm(total=len(game_args))
            pbar.set_description("Processing games in parallel")
            
            # Process results in order to maintain deterministic output
            for result in pool.imap(process_single_game, game_args):
                pbar.update(1)
                if result:
                    # Update results file safely
                    update_results_file_safe(args.results_file, result)
            
            pbar.close()


if __name__ == "__main__":
    # This is important for multiprocessing on Windows and some Unix systems
    multiprocessing.set_start_method('spawn', force=True) if hasattr(multiprocessing, 'set_start_method') else None
    main()
