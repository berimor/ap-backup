from .work_object_manager import work_object_class

__author__ = 'Alexander Pikovsky'


class BackupObject(object):
    """Base class for backup objects."""

    def __init__(self, object_section):
        # target subfolder (of the backup folder)
        self.target_subfolder = object_section.target_subfolder


@work_object_class('mysql')
class BackupObjectMySql(BackupObject):
    """MySql backup object."""

    def __init__(self, object_section):
        super(BackupObjectMySql, self).__init__(object_section)

        self.target_file_name = object_section.target_file_name
        self.database = object_section.database
        self.user = object_section.user
        self.password = object_section.password
        self.port = object_section.get_optional('port', None)


@work_object_class('svn')
class BackupObjectSvn(BackupObject):
    """Subversion repository backup object."""

    def __init__(self, object_section):
        super(BackupObjectSvn, self).__init__(object_section)

        self.repository_folder = object_section.repository_folder


@work_object_class('file')
class BackupObjectFile(BackupObject):
    """File backup object."""

    def __init__(self, object_section):
        
        super(BackupObjectFile, self).__init__(object_section)

        # full path to the file to copy
        self.src_file_path = object_section.src_file_path

        # name of the target file or None to use source file name
        self.target_file_name = object_section.get_optional('target_file_name', None)


@work_object_class('folder')
class BackupObjectFolder(BackupObject):
    """Folder backup object."""

    def __init__(self, object_section):
        super(BackupObjectFolder, self).__init__(object_section)

        # full path to the folder to copy
        self.src_folder_path = object_section.src_folder_path

