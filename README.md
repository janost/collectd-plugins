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

    <Module "tcplat">
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

    <Module "compal">
        IP "192.168.100.1"
        Password "supersecret"
    </Module>
</Plugin>
```

### exping_icmp
Sends ICMP echo requests (ping) to specified targets. Provides more detailed statistics than the built-in collectd ping plugin.

Example configuration:
```
<Plugin python>
    ModulePath "/path/to/the/plugin"
    LogTraces false
    Interactive false
    Import "exping_icmp"

    <Module "exping_icmp">
        Target "192.168.1.1"
        Target "8.8.8.8"
        Timeout 100
        Interval 1000
    </Module>
</Plugin>
```

### exping_tcp
Sends TCP SYN packets to specified targets and records statistics about response times.

Example configuration:
```
<Plugin python>
    ModulePath "/path/to/the/plugin"
    LogTraces false
    Interactive false
    Import "exping_tcp"

    <Module "exping_tcp">
        Target "192.168.1.1:80"
        Target "8.8.8.8:53"
        Timeout 100
        Interval 1000
    </Module>
</Plugin>
```

### exping_udp
Sends a UDP packet to port 0 of the configured targets and waits for an ICMP port unreachable response and records statistics about response times.

Example configuration:
```
<Plugin python>
    ModulePath "/path/to/the/plugin"
    LogTraces false
    Interactive false
    Import "exping_udp"

    <Module "exping_udp">
        Target "192.168.1.1"
        Target "8.8.8.8"
        Timeout 100
        Interval 1000
    </Module>
</Plugin>
```

### Contributions
Contributions are welcome.

### License
WTFPL
