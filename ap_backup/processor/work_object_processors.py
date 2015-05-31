from abc import abstractmethod, ABCMeta
import os
import sh
import shutil
import subprocess

from ap_backup.config import BackupObjectFile, BackupObjectFolder, BackupObjectMySql, BackupObjectSvn

from .work_object_processor_manager import work_object_processor_class


class BackupObjectProcessor(object):
    """Base class for backup object processors."""
    __metaclass__ = ABCMeta

    def __init__(self, work_object, backup_processor):
        self.reporter = backup_processor.reporter
        self.work_object = work_object   # corresponding backup object
        self.backup_processor = backup_processor   # parent processor

        self.target_folder = os.path.join(self.backup_processor.last_backup_folder, self.work_object.target_subfolder)

    def ensure_target_folder_exists(self):
        if not os.path.isdir(self.target_folder):
            os.makedirs(self.target_folder)

    def ensure_target_folder_does_not_exist(self):
        """Ensures that the parent of the target folder exists, but the target folder does not."""
        if os.path.exists(self.target_folder):
            raise Exception("Target folder '{0}' already exists, please select another folder.")

        parent_folder = os.path.dirname(self.target_folder)
        if not os.path.isdir(parent_folder):
            os.makedirs(parent_folder)

    @abstractmethod
    def process(self):
        raise Exception("This method must be overridden.")


@work_object_processor_class(BackupObjectFile)
class BackupObjectFileProcessor(BackupObjectProcessor) :
    """File backup object processor."""

    def __init__(self, work_object, backup_processor):
        super(BackupObjectFileProcessor, self).__init__(work_object, backup_processor)

    def process(self):
        self.ensure_target_folder_exists()

        src_file = self.work_object.src_file_path
        if not os.path.isfile(src_file):
            raise Exception("Source file '{0}' does not exist!".format(src_file))

        target_file_name = self.work_object.target_file_name
        if not target_file_name:
            target_file_name = os.path.basename(src_file)

        self.reporter.info("Copying file '{0}' to '{1}'...".format(src_file, target_file_name))
        target_file = os.path.join(self.target_folder, target_file_name)
        shutil.copyfile(src_file, target_file)
        self.reporter.info("Done")


@work_object_processor_class(BackupObjectFolder)
class BackupObjectFolderProcessor(BackupObjectProcessor) :
    """Folder backup object processor."""

    def __init__(self, work_object, backup_processor):
        super(BackupObjectFolderProcessor, self).__init__(work_object, backup_processor)

    def process(self):
        self.ensure_target_folder_does_not_exist()

        src_folder = self.work_object.src_folder_path
        if not os.path.isdir(src_folder):
            raise Exception("Source folder '{0}' does not exist!".format(src_folder))

        self.reporter.info("Copying folder '{0}' to '{1}'...".format(src_folder, self.target_folder))
        shutil.copytree(src_folder, self.target_folder)
        self.reporter.info("Done")


@work_object_processor_class(BackupObjectMySql)
class BackupObjectMySqlProcessor(BackupObjectProcessor) :
    """MySql backup object processor."""

    def __init__(self, work_object, backup_processor):
        super(BackupObjectMySqlProcessor, self).__init__(work_object, backup_processor)

    def process(self):
        self.ensure_target_folder_exists()
        target_file_path = os.path.join(self.target_folder, self.work_object.target_file_name)

        try:
            self.reporter.info("Backing up MySql database '{0}'...".format(self.work_object.database))

            kwargs = {
                'user': self.work_object.user,
                'password': self.work_object.password,
                '_out': target_file_path
            }
            if self.work_object.host is not None:
                kwargs['host'] = self.work_object.host
            if self.work_object.port is not None:
                kwargs['port'] = self.work_object.port

            # noinspection PyUnresolvedReferences
            sh.mysqldump(self.work_object.database, '--lock-tables', '--opt', '--skip-extended-insert', **kwargs)

            self.reporter.info("Database backup complete.")

        except sh.ErrorReturnCode as ex:
            raise Exception("MySQL backup for database '{0}' failed: {1}"
                            .format(self.work_object.database, ex.message))
        except Exception as ex:
            raise Exception("MySQL backup for database '{0}' failed: {1}"
                            .format(self.work_object.database, repr(ex)))


@work_object_processor_class(BackupObjectSvn)
class BackupObjectSvnProcessor(BackupObjectProcessor):
    """Subversion repository backup object processor."""
           
    def __init__(self, work_object, backup_processor):       
        super(BackupObjectSvnProcessor, self).__init__(work_object, backup_processor)

    def process(self):
        self.ensure_target_folder_does_not_exist()

        try:
            self.reporter.info("Backing up Subversion repository '{0}'...".format(self.work_object.repository_folder))
            # noinspection PyUnresolvedReferences
            sh.svnadmin('hotcopy', self.work_object.repository_folder, self.target_folder)
            self.reporter.info("Subversion repository backup complete.")
            
        except sh.ErrorReturnCode as ex:
            raise Exception("Subversion backup for repository folder '{0}' failed: {1}".format(
                self.work_object.repository_folder, ex.message))
        except subprocess.CalledProcessError as ex:
            raise Exception("Subversion backup for repository folder '{0}' failed: {1}".format(
                self.work_object.repository_folder, repr(ex)))

