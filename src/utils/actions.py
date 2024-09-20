import sys
import json
import os
import printer

class Tester:
    def __init__(self, **kwargs):
        self.ip = kwargs["ip"]
        self.pass_file = kwargs["pass_file"]
        self.default_save_dir = kwargs["default_save_dir"]
        self.repo_path = kwargs["repo_path"]

class BuilderRemote:
    def __init__(self, **kwargs):
        self.ip = kwargs["ip"] 
        self.pass_file = kwargs["pass_file"]
        self.project_dir = kwargs["project_dir"]


class BuilderLocal:
    def __init__(self, project_path):
        self.project_path = project_path

class Actor:
    def __init__(self, config):
        self.config = config
        self.tester = Tester(**config.get_tester_data())
        if config.get_if_builder_is_coder():
            self.builder = BuilderRemote(**config.get_builder_data())
        else:
            self.builder = BuilderLocal(config.get_current_project()["project_path"])
        