from colorama import Fore, Style, init 

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