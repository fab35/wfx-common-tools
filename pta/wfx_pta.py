#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set sw=4 expandtab:
#
# Created: 2019-08-06
# Main authors:
#     - Marc Dorval <marc.dorval@silabs.com>
#
# Copyright (c) 2019, Silicon Laboratories
# See license terms contained in COPYING file
#

# Use wfx_pta_data to prepare PTA bytes from input parameters
# then send them to the target

# TODO:
# * Check int vs str + Add robust str processing (remove case-sensitive in wfx_pta_data?)
# * Check ActiveLevel effect in wfx_pta_data
# * Extend the list of possible values for priority: Add 0xYYYY capability
# * Clean the code (and remove debug / comments...)
# * Note: 
#   (1) settings must be defined BEFORE activating PTA (i.e. order: wfx_driver_reload -> settings -> state ON)
#   (2) potential shell script to simplify call + properly set envt/paths (ex: call from anywhere a simple "wfx_pta_state ON")

from __future__ import print_function

# If you modify this file, please don't forget to increment version number.
__version__ = "0.1.1"

import sys
import time
from wfx_pta_data import *

MAIN_TEST_MODE = not (__name__ == '__main__') #0
DEBUG_FP = 0

if MAIN_TEST_MODE>0:
  sys.path.append('../connection')
  import wfx_connection as wfx_cnx

HI_STATUS_SUCCESS = '0'
HI_STATUS_FAILURE = '1'
HI_INVALID_PARAMETER = '2'
HI_ERROR_UNSUPPORTED_MSG_ID = '4'

class WfxPtaTarget(object):

    def __init__(self, nickname, **kwargs):
        self.nickname = nickname
        self.pta_data = None
        self.pta_mode = 'quiet'
        self.link = None
        # Added connect={True,False} option (rather redundant verif), with default=True or False?
        if 'connect' in kwargs:
            self.connect = True #kwargs['connect']
        else:
            self.connect = False

        if 'host' in kwargs or nickname or self.connect:
            sys.path.append('../connection')
            import wfx_connection as wfx_cnx #from wfx_connection import *

        if 'host' in kwargs:
            host = kwargs['host']
            port = kwargs['port'] if 'port' in kwargs else 22
            user = kwargs['user'] if 'user' in kwargs else 'root'
            print('%s: Configuring a SSH connection to host %s for user %s (port %d)' % (nickname, host, user, port))
            password = kwargs['password'] if 'password' in kwargs else None
            self.link = wfx_cnx.Ssh(nickname, host=host, user=user, port=port, password=password)

        if not self.link:
            if 'port' in kwargs:
                port = kwargs['port']
                print('%s: Configuring a UART connection using %s' % (nickname, port))
                self.link = wfx_cnx.Uart(nickname, port=port)
                if self.link is None:
                    if port in wfx_cnx.uarts():
                        raise Exception(port + ' is detected but is not available. Check for other applications using ' + port)

        if not self.link:
            if not kwargs:
                print('%s: Configuring a Direct connection' % nickname)
                self.link = wfx_cnx.Direct(nickname)

    def write(self, text):
        if self.link is not None:
            #self.link.write(text.encode('ascii'))
            self.link.write(text)

    def read(self):
        if self.link is not None:
            return self.link.read()
        else:
            return ''

    def run(self, cmd, wait_ms=0):
        self.write(cmd)
        time.sleep(wait_ms/1000.0)
        return self.read()

    def pta_help(self):
        pta = WfxPtaData()
        pta.set_args('--help')
        return pta.data()

    def _prepare_pta_data(self, args_text, mode):
        pta = WfxPtaData(mode)
        pta.set_args(args_text)
        self.pta_data = pta.data()

    def settings(self, options, mode='quiet'):
        return self.send_pta('settings', options, mode)

    def priority(self, options, mode='quiet'):
        return self.send_pta('priority', options, mode)

    def state(self, options, mode='quiet'):
        return self.send_pta('state', options, mode)

    def send_pta(self, command, options, mode='quiet'):
        self._prepare_pta_data(command + ' ' + options, mode)
        if self.pta_data is not None and self.connect:
            send_result = self.link.run(r'wfx_exec wfx_hif_send_msg "' + self.pta_data + r'"')
            if send_result == HI_STATUS_SUCCESS:
                return 'HI_STATUS_SUCCESS'
            else:
                if send_result == HI_STATUS_FAILURE:
                    return 'HI_STATUS_FAILURE'
                elif send_result == HI_INVALID_PARAMETER:
                    return 'HI_INVALID_PARAMETER'
                elif send_result == HI_ERROR_UNSUPPORTED_MSG_ID:
                    return 'HI_ERROR_UNSUPPORTED_MSG_ID'
                else:
                    return 'unknown_error_sending PTA data: ' + str(send_result) + ' (' + str(type(send_result)) + ')'
        else:
            return "Error applying " + command + " '" + options + "'"

    def selftest(self, mode='verbose'):
        stored_trace = self.link.trace
        self.link.trace = True
        print('settings result: ' + self.settings('--Config 3W_NOT_COMBINED_BLE', mode=mode))
        print('priority result: ' + self.priority('--PriorityMode BALANCED', mode=mode))
        print('state    result: ' + self.state('--State OFF', mode=mode))
        self.link.trace = stored_trace


if __name__ == '__main__':

    if MAIN_TEST_MODE == 1:
        print('Main Test: You are using a ', sys.platform, 'platform')
        print(wfx_cnx.uarts())
        print(wfx_cnx.networks())

        #eth = WfxPtaTarget('Pi203', host='pi203', user='pi', port=22, password='default_password')
        eth = WfxPtaTarget('RPIM', host='rns-fullefr-master', user='pi', port=2202, password='whifer', connect=True)
        #uart = WfxPtaTarget('OutSerial', port='COM8') #, connect=True
        me = WfxPtaTarget('ThisPC') #, connect=True
        me.link.trace = False
        print(me.run('dir wfx_*.py'))

        dut = eth
        #print(dut.pta_help())
        print(dut.run('uname -a'))
        dut.link.trace = True

        print(dut.settings('--Config 3W_NOT_COMBINED_BLE'))
        print(dut.settings('--Config 3W_NOT_COMBINED_BLE --FirstSlotTime 123', mode='verbose'))
        print(dut.priority('--PriorityMode BALANCED'))
        print(dut.state('--State OFF'))

    elif MAIN_TEST_MODE == 2:
        print('Main CommandLine: You are using a ', sys.platform, 'platform')
        dut = WfxPtaTarget('Local')
        if 'verbose' in sys.argv:
            dut.trace = True
            dut.link.trace = True
            sys.argv.remove('verbose')
            mode = 'verbose'
        else:
            mode = 'quiet'
        sys.exit(dut.send_pta(sys.argv[1], ' '.join(sys.argv[2:]), mode))

    else: #MAIN_TEST_MODE == 0
      def parse_cmdline_(args=sys.argv[1:]):
        # Potential preprocessing of args  

        # Define parser
        parser = argparse.ArgumentParser(description="""Generates a Bytes-frame that can be sent to HIF to configure PTA options. \r\n\
          Optionally calls the wfx_exec(HIF) to send this stream on the current device.  \r\n\
          Use cases: \r\n \
           * %(prog)s state {ON,OFF}.                                                . \r\n \
           * %(prog)s priority {COEX_MAXIMIZED,COEX_HIGH,BALANCED,WLAN_HIGH,WLAN_MAXIMIZED,0xYYYY} where YYYY is an hexa value.                 . \r\n \
           * %(prog)s settings {3W_BLE,3W_NOT_COMBINED_ZIGBEE,3W_COMBINED_ZIGBEE} [options], w/ options described appending --help. """) 
           #usage="%(prog)s [command [options]]"), prefix_chars='-', allow_abbrev=False
        # Parser arguments: Optional
        parser.add_argument('--version',       action='version',   version='%(prog)s {version}'.format(version=__version__))
        parser.add_argument("-m",              dest="mode", default="QUIET", choices=['QUIET','VERBOSE'], help="Specify output mode (debug display): QUIET or VERBOSE") #"--mode"
        parser.add_argument("-v", "--verbose", dest="mode", action="store_const", const="VERBOSE", help="Shortcut for --mode=VERBOSE")
        parser.add_argument("-x",              dest="exeh", action="store_true", help="Flag to run the command on the current device, using wfx_exec")
        #parser.add_argument("-S", "--settings", dest="cmd", action='append',            help="xxx")
        #parser.add_argument("-O", "--state",    dest="cmd", action='append',    choices=['ON', 'OFF'],  help="PTA State ON or OFF xxx")
        #parser.add_argument("-P", "--priority", dest="cmd", action='append', choices=['x', 'y'],    help="xxx")
        # Parser arguments: Mandatory
        parser.add_argument("command", action='store', metavar="command", choices=['STATE','PRIORITY','SETTINGS'], type=str.upper, help="Command among {STATE,PRIORITY,SETTINGS}") # ARGUMENT1 ,action="append", 
        #parser.add_argument("value",   action='store', nargs='+') # ARGUMENT2 ,action="append", nargs=argparse.REMAINDER
        parser.add_argument("value",   action='store', type=str.upper, help="Value depending on the command")             # ARGUMENT3
        #parser.add_argument("options", action='store', type=str.upper, nargs='*', help="optional arguments for the settings command: ...")  # ARGUMENT4... ,action="append", nargs=argparse.REMAINDER
        parser.add_argument("options", action='store', type=str, nargs=argparse.REMAINDER, help="Optional arguments for the settings command: ...")  # ARGUMENT4... ,action="append", nargs=argparse.REMAINDER
        # Apply Parser
        ret_args = parser.parse_args(args) #, namespace=apta #.upper() #print(apta)
        return ret_args #vars(ret_args)

      def main(argp):
        res2 = None
        restxt = ""
        status = 0  
        mode = argp["mode"] #argp.mode
        if mode == "VERBOSE": print("argp =",argp)
        if DEBUG_FP: print("(2) mode =",mode)
        pta  = WfxPtaData(mode) #pta  = WfxPtaData() #
        #cmd  = argp.cmd if argp.cmd else "" #"state"
        cmd  = argp["command"] if argp["command"] else "" 
        if DEBUG_FP: print("(2) cmd  =",cmd)
        # You can define your simplification mapping here if there are mandatory+redundant arguments...
        if   cmd.upper() == "STATE":    header='state --State '
        elif cmd.upper() == "PRIORITY": header='priority --PriorityMode '
        elif cmd.upper() == "SETTINGS": header='settings --Config '
        else :                        header=''
        value   = argp["value"]   if argp["value"]   else "" # or "_" if we want the list of possible values 
        options = argp["options"] if argp["options"] else "" 
        #args_text = header + ''.join(str(cmd)) # options #
        args_text = header + ''.join(str(value)) #.join(str(options)) # options #
        if DEBUG_FP: print("(2) header =",header)
        if DEBUG_FP: print("(2) value =",value)
        if DEBUG_FP: print("(2) options =",options)
        #print(type(options))
        #print((str(options)))
        #print(''.join(str(options)))
        if options:
          args_opts = " ".join(options)
        else:
          args_opts = ""
        args_alls = (args_text + ' ' + args_opts).strip() # TODO: should equal args_text if not in command "settings"
        if DEBUG_FP: print("(2) args_text =",args_text)
        if DEBUG_FP: print("(2) args_opts =",args_opts)
        if DEBUG_FP: print("(2) args_alls =",args_alls)
        if args_alls: pta.set_args(args_alls)
        # else: #TODO
        pta_data = pta.data()
        #if DEBUG_FP: print("(2) output data bytes='%s'" % str(pta_data))
        if DEBUG_FP: print("(2) args_alls =",args_alls)
        # Optional execution through HIF ("-x" option)
        exeh = argp["exeh"] 
        if exeh: 
          import subprocess #import os
          if (mode == "VERBOSE"): 
              #print("Data = "+str(pta_data))      
              print("Sending the frame to the device (-x) ...")
          send_result = None #send_result = os.system(r'wfx_exec wfx_hif_send_msg "' + pta_data + r'"')
          try: # depending on versions of Python and Libs...
            #send_result = subprocess.call(r'wfx_exec wfx_hif_send_msg "' + pta_data + r'"', shell=True, timeout=15) # or Popen(shlex.split(cmd...))
            send_result = subprocess.run(r'wfx_exec wfx_hif_send_msg "' + pta_data + r'"', shell=True, timeout=15, capture_output=True) # or Popen(shlex.split(cmd...))
            # TODO: Check there are no pb of returned value != displayed from wfx_exec 
            # TODO: ensure local exec OK + post-process the returned send_result... + try/catch exceptions
            #res1  = send_result.returncode
            res2  = int(str(send_result.stdout.decode('ascii'))) #'utf-8'
            restxt = str(res2)
            #if (mode == "VERBOSE"): print(restxt)
            if res2 < 0:
              print("Execution was terminated by signal", -res2, file=sys.stderr)
            else:
              pass #if (mode == "VERBOSE"): print("Execution returned", res2, file=sys.stderr)
          #except TimeoutExpired as e: #TODO
          except OSError as e:
              print("Execution failed:", e, file=sys.stderr)    
          except Exception as e: #TODO         
              print("Execution exception:", e, file=sys.stderr)       
          if   restxt == HI_STATUS_SUCCESS:           status = 'HI_STATUS_SUCCESS (0)' # +str(pta_data)
          elif restxt == HI_STATUS_FAILURE:           status = 'HI_STATUS_FAILURE (1)'
          elif restxt == HI_INVALID_PARAMETER:        status = 'HI_INVALID_PARAMETER (2)'
          elif restxt == HI_ERROR_UNSUPPORTED_MSG_ID: status = 'HI_ERROR_UNSUPPORTED_MSG_ID (4)'
          else:                                       status = 'Unknown_error_sending PTA data: ' + str(send_result) + ' (' + str(type(send_result)) + ')'
          if (mode == "VERBOSE") or (restxt != HI_STATUS_SUCCESS): 
              print("Sent = " + str(pta_data))
              print("Status = " + str(status))
        else: 
            if (mode == "VERBOSE"): print("No signal sent.")
            print("Data = "+str(pta_data))      
        return res2 #status #pta_data

      if 1: #__name__ == '__main__':
        if sys.version_info < (3, 0):
            sys.stderr.write("This tools was developed for Python 3 and was not tested with Python 2.x\n")
        #options = ' '.join(sys.argv[1:]) #parse_cmdline()
        argp = parse_cmdline_()
        if DEBUG_FP: print("(1) options =", argp)
        #sys.exit(main(options))
        sys.exit(main(vars(argp)))
