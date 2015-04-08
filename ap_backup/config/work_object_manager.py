__author__ = "Alexander Pikovsky"


class WorkObjectManager(object):
    """
    Manages available backup object types.
    """

    def __init__(self):
        self._object_classes = {}  # backup object classes by type name

    def __del__(self):
        pass

    def register_object_class(self, object_class, object_type):
        """Must be called at module load time to register backup object classes."""

        #check duplicates (ignore multiple registering for the same class, maybe loaded over different module path)
        another_class = self._object_classes.get(object_type)
        if another_class and another_class.__name__ != object_class.__name__:
            raise Exception(
                "Cannot register backup object class '{0}' for type name '{1}', since another class "
                "'{2}' is registered for the same object type."
                .format(object_class.__name__, object_type, another_class.__name__))

        #register
        self._object_classes[object_type] = object_class

    def create_object(self, object_section):
        """
        Creates backup object for the given configuration section.

        :returns: importer instance; None if type not registered
        """

        object_type = object_section.type
        object_class = self._object_classes.get(object_type, None)
        return object_class(object_section) if object_class else None


#initialize the global instance of the workflow config
work_object_manager = WorkObjectManager()


# noinspection PyPep8Naming
class work_object_class(object):
    """
    Decorator to register a class in the work_object_manager.

    Decorator parameters:
    - object_type: backup object type
    """

    def __init__(self, object_type):
        self._object_type = object_type

    def __call__(self, cls):
        work_object_manager.register_object_class(cls, self._object_type)
        return cls










