
def issort_list(list1):
    return all(a <= b for a, b in zip(list1, list1[1:]))
