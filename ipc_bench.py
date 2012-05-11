#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Accumulates data produced by ipc-bench.

@author: Nicola Coretti
@contact: nico.coretti@gmail.com
@version: 0.1.0
'''
import sys
import os
import argparse
import platform
import subprocess
import datetime
import shutil
import zipfile

GNUPLOT_TEMPLATE = """
# output file and format
set output 'ipc_performance_test.png'
set terminal png

# title
set title 'IPC-Performance Test'

# axis and grid
set xlabel 'Message size in Bytes'
set xrange [0:8192]
set xtic out nomirror rotate 1 1024 scale 1,0.5
set ylabel 'Throughput in Mbit/s'
set grid ytics
set border 3
set yrange [0:6000]

# legend
set key outside bottom center box title 'IPC-Methods'

# plot
plot {0}
"""


class Info(object):
    
    def __init__(self, info_file):
        self._info = self._create_info(info_file)

    def _create_info(self, path):
        infos = {}
        file = None
        try:
            file = open(path, "r")
            for line in file:
                line_parts = line.split(":")
                key = line_parts[0].strip()
                value = "".join(line_parts[1:]).strip()
                infos[key] = value
        except IOError as ex:
            # TODO: Exception handling
            raise
        finally: 
            if file: file.close() 
            
        return infos
    
    def __getattr__(self, name):
        try:
            attr_name = name.replace("_", " ")
            attr = self._info[attr_name]
        except KeyError as ex:
            raise AttributeError("Unkown attribute")
        
        return attr

class CpuInfo(Info):
    """
    This class provides various information about the CPU of the current system.
    """
    
    def __init__(self):
        super(CpuInfo, self).__init__("/proc/cpuinfo")


class MemInfo(Info):
    """
    This class provides various information about the CPU of the current system.
    """
       
    def __init__(self):
        super(MemInfo, self).__init__("/proc/meminfo")
    
    
class TestEnviromentInfo(object):
    """
    This class provides various information about the system.
    """
    
    def __init__(self):
        cpuinfo = CpuInfo()
        meminfo = MemInfo()
        self.os = platform.platform()
        self.cpu_name = cpuinfo.model_name
        self.cpu_cache_size = cpuinfo.cache_size
        self.system_memory = meminfo.MemTotal

    def __str__(self):
        str  = "OS: {os}\n"
        str += "CPU-Name: {cpu_name}\n" 
        str += "CPU-Cache: {cpu_cache}\n"
        str += "System-Memeory: {memory}"
        str = str.format(os=self.os, cpu_name=self.cpu_name, 
                         cpu_cache=self.cpu_cache_size, 
                         memory=self.system_memory)
        
        return str
        
        
class IpcTest(object):
    
    def __init__(self, programm):
        self.programm = programm
        
        
    def extract_value(self, str):
        parts = str.strip().split(" ")
        value = parts[0].strip()
        value = int(value)
        
        return value
    

    def run_test(self, message_size, message_count):
        """
        Runs the ipc test.
        
        @param message_size: in bytes.
        @param message_count: amount of messages which will be sent.
        
        @return: A test result dictionary.
        The test result dictionary contains 4 key value pairs:
            Key                       Description
            message_size              Size of the messages for this test.  
            message_count             Amount of messages sent in this test.
            avg_thr_msgs              Avarage performance in Messages/s.
            avg_thr_mbs               Avarage performance in Mb/s.
        """
        cmd = [self.programm, str(message_size), str(message_count)]
        self.cmd_obj = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        test_result = {}
        for line in self.cmd_obj.stdout:
            line_parts = line.split(":")
            key = line_parts[0]
            if key == "message size":
                test_result["message_size"] = self.extract_value(line_parts[1])
            elif key == "message count":
                test_result["message_count"] = self.extract_value(line_parts[1])
            elif key == "average throughput":
                value = line_parts[1].rstrip()
                if value.endswith("msg/s"):
                    test_result["avg_thr_msgs"] = self.extract_value(line_parts[1])
                elif value.endswith("Mb/s"):
                    test_result["avg_thr_mbs"] = self.extract_value(line_parts[1])
                else: 
                    raise Exception("Unknown Data")
            else:
                raise Exception("Unknown Data")
            
        return test_result
    
    
    def run_tests(self, message_size, message_count, test_count):
        test_results = []
        for i in range(1, test_count + 1):
            test_results.append(self.run_test(message_size, message_count))
        test_results = self.accumulate_test_data(test_results, message_size, 
                                                 message_count, test_count)
        
        return test_results
    
    
    def accumulate_test_data(self, test_results, message_size, message_count, test_count):
        results = {}
        avg_thr_msgs = [v for test in test_results for k,v in test.items() if k == "avg_thr_msgs"]
        avg_thr_mbs  = [v for test in test_results for k,v in test.items() if k == "avg_thr_mbs"]
        
        results["avg_thr_msgs"] = (sum(avg_thr_msgs) / len(avg_thr_msgs), "Msg/s")
        results["avg_thr_mbs"] =  (sum(avg_thr_mbs) / len(avg_thr_mbs), "Mb/s")
        results["message_size"] = (message_size, "Byte")
        results["message_count"] = (message_count, "Messages") 
        results["test_count"] = (test_count, "Tests")
        
        return results


def pretty_print_results(test_data):
    """
    Pretty prints test results to stdout.
    """
    print("=" * 80)
    test_env_info = TestEnviromentInfo()
    print(test_env_info)
    print("=" * 80)
    for ipc_mehtod,test_data in test_data.items():
        print("IPC-Method: {0}".format(ipc_mehtod))
        info = "Tests: {0}, Messages sent for each test: {1}, Message size: {2} Byte"
        info = info.format(test_data["test_count"][0], 
                           test_data["message_count"][0], 
                           test_data["message_size"][0])
        print(info)
        print("Average Throughput: {0} Msg/s".format(test_data["avg_thr_msgs"][0]))
        print("Average Throughput: {0} Mb/s".format(test_data["avg_thr_mbs"][0]))
        print("-" * 80)
        

def run_tests(ipc_method, message_size):
    """
    Check whether the ipc tests for an specific method can be run 
    with the specified message size.
    
    @param ipc_method: name of the ipc method. 
    @type ipc_method: string (pipe, named_pipe, unix_socket, tcp_socket, message_queue)
    
    @param message_size: which shall be used for the specified ipc method.
    @type message_size: int
    
    @return: True if the ipc method can run with the specified message size,
             otherwise False.
    """
    can_run_tests = True
    # Message queues only supporting a max message size of 8192 Bytes
    if (message_size > 8192) and (ipc_method == 'message_queue'):
        can_run_tests = False
    # Got an error when used a message size > 16000 Byte for the unix socket
    if (message_size > 16000) and (ipc_method == 'unix_socket'):
        can_run_tests = False
    
    return can_run_tests


def ipc_bench(ipc_tests, message_count, test_count):
    message_sizes = [8, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16000, 32768, 65536]
    test_results = {}
    for size in message_sizes:
        results = {}
        for ipc_method in ipc_tests:
            msg = "Running {0:<30} messsage size [{1} Bytes]"
            msg = msg.format(ipc_method + "-tests", size)
            print(msg)

            if run_tests(ipc_method, size):
                test_data = ipc_tests[ipc_method].run_tests(size, message_count, test_count)
                data = {"throughput": test_data["avg_thr_mbs"][0], 
                        "unit": test_data["avg_thr_mbs"][1]}
                results[ipc_method] = data
        test_results[size] = results
    
    return test_results


def create_dat_files(ipc_tests, test_results, dst_dir):
    """
    Creates .dat files for all the test_results.
    
    @param ipc_tests: list of ipc tests which was used to created the data.
    @param test_results: dictionary containing all test results.
    @param dst_dir: directory where the .dat-files shall be stored.
    
    @return: a list of paths to all dat files which where created.
    @rtype: list of strings. e.g. ["path1", "path2", ... ]
    """
    dat_files = {}
    for  ipc_method in ipc_tests:
        filename = "{0}.dat".format(ipc_method)
        filename = os.path.join(dst_dir, filename) 
        out_file = None
        try:
            out_file = open(filename, "w")
            line = "# message_size (in Bytes) throughput (in Mbit/s)\n"
            out_file.write(line)            
            for message_size in sorted(test_results.keys()):
                throughput = None
                try:
                    throughput = test_results[message_size][ipc_method]["throughput"]
                except KeyError as ex:
                    throughput = "-"
                line = "{0}\t{1}\n".format(message_size, throughput)
                out_file.write(line)
            dat_files[ipc_method] = ipc_method + ".dat"
        except IOError as ex:
            raise
        finally:
            if out_file: out_file.close()
     
    return dat_files    


def create_gnu_plot_file(dat_files, dst_dir):
    plot_str = ""
    for dat_file_key in dat_files.keys():
        line = "'{0}' using 1:2 title '{1}' with lines,\\\n"
        line = line.format(dat_files[dat_file_key], dat_file_key)
        plot_str += line
    plot_str = GNUPLOT_TEMPLATE.format(plot_str[0:-3])
    
    out_file = None
    try:
        filename = os.path.join(dst_dir, "ipc-test.gnu")
        out_file = open(filename, "w")
        out_file.write(plot_str)
    except IOError as ex:
        raise
    finally:
        if out_file: out_file.close()
        

def create_args_parser():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('--message-size', type=int, default=1024, metavar='N',
                   help='size of the test messages which will be transfered via ipc.')
    args_parser.add_argument('--message-count', type=int, default=10000, metavar='N',
                   help='amount of messages which will be transfered via ipc for each test.')
    args_parser.add_argument('--test-count', type=int, default=1, metavar='N',
                   help='amount of test which shall be run.')
    args_parser.add_argument('--ipc-bench',  metavar='NAME', 
                   help='if supplied multiple test will run and gnuplot output is produced.')
    args_parser.add_argument('--all', default=False, action='store_true', 
                             help= 'enables all ipc performance tests')
    args_parser.add_argument('--msgq', default=False, action='store_true',
                             help='enables ipc performance tests for message queues.')
    args_parser.add_argument('--pipe', default=False, action='store_true',
                             help='enables ipc performance tests for pipe.')
    args_parser.add_argument('--named-pipe', default=False, action='store_true',
                             help='enables ipc performance tests for named pipe.')
    args_parser.add_argument('--unix-sock', default=False, action='store_true',
                             help='enables ipc performance tests for unix socket.')
    args_parser.add_argument('--tcp-sock', default=False, action='store_true',
                             help='enables ipc performance tests for tcp socket.')
    
    return args_parser


if __name__ == '__main__':

    parser = create_args_parser()
    args = parser.parse_args(sys.argv[1:])
    
    test_data = {}
    test_count = args.test_count
    message_size = args.message_size
    message_count = args.message_count
    
    pipe_thr = IpcTest("./pipe_thr")
    named_pipe_thr = IpcTest("./named_pipe_thr")
    unix_thr = IpcTest("./unix_thr")
    msgq_thr = IpcTest("./msgq_thr")
    tcp_thr  = IpcTest("./tcp_thr")
    
    ipc_tests = {}
    if args.all:
        ipc_tests["pipe"] = pipe_thr
        ipc_tests["named_pipe"] = named_pipe_thr
        ipc_tests["unix_socket"] = unix_thr
        ipc_tests["message_queue"] = msgq_thr
        ipc_tests["tcp_socket"] = tcp_thr
    else:
        if args.msgq: ipc_tests["message_queue"] = msgq_thr
        if args.pipe: ipc_tests["pipe"] = pipe_thr
        if args.named_pipe: ipc_tests["named_pipe"] = named_pipe_thr
        if args.unix_sock: ipc_tests["unix_socket"] = unix_thr
        if args.tcp_sock: ipc_tests["tcp_socket"] = tcp_thr
    
    if args.ipc_bench:
        # The message size is ignored by the ipc_bench test
        test_results = ipc_bench(ipc_tests, message_count, test_count)
        try:
            os.mkdir(args.ipc_bench)
        except OSError as ex:
           if ex.errno == 17:
               shutil.copytree(args.ipc_bench, args.ipc_bench + datetime.datetime.now().isoformat() + ".bak")
               shutil.rmtree(args.ipc_bench)
               os.mkdir(args.ipc_bench)
    
        dat_files = create_dat_files(ipc_tests, test_results, args.ipc_bench)
        create_gnu_plot_file(dat_files, args.ipc_bench)
        result_file = None
        try:
            subprocess.call(["tar", "-czf", args.ipc_bench + ".tar.gz", args.ipc_bench])
            shutil.rmtree(args.ipc_bench)
            result_file = args.ipc_bench + ".tar.gz"
        except Exception as ex:
            raise
        
        print("\nAll tests finished, results => ** {0} **".format(result_file))
        sys.exit(0)
    
    else:    
        for ipc_method in ipc_tests:
            test_data[ipc_method] = ipc_tests[ipc_method].run_tests(message_size, message_count, test_count)
        pretty_print_results(test_data)
        sys.exit(0)

    



    
    

