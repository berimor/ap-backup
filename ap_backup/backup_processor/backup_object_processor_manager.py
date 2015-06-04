__author__ = "Alexander Pikovsky"


class BackupObjectProcessorManager(object):
    """
    Manages available backup object types.
    """

    def __init__(self):
        self._processor_classes = {}  # processor classes by work object class

    def __del__(self):
        pass

    def register_processor_class(self, processor_class, backup_object_class):
        """Must be called at module load time to register backup object classes."""

        #check duplicates (ignore multiple registering for the same class, maybe loaded over different module path)
        another_class = self._processor_classes.get(backup_object_class)
        if another_class and another_class.__name__ != processor_class.__name__:
            raise Exception(
                "Cannot register backup object processor class '{0}' for work object class '{1}', since another class "
                "'{2}' is registered for the same work object class."
                .format(processor_class.__name__, backup_object_class, another_class.__name__))

        #register
        self._processor_classes[backup_object_class] = processor_class

    def create_processor(self, backup_object, backup_processor):
        """
        Creates backup processor for the given backup object.

        :param backup_object: work object to process
        :param backup_processor: parent backup processor
        :returns: processor instance; None if type not registered
        """

        backup_object_class = type(backup_object)
        processor_class = self._processor_classes.get(backup_object_class, None)
        # noinspection PyCallingNonCallable
        return processor_class(backup_object, backup_processor) if processor_class else None


#initialize the global instance
backup_object_processor_manager = BackupObjectProcessorManager()


# noinspection PyPep8Naming
class backup_object_processor_class(object):
    """
    Decorator to register a class in the backup_object_processor_manager.

    Decorator parameters:
    - object_type: work object class
    """

    def __init__(self, backup_object_class):
        self._backup_object_class = backup_object_class

    def __call__(self, cls):
        backup_object_processor_manager.register_processor_class(cls, self._backup_object_class)
        return cls

