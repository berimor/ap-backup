__author__ = 'Alexander Pikovsky'


class BackupObject :
    """Base class for backup objects."""

    name = None
    targetSubfolder = None # target subfolder (of the backup folder)

    def __init__(self, raw_config):
        self.targetSubfolder = helpers.getRequiredConfigValue(raw_config, "TargetSubfolder")



class BackupObjectMySql(BackupObject) :
    """MySql backup object."""

    targetFileName = None
    database = None
    user = None
    password = None
    port = None #optional

    def __init__(self, name, raw_config):
        super().__init__(name, raw_config)

        self.targetFileName = helpers.getRequiredConfigValue(raw_config, "TargetFileName")
        self.database = helpers.getRequiredConfigValue(raw_config, "Database")
        self.user = helpers.getRequiredConfigValue(raw_config, "User")
        self.password = helpers.getRequiredConfigValue(raw_config, "Password")
        self.port = helpers.getOptionalConfigValue(raw_config, "Port", None)



class BackupObjectSvn(BackupObject) :
    """Subversion repository backup object."""

    repositoryFolder = None

    def __init__(self, name, raw_config):
        super().__init__(name, raw_config)

        self.repositoryFolder = helpers.getRequiredConfigValue(raw_config, "RepositoryFolder")



class BackupObjectFile(BackupObject) :
    """File backup object."""

    srcFilePath = None #full path to the file to copy
    targetFileName = None   #name of the target file or None to use source file name

    def __init__(self, name, raw_config):
        super().__init__(name, raw_config)

        self.srcFilePath = helpers.getRequiredConfigValue(raw_config, "SrcFilePath")
        self.targetFileName = helpers.getOptionalConfigValue(raw_config, "TargetFileName", None)



class BackupObjectFolder(BackupObject) :
    """Folder backup object."""

    srcFolderPath = None #full path to the folder to copy

    def __init__(self, name, raw_config):
        super().__init__(name, raw_config)

        self.srcFolderPath = helpers.getRequiredConfigValue(raw_config, "SrcFolderPath")

