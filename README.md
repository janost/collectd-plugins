## collectd plugins

### tcplat
Measures the time it takes to establish a TCP connection to configurable targets.
Example configuration:
```
<Plugin python>
    ModulePath "/path/to/the/plugin"
    LogTraces false
    Interactive false
    Import "tcplat"

    <Module tcplat>
        Target "192.168.1.1:80"
        Target "8.8.8.8:53"
        Timeout 100
        Interval 1000
    </Module>
</Plugin>
```

### compal
Reports downstream/upstream power and downstream SNR of your Compal CH7465LG cable modem.
Code is based on [compal_CH7465LG_py](https://github.com/ties/compal_CH7465LG_py).

Example configuration:
```
<Plugin python>
    ModulePath "/path/to/the/plugin"
    LogTraces false
    Interactive false
    Import "compal"

    <Module compal>
        IP "192.168.100.1"
        Password "supersecret"
    </Module>
</Plugin>
```

### Contributions
Contributions are welcome.

### License
WTFPL
