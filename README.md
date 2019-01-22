# solcwrapper

* A wrapper for solc that allows to specify a released version of solc as a commandline option (`--x-version=0.5.1`)
  * automatically installs the version if it is *not yet* installed
    * downloads either a static (`--x-from-static`) binary of solc, or a source-code archive (`--x-from-source`) and compiles it
    * installs the binary to `/usr/local/bin/solc-<version>`
  * transparently invokes the specified version of solc passing all parameters to it


# examples

```
SOLCWrapper

Options:
    --x-list=<version>
    --x-version=<version>
    --x-from-source
    --x-from-static

Usage:
    #> python3 -m solcwrapper --x-list
    #> python3 -m solcwrapper --x-list=0.5.0
    #> python3 -m solcwrapper --x-version=0.5.1 <solc options and args>
```
