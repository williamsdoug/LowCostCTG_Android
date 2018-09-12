# coding: utf-8

#
#  Copyright Douglas Williams, 2018
#  All Rights Reserved
#

#
#  TocoPatch Supporting Library
#
# Includes:
#   - HeartyPatch_TCP_Parser: Wire format Parser
#   - HeartyPatch_Listener: TCP Listener routine
#   - HeartyPatch_Emulator: Listener Emulator (returns data from recording file performing similar callbacks)
#   - parseTocopatchRecording:  Basic recording file parsing
#   - parseHeader: Parses and returns recording metadata
#   - getTocopatchData: Returns data after masic processing, including timescale interpolation
#

import socket
import sys
import os
import threading
import struct

import numpy as np
import time

from CONFIG import TOCO_ENABLE_EMULATE, TOCO_EMULATION_RECORDING, TOCO_EMULATION_DELAY


def ping_tocopatch(host, port=4567, connection_timeout=30, read_timeout=60):
    if TOCO_ENABLE_EMULATE:
        return True

    try:
        soc = socket.create_connection((host, port), timeout=connection_timeout)
    except Exception:
        try:
            soc.close()
        except Exception:
            pass
        try:
            soc = socket.create_connection((host, port), timeout=connection_timeout)
        except Exception:
            return False

    # read sample packet
    soc.settimeout(read_timeout)
    try:
        txt = soc.recv(16 * 1024)  # discard any initial results
        soc.close()
    except Exception:
        soc.close()
        return False

    return True


class HeartyPatch_TCP_Parser:
    # Packet Validation
    CESState_Init = 0
    CESState_SOF1_Found = 1
    CESState_SOF2_Found = 2
    CESState_PktLen_Found = 3

    # CES CMD IF Packet Format
    CES_CMDIF_PKT_START_1 = 0x0A
    CES_CMDIF_PKT_START_2 = 0xFA
    CES_CMDIF_PKT_STOP = 0x0B

    # CES CMD IF Packet Indices
    CES_CMDIF_IND_LEN = 2
    CES_CMDIF_IND_LEN_MSB = 3
    CES_CMDIF_IND_PKTTYPE = 4
    CES_CMDIF_PKT_OVERHEAD = 5
    CES_CMDIF_PKT_DATA = CES_CMDIF_PKT_OVERHEAD


    ces_pkt_seq_bytes   = 4  # Buffer for Sequence ID
    ces_pkt_ts_bytes   = 8  # Buffer for Timestamp
    ces_pkt_rtor_bytes = 4  # R-R Interval Buffer
    ces_pkt_ecg_bytes  = 4  # Field(s) to hold ECG data

    Expected_Type = 3        # new format
    
    min_packet_size = 19
    
    def __init__(self):
        self.state = self.CESState_Init
        self.data = ''
        self.packet_count = 0
        self.bad_packet_count = 0
        self.bytes_skipped = 0
        self.total_bytes = 0
        self.all_seq = []
        self.all_ts = []
        self.all_rtor = []
        self.all_hr = []
        self.all_ecg = []
        self.ecg_per_packet = None
        pass
    
    def add_data(self, new_data):
        self.data += new_data
        self.total_bytes += len(new_data)
    
    
    def process_packets(self):
        while len(self.data) >= self.min_packet_size:
            if self.state == self.CESState_Init:
                if ord(self.data[0]) == self.CES_CMDIF_PKT_START_1:
                    self.state = self.CESState_SOF1_Found
                else:
                    self.data = self.data[1:]    # skip to next byte
                    self.bytes_skipped += 1
                    continue
            elif self.state == self.CESState_SOF1_Found:
                if ord(self.data[1]) == self.CES_CMDIF_PKT_START_2:
                    self.state = self.CESState_SOF2_Found
                else:
                    self.state = self.CESState_Init
                    self.data = self.data[1:]    # start from beginning
                    self.bytes_skipped += 1
                    continue
            elif self.state == self.CESState_SOF2_Found:
                # sanity check header for expected values
                
                pkt_len = 256 * ord(self.data[self.CES_CMDIF_IND_LEN_MSB]) + ord(self.data[self.CES_CMDIF_IND_LEN])
                # Make sure we have a full packet
                if len(self.data) < (self.CES_CMDIF_PKT_OVERHEAD + pkt_len + 2):
                    break


                if (ord(self.data[self.CES_CMDIF_IND_PKTTYPE])  != self.Expected_Type
                    or ord(self.data[self.CES_CMDIF_PKT_OVERHEAD+pkt_len+1]) != self.CES_CMDIF_PKT_STOP):

                    if True:
                        print 'pkt_len', pkt_len
                        print ord(self.data[self.CES_CMDIF_IND_PKTTYPE]), self.Expected_Type,
                        print ord(self.data[self.CES_CMDIF_IND_PKTTYPE])  != self.Expected_Type

                        for j in range(0, self.CES_CMDIF_PKT_OVERHEAD):
                            print format(ord(self.data[j]),'02x'),
                        print

                        for j in range(self.CES_CMDIF_PKT_OVERHEAD, self.CES_CMDIF_PKT_OVERHEAD+pkt_len):
                            print format(ord(self.data[j]),'02x'),
                        print

                        for j in range(self.CES_CMDIF_PKT_OVERHEAD+pkt_len, self.CES_CMDIF_PKT_OVERHEAD+pkt_len+2):
                            print format(ord(self.data[j]),'02x'),
                        print
                        print self.CES_CMDIF_PKT_STOP,
                        print ord(self.data[self.CES_CMDIF_PKT_OVERHEAD+pkt_len+2]) != self.CES_CMDIF_PKT_STOP
                        print

                    # unexpected packet format
                    self.state = self.CESState_Init
                    self.data = self.data[1:]    # start from beginning
                    self.bytes_skipped += 1
                    self.bad_packet_count += 1
                    continue

                # Parse Payload
                payload = self.data[self.CES_CMDIF_PKT_OVERHEAD:self.CES_CMDIF_PKT_OVERHEAD+pkt_len+1]

                ptr = 0
                # Process Sequence ID
                seq_id = struct.unpack('<I', payload[ptr:ptr+4])[0]
                self.all_seq.append(seq_id)
                ptr += self.ces_pkt_seq_bytes

                # Process Timestamp
                ts_s = struct.unpack('<I', payload[ptr:ptr+4])[0]
                ts_us = struct.unpack('<I', payload[ptr+4:ptr+8])[0]
                timestamp = ts_s + ts_us/1000000.0
                self.all_ts.append(timestamp)
                ptr += self.ces_pkt_ts_bytes

                # Process R-R Interval
                rtor = struct.unpack('<I', payload[ptr:ptr+4])[0]
                self.all_rtor.append(rtor)
                if rtor == 0:
                    self.all_hr.append(0)
                else:
                    self.all_hr.append(60000.0/rtor)

                ptr += self.ces_pkt_rtor_bytes


                assert ptr == 16
                assert pkt_len == (16 + 8 * 4)
                # Process Sequence ID
                count = 0
                while ptr < pkt_len:
                    ecg = struct.unpack('<i', payload[ptr:ptr+4])[0] / 1000.0
                    self.all_ecg.append(ecg)
                    ptr += self.ces_pkt_ecg_bytes
                    count += 1

                if self.ecg_per_packet is None:
                    self.ecg_per_packet = count

                self.packet_count += 1                    
                self.state = self.CESState_Init
                self.data = self.data[self.CES_CMDIF_PKT_OVERHEAD+pkt_len+2:]    # start from beginning


class HeartyPatch_Listener:

    def __init__(self, host='heartypatch.local', port=4567, connection_timeout=30, warmup_sec=30,
                 max_packets=10000, max_seconds=-1, outfile=None,
                 connection_callback=None, update_callback=None, update_interval=50,
                 completion_callback=None):
        self.host = host
        self.port=port
        self.connection_timeout=connection_timeout
        self.connection_callback = connection_callback
        self.update_callback = update_callback
        self.update_interval=update_interval
        self.completion_callback = completion_callback
        self.max_packets = max_packets
        self.max_seconds = max_seconds
        self.warmup_sec=warmup_sec
        self.outfile=outfile

        self.parser = HeartyPatch_TCP_Parser()   # create parser instance
        self.soc = None
        self.tStart = None
        self.tEnd = None
        self.tcp_reads = 0
        self.sample_rate = 128
        self.wasAborted = False

        self.enabled = threading.Event()

        self.output_fd = None
        self.output_ptr = 0


    def get_start_time(self):
        return self.tStart

    def get_sample_rate(self):
        return self.sample_rate


    def collect_data(self):
        self.enabled.set()
        # establish socket connection to heartypatch
        try:
            self.soc = socket.create_connection((self.host, self.port), timeout=self.connection_timeout)
        except Exception:
            try:
                self.soc.close()
            except Exception:
                pass
            try:
                self.soc = socket.create_connection((self.host, self.port), timeout=self.connection_timeout)
            except Exception:
                self.wasAborted = True
                self.enabled.clear()

        if self.enabled.is_set() and self.connection_callback:
            self.connection_callback()

        # discard first set of packets
        try:
            txt = self.soc.recv(16 * 1024)    # discard any initial results
        except Exception:
            self.finish(abort=True)
            return


        self.tStart = time.time()
        last_packet_count = 0
        while self.enabled.is_set():
            try:
                txt = self.soc.recv(16*1024)
            except Exception:
                self.finish(abort=True)
                return

            self.parser.add_data(txt)
            self.parser.process_packets()

            deltaT = time.time() - self.tStart
            if deltaT > 3*60:
                samples = self.parser.packet_count * self.parser.ecg_per_packet
                new_sample_rate = float(samples)/deltaT
                #print 'new_sample_rate:', new_sample_rate
                self.sample_rate = new_sample_rate
            self.tcp_reads += 1
            self.save_data(final=False)

            if self.max_packets > 0 and self.parser.packet_count >= self.max_packets:
                self.enabled.clear()
                break

            if self.max_seconds > 0 and time.time() - self.tStart > self.max_seconds:
                # Exceeded requested duration
                self.enabled.clear()
                break

            if self.update_callback and self.parser.packet_count - last_packet_count >= self.update_interval:
                last_packet_count = self.parser.packet_count
                self.update_callback(self, self.parser.packet_count)

        self.finish()


    def finish(self, abort=False):
        self.tEnd = time.time()
        if self.soc is not None:
            self.soc.close()
        if not abort:
            self.save_data(final=True)
        self.wasAborted = abort
        if self.completion_callback:
            self.completion_callback(self, abort=abort)

    def run(self):
        self.thread = threading.Thread(target=self.collect_data)
        self.thread.start()
        self.wait()

    def go(self):
        self.thread = threading.Thread(target=self.collect_data)
        self.thread.start()


    def stop(self, isCancelled=False):
        if isCancelled:
            self.wasAborted = True
        self.enabled.clear()   # disable execution
        print
        print 'called stop'
        sys.stdout.flush()


    def wait(self):
        while self.thread.isAlive():
            self.thread.join(5)
        return self.wasAborted


    def getStats(self):
        if self.parser.ecg_per_packet is None or self.parser.packet_count == 0:
            return {'packet_count': 0}

        duration = self.tEnd - self.tStart
        packet_count = self.parser.packet_count
        total_bytes = self.parser.total_bytes
        nSamples = len(self.parser.all_ecg)
        packet_rate = float(packet_count)/duration
        sample_rate = float(nSamples) / duration
        bytes_per_packet = total_bytes/float(packet_count)
        bad_packet_count = self.parser.bad_packet_count
        bytes_skipped = self.parser.bytes_skipped
        samples_per_packet = self.parser.ecg_per_packet

        stats = {
            'duration': duration,
            'packet_count': packet_count,
            'total_bytes': total_bytes,
            'nSamples': nSamples,
            'packet_rate': packet_rate,
            'sample_rate': sample_rate,
            'bytes_per_packet': bytes_per_packet,
            'bad_packet_count': bad_packet_count,
            'bytes_skipped': bytes_skipped,
            'tStart': self.tStart,
            'samples_per_packet':samples_per_packet,
        }

        return stats

    def getData(self):
        return self.parser.all_ecg, self.parser.all_ts, self.parser.all_seq


    def save_data(self, final=False, abort=False):
        if not self.outfile:
            return

        if self.parser.ecg_per_packet is None or self.parser.packet_count == 0:
            abort = True
            self.wasAborted = True

        if abort:
            if self.output_fd is not None:
                self.output_fd.close()
            self.output_fd = None
            try:
                os.remove(self.outfile)
                print 'removed file', self.outfile
            except Exception:
                pass
            return True

        if self.output_fd is None:
            try:
                self.output_fd = open(self.outfile,"w")
            except Exception:
                print 'Unable to open file', self.outfile
                self.outfile = None
                return False
            print 'opened file', self.outfile

            # now add header
            self.output_fd.write('# {}   epoch: {}  ecg_per_packet: {}\n'.format(
                time.ctime(self.tStart), self.tStart, self.parser.ecg_per_packet))
            self.output_fd.write('# seqID, timestamp_in_sec, ecg_data\n')
            self.output_ptr = 0

        n = min(len(self.parser.all_ts), len(self.parser.all_seq),
                len(self.parser.all_ecg) // self.parser.ecg_per_packet)

        ecg_ptr = self.output_ptr * self.parser.ecg_per_packet
        while self.output_ptr < n:
            for i in range(self.parser.ecg_per_packet):
                if i == 0:
                    self.output_fd.write('{}, {}, {}\n'.format(self.parser.all_seq[self.output_ptr],
                                                               self.parser.all_ts[self.output_ptr],
                                                               self.parser.all_ecg[ecg_ptr]))
                else:
                    self.output_fd.write('{}, {}, {}\n'.format(-1, -1, self.parser.all_ecg[ecg_ptr]))
                    ecg_ptr += 1
            self.output_ptr += 1

        if final:
            print
            print 'closing file', self.outfile
            self.output_fd.close()
            self.output_fd = None
        return True

#
# Routines for dealing with TocoPatch Recordings
#

def parseHeader(txt, params=[]):
    meta = {}
    tokens = txt.split()
    i = 0
    while i < len(tokens) - 1:
        tok = tokens[i]
        if not tok.endswith(':'):
            i += 1
            continue

        key = tok.split(':')[0]
        if key not in params:
            i += 1
            continue

        # parse value
        try:
            value = int(tokens[i + 1])
        except Exception:
            try:
                value = float(tokens[i + 1])
            except Exception:
                value = None
        meta[key] = value
        i += 1
    return meta


def parseTocopatchRecording(fname, params=['epoch', 'ecg_per_packet']):
    """Basic parsing to TocoPatch trace file"""
    seqID = []
    ts = []
    sig = []
    meta = {}

    with open(fname, 'r') as fd:
        for line in fd:
            if line.startswith('#'):
                # print line
                meta.update(parseHeader(line, params=params))
                continue
            vals = line.split(',')
            seqID.append(int(vals[0]))
            ts.append(float(vals[1]))
            sig.append(float(vals[2]))

    return seqID, ts, sig, meta


def getTocopatchData(fname, interpolateTimescale=True,
                     params=['epoch', 'ecg_per_packet']):
    """Read tocopatch recording, returning results in numpy format
    and performing optional timescale interpolation"""

    seqID, ts, sig, meta = parseTocopatchRecording(fname, params=params)

    seqID = np.array(seqID)
    ts = np.array(ts)
    sig = np.array(sig)

    if interpolateTimescale:
        mask = ts != -1  # find valid timestamps
        x = np.arange(len(ts))
        ts = np.interp(x, x[mask], ts[mask])

    return seqID, ts, sig, meta


class DummyParser:
    def __init__(self):
        self.packet_count = 0
        self.ecg_per_packet = 0
        self.all_ecg = []
        self.all_ts = []
        self.all_seq = []


class HeartyPatch_Emulator(HeartyPatch_Listener):

    def __init__(self, infile=None, delay=1, warmup_sec=3,
                 max_packets=10000, max_seconds=-1, outfile=None,
                 connection_callback=None,
                 update_callback=None, update_interval=50,
                 completion_callback=None, **kwargs):
        self.connection_callback = connection_callback
        self.update_callback = update_callback
        self.update_interval = update_interval
        self.completion_callback = completion_callback
        self.max_packets = max_packets
        self.max_seconds = max_seconds
        self.warmup_sec = warmup_sec

        self.infile = TOCO_EMULATION_RECORDING
        self.outfile = outfile
        self.delay = TOCO_EMULATION_DELAY

        self.tStart = None
        self.tEnd = None
        self.sample_rate = 128
        self.wasAborted = False

        self.enabled = threading.Event()

        self.output_fd = None
        self.output_ptr = 0

        # emulate state of parser
        self.parser = DummyParser()


    def get_start_time(self):
        return self.tStart


    def get_sample_rate(self):
        return self.sample_rate


    def collect_data(self):
        self.enabled.set()
        try:
            (self.in_seqID, self.in_ts, self.in_sig, self.meta) = parseTocopatchRecording(self.infile)
            self.parser.ecg_per_packet = self.meta['ecg_per_packet']
            #self.tStart = self.meta['epoch']

            print 'finished loading data from', self.infile
            print len(self.in_sig), len(self.in_ts), len(self.in_seqID)

        except Exception:
            self.wasAborted = True
            self.enabled.clear()

        if self.enabled.is_set() and self.connection_callback:
            self.connection_callback()

        samples_per_packet = self.parser.ecg_per_packet
        currentPackets = 0
        self.tStart = time.time()
        while self.enabled.is_set():
            if self.delay > 0:
                time.sleep(self.delay)
            else:
                time.sleep(0)

            currentPackets += self.update_interval
            ptr = currentPackets * samples_per_packet
            self.parser.all_ecg = self.in_sig[:ptr]
            self.parser.all_ts = self.in_ts[:ptr:samples_per_packet]
            self.parser.all_seq = self.in_seqID[:ptr:samples_per_packet]
            self.parser.packet_count = len(self.parser.all_seq)

            # if self.tStart is None:
            #     self.tStart = self.parser.all_ts[0]

            #self.save_data(final=False)

            # stop when we run out of data
            if ptr >= len(self.in_sig):
                self.parser.packet_count = len(self.parser.all_seq)
                self.enabled.clear()
                break

            if self.max_packets > 0 and currentPackets >= self.max_packets:
                self.enabled.clear()
                break

            if self.max_seconds > 0 and self.parser.all_ts[-1] - self.tStart > self.max_seconds:
                # Exceeded requested duration
                self.enabled.clear()
                break

            if self.update_callback:
                self.update_callback(self, currentPackets)

        self.finish()

    def finish(self, abort=False):
        self.tEnd = time.time()

        # durationInSec = len(self.parser.all_ts)/self.sample_rate
        # self.tEnd = self.tStart + durationInSec

        # if not abort:
        #     self.save_data(final=True)
        self.wasAborted = abort
        if self.completion_callback:
            self.completion_callback(self, abort=abort)

    # Note:  Incomplete emulation of stats
    def getStats(self):
        duration = self.tEnd - self.tStart
        #return {'packet_count': 0}

        stats = {
            'duration': duration,
            'packet_count': 0,
            # 'total_bytes': total_bytes,
            # 'nSamples': nSamples,
            # 'packet_rate': packet_rate,
            'sample_rate': self.sample_rate,
            # 'bytes_per_packet': bytes_per_packet,
            # 'bad_packet_count': bad_packet_count,
            # 'bytes_skipped': bytes_skipped,
            'tStart': self.tStart,
            #'samples_per_packet': samples_per_packet,
        }

        return stats

