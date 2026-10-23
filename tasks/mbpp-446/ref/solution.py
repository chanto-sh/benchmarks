
from collections import Counter 
def count_Occurrence(tup, lst): 
    return sum(tup.count(ele) for ele in lst)
