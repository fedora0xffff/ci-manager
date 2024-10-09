
import os
import json
import printer

# contains json field names
class JsonNames:
    
    project_path = "project_path"
    default_project = "default_project"

    #builder
    builder_ip = "builder_ip"
    builder_user = "builder_user"
    builder_proj_dir = "builder_proj_dir"
    builder_pass_file = "builder_pass_file"

    #tester
    tester_ip = "tester_ip"
    tester_user = "tester_user"
    tester_save_dir = "tester_save_dir"
    tester_pass_file = "tester_pass_file"
    #build cmd
    build_cmd_debug = "build_cmd_debug"
    build_cmd_release = "build_cmd_release"
    #rsync inclusion files 
    path_inclusion_file_bins = "path_inclusion_file_bins"
    path_inclusion_file_sources = "path_inclusion_file_sources"

    #change all string literals to variable names
    json_to_user_friendly = {
        builder_ip: "builder IP",
        builder_user: "builder User",
        builder_proj_dir: "builder Project Dir",
        builder_pass_file: "builder Password File (for sshpass)",
        tester_ip: "tester IP",
        tester_user: "tester user",
        tester_save_dir: "tester default save directory",
        tester_pass_file: "tester Password File (for sshpass)",
        build_cmd_debug: "build command dor a debug build",
        build_cmd_release: "build command for a release build",
        path_inclusion_file_bins: "path to inclusion file for binaries sync using rsync", 
        path_inclusion_file_sources: "path to inclusion file for sources sync using rsync",
        default_project: "default project"
    }

    fields_common = {project_path, tester_ip, tester_user, tester_pass_file, 
                     build_cmd_release, build_cmd_debug , tester_save_dir, 
                     path_inclusion_file_bins}
    
    fields_builder = {builder_user, builder_ip,builder_pass_file, 
                    builder_proj_dir, path_inclusion_file_sources} 

    fields_tester = {tester_ip, tester_user, tester_pass_file, 
                    tester_save_dir, path_inclusion_file_bins}

class Config:
    names = JsonNames()

    # is created inside $HOME
    config_path = ".ci-manager/config.json"
   
    def __init__(self):
        if not self.load():
            self.json_data = {}

    def save(self):
        with open(self.config_path, 'w') as json_file:
            json.dump(self.json_data, json_file)
    
    def load(self):
        full_cfg_path = os.environ['HOME'] + "/" + self.config_path

        try:
            with open(full_cfg_path, 'r') as json_file:
                self.json_data = json.load(json_file)

        except Exception as ex:
            printer.print_status(f"An error occurred while loading: {full_cfg_path}, creating default cfg", "error")
            return False
        
        return True

    # getters
    # get current project name
    def get_current(self):
        return self.json_data['default_project']

    # get current project data
    def get_current_project(self):
        return self.json_data[self.get_current()]
    
    def get_project(self, name):
        return self.json_data[name]
    
    def get_common_fields(self):
        res = {}
        for elem in self.names.fields_common:
            res.update({elem: self.names.json_to_user_friendly[elem]})
        return res
    
    def get_builder_fields(self):
        return self.fields_builder

    def has_project(self, name):
        return name in self.json_data
    
    def get_project_names(self):
        return list(self.json_data.keys())
    
    def delete_project(self, name):
        del self.json_data[name]
        self.save()

    def get_template_allinone(self):
        res = {}
        for elem in self.names.fields_builder:
            res.update({elem: self.names.json_to_user_friendly[elem]})

        return self.names.fields_common | res
    
    def get_template_separate(self):
        return self.names.fields_common
    
    def get_if_builder_is_coder(self):
        return self.get_current_project()['builder_is_coder']
    
    #TODO return tester fields. Proc data for commands on the receiver side 
    def get_tester_data(self):
        data = {}
        project = self.get_current_project()
        data["ip"] = project['tester_ip']
        data["user"] = project['tester_user']
        data["pass_file"] = project['tester_pass_file']
        data["save_dir"] = project['tester_save_dir']
        data["sync_dst"] = project['project_path']
        data["sync_src"] = project['project_path']
        data["path_inclusions"] = project['path_inclusion_file_bins']
        data["path_inclusions_src"] = project['path_inclusion_file_sources']

        return data
    
    # {"builder_user", "builder_ip","builder_pass_file","builder_proj_dir", 
    # "path_inclusion_file_sources"} 
    def get_builder_data(self):
        project = self.get_current_project()
        if not project['builder_is_coder']:
            data = {}
            data["ip"] = project['builder_ip']
            data["user"] = project['builder_user']
            data["pass_file"] = project['builder_pass_file']
            data["sync_dst"] = project['builder_proj_dir']
            data["sync_src"] = project['project_path']
            data["src_inclusion_file"] = project['path_inclusion_file_sources']
            data["bin_inclusion_file"] = project['path_inclusion_file_bins']
            data["command_d"] = project['build_cmd_debug']
            data["command_r"] = project['build_cmd_release']
        else:
            data = project["project_path"]
        return data

    #setters
    def set_current(self, name):
        self.json_data['default_project'] = name
        self.save()

    def add_project(self, name, **kwargs):
        if "builder_ip" in kwargs:
            kwargs["builder_is_coder"] = True
        else:
            kwargs["builder_is_coder"] = False
        self.json_data[name] = kwargs
        self.save()