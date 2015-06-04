import codecs
from copy import copy
import os
import yaml
            
                       
class DestinationStatus(object):
    """Holds a backup status for the given destination."""

    def __init__(self, destination_name):
        self.destination_name = destination_name
        self.last_backup_result = None
        self.last_successful_backup_time = None
        self.last_backup_attempt_time = None

    def serialize(self):
        return copy(self.__dict__)

    def deserialize(self, data):
        self.__dict__ = copy(data)


class BackupStatus(object):
    """Holds backup status (infos for all destinations)), reads and writes it from/to config file."""

    def get_file_path(self):
        return os.path.join(self.status_dir, self.backup_name + ".bstat")
    
    def __init__(self, backup_name, status_dir):
        """Loads backup status file if exists, otherwise creates one."""
        
        self.status_dir = status_dir
        self.backup_name = backup_name

        #map of destination_name -> DestinationStatus
        self.destination_statuses = {}

        #read config file if exists
        file_path = self.get_file_path()
        if os.path.exists(file_path):
            with codecs.open(file_path, mode='r', encoding='utf-8') as in_file:
                data = yaml.load(in_file)
                self.deserialize(data)

    def get_or_create_destination_status(self, destination_name):
        """Gets status for the given destination or creates one (and adds to map) if does not exist."""
        destination_status = self.destination_statuses.get(destination_name)
        if not destination_status:
            destination_status = DestinationStatus(destination_name)
            self.destination_statuses[destination_name] = destination_status

        return destination_status

    def save(self):
        data = self.serialize()
        with open(self.get_file_path(), 'w') as out_file:
            out_file.write(yaml.safe_dump(data, default_flow_style=False))

    def deserialize(self, data):
        self.destination_statuses = {}
        for destination_name, destination_status_data in data['destination_statuses'].iteritems():
            destination_status = DestinationStatus(destination_name)
            destination_status.deserialize(destination_status_data)
            self.destination_statuses[destination_name] = destination_status

    def serialize(self):
        data = {'destination_statuses': {}}

        destination_statuses = data['destination_statuses']
        for destination_name, destination_status in self.destination_statuses.iteritems():
            destination_statuses[destination_name] = destination_status.serialize()

        return data
