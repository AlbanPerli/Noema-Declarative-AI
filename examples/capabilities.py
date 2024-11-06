
def write_to_file(file: str, content: str) -> None:
    """
    Write some content to a file.
    Create the file if it does not exist.

    :param file: The file to write to
    :param content: The content to write
    """
    with open(file, "w") as f:
        f.write(content)
        
        
def read_file(file: str) -> str:
    """
    Read the content of a file.

    :param file: The file to read
    :return: The content of the file
    """
    with open(file, "r") as f:
        return f.read()


def multiply(a: int, b: int) -> int:
    """
    Multiply two integers together.

    :param a: The first integer
    :param b: The second integer
    :return: The product of the two integers
    """
    return a * b


def multiply(a: float, b: float) -> float:
    """
    Multiply two float together.

    :param a: The first float
    :param b: The second float
    :return: The product of the two floats
    """
    return a * b


def sum(a: int, b: int) -> int:
    """
    Sum two integers together.

    :param a: The first integer
    :param b: The second integer
    :return: The sum of the two integers
    """
    return a * b


def sum(a: float, b: float) -> float:
    """
    Sum two float together.

    :param a: The first float
    :param b: The second float
    :return: The sum of the two floats
    """
    return a * b


def remove_from_list(a: list, b: int) -> list:
    """
    Remove an element from a list.

    :param a: The list
    :param b: The index of the element to remove
    :return: The list without the element
    """
    a.pop(b)
    return a