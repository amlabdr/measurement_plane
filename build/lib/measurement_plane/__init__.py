# List to hold all registered capabilities
registered_capabilities = []

def capability(cls):
    """
    Decorator to register capabilities.
    """
    print(f"Registering capability: {cls.__name__}")
    registered_capabilities.append(cls)
    return cls