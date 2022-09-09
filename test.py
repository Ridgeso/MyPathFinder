from timeit import timeit

py = timeit("astar.main()", "import astar", number=500)
cy = timeit("astarc.main()", "import build.astarc as astarc", number=500)

print(f"Python took {py:0.4}")
print(f"C      took {cy:0.4}")
print(f"Performance difference {py / cy:0.6}")
