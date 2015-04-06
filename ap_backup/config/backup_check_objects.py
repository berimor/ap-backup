__author__ = 'Alexander Pikovsky'


class BackupCheckObject :
    """Base class for backup checker objects."""

    name = None # name of the backup object

    scheduleType = None
    scheduleFrequency = None
    scheduleMinutes = None

    def __init__(self, name, configSection):
        self.name = name

        self.scheduleType = helpers.getRequiredConfigValue(configSection, "ScheduleType")
        self.scheduleFrequency = int(helpers.getRequiredConfigValue(configSection, "ScheduleFrequency"))

        #parse min level
        self.scheduleMinutes = ParseScheduleTypeToMinutes(self.scheduleType, name) * self.scheduleFrequency


class BackupCheckObjectRecentFileExists(BackupCheckObject) :
    """RecentFileExists backup checker object."""

    backupFolder = None
    backupFileNamePattern = None

    def __init__(self, name, configSection):
        super().__init__(name, configSection)

        self.backupFolder = helpers.getRequiredConfigValue(configSection, "BackupFolder")
        self.backupFileNamePattern = helpers.getRequiredConfigValue(configSection, "BackupFileNamePattern")


class BackupCheckObjectCompareFileToSrc(BackupCheckObject) :
    """CompareFileToSrc backup checker object."""

    backupFile = None
    srcFile = None

    def __init__(self, name, configSection):
        super().__init__(name, configSection)

        self.backupFile = helpers.getRequiredConfigValue(configSection, "BackupFile")
        self.srcFile = helpers.getRequiredConfigValue(configSection, "SrcFile")
