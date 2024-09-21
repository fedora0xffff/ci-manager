
import argparse
import sys
import os
from utils import config, printer, actions

# manage projects:
# add-project <name>
# set-current <name>
# remove-project <name>
# list-projects
# list-current
# CI:
# build <configuration>
# update-builder <branch_name> (from branch)
# update-tester (with sources and bins)

def check_answer_is_valid(answer, options):
    ans=answer.lower()
    if ans in options:
        return True
    else:
        return False

def prompt_input(question, default='n', options=['y', 'n']):
    question_str = "{q}[y/n]\n"
    res = input(question_str(q=question))
    is_valid = check_answer_is_valid(res, options)
    while not is_valid:
        print("Please, answer one of: {}".format(options))
        res = input(question_str(q=question))
        is_valid = check_answer_is_valid(res, options)
    return res

def add_project(name):
    config = config.Config()
    if config.has_project(name):
        print("Project {} already exists".format(name))
        res = prompt_input("Rewrite?")
        if res == 'y':
            config.delete_project(name)
        else:
            return
    res = prompt_input("Single machine for build and coding?")
    if res == 'y':
        # параметры, которые необходимо заполнить
        fields = config.get_template_allinone()
    else:
        fields = config.get_template_separate()

    fields_dict = dict.fromkeys(fields, "")
    # pairs: key - user friendly field name, value - user's input
    for key, value in fields_dict.items():
        value = input("Enter {}: ".format(key))
    config.add_project(name, **fields)
    config.save()
    printer.print_status("Done!", "info")

def remove_project(name):
    config = config.Config()
    if not config.has_project(name):
        print("Project {} doesn't exist".format(name))
        return
    config.delete_project(name)
    printer.print_status("Done!", "info")
    config.save()

def set_current(name):
    config = config.Config()
    if not config.has_project(name):
        print("Project {} doesn't exist".format(name))
        return
    config.set_current(name)
    printer.print_status("Done!", "info")
    config.save()

def list_projects():
    config = config.Config()
    projects = config.get_project_names()
    for name in projects:
        print(name)

def list_current():
    config = config.Config()
    name = config.get_current()
    print(name)

#build default
def build(verbose, debug):
    # get project data
    config = config.Config()
    actor = actions.Actor(config.get_current_project())
    actor.build(verbose, debug)

def update_builder(verbose):
    config = config.Config()
    actor = actions.Actor(config.get_current_project())
    actor.update_builder(verbose)

def update_tester(verbose):
    config = config.Config()
    actor = actions.Actor(config.get_current_project())
    actor.update_tester(verbose)


def main():

    # read projects info to a variable 'projects'
    parser=argparse.ArgumentParser(description="CI manager")
    parser.add_argument('--add-project', type=str, help="add the new project info")
    # TODO: show 'projects' as a list for choice
    parser.add_argument('--set_current', '-s', type=str, help="make the project current (default)") 
    parser.add_argument('--remove-project', type=str, help="delete project info")
    parser.add_argument('--list-projects', '-l', action='store_true', help="list all added projects")
    parser.add_argument('--list-current', action='store_true', help="list current project")
    parser.add_argument('--build', '-b', action='store_true', help="build the project")
    parser.add_argument('-release', '-r', action='store_true', help="makes sense only with --build")
    parser.add_argument('--update-builder', action='store_true', help="update the builder sources")
    parser.add_argument('--update-tester', action='store_true', help="update the tester with sources and binaries")
    parser.add_argument('--verbose', '-v', action='store_true', help="Enable verbose mode")


    args = parser.parse_args()
    print(args)

    if args.add_project:
        add_project(args.add_project)
    elif args.set_current:
        set_current(args.set_current)
    elif args.remove_project:
        remove_project(args.remove_project)
    elif args.list_projects:
        list_projects()
    elif args.list_current:
        list_current()
    elif args.build:
        if not args.release:
            build(args.verbose, True)
        else:
            build(args.verbose, False)
    elif args.update_builder:
        update_builder(args.verbose)
    elif args.update_tester:
        update_tester(args.verbose)
    else:
        parser.print_help()