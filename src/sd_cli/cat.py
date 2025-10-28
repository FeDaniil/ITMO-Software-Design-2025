def cat(path: str):
    with open(path) as in_f:
        for line in in_f:
            print(line, end="")