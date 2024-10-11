## Brief

[developing]

This project contains scripts that help automate develop-build-test cycle in cases where there are no other tools, e.g., when the builder machine is too old to use the vs code ssh on it directly and so one needs some means to make it seem like they code and build on the same machine. After building, the binaries (and sources for debug purposes) can be moved to a tester machine - all in a couple of commands. 

## TODO
- support the builder update
- support diffs?
- support sending files to tester/builder to a specified dir
- add a user manual concerning details like sshpass, rsync inclusions, etc
