
def digit_distance_nums(n1, n2):
    return sum([abs(int(c1) - int(c2)) for c1, c2 in zip(str(n1), str(n2))])
