"""Jobs the process runs by itself, at boot or on a timer, never because of a request.
recovery.py rebuilds the registry from the database when the server starts; sweeper.py
drops games that have been left waiting on a human for too long.
"""
