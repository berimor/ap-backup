__author__ = "Alexander Pikovsky"


class WorkObjectProcessorManager(object):
    """
    Manages available backup object types.
    """

    def __init__(self):
        self._processor_classes = {}  # processor classes by work object class

    def __del__(self):
        pass

    def register_processor_class(self, processor_class, work_object_class):
        """Must be called at module load time to register backup object classes."""

        #check duplicates (ignore multiple registering for the same class, maybe loaded over different module path)
        another_class = self._processor_classes.get(work_object_class)
        if another_class and another_class.__name__ != processor_class.__name__:
            raise Exception(
                "Cannot register backup object processor class '{0}' for work object class '{1}', since another class "
                "'{2}' is registered for the same work object class."
                .format(processor_class.__name__, work_object_class, another_class.__name__))

        #register
        self._processor_classes[work_object_class] = processor_class

    def create_processor(self, work_object):
        """
        Creates backup object for the given configuration section.

        :returns: importer instance; None if type not registered
        """

        work_object_class = type(work_object)
        processor_class = self._processor_classes.get(work_object_class, None)
        # noinspection PyCallingNonCallable
        return processor_class(work_object) if processor_class else None


#initialize the global instance
work_object_processor_manager = WorkObjectProcessorManager()


# noinspection PyPep8Naming
class work_object_processor_class(object):
    """
    Decorator to register a class in the work_object_processor_manager.

    Decorator parameters:
    - object_type: work object class
    """

    def __init__(self, work_object_class):
        self._work_object_class = work_object_class

    def __call__(self, cls):
        work_object_processor_manager.register_processor_class(cls, self._work_object_class)
        return cls

