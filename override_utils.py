from types import MethodType

def override_object_function(obj, func_name, new_func):
    """
    Override a method on a specific object instance.
    """
    if not hasattr(obj, func_name):
        raise AttributeError(f"{obj} has no attribute {func_name}")

    # Bind the function to the instance
    bound_method = MethodType(new_func, obj)
    setattr(obj, func_name, bound_method)

