## youtube channel archiver

project im working on a bit

## stuff todo/have done

### gotta finish

- [ ] prevent youtube bot detection
- [ ] add html, js and css code so the user can use the application better

(pls request things to do)

### finished

- [X] make setup.py:
    - downloads needed packages, gets needed data from user.

- [X] add a fast way to convert videos to different file types:
    - using `ffmpeg` basically all video file types are supported.

- [X] allow the user to change settings:
    - running `setup.py` again will let you change settings.

- [X] add video optimazation:
    - allowing the user to do api video optimization with `Freeconvert.com` video optimization (needs api key, not good for big channels).
    - also letting the user do local optimization using `ffmpeg`.

- [X] show user information:
    - using `psutil` and `platform` to get storage, os, other drives.

- [X] improve video download speed:
    - using the concurrent fragments `ydl_opts` and setting it to `5`.

- [X] optimize youtube api calls:
    - saving called data locally then calling it when the user calls the same channel id.

- [X] clean code up (seperate `archiver.py` into multiple files)
    - made every fuction into group file.