## /compression 

## file tree 
    - api.py
    - local.py  
    - compressor.py 

### api.py
Allow the user to compress their videos using the api service `Freeconvert.com` this will probably be updated in he future to include more compression api services.

### local.py  
`local.py` Allows the user to compress all their videos locally using `ffmpeg`, as well letting them select between a simple or advanced mode when compressing.  

### compressor.py
Allows the user to select between either `api.py` or `local.py` and is called in the `archiver.py`, 