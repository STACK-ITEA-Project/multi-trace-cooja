#!/usr/bin/env python3

import argparse
import os
import re
import sys
import traceback

from humanfriendly.tables import format_pretty_table

import coojautils


class Mote:
    mote_id = None
    address = None
    output = None
    transmissions = None
    discovered = None

    def __init__(self, mote_id, discovered):
        self.mote_id = mote_id
        self.output = []
        self.transmissions = []
        self.discovered = discovered


class Event:
    time = None
    event_type = None
    description = None

    def __init__(self, line):
        data = line.split('\t', 2)
        if len(data) < 3:
            raise coojautils.ParseException("Failed to parse event data")
        self.time = int(data[0])
        self.event_type = data[1]
        self.description = data[2]


class MoteOutput:
    time = None
    mote_id = None
    message = None

    def __init__(self, line):
        data = line.split('\t', 2)
        if len(data) < 3:
            raise coojautils.ParseException("Failed to parse mote output")
        self.time = int(data[0])
        self.mote_id = int(data[1])
        self.message = data[2]


class RadioTransmission:
    time_start = None
    time_end = None
    radio_channel = None
    mote_id = None
    receivers = None
    interfered = None
    interferedNoneDestinations = None
    data = None

    def __init__(self, line):
        data = line.split('\t', 7)
        if len(data) < 8:
            raise coojautils.ParseException("Failed to parse radio transmission")
        self.time_start = int(data[0])
        self.time_end = int(data[1])
        self.radio_channel = int(data[2])
        self.mote_id = int(data[3])
        self.receivers = data[4]
        self.interfered = data[5]
        self.interferedNoneDestinations = data[6]
        self.data = data[7]


class Script:
    time = None
    description = None

    def __init__(self, line):
        data = line.split('\t', 1)
        if len(data) < 2:
            raise coojautils.ParseException("Failed to parse event data")
        self.time = int(data[0])
        self.description = data[1]


class CoojaTrace:
    motes = None
    events = None
    mote_output = None
    transmissions = None
    _is_file_based = False

    def __init__(self, trace_name):
        self.motes = {}
        self.mote_output = []
        self.events = []
        self.transmissions = []
        self.script = []

        if not os.path.isdir(trace_name):
            m = re.match(r'(.+-dt-\d+)(-.+[.].+)?$', trace_name)
            if not m:
                sys.exit(f"File name not matching Cooja data trace: '{trace_name}'")
            self.data_trace_name = m.group(1)
            self._is_file_based = True
            # radio_log = self.data_trace_name + '-radio-log.pcap'
            coojautils.read_log(self.data_trace_name + '-event-output.log', self._process_events, max_errors=1)
            coojautils.read_log(self.data_trace_name + '-mote-output.log', self._process_mote_output, max_errors=1)
            coojautils.read_log(self.data_trace_name + '-radio-medium.log', self._process_radio_medium, max_errors=1)
            coojautils.read_log(self.data_trace_name + '-script.log', self._process_script, max_errors=1)
        else:
            self.data_trace_name = trace_name
            coojautils.read_log(os.path.join(self.data_trace_name, 'events.log'), self._process_events,
                                max_errors=1)
            coojautils.read_log(os.path.join(self.data_trace_name, 'mote-output.log'), self._process_mote_output,
                                max_errors=1)
            coojautils.read_log(os.path.join(self.data_trace_name, 'radio-medium.log'), self._process_radio_medium,
                                max_errors=1)
            coojautils.read_log(os.path.join(self.data_trace_name, 'script.log'), self._process_script,
                                max_errors=1)

        # Get address from 'Tentative link-local IPv6 address: fe80::222:22:22:22'
        p = re.compile(r'.*Tentative link-local IPv6 address: fe80(::[\d:a-f]+)$')
        for o in self.mote_output:
            m = p.match(o.message)
            if m:
                mote = self.add_mote(o.mote_id, o.time)
                mote.address = m.group(1)

    def _process_events(self, line):
        self.events.append(Event(line))

    def _process_script(self, line):
        self.script.append(Script(line))

    def _process_mote_output(self, line):
        output = MoteOutput(line)
        self.add_mote(output.mote_id, output.time).output.append(output)
        self.mote_output.append(output)

    def _process_radio_medium(self, line):
        t = RadioTransmission(line)
        self.add_mote(t.mote_id, t.time_start).transmissions.append(t)
        self.transmissions.append(t)

    def get_file_name(self, filename):
        if self._is_file_based:
            return self.data_trace_name + '-' + filename
        else:
            return os.path.join(self.data_trace_name, filename)

    def is_file(self, filename):
        return os.path.isfile(self.get_file_name(filename))

    def get_log_writer(self, filename, is_binary=False, overwrite=False):
        log_file = self.get_file_name(filename)
        if not overwrite and os.path.exists(log_file):
            raise FileExistsError(f'file "{log_file}" already exists')
        return coojautils.LogWriter(log_file, mode='wb' if is_binary else 'wt')

    def get_events(self, event_type=None, description=None, start_time=None, end_time=None):
        output = list(self.events)
        if start_time is not None:
            output = [v for v in output if v.time >= start_time]
        if end_time is not None:
            output = [v for v in output if v.time <= end_time]
        if event_type:
            output = [e for e in output if e.event_type == event_type]
        if description:
            output = [e for e in output if e.description == description]
        return output

    def get_script(self, description=None, start_time=None, end_time=None):
        output = list(self.script)
        if start_time is not None:
            output = [v for v in output if v.time >= start_time]
        if end_time is not None:
            output = [v for v in output if v.time <= end_time]
        if description:
            output = [e for e in output if description in e.description]
        return output

    def get_mote_output(self, regex=None, start_time=None, end_time=None):
        output = list(self.mote_output)
        if start_time is not None:
            output = [v for v in output if v.time >= start_time]
        if end_time is not None:
            output = [v for v in output if v.time <= end_time]
        if regex:
            p = re.compile(regex)
            output = [v for v in output if p.match(v.message)]
        return output

    def add_mote(self, mote_id, time):
        if mote_id in self.motes:
            return self.motes[mote_id]
        mote = Mote(mote_id, time)
        self.motes[mote_id] = mote
        return mote

    def get_mote(self, mote_id):
        return self.motes[mote_id] if mote_id in self.motes else None

    def print_summary(self):
        print(f"Data Traces from {self.data_trace_name}")
        print(f"  {len(self.motes)} motes, {len(self.events)} events, "
              f"{len(self.mote_output)} log outputs, {len(self.transmissions)} radio transmissions.")
        print()
        data = list(map(lambda e: [e.time, e.event_type, e.description], self.events))
        columns = ['Time', 'Event', 'Description']
        print(format_pretty_table(data, columns))
        data = list(map(lambda e: [e.mote_id, e.address, len(e.output), len(e.transmissions)], self.motes.values()))
        data.sort(key=lambda d: d[1])
        columns = ['Mote', 'Address', 'Log Outputs', 'Transmissions']
        print(format_pretty_table(data, columns))


def main(parser=None):
    if not parser:
        parser = argparse.ArgumentParser()
    parser.add_argument('-s', action='store_true', dest='summary', default=False)
    parser.add_argument('input')
    try:
        args = parser.parse_args(sys.argv[1:])
    except Exception as e:
        sys.exit(f"Illegal arguments: {str(e)}")
    try:
        trace = CoojaTrace(args.input)
        if args.summary:
            trace.print_summary()
        return trace
    except (OSError, IOError, coojautils.ParseException):
        traceback.print_exc()
        sys.exit(f"Failed to parse Cooja traces: {args.input}")


if __name__ == '__main__':
    main()
