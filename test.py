from functools import reduce
x = [[1,2,3],[],[4,0,5]]


def noZeroList(l):
    return reduce(lambda res,x: res+[x] if 0 not in x else res, l ,[])

[[1,2,3],[]]

print(noZeroList(x))



 