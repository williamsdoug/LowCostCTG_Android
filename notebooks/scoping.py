FOO = 'unitialized'

def getFOO():
    return FOO

def setFOO(val):
    global FOO
    FOO = val
