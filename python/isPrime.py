from typing import Callable

isPrimeLambda: Callable[[int], bool] = lambda num: False if num < 2 or num % 2 == 0 and num > 2 else len(list(filter(lambda denominator: num % denominator == 0, list(range(1, 1+int(num/2)))))) < 2


def isPrimeIterative(num: int) -> bool:

    if num < 2 or not isinstance(num, int):
        raise ValueError(f"A prime number is a positive integer greater than 1 that has exactly two factors: 1 and itself. {num} is not a positive integer.")

    if num % 2 == 0 and num > 2:
        return False

    factors = 0
    for denominator in range(1, 1+int(num/2)):

        if num % denominator == 0:
            factors += 1

        if factors >= 2:
            return False

    return True
