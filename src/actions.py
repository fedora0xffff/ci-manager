import subprocess as sp
from enum import Enum
import json
import os
import printer

class Action_type(Enum):
    BUILD=1,
    UPDATE_TESTER=2,
    DEPLOY=3,
    UPDATE_BUILDER=4,
    SDL=5 # sync src, build, sync bins, deploy

class Cmd_type(Enum):
    SCP=1
    SSH_DO=2
    RSYNC=3

class Cmd:
    # add exclusion files for source sync (only sources) and for the after build sync (only binaries)
    ssh_pass = "sshpass -f {pass_file}"
    scp = "scp {file_src} {user}@{ip}:{dir_dst}"
    ssh_do = "ssh {user}@{ip} \'{command}\'"
    # for rsync 3.0.6 or higher
    rsync = "rsync --progress -zarv --list-only --include-from=\"{path_inclusions}\" --exclude=\"*\" \"{sync_src}\\\" {user}@{ip}:{sync_dst}"
    rsync_diff = "rsync --progress --dry-run -acr --include-from=\"{path_inclusions}\" --exclude=\"*\" \"{sync_src}\\\" {user}@{ip}:{sync_dst}"

    argnames_ssh = {"ip", "user", "pass_file", "command"}
    argnames_scp = {"ip", "user", "pass_file", "file_src", "dir_dst"}
    argnames_rsync = {"ip", "user", "pass_file", "path_inclusions", "sync_src", "sync_dst"}


    def get_argnames(self, cmd_type):
        switcher = {
        Cmd_type.RSYNC: self.argnames_rsync,
        Cmd_type.SCP: self.argnames_scp,
        Cmd_type.SSH_DO: self.argnames_ssh
        }
        return switcher.get(cmd_type, 'unknown')


# runs a @command with args @**kwargs
# return True on seccuess, False otherwise
def run_command(command, verbose, **kwargs):
        command = command.format(**kwargs)
        if verbose:
            printer.print_status(f"Running: {command}")
        try:
            child = sp.Popen(command, stdout=sp.PIPE) # + stderr
            stream_data = child.communicate()[0]
            rc = child.returncode
            if not rc == 0:
                printer.print_status(f"Command failed: {command}", "error")
                return False
        except Exception as ex:
            printer.print_status(f"An error occurred while running: {command}", "error")
            printer.print_status(f"Error: {ex}", "error")
            return False
        return True

class Tester:
    def __init__(self, **kwargs):
        self.arg_data = kwargs

    def update(self, verbose):
        if verbose:
            printer.print_status("Updating tester... {self.arg_data['user']}@{self.arg_data['ip']}")
        #1. update tester bins
        if not run_command(rsync, verbose, **self.arg_data):
            return False
        #2. update sources
        self.arg_data["path_inclusions"] = self.arg_data["path_inclusions_src"]
        if not run_command(rsync, verbose, **self.arg_data):
            return False

        return True

class BuilderRemote:
    def __init__(self, **kwargs):
        self.arg_data = kwargs

        self.src_sync_include = kwargs["src_inclusion_file"]
        self.bindir_sync_include = kwargs["bin_inclusion_file"]

    def build(self, verbose, debug=True):
        if verbose:
            printer.print_status("Building remote... {self.arg_data['user']}@{self.arg_data['ip']}")

        # 1. update bldr sources (rsync)
        # subst 'path_inclusions'
        self.arg_data["path_inclusions"] = self.arg_data["src_inclusion_file"]
        if not run_command(rsync, verbose, **self.arg_data): 
            return False
        # 2. build
        if debug:
            self.arg_data["command"] = "cd " + self.arg_data["sync_dst"] + " && " + self.arg_data["command_d"]
        else:
            self.arg_data["command"] = "cd " + self.arg_data["sync_dst"] + " && " + self.arg_data["command_r"]
        if not run_command(ssh_do, verbose, **self.arg_data):
            return False
        
        # 3. update bins on the coder machine
        self.arg_data["path_inclusions"] = self.arg_data["bin_inclusion_file"]
        temp = self.arg_data["sync_dst"]
        self.arg_data["sync_dst"] = self.arg_data["sync_src"]
        self.arg_data["sync_src"] = temp
        if not run_command(rsync, verbose, **self.arg_data):
            return False
        
        printer.print_status("Finished building remote... {self.arg_data['user']}@{self.arg_data['ip']}")
        return True
    
    def update(self, verbose):
        if verbose:
            printer.print_status("Updating remote... {self.arg_data['user']}@{self.arg_data['ip']}")
        printer.print_status("Not implemented", "warn")
        return True

class BuilderLocal:
    def __init__(self, project_path, dbg, release):
        self.project_path = project_path
        self.build_cmd_debug = dbg
        self.build_cmd_release = release

    def build(self, verbose, debug=True):
        if verbose:
            printer.print_status("Building local... {self.project_path}")
        if not debug:
            if not run_command("cd {self.project_path} && {self.build_cmd_release}", verbose):
                return False
        else: 
            if not run_command("cd {self.project_path} && {self.build_cmd_debug}", verbose):
                return False
        return True

class Actor:
    def __init__(self, config):
        self.project = config.get_current_project()
        self.tester = Tester(**config.get_tester_data())
        if config.get_if_builder_is_coder():
            self.builder = BuilderRemote(**config.get_builder_data())
        else:
            self.builder = BuilderLocal(self.project["project_path"],
                                        self.project["build_cmd_debug"],
                                        self.project["build_cmd_release"])

    def build(self, verbose, debug):
        return self.builder.build(verbose, debug)
    
    def update_tester(self, verbose):
        return self.tester.update(verbose)
    
    def update_builder(self, verbose):
        return self.builder.update(verbose)
    
    #TODO: add deploy
    def deploy(self, verbose):
        printer.print_status("Not implemented", "warn")
        return True
    
    def do(self, action, verbose):
        if action == Action_type.BUILD:
            return self.build(verbose, )
        elif action == Action_type.UPDATE_TESTER:
            return self.update_tester(verbose)
        elif action == Action_type.UPDATE_BUILDER:
            return self.update_builder(verbose)
        elif action == Action_type.DEPLOY:
            return self.deploy(verbose)

    

        