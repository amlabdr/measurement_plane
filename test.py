def logger(func):
    def wrapper(*args, **kwargs):
        print(f"Function {func.__name__} called with arguments {args} and {kwargs}")
        return func(*args, **kwargs)
    def wrapper2(*args, **kwargs):
        
        return None
    return wrapper2

@logger
def add(a, b):
    return a + b

@logger
def multiply(a, b):
    return a * b

add(2, 3)
multiply(4, 5)
