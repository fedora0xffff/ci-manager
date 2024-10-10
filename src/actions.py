import os
import json
import config
import printer
from enum import Enum
import subprocess as sp

# TODO: move cmd data to a separate file

class Action_type(Enum):
    SDL=1 # sync src && build && sync bins && deploy
    BUILD=2,
    DEPLOY=3,
    UPDATE_TESTER=4,
    UPDATE_BUILDER=5,

class Cmd_type(Enum):
    SCP=1
    RSYNC=2
    SSH_DO=3

class ArgNames:
    ip = "ip"
    dst = "dst"
    src = "src"
    user = "user"
    sync_dst = "sync_dst"
    sync_src = "sync_src"
    command = "command"
    pass_file = "pass_file"
    path_inclusions = "path_inclusions"

class Cmd:
    arg = ArgNames()

    # add exclusion files for source sync (only sources) and for the after build sync (only binaries)
    ssh_pass = "sshpass -f {pass_file}"
    scp = "scp {src} {user}@{ip}:{dst}"
    ssh_do = "ssh {user}@{ip} \'{command}\'"

    # (!) for rsync 3.0.6 or higher
    # TODO: at least, check the rsync version to show an error msg
    rsync = "rsync --progress -zavr --list-only --include-from=\"{path_inclusions}\" --exclude=\"*\" \"{sync_src}\\\" {user}@{ip}:{sync_dst}"
    rsync_diff = "rsync --progress --dry-run -acr --include-from=\"{path_inclusions}\" --exclude=\"*\" \"{sync_src}\\\" {user}@{ip}:{sync_dst}"

    argnames_ssh = {arg.ip, arg.user, arg.pass_file, arg.command}
    argnames_scp = {arg.ip, arg.user, arg.pass_file, arg.src, arg.dst}
    argnames_rsync = {arg.ip, arg.user, arg.pass_file, arg.path_inclusions, arg.src, arg.dst}

    def get_argnames(self, cmd_type):
        switcher = {
        Cmd_type.SCP: self.argnames_scp,
        Cmd_type.RSYNC: self.argnames_rsync,
        Cmd_type.SSH_DO: self.argnames_ssh
        }
        return switcher.get(cmd_type, 'unknown')

# runs a @command with args @**kwargs
# return True on success, False otherwise
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
            if verbose:
                printer.print_status(f"Command result: {stream_data}")
        except Exception as ex:
            printer.print_status(f"An error occurred while running: {command}", "error")
            printer.print_status(f"Error: {ex}", "error")
            return False
        return True

class Tester:
    cmd = Cmd()

    def __init__(self, **kwargs):
        self.prepare_data(kwargs)

    def prepare_data(self, **kwargs):
        self.arg_data = {}
        self.arg_data[self.cmd.arg.ip] = kwargs[config.JsonNames.tester_ip]
        self.arg_data[self.cmd.arg.user] = kwargs[config.JsonNames.tester_user]
        self.arg_data[self.cmd.arg.dst] = kwargs[config.JsonNames.tester_save_dir]
        self.arg_data[self.cmd.arg.sync_src] = kwargs[config.JsonNames.project_path]
        self.arg_data[self.cmd.arg.sync_dst] = kwargs[config.JsonNames.project_path]
        self.arg_data[self.cmd.arg.pass_file] = kwargs[config.JsonNames.tester_pass_file]
        self.arg_data[self.cmd.arg.path_inclusions] = kwargs[config.JsonNames.path_inclusion_file_bins]

    def update(self, verbose):
        if verbose:
            printer.print_status(f"Updating tester... {self.arg_data['user']}@{self.arg_data['ip']}")
        #1. update tester bins
        if not run_command(self.cmd.rsync, verbose, **self.arg_data):
            return False
        #2. update sources
        self.arg_data["path_inclusions"] = self.arg_data["path_inclusions_src"]
        if not run_command(self.cmd.rsync, verbose, **self.arg_data):
            return False

        return True

class BuilderRemote:
    cmd = Cmd()

    def __init__(self, **kwargs):
        self.prepare_data(kwargs)

    def prepare_data(self, **kwargs):
        self.arg_data = {}
        self.arg_data[self.cmd.arg.ip] = kwargs[config.JsonNames.builder_ip]
        self.arg_data[self.cmd.arg.user] = kwargs[config.JsonNames.builder_user]
        self.arg_data[self.cmd.arg.sync_src] = kwargs[config.JsonNames.project_path]
        self.arg_data[self.cmd.arg.sync_dst] = kwargs[config.JsonNames.builder_proj_dir]
        self.arg_data[self.cmd.arg.pass_file] = kwargs[config.JsonNames.builder_pass_file]
        self.arg_data[self.cmd.arg.path_inclusions] = kwargs[config.JsonNames.path_inclusion_file_bins]

        self.inclusion_src = kwargs[config.JsonNames.path_inclusion_file_sources]
        self.inclusion_bin = kwargs[config.JsonNames.path_inclusion_file_bins]
        self.build_release = kwargs[config.JsonNames.build_cmd_release]
        self.build_debug = kwargs[config.JsonNames.build_cmd_debug]

    def build(self, verbose, debug=True):
        if verbose:
            printer.print_status("Building remote... {self.arg_data['user']}@{self.arg_data['ip']}")

        # 1. update bldr sources (rsync)
        # subst 'path_inclusions' for sources sync
        self.arg_data[self.cmd.arg.path_inclusions] = self.inclusion_src
        if not run_command(self.cmd.rsync, verbose, **self.arg_data): 
            return False
        
        # 2. build
        self.arg_data[self.cmd.arg.command] = "cd " + self.arg_data[self.cmd.arg.sync_dst] + " && "

        if debug:
            self.arg_data[self.cmd.arg.command] += self.build_debug
        else:
            self.arg_data[self.cmd.arg.command] += self.build_release

        if not run_command(self.cmd.ssh_do, verbose, **self.arg_data):
            return False
        
        # 3. update bins on the coder machine
        # subst 'path_inclusions' for binaries sync
        self.arg_data[self.cmd.arg.path_inclusions] = self.inclusion_bin
        # switch src and dst places
        temp = self.arg_data[self.cmd.arg.sync_dst]
        self.arg_data[self.cmd.arg.sync_dst] = self.arg_data[self.cmd.arg.sync_src]
        self.arg_data[self.cmd.arg.sync_src] = temp

        if not run_command(self.cmd.rsync, verbose, **self.arg_data):
            return False
        printer.print_status(f"Finished building remote... {self.arg_data['user']}@{self.arg_data['ip']}")
        return True
    
    # TODO: fill in
    def update(self, verbose):
        if verbose:
            printer.print_status("Updating remote... {self.arg_data['user']}@{self.arg_data['ip']}")
        printer.print_status("Not implemented", "warn")
        return True

class BuilderLocal:
    def __init__(self, project_path, dbg, release):
        self.project_path = project_path
        self.build_debug = dbg
        self.build_release = release

    def build(self, verbose, debug=True):
        if verbose:
            printer.print_status("Building local... {self.project_path}")
        if not debug:
            if not run_command("cd {self.project_path} && {self.build_release}", verbose):
                return False
        else: 
            if not run_command("cd {self.project_path} && {self.build_debug}", verbose):
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

    

        