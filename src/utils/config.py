
import json
import printer

# +- structure 
# default_project : name
# project_name {
#     project_path: "path/to/project"
#     builder_is_coder: True/False
#     builder_info {
#         ip : "127.0.01",
#         pass_file : "path/to/pass",
#         project_dir : "path/to/project"
#     },
#     tester_info {
#         ip : "127.0.01",
#         pass_file : "path/to/pass",
#     },
#     build_cmd_release: "cmd"
#     build_cmd_debug: "cmd"
#     tester_save_dir: "/home/.ic"
#}
# 


class Config:
    config_path = "/etc/ci-manager/config.json"
    fields_builder = {"builder_user", "builder_ip","builder_pass_file","builder_proj_dir", "path_inclusion_file_sources"} 
    fields_common = {"builder_is_coder","project_path","tester_ip", "tester_user", "tester_pass_file", 
                     "build_cmd_release", "build_cmd_debug" , "tester_save_dir", "path_inclusion_file_bins"}
    def __init__(self):
        with open(self.config_path, 'r') as json_file:
            self.json_data = json.load(json_file)

    def save(self):
        with open(self.config_path, 'w') as json_file:
            json.dump(self.json_data, json_file)

    def get_current(self):
        return self.json_data['default_project']
    
    def set_current(self, name):
        self.json_data['default_project'] = name
        self.save()
    
    def get_current_project(self):
        return self.json_data[self.get_current()]
    
    def get_project(self, name):
        return self.json_data[name]
    
    def get_common_fields(self):
        return self.fields_common
    
    def get_builder_fields(self):
        return self.fields_builder

    def has_project(self, name):
        return name in self.json_data
    
    def get_project_names(self):
        return list(self.json_data.keys())
    
    def add_project(self, name, **kwargs):
        if "builder_ip" in kwargs:
            kwargs["builder_is_coder"] = True
        else:
            kwargs["builder_is_coder"] = False
        self.json_data[name] = kwargs
        self.save()
    
    def delete_project(self, name):
        del self.json_data[name]
        self.save()

    def get_template_allinone(self):
        return self.fields_common | self.fields_builder
    
    def get_template_separate(self):
        return self.fields_common
    
    def get_if_builder_is_coder(self):
        return self.get_current_project()['builder_is_coder']
    
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