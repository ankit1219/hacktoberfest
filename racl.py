

########################################################################################################################
#
#TOPOLOGY :
# 				  ____________       
#  				 |            |     
# 				 |            |     
#[Ixia]----------|            |----------[Ixia]
#  				 |  UUT1(FX2) |    
#|               |            |
#  				 |            |     
# 				 |____________|     

#  topology requirement :- 1 FX2 switch
#                          2 links to Ixia
#    					   sup-eth0 is monitor
########################################################################################################################



#!/usr/bin/env python

# import the aetest module
from ats import tcl
from ats import aetest
from ats.log.utils import banner
import time
import logging
import os
import sys
import re
import pdb
import json
import pprint
import socket
import struct
import inspect
#import acp_span_lib
#import ctsPortRoutines
import pexpect
#import span_lib
#libs_dir_path = os.path.join(cur_dir_path, 'libs')
import nxos.lib.nxos.util as util
#import nxos.lib.common.topo as topo



from ixiatcl import IxiaTcl
from ixiahlt import IxiaHlt
from ixiangpf import IxiaNgpf
from ixiaerror import IxiaError
from time import sleep

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
global uut1, tgen

global uut1_ixia_intf1, uut1_ixia_intf2
global ixia_uut1_1, ixia_uut1_2

def printDict(obj, nested_level=0, output=sys.stdout):
    spacing = '   '
    if type(obj) == dict:
       print('%s' % ((nested_level) * spacing))
       for k, v in list(obj.items()):
           if hasattr(v, '__iter__'):
               print('%s%s:' % ((nested_level + 1) * spacing, k))
               printDict(v, nested_level + 1)
           else:
               print('%s%s: %s' % ((nested_level + 1) * spacing, k, v))
       print('%s' % (nested_level * spacing))
    elif type(obj) == list:
       print('%s[' % ((nested_level) * spacing))
       for v in obj:
           if hasattr(v, '__iter__'):
               printDict(v, nested_level + 1)
           else:
               print('%s%s' % ((nested_level + 1) * spacing, v))
       print('%s]' % ((nested_level) * spacing))
    else:
       print('%s%s' % (nested_level * spacing, obj))


class ForkedPdb(pdb.Pdb):
    '''A Pdb subclass that may be used
    from a forked multiprocessing child1
    '''
    def interaction(self, *args, **kwargs):
        _stdin = sys.stdin
        try:
            sys.stdin = open('/dev/stdin')
            pdb.Pdb.interaction(self, *args, **kwargs)
        finally:
            sys.stdin = _stdin
################################################################################
####                       COMMON SETUP SECTION                             ####
################################################################################

class common_setup(aetest.CommonSetup):

    @aetest.subsection
    def span_topo_parse(self,testscript,testbed,R1):

        global uut1, tgen 

        global uut1_ixia_intf1, uut1_ixia_intf2
        global ixia_uut1_1, ixia_uut1_2
        global ixia_chassis_ip, ixia_tcl_server, ixia_ixnetwork_tcl_server,ixia_username, ixia_reset_flag
        
        global custom
        global device1
        
        
        uut1 = testbed.devices[R1]
        
        tgen = testbed.devices['ixia']
        testscript.parameters['tgen'] = tgen
        
        tgen_attributes = tgen.connections.hltapi
        ixia_chassis_ip = str(tgen_attributes.ip)
        ixia_tcl_server = tgen_attributes.tcl_server
        ixia_ixnetwork_tcl_server = tgen_attributes.ixnetwork_tcl_server
        ixia_username = tgen_attributes.username
        ixia_reset_flag = tgen_attributes.reset
        
        
        ###  UUT 1 INTERFACES  ####
        uut1_ixia_intf1 = testbed.devices[R1].interfaces['uut1_ixia_intf1']
        uut1_ixia_intf2 = testbed.devices[R1].interfaces['uut1_ixia_intf2']
        #uut1_dest_intf1 = testbed.devices[R1].interfaces['uut1_dest_intf1']

        testscript.parameters['uut1_ixia_intf1'] = uut1_ixia_intf1
        testscript.parameters['uut1_ixia_intf2'] = uut1_ixia_intf2
        #testscript.parameters['uut1_dest_intf1'] = uut1_dest_intf1
        
        testscript.parameters['uut1_ixia_intf1'].name = testscript.parameters['uut1_ixia_intf1'].intf
        testscript.parameters['uut1_ixia_intf2'].name = testscript.parameters['uut1_ixia_intf2'].intf
        #testscript.parameters['uut1_dest_intf1'].name = testscript.parameters['uut1_dest_intf1'].intf
        
        ###  Ixia interfaces  ####
        
        ixia_uut1_1 = testbed.devices['ixia'].interfaces['ixia_uut1_1']
        ixia_uut1_2 = testbed.devices['ixia'].interfaces['ixia_uut1_2']
        
        testscript.parameters['ixia_uut1_1'] = ixia_uut1_1
        testscript.parameters['ixia_uut1_2'] = ixia_uut1_2
        
        testscript.parameters['ixia_uut1_1'].name = testscript.parameters['ixia_uut1_1'].intf
        testscript.parameters['ixia_uut1_2'].name = testscript.parameters['ixia_uut1_2'].intf


        uut1_ixia_intf1 =uut1_ixia_intf1.intf
        uut1_ixia_intf2 =uut1_ixia_intf2.intf
        #uut1_dest_intf1 = uut1_dest_intf1.intf

        ixia_uut1_1 = ixia_uut1_1.intf
        ixia_uut1_2 = ixia_uut1_2.intf

        
        log.info("uut1_ixia_intf1=%s" % uut1_ixia_intf1)
        log.info("uut1_ixia_intf2=%s" % uut1_ixia_intf2)
        #log.info("uut1_dest_intf1=%s" % uut1_dest_intf1)
        log.info("ixia_uut1_1=%s" % ixia_uut1_1)
        log.info("ixia_uut1_2=%s" % ixia_uut1_2)
        
    @aetest.subsection
    def connect_to_devices(self, testscript, testbed, R1):
        
        log.info("\n************ Connecting to Device:%s ************" % uut1.name)
        try:
            uut1.connect()
            log.info("Connection to %s Successful..." % uut1.name)
        except Exception as e:
            log.info("Connection to %s Unsuccessful " \
                        "Exiting error:%s" % (uut1.name, e))
            self.failed(goto=['exit'])
         
    @aetest.subsection     
    def configure_interfaces(self,testscript, testbed):
         """configure required L2 trunk interface on devices"""
                  
         status = l2ptLib.config_L2_interface(uut1,uut1_ixia_intf1,10)
         status = l2ptLib.config_L2_interface(uut1,uut1_ixia_intf2,10)
         
         if status != True:
                 log.error("\nConfiguration Failed!!")
                 self.failed(goto=['exit'])
         self.passed("Configuration was Successful!!")
       
    @aetest.subsection
    def connect_to_ixia(self, testscript, testbed):
       """Connect Ixia and get port handles"""
       #ixia_port_list = [ixia_hdl1, ixia_hdl2]
       ixia_port_list = [ixia_uut1_1, ixia_uut1_2]
       global ixia_
       global ixia_port_1_handle,ixia_port_2_handle
       
       status,port_handle = l2ptLib.connect_ixia(ixia_chassis_ip, ixia_tcl_server, ixia_ixnetwork_tcl_server, \
                                                       ixia_port_list, ixia_reset_flag, ixia_username)
       if status != True:
           log.error("\nFail to Connect Ixia!!")
           self.failed(goto=['exit'])
       else:
           # ForkedPdb().set_trace()
           ixia_port_1_handle = port_handle.split(' ')[0]
           ixia_port_2_handle = port_handle.split(' ')[1]
           log.info("\nixia_port_1_handle = {}".format(ixia_port_1_handle))
           log.info("\nixia_port_2_handle = {}".format(ixia_port_2_handle))
           self.passed("Connected Ixia and got port handles!!")
          
        ##############################################################
        # config the parameters for IXIA stream
        ##############################################################
    @aetest.subsection
    def configure_ixia_interfaces(self):
        """Configure IPs to ixia interfaces"""
        global protocol_intf_handle_9,protocol_intf_handle_20
        global ixia_port_list
        intf_handle_list = []
        ixia_port_list = [ixia_port_1_handle, ixia_port_2_handle]
        #ForkedPdb().set_trace()
        
        status,interface_handle = l2ptLib.config_ixia_L2_interfaces(ixia_port_1_handle,'00:00:00:10:bc:ce','10')
        if status != True:
            log.error("\n Fail to configure mac address to port 1")
            self.failed(goto=['exit'])
        else:
            intf_handle_list.append(interface_handle)
            log.info("\nSuccessfully configured mac address to port 1")
            
        status,interface_handle = l2ptLib.config_ixia_L2_interfaces(ixia_port_2_handle,'00:00:00:20:bc:ce','10')
        if status != True:
            log.error("\n Fail to configure mac address to port 2")
            self.failed(goto=['exit'])
        else:
            intf_handle_list.append(interface_handle)
            log.info("\nSuccessfully configured mac address to port 2")
        
        protocol_intf_handle_9 = intf_handle_list[0]
        protocol_intf_handle_20 = intf_handle_list[1]
        
        log.info("\n\nConfigured interface handles:")
        log.info("protocol_intf_handle_9: {}".format(protocol_intf_handle_9))
        log.info("protocol_intf_handle_20: {}".format(protocol_intf_handle_20))
        
        self.passed("IP configuration  to ixia interfaces Successful!!")    
    
    
    @aetest.subsection
    def configure_ixia_traffic_streams(self):
        """Configure regular traffic streams on ixia ports"""

        global traffic_stream_id_1
        stream_handle_list = []
        #ForkedPdb().set_trace()
        intf_handle_list = [protocol_intf_handle_9, protocol_intf_handle_20]
        

        #####traffic stream Isolated to trunk secondary via trunk promiscous port ##########
        status,stream_handle = l2ptLib.config_traffic_stream1(protocol_intf_handle_9,protocol_intf_handle_20,'span-bi-directional','1000','ethernet_vlan')
        
        if status != True:
            log.error("\n Fail to create first traffic stream")
            self.failed(goto=['exit'])
        else:
            stream_handle_list.append(stream_handle)
            log.info("\nSuccessfully created 1st traffic stream")
                    

        traffic_stream_id_1 = stream_handle_list[0]
       
        
        log.info("traffic_stream_id_1: {}".format(traffic_stream_id_1))
       
        
        self.passed("Regular Ixia streams are configured Successfully!!")
        
    @aetest.subsection
    def start_traffic_streams(self):
        """Start all ixia traffic streams and validate counters"""
        
        global data_stream_ids
        
        data_stream_ids = [traffic_stream_id_1]
        
        l2ptLib.run_traffic_stream1(traffic_stream_id_1)
        time.sleep(30)

        
        self.passed("No issues seen in starting ixia streams and fetching stats!!")    
       
   ################################################################################################################# 
        
    @aetest.subsection     
    def configure_monitor_interface(self,testscript, testbed,R1):
         """configure L2 monitor interface"""
         
         cmd = """monitor session 10
                  source interface %s 
                  destination int sup-eth0
                  no shut
               """%(uut1_ixia_intf1)
         uut1.configure(cmd)

###############################################################################################

###############################################################################################


class CSCwe38173(aetest.Testcase):
    """NR3f FX2 span || VLAN header gets removed in spanned traffic for Egress packet."""

    @aetest.setup
    def tc01_setup(self):

        log.info("Verify version of the DUT")
        cmd = "show version"
        uut1.execute(cmd)
        
        cmd = """logging console 6 """
        uut1.configure(cmd)
        
        log.info("Verify Span session is created and status is up")
        cmd = "show monitor session 10"
        uut1.execute(cmd)
        
        cmd = "show monitor session 10 | in state"
        output = uut1.execute(cmd)
        match = re.search("up",output)

        if match :
            log.info("monitor session is up")
        else:
            self.failed("monitor session is down") 
        
        #time.sleep(60)
        # ForkedPdb().set_trace()
        ###############################################################################################################

    @aetest.test     
    def source_interface_tx(self,testscript, testbed):
         """configure source interface as tx and verify the traffic"""
         
         cmd = """monitor session 10
                  source interface %s tx
                  destination int sup-eth0
                  no shut
               """%(uut1_ixia_intf1)
         uut1.configure(cmd)
    
         cmd="""ethanalyzer local interface inband mirror autostop duration 30"""
         op=uut1.configure(cmd)
         if 'ID: 10' in op :
            log.info("Test case is Passed")
         else :
            log.info("Failed")
            self.failed(goto=['exit']) 
            
    @aetest.test     
    def source_interface_rx(self,testscript, testbed):
         """configure source interface as tx and verify the traffic"""
         
         cmd = """monitor session 10
                  source interface %s rx
                  destination int sup-eth0
                  no shut
               """%(uut1_ixia_intf1)
         uut1.configure(cmd)
    
         cmd="""ethanalyzer local interface inband mirror autostop duration 30"""
         op=uut1.configure(cmd)
         if 'ID: 10' in op :
            log.info("Test case is Passed")
         else :
            log.info("Failed")
            self.failed(goto=['exit']) 
            
        ###############################################################################################################

    @aetest.cleanup
    def tc01_cleanup(self):
        
        log.info("remove monitor session created")
        cmd = """no monitor session all""" 
        try:
            uut1.configure(cmd)
        except:
            log.error('Invalid CLI given: %s' % (cfg))
            log.error('Error with cli')
            log.error(sys.exc_info())
            self.failed(goto=['exit'])
            
        log.info("remove vlan created")
        cmd = """no vlan 10"""
        uut1.configure(cmd)

        
########################################################################################################################
################################################################################
####                       COMMON CLEANUP SECTION                           ####
################################################################################


class common_cleanup(aetest.CommonCleanup):

    @aetest.subsection
    def remove_configuration(self):

        ##############################################################
        # clean up the session, release the ports reserved and cleanup the dbfile
        ##############################################################


        log.info('remove configuration in {0}'.format(uut1))
        cmd = """ default interface %s """%(uut1_ixia_intf1)
        uut1.configure(cmd)
        cmd = """ default interface %s """%(uut1_ixia_intf2)
        uut1.configure(cmd)
        # cmd = """ default interface %s """%(uut1_dest_intf1)
        # uut1.configure(cmd)


if __name__ == '__main__': # pragma: no cover
    import argparse
    from ats import topology
    parser = argparse.ArgumentParser(description='standalone parser')
    parser.add_argument('--testbed', dest='testbed', type=topology.loader.load)
    parser.add_argument('--R1', dest='R1', type=str)
    parser.add_argument('--mode',dest = 'mode',type = str)
    args = parser.parse_known_args()[0]
    aetest.main(testbed=args.testbed,
                R1_name=args.R1,
                mode = args.mode,
                pdb = True)
