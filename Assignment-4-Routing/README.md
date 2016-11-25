How to Start a Router:
The code to start a router is in start_router.py. For example, run the following commands in 3 separate terminals will start 3 routers:  
python start_router.py config/small-1  
python start_router.py config/small-2  
python start_router.py config/small-3

Test Case 1: Small Network
Configuration files are provided in config/small-{1,2,3}.
After all routers converge to the right shortest path, update link cost of (1,2) from 4 to 60 in config/small-1.
And after all routers converge to the right shortest path, update link cost of (1,2) from 60 back to 4.

Test Case 2: Large Network
Configuration files are provided in config/large-{1..10}. Start 10 router processes with these config files.
Feel free to update any link cost, and see how that information if propagated throughout, and check all routers can converge to the new right shortest paths.
