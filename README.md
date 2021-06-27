# Hello
### I wrote an A* visualization in Tkinter

##### All you need to know are these shortcuts:
    * s + Left button: set the start point
    * e + Left button: set the end point
    * Left button: draw walls


If you compile pathfinder.py with the -c argument, the cython version of A* will load.
But first, you need cython downloaded and then write in terminal in that directory
`$ python3 setup.py build_ext -i`
which will build cython files.

You can also compile astar.py itself and everything will only happen in terminal only
I leaved test.py which seys how much faster cython version is faster than python
I was able to get up to 3 times the efficient