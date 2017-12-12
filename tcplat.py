#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
import threading
import socket
import time
import timeit
import collectd
import numpy as np

TARGETS = []
MONITORS = []
INTERVAL = 1000
TIMEOUT = 100


class TCPLatencyMonitor(threading.Thread):
    def __init__(
            self,
            target,
            interval,
            timeout,
        ):
        super(TCPLatencyMonitor, self).__init__()
        self.shutdown_flag = threading.Event()
        self.target = target
        self.interval = interval
        self.timeout = timeout
        self.running = True
        self.reset()

    def reset(self):
        self.latency = []
        self.success = 0
        self.failed = 0

    def read(self):
        r_latency = list(self.latency)
        r_success = self.success
        r_failed = self.failed
        self.reset()
        return (r_latency, r_success, r_failed)

    def run(self):
        while not self.shutdown_flag.is_set():
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            start_time = 0
            conn_time = 0
            try:
                conn.settimeout(self.timeout / 1000.0)
                start_time = timeit.default_timer()
                conn.connect(self.target)
                conn.settimeout(None)
                conn_time = timeit.default_timer() - start_time
                conn.close()
                self.success += 1
                self.latency.append(conn_time * 1000)
            except Exception, e:
                collectd.info(str(e))
                self.failed += 1

            sleep_time = self.interval / 1000.0 - conn_time
            if sleep_time > 0:
                time.sleep(sleep_time)

def log_info(msg):
    collectd.info('TCPLAT: ' + msg)

def read_config(config):
    for node in config.children:
        key = node.key.lower()
        val = node.values[0]

        if key == 'target':
            (host, port) = val.split(':')
            log_info('Adding target: %s:%i' % (host, int(port)))
            TARGETS.append((host, int(port)))
        elif key == 'timeout':
            log_info('Setting timeout: %i' % int(val))
            global TIMEOUT
            TIMEOUT = int(val)
        elif key == 'interval':
            log_info('Setting interval: %i' % int(val))
            global INTERVAL
            INTERVAL = int(val)
        else:
            log_info('Unknown config key "%s"' % key)

def start_monitoring():
    for target in TARGETS:
        log_info('Starting monitoring thread for %s, interval: %i, timeout: %i'
                 % (str(target), INTERVAL, TIMEOUT))
        m = TCPLatencyMonitor(target, INTERVAL, TIMEOUT)
        MONITORS.append(m)
        m.start()

def read_data():
    for m in MONITORS:
        (lat_arr, success, failed) = m.read()
        if success > 0 or failed > 0:
            latency = np.array(lat_arr)
            generate_metrics(m.target, success, failed, latency)

def shutdown():
    for m in MONITORS:
        m.shutdown_flag.set()

def generate_metrics(
        target,
        success,
        failed,
        latency,
    ):
    target_str = '%s:%i' % (target[0], target[1])
    droprate = failed / (success + failed)
    v = collectd.Values(plugin='tcplat', type='tcplat',
                        plugin_instance=target_str)
    v.dispatch(values=[
        droprate,
        np.mean(latency),
        np.std(latency),
        np.amin(latency),
        np.amax(latency),
        np.percentile(latency, 99),
        np.percentile(latency, 95),
        np.percentile(latency, 90),
        ])


collectd.register_config(read_config)
collectd.register_read(read_data)
collectd.register_init(start_monitoring)
collectd.register_shutdown(shutdown)
