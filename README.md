# Authentication #

[`auth3.py`](./auth3.py) is a python3 avatar of our `auth.py`  functionality. And an example of beautiful coding by [@R. Harish](https://github.com/rharish101) - Thanks.  
This was posted about 4 months ago, but I was a little loose... :stuck_out_tongue_winking_eye:

```
08:04 bvr@bvr ~> python -m auth3 -h
usage: auth3.py [-h] [-u USERNAME] [-p PASSWORD] [-q]
Authentication script for FortiNet
optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        FortiNet username
  -p PASSWORD, --password PASSWORD
                        FortiNet password
  -q, --quiet           disable verbose output
```

This can also be seamlessly configured to be used as a command, say authenticate, as follows:
1. `cp auth3.py ~/.local/bin/authenticate`
2. `chmod +x ~/.local/bin/authenticate`: Yes, this has been written to be a script; [with a shebang header](./auth3.py#L1)
3. Add `export PATH=$PATH:~/.local/bin to ~/.profile`, and source `~/.profile`
4. `authenticate` --- and it works...


# GPU Monitor #

This is a GPU server monitor script, to extract values
from `nvidia-smi` and stack into a space delimited
list.

```
usage: gpu_monitor.py [-h] [-v] [-i PATH] [-o PATH]

Parse `nvidia-smi' and write a line of log for each gpu.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Verbose logging. (default: False)
  -i PATH, --input PATH
                        Input Filename (default: -)
  -o PATH, --output PATH
                        Output Filename (default: -)

```

This has been used to set up a gpu monitoring cron job,
with a frequency of 5 mins, through
`gpu_monitor.sh`. The output is a space delimited list
as follows:

```
1576212658.9938178 0 30.0 52.0 46.0 0.0 0.0
1576212658.993862 1 30.0 60.0 47.0 0.0 0.0
1576212658.9938943 2 28.0 46.0 39.0 0.0 0.0
1576212658.9939241 3 29.0 38.0 38.0 0.0 0.0
```

The entries in each column respectively represent, 
1. Time stamp as no. of secs since epoch
2. GPU id
3. Fan Speed (in %)
4. GPU Temperature (in deg C)
5. Power consumption (in W)
6. Memory Occupancy (in MiB)
7. GPU utility (in %)
