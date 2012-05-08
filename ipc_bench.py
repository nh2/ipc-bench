#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
Accumulates data produced by ipc-bench.

@author: Nicola Coretti
@contact: nico.coretti@gmail.com
@version: 0.1.0
'''
import sys
import argparse
import platform
import subprocess
import datetime


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
        
        
def create_args_parser():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('message_size', metavar='<message_size>', type=int, 
                   help='size of the test messages which will be transfered via ipc.')
    args_parser.add_argument('message_count', metavar='<message count>', type=int, 
                   help='amount of messages which will be transfered via ipc for each test.')
    args_parser.add_argument('test_count', metavar='<test count>', type=int, 
                   help='amount of test which shall be run.')
    args_parser.add_argument('--ipc-test',  action='store_true', 
                   help='if supplied a cvs file with the accumulated data will be produced.')
    
    return args_parser


def pretty_print_results(test_data):
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
        

def create_csv_file(test_data, test_count):
    message_count = 5000
    message_sizes = [8, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16000, 32768, 65536]
    test_results = {}
    for size in message_sizes:
        print("Running test for messsage size: [{0} Bytes]".format(size))
        results = {}
        test_data = pipe_thr.run_tests(size, message_count, test_count)
        data = {"throughput": test_data["avg_thr_mbs"][0], 
                "unit": test_data["avg_thr_mbs"][1]}
        results["pipe"] = data
        test_data = named_pipe_thr.run_tests(size, message_count, test_count)
        data = {"ipc-method": "named_pipe", "throughput": test_data["avg_thr_mbs"][0], 
                "unit": test_data["avg_thr_mbs"][1]}
        results["named_pipe"] = data
        test_data = tcp_thr.run_tests(size, message_count, test_count) 
        data = {"throughput": test_data["avg_thr_mbs"][0], 
                "unit": test_data["avg_thr_mbs"][1]}
        results["tcp_socket"] = data
        # Message queues only supporting a max message size of 8192 Bytes
        if size <= 8192:
            test_data = msgq_thr.run_tests(size, message_count, test_count)
            data = {"throughput": test_data["avg_thr_mbs"][0], 
                    "unit": test_data["avg_thr_mbs"][1]}
            results["message_queue"] = data
        if size <= 16000:
            test_data = unix_thr.run_tests(size, message_count, test_count)
            data = {"throughput": test_data["avg_thr_mbs"][0], 
                    "unit": test_data["avg_thr_mbs"][1]}
            results["unix_socket"] = data
        test_results[size] = results
        print("Done")
        
    filename = "ipc_bench_{0}".format(datetime.datetime.now().isoformat())
    f = None
    try:
        ipc_methods = ["pipe", "named_pipe", "unix_socket", "tcp_socket", "message_queue"]
        f = open(filename, "w")
        for ipc_method in ipc_methods:
            f.write(ipc_method + "\n")
            f.write(accumulate_ipc_data(test_results, ipc_method))
            f.write("-" * 80 + "\n")
    except (IOError, KeyError) as ex:
        print(test_results)
        raise
    finally:
        if f: f.close()
        
        
def accumulate_ipc_data(test_data, ipc_method):
    str_msg_size = "message size: "
    str_mbs_thr = "throughput: "
    for key in sorted(test_data.keys()):
        str_msg_size += str(key) + ","
        try:
            str_mbs_thr += str(test_data[key][ipc_method]["throughput"]) + ","
        except KeyError as ex:
            str_mbs_thr += "-,"
            
    return str_msg_size + "\n" + str_mbs_thr + "\n"


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
    
    
    if args.ipc_test:
        create_csv_file(test_data, test_count)
        sys.exit(0)
    else:    
        test_data["pipe"] = pipe_thr.run_tests(message_size, message_count, test_count)
        test_data["named_pipe"] = named_pipe_thr.run_tests(message_size, message_count, test_count)
        test_data["unix_socket"] = unix_thr.run_tests(message_size, message_count, test_count)
        test_data["message_queue"] = msgq_thr.run_tests(message_size, message_count, test_count)
        test_data["tcp_socket"] = tcp_thr.run_tests(message_size, message_count, test_count)
        pretty_print_results(test_data)
        sys.exit(0)

    



    

    
