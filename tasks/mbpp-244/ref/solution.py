
import math  
def next_Perfect_Square(N): 
    if N < 0:
        return 0
    nextN = math.floor(math.sqrt(N)) + 1
    return nextN * nextN 
