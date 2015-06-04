from .work_object_manager import work_object_class

__author__ = 'Alexander Pikovsky'


class CheckObject(object):
    """Base class for backup checker objects."""

    def __init__(self, object_section):
        self.schedule = object_section.schedule


@work_object_class('recent_file_exists')
class CheckObjectRecentFileExists(CheckObject) :
    """RecentFileExists backup checker object."""

    def __init__(self, object_section):
        super(CheckObjectRecentFileExists, self).__init__(object_section)

        self.backup_folder = object_section.backup_folder
        self.backup_file_name_pattern = object_section.backup_file_name_pattern


@work_object_class('compare_file_to_src')
class CheckObjectCompareFileToSrc(CheckObject) :
    """CompareFileToSrc backup checker object."""

    def __init__(self, object_section):
        super(CheckObjectCompareFileToSrc, self).__init__(object_section)

        self.backup_file = object_section.backup_file
        self.src_file = object_section.src_file
