from os import path
from ap_utils.yaml_processor import YamlProcessor

from .backup_objects import BackupObject
from .check_objects import CheckObject
from .work_object_manager import work_object_manager


class BackupDestination:

    def __init__(self, config_section):
        self.name = config_section.name
        self.folder = config_section.folder
        self.num_copies = int(config_section.num_copies)
        self.schedule = config_section.schedule


class BackupConfig:

    BACKUP_TYPE_ARCHIVE = "archive"
    BACKUP_TYPE_CHECKER = "checker"

    BACKUP_TYPES = {BACKUP_TYPE_ARCHIVE, BACKUP_TYPE_CHECKER}

    DEFAULT_CHECKER_ACCURACY_DAYS = 2
    DEFAULT_DATA_FOLDER = '/var/lib/ap-backup/{backup_name}'

    def __init__(self, backup_config_file):
        # backup name
        self.name = None

        # backup type (see BACKUP_TYPE_xxx constants)
        self.backup_type = None

        #folder where backup and status files will are located
        self.data_folder = None

        # Number of days ignored by the backup checker. Only relevant for backup checker configs.
        # Optional, default is DEFAULT_CHECKER_ACCURACY_DAYS.
        self.checker_accuracy_days = None

        # dict: destination_name -> BackupDestination
        self.destination_by_name = None

        #list of backup work objects (derived from BackupObject or CheckObject)
        self.backup_objects = None

        self._read_config(backup_config_file)

    def _read_config(self, backup_config_file):

        self.name = path.splitext(path.basename(backup_config_file))[0]

        if not path.exists(backup_config_file) :
            raise ValueError("Backup configuration file '{0}' does not exist.".format(backup_config_file))

        with YamlProcessor(backup_config_file) as yaml_processor:
            main_section = yaml_processor.data

        self.backup_type = main_section.backup_type
        if self.backup_type not in self.BACKUP_TYPES:
            raise ValueError("Unsupported backup type '{0}' in configuration file '{1}'."
                             .format(self.backup_type, backup_config_file))

        self.data_folder = main_section.get_optional('data_folder', self.DEFAULT_DATA_FOLDER)
        self.data_folder = self.data_folder.format(backup_name=self.name)

        self.checker_accuracy_days = \
            int(main_section.get_optional('checker_accuracy_days', self.DEFAULT_CHECKER_ACCURACY_DAYS))

        self.destination_by_name = {}
        for object_section in main_section.get_optional_list('destinations'):
            self.destination_by_name[object_section.name] = BackupDestination(object_section)

        self.backup_objects = []
        for object_section in main_section.get_list('objects'):
            self.backup_objects.append(self._read_backup_object(object_section, backup_config_file))

    def _read_backup_object(self, object_section, backup_config_file):
        object_type = object_section.type
        backup_object = work_object_manager.create_object(object_section)
        if not backup_object:
            raise Exception("Unsupported backup object type '{0}' in configuration file '{1}'."
                            .format(object_type, backup_config_file))

        if (self.backup_type == self.BACKUP_TYPE_ARCHIVE and not isinstance(backup_object, BackupObject)) or \
           (self.backup_type == self.BACKUP_TYPE_CHECKER and not isinstance(backup_object, CheckObject)):
            raise Exception("Object type '{0}' is not supported for backup type '{1}' in configuration file '{2}'."
                            .format(object_type, self.backup_type, backup_config_file))

        return backup_object