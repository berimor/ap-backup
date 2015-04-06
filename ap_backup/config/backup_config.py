from os import path
from ap_utils.yaml_processor import YamlProcessor


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

    def __init__(self, backup_config_file):
        # backup name
        self.name = None

        # backup type (see BACKUP_TYPE_xxx constants)
        self.backup_type = None

        # Number of days ignored by the backup checker. Only relevant for backup checker configs.
        # Optional, default is DEFAULT_CHECKER_ACCURACY_DAYS.
        self.checker_accuracy_days = None

        # dict: destination_name -> BackupDestination
        self.destination_by_name = None

        #list of backup objects (derived from BackupObject)
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

        self.checker_accuracy_days = \
            int(main_section.get_optional('checker_accuracy_days', self.DEFAULT_CHECKER_ACCURACY_DAYS))

        self.destination_by_name = {}
        for destination_section in main_section.get_optional('destinations', []):
            self.destination_by_name[destination_section.name] = BackupDestination(destination_section)

        # #distinguish by backup type
        # if (self.backup_type == BACKUP_TYPE_ARCHIVE) :
        #     #Archive backup config
        #
        #     #enumerate backup objects
        #     self.backupObjects = []
        #     backupObjectTypeMap = {
        #         "mysql": lambda name,section: BackupObjectMySql(name, section),
        #         "svn": lambda name,section: BackupObjectSvn(name, section),
        #         "file": lambda name,section: BackupObjectFile(name, section),
        #         "folder": lambda name,section: BackupObjectFolder(name, section)
        #         }
        #     for sectionName in configFile :
        #         if (not sectionName.startswith("Backup_")) :
        #             continue
        #         section = configFile[sectionName]
        #         subname = sectionName[len("Backup_"):]
        #         found = False
        #         for objTypeName in backupObjectTypeMap :
        #             if (subname.lower().startswith(objTypeName + "_")) :
        #                 self.backupObjects.append(backupObjectTypeMap[objTypeName](subname[len(objTypeName + "_"):], section))
        #                 found = True
        #                 break
        #
        #         if (not found) :
        #             raise Exception("Backup object '{0}' in backup '{1}' is not recognized or not supported.".format(sectionName, self.name))
        #
        # elif (self.backup_type == BACKUP_TYPE_CHECKER) :
        #     #Checker backup config
        #
        #     #enumerate backup checker objects
        #     self.backupCheckObjects = []
        #     backupObjectTypeMap = {
        #         "recentfileexists": lambda name,section: BackupCheckObjectRecentFileExists(name, section),
        #         "comparefiletosrc": lambda name,section: BackupCheckObjectCompareFileToSrc(name, section)
        #         }
        #     for sectionName in configFile :
        #         if (not sectionName.startswith("BackupCheck_")) :
        #             continue
        #         section = configFile[sectionName]
        #         subname = sectionName[len("BackupCheck_"):]
        #         found = False
        #         for objTypeName in backupObjectTypeMap :
        #             if (subname.lower().startswith(objTypeName + "_")) :
        #                 self.backupCheckObjects.append(backupObjectTypeMap[objTypeName](subname[len(objTypeName + "_"):], section))
        #                 found = True
        #                 break
        #
        #         if (not found) :
        #             raise Exception("Backup checker object '{0}' in backup '{1}' is not recognized or not supported.".format(sectionName, self.name))
        #
        # else :
        #     raise Exception("Unsupported backup type '{0}' in backup '{1}'".format(self.backup_type, self.name))
                