## youtube channel archiver

project im working on a bit

## stuff todo/have done

### gotta finish

### future

- [ ] create pip package so you can just `python -m yt_archiver 'channel id'`
    - [X] create way for the user to create/bypass the `config.py`
        - can be done if enough of `yt_data` is saved then you can just call that data and no api
        - for ffmpeg and api they will be prompted but for just normal downloading if the data is stored there will be no prompt
        - [X] uses moviepy instead of ffmpeg for compressing and soon to be converting
    - [X] add more options to that like the following
        - [X] -c `compression` then they will be prompted with either simple or advanced after downloading
        - [ ] -cv `convert` they will be given the prompt with telling them to use mp4, mov etc (using `ffmpeg`)
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

- [X] clean code up:
    - seperated the functions in `archiver.py` into group files.

- [X] prevent youtube bot detection:
    - when detected the code will retry then if it fails again it will change the user agent.
