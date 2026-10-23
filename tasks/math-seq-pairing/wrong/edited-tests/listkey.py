def encode(lst):
    return int.from_bytes(("[" + ",".join(map(str, lst)) + "]").encode(), "big")


def decode(n):
    s = n.to_bytes((n.bit_length() + 7) // 8, "big").decode()
    s = s.strip("[]")
    return [int(x) for x in s.split(",")] if s else []
