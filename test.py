from timeit import timeit

py = timeit("astar.main()", "import astar", number=100)
cy = timeit("astarc.main()", "import astarc", number=100)

print(py/cy)
