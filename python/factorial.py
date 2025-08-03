from functools import reduce
from typing import Callable

factorialLambda: Callable[[int], int] = lambda num: 1 if num == 0 else num * factorialLambda(num - 1)

def factorialRecursive(num: int) -> int:

    if num < 0 or not isinstance(num, int):
        raise ValueError(f"The factorial is a function defined only for the natural numbers, that is, the non-negative integers. Look for Gamma function if you want a extension to the Complexes numbers.")

    if num == 0:
        return 1

    return num * factorialRecursive(num-1)

def factorialIterative(num: int) -> int:

    if num < 0 or not isinstance(num, int):
        raise ValueError(f"The factorial is a function defined only for the natural numbers, that is, the non-negative integers. Look for Gamma function if you want a extension to the Complexes numbers.")

    i = num
    fat = 1
    while i > 0:
        fat *= i
        i -= 1

    return fat

def factorialReduce(num: int) -> int:

    if num < 0 or not isinstance(num, int):
        raise ValueError(f"The factorial is a function defined only for the natural numbers, that is, the non-negative integers. Look for Gamma function if you want a extension to the Complexes numbers.")

    return reduce(lambda x, y: x * y, range(num+1), 1)

