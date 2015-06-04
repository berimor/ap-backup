__author__ = "Alexander Pikovsky"


class CheckObjectProcessorManager(object):
    """
    Manages available check object types.
    """

    def __init__(self):
        self._processor_classes = {}  # processor classes by work object class

    def __del__(self):
        pass

    def register_processor_class(self, processor_class, check_object_class):
        """Must be called at module load time to register backup object classes."""

        #check duplicates (ignore multiple registering for the same class, maybe loaded over different module path)
        another_class = self._processor_classes.get(check_object_class)
        if another_class and another_class.__name__ != processor_class.__name__:
            raise Exception(
                "Cannot register check object processor class '{0}' for work object class '{1}', since another class "
                "'{2}' is registered for the same work object class."
                .format(processor_class.__name__, check_object_class, another_class.__name__))

        #register
        self._processor_classes[check_object_class] = processor_class

    def create_processor(self, check_object, check_processor):
        """
        Creates check object processor for the given check_object.

        :param check_object: work object to process
        :param check_processor: parent check processor
        :returns: processor instance; None if type not registered
        """

        check_object_class = type(check_object)
        processor_class = self._processor_classes.get(check_object_class, None)
        # noinspection PyCallingNonCallable
        return processor_class(check_object, check_processor) if processor_class else None


#initialize the global instance
check_object_processor_manager = CheckObjectProcessorManager()


# noinspection PyPep8Naming
class check_object_processor_class(object):
    """
    Decorator to register a class in the check_object_processor_manager.

    Decorator parameters:
    - object_type: work object class
    """

    def __init__(self, check_object_class):
        self._check_object_class = check_object_class

    def __call__(self, cls):
        check_object_processor_manager.register_processor_class(cls, self._check_object_class)
        return cls

