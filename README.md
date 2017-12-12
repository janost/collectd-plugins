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

### License
WTFPL
