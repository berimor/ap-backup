from os import path
import glob
import os
from ap_utils.yaml_processor import YamlProcessor

from .backup_config import BackupConfig


class AppConfig:
    """Loads and holds application configuration."""

    def __init__(self, config_file):
        self.backup_configs = None   # list of BackupConfig objects

        self._read_config(config_file)

        #extend PATH
        path_env = os.getenv('PATH', '')
        os.environ['PATH'] = path_env+':/usr/local/bin'

    def _read_config(self, config_file):
        config_file = path.abspath(config_file)
        config_dir = path.dirname(config_file)

        #read config file
        if not path.exists(config_file):
            raise Exception("Configuration file '{0}' does not exist.".format(config_file))
        
        with YamlProcessor(config_file) as yaml_processor:
            main_section = yaml_processor.data

        #enumerate backup config folder sections
        self.backup_configs = []
        for backup_configs_folder in main_section.backup_configs_folders:
            #get absolute backup-configs folder
            if not path.isabs(backup_configs_folder):
                backup_configs_folder = path.join(config_dir, backup_configs_folder)
            if not path.exists(backup_configs_folder):
                raise Exception("Backup configurations folder '{0}' does not exist.".format(backup_configs_folder))

            #discover and read backup configs
            backup_config_file_paths = glob.glob(path.join(backup_configs_folder, "*.yaml"))
            for backup_config_file_path in backup_config_file_paths :
                self.backup_configs.append(BackupConfig(backup_config_file_path))
