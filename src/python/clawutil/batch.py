r"""Simple controller for runs with GeoClaw

Includes support for multiple runs at the same time

"""
# ============================================================================
#      Copyright (C) 2013 Kyle Mandli <kyle@ices.utexas.edu>
#
#  Distributed under the terms of the Berkeley Software Distribution (BSD) 
#  license
#                     http://www.opensource.org/licenses/
# ============================================================================

import subprocess
import os
import time
import glob

# from pyclaw.runclaw import runclaw
# from pyclaw.plotters.plotclaw import plotclaw

def print_tests(tests):
    for (i,test) in enumerate(tests):
        print "====== Test #%s ============================" % (i)
        print str(test)

def run_tests(tests,plot=True,tar=False,max_processes=None,parallel=True,
                verbose=False,terminal_output=False,executable="xclaw"):
    # Parameters
    if os.environ.has_key('DATA_PATH'):
        base_path = os.environ['DATA_PATH']
    else:
        base_path = os.getcwd()
    base_path = os.path.expanduser(base_path)
    
    poll_interval = 5.0
    if max_processes is None:
        if os.environ.has_key('OMP_NUM_THREADS'):
            max_processes = int(os.environ['OMP_NUM_THREADS'])
        else:
            max_processes = 4
    
    process_queue = []
    RUNCLAW_CMD = "python $CLAW/python/pyclaw/runclaw.py"
    PLOTCLAW_CMD = "python $CLAW/python/pyclaw/plotters/plotclaw.py"
    
    # Run tests
    for (i,test) in enumerate(tests):
        # Create output directory
        data_dirname = ''.join((test.prefix,'_data'))
        output_dirname = ''.join((test.prefix,"_output"))
        plots_dirname = ''.join((test.prefix,"_plots"))
        log_name = ''.join((test.prefix,"_log.txt"))
        
        if len(test.type) > 0:
            test_path = os.path.join(base_path,test.type,test.name)
        else:
            test_path = os.path.join(base_path,test.name)
        test_path = os.path.abspath(test_path)
        data_path = os.path.join(test_path,data_dirname)
        output_path = os.path.join(test_path,output_dirname)
        plots_path = os.path.join(test_path,plots_dirname)
        log_path = os.path.join(test_path,log_name)

        # Create test directory if not present
        if not os.path.exists(test_path):
            os.makedirs(test_path)

        # Clobber old data directory
        if os.path.exists(data_path):
            data_files = glob.glob(os.path.join(data_path,'*.data'))
            for data_file in data_files:
                os.remove(data_file)
        else:
            os.mkdir(data_path)

        # Open and start log file
        log_file = open(log_path,'w')
        tm = time.localtime()
        year = str(tm[0]).zfill(4)
        month = str(tm[1]).zfill(2)
        day = str(tm[2]).zfill(2)
        hour = str(tm[3]).zfill(2)
        minute = str(tm[4]).zfill(2)
        second = str(tm[5]).zfill(2)
        date = 'Started %s/%s/%s-%s:%s.%s' % (year,month,day,hour,minute,second)
        log_file.write(date)
    
        # Write out data
        temp_path = os.getcwd()
        os.chdir(data_path)
        test.write_data_objects()
        os.chdir(temp_path)
        
        # Run the simulation
        run_cmd = "%s %s %s T F %s" % (RUNCLAW_CMD,executable,output_path,data_path)
        plot_cmd = "%s %s %s %s" % (PLOTCLAW_CMD,output_path,plots_path,test.setplot)
        tar_cmd = "tar -cvzf %s.tgz %s" % (plots_path,plots_path)
        cmd = run_cmd
        if plot:
            cmd = ";".join((cmd,plot_cmd))
            if tar:
                cmd = ";".join((cmd,tar_cmd))
        print cmd
        if parallel:
            while len(process_queue) == max_processes:
                if verbose:
                    print "Number of processes currently:",len(process_queue)
                for process in process_queue:
                    if process.poll() == 0:
                        process_queue.remove(process)
                time.sleep(poll_interval)
            process_queue.append(subprocess.Popen(cmd,shell=True,
                    stdout=log_file,stderr=log_file))
            
        else:
            if terminal_output:
                log_file.write("Outputting to terminal...")
                subprocess.Popen(cmd,shell=True).wait()
                log_file.write("Command completed.")
            else:
                subprocess.Popen(cmd,shell=True,stdout=log_file,
                    stderr=log_file).wait()
    
    # Wait to exit while processes are still going
    # while len(process_queue) > 0:
    #     for process in process_queue:
    #         if process.poll() == 0:
    #             process_queue.remove(process)
    #             print "Number of processes currently:",len(process_queue)
    #     time.sleep(poll_interval)


class Test(object):
    
    def __init__(self):
        # Base test traits
        self.type = ""
        self.name = ""
        self.setplot = "setplot"
        
    def __str__(self):
        output = "Test %s: %s" % (self.name,self.prefix)
        output += "\n  Setplot: %s" % self.setplot
        return output
        
    def write_data_objects(self):
        pass
