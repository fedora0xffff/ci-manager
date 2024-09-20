#!/usr/bin/env python3

import subprocess
import sys
import json
import os

"""
This is a testing script for the se-wrapper util. This script uses a predefined 
set of command line options to track the build stability. 

Usage
1. no cmd-line params: run all test scenarios and output results
2. ./tester.py valgrind: run all test scenarios under Valgrind, 
output tests results and save valgrind logs to valdrind_logs/
3. ./tester.py valgrind/none test_case: run a specified test case
4. ./tester.py valgrind/none <app_path=path> <testElf=path> <testNonElf=path> <extraElf=path>: 
substitute default test params
"""

def print_status(text, level=""):
    colors = {
        "red" : Fore.RED,
        "green" : Fore.GREEN,
        "yellow" : Fore.YELLOW,
        "cyan" : Fore.CYAN,
    }
    if level == "info":
        color = colors.get("green", Fore.RESET)
        print(f"{color}[INFO]: {text}{Style.RESET_ALL}")
    elif level == "warn":
        color = colors.get("yellow", Fore.RESET)
        print(f"{color}[WARNING]: {text}{Style.RESET_ALL}")
    elif level == "error":
        color = colors.get("red", Fore.RESET)
        print(f"{color}[ERROR]: {text}{Style.RESET_ALL}")
    else:
        color = colors.get("cyan", Fore.RESET)
        print(f"{color}[STATUS]: {text}{Style.RESET_ALL}")


def composeCommand(prefix, command):
    temp = [prefix, command]
    return ' '.join(temp)


def launchTests(command_dict, isPositive, defaults, prefix, kwargs):
    success_ctr = 0
    fail_ctr = 0
    for name, cmd in command_dict.items():
        print_status(f"Running {name}...")
        params = {**defaults, **kwargs}
        command = cmd.format(**params)
        if not prefix == "sudo":
            pr = prefix.format(cmd = name)
        if runTest(composeCommand(pr, command), isPositive):
            success_ctr += 1
        else: 
            fail_ctr += 1
    print_status(f"Tests passed: {success_ctr}, tests failed: {fail_ctr}\n", "info")


def runTest(command, isPositive):
    expected = "success" if isPositive else "failed"
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        if expected in result.stdout.lower():
            print(f"Test is ok: {command}")
            return True
        else:
            print_status(f"Test failed: {command}", "error")
            print_status(f"Output: {result.stdout}", "error")
            if (result.stderr):
                print_status(f"Output cerr: {result.stderr}", "error")
    except Exception as ex:
        print_status(f"An error occurred while running: {command}", "error")
        print_status(f"Error: {ex}", "error")
    

def loadDefaultParams():
    with open('default_params.json', 'r') as file:
        default = json.load(file)
    return default


def saveDefaultParams(default):
    with open('default_params.json', 'w') as file:
       json.dump(default, file, indent=4) 


def validateKwargs(kwargs, valid_params):
    for key in kwargs:
        if key not in valid_params:
            print_status(f"Error: Invalid param '{key}'", "error")
            sys.exit(1)


def main(action, mode, save_defaults, **kwargs):
    if os.path.exists('default_params.json'):
        defaults = loadDefaultParams()
        print("Loaded default params from json")
    else:
        #predefined params for a quick default launch
        defaults = {
            "app_path": "../out/debug/se-wrapper",
            "testElf": "data/tester",
            "testNonElf": "data/hello.py",
            "extraElf": "/usr/bin/ssh" #! perms may be modififed
        }
        print("Using predefined params")
 
    options = ["app_path", "testElf", "testNonElf", "testNonElf"]

    #must be successful
    cmds_positive = {
        "add_autocalc_elf" : "{app_path} --do add -p {testElf} -C", # + check that it was added as elf
        "add_autocalc_nonelf" : "{app_path} --do add -p {testNonElf} -C",
        "add_extra_elf" : "{app_path} --do add -p {extraElf} -C",
        "alias" : "sudo {app_path} --do config --add-command tester --path-elf {testElf}",
        "alias_extra" : "{app_path} --do config --add-command tester_extra --path-elf {testElf} --path-exec {extraElf}",
        "run_by_path" : "{app_path} --do exec -p {testElf}",
        "run_by_alias" : "{app_path} --do exec -c tester",
        "run_by_alias_extra" : "{app_path} --do exec -c tester_extra",
        "restore_extra_elf" : "{app_path} --do restore -b {extraElf}", # check its perms after
        "restore_execs" : "{app_path} --do restore --all-execs",
        "restore_aliases" : "{app_path} --do restore --all-aliases",
    }

    valgrind_cmd = "sudo valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes --verbose --log-file=valgrind_logs/{cmd}.txt"
    
    #must be failed
    cmds_negative = {
        "add_no_path" : "{app_path} --do add -p /path/any -C", 
        "run_no_exec" : "{app_path} --do exec -p /path/any",
        "add_existing_cmd" : "{app_path} --do add -p {testElf} -C\n sudo {app_path} --do config --add-command test -p {testElf}\n {app_path} --do config --add-command test -p {testElf}",
    }

    validateKwargs(kwargs, options)
    params = {**defaults, **kwargs}

    if mode == "valgrind":
        prefix = valgrind_cmd
        if not os.path.isdir('valgrind_logs'):
            os.mkdir("valgrind_logs")
    else:
        prefix = "sudo"

    if (action in cmds_positive or action in cmds_negative):
        isPositive = True if (action in cmds_positive) else False
        command = command_dict[action].format(**params)
        if not prefix == "sudo":
            prefix = prefix.format(cmd = action)
        runTest(composeCommand(prefix, command), isPositive)
    elif (action == "save"):
        saveDefaultParams(params)
        print_status("Default params are updated", "info")
    else:
        launchTests(cmds_positive, True, defaults, prefix, kwargs)
        launchTests(cmds_negative, False, defaults, prefix, kwargs)


if __name__=="__main__":
    print("Usage: tester.py <mode> <command> [key=val],")
    print("command: a test case name or 'save' to save params;")
    print("mode: specify 'valgrind' to test under valgrind;")
    print("Available test params: 'app_path', 'testElf', 'testNonElf', 'testNonElf'")
    print("If nothing is specified, then all scenarios are tested.\n")
    print("Make sure to ./prepare_test_env.sh before running this script with defaults.\n")

    mode = None
    action = None
    kwargs = {}
    save_defaults = False

    if len(sys.argv) > 2:
        action = sys.argv[2]
        mode = sys.argv[1]
        kwargs = dict(arg.split('=') for arg in sys.argv[3:])
        save_defaults = True
    elif len(sys.argv) > 1:
        mode = sys.argv[1]
        kwargs = dict(arg.split('=') for arg in sys.argv[2:])
        save_defaults = True

    main(action, mode, save_defaults, **kwargs)

