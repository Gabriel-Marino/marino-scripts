SortListOfWordsFromSingleString = lambda str: print(",".join(sorted(str.split(","))))

def SortWordsSingleString(WORDS: str) -> None:
    """
    Sorts a list of words given as a single string (comma-separated) and prints out the sorted list.

    Parameters
    ----------
    WORDS : str
        A comma-separated string of words.

    Returns
    -------
    None
    """    
    LIST = WORDS.split(",")
    LIST.sort()
    print(",".join(LIST))


SortListOfWordsFromSingleString(" hyperref, cleveref, url")
SortWordsSingleString(" hyperref, cleveref, url")