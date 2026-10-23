
def multiply_num(numbers):  
    from functools import reduce
    return reduce(lambda x, y: x * y, numbers) / len(numbers)
