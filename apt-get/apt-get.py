import commands
import sys
import logging
import os
import time

LOGGER = logging.getLogger("deploy")

usage = '''
Usage:
    rockgo.py [options] [parameters]

Options:
    [-h | --help]
    [-t | --tar]
    [-d | --decompression]
    [-n | --nfs_deploy]
    [-s | --single_node_deploy]
    [-u | --undeploy]

Parameters:

'''

class CmdError(Exception):
    """
    Error when the execution of shell command failed.
    """

    def __init__(self, code, message, cmd):
        Exception.__init__(self)
        self.code = code
        self.message = message
        self.cmd = cmd

def exec_root_cmd(cmd, user = "root"):
    '''
    Execute remote command with ssh.

    Keyword arguments:
    target -- the target computer where the command will be executed
    cmd -- the command to be executed
    user -- the user to execute command (default: root)
    '''

    #print "%s@%s 'sudo -u %s sh -c \"%s\"'" % (CONF["ssh_cmd_prefix"], target, user, cmd)
    #return exec_cmd("%s@%s ' %s ' "
    #    % (CONF["ssh_cmd_prefix"], target, user, cmd))
    return exec_cmd("sudo -u %s sh -c \"%s\""
        % (user, cmd))

def exec_cmd(cmd):
    '''
    Execute the command.

    Keyword arguments:
    cmd -- the command to be executed.
    '''
    LOGGER.info("Execute shell command: %s" % cmd)
    LOGGER.debug("*****The output of the shell command is from here:*****")
    result = commands.getstatusoutput(cmd)
    for line in result[1].split("\n"):
        LOGGER.debug(line)
    LOGGER.debug("*****The output of the shell command is to here.  *****")
    LOGGER.debug("")
    LOGGER.debug("")
    '''
    #When running puppetd, even if there was no error in messages,
    #status 512 was returned, so I add the following if condition.
    #(cmd.find("puppetd") != -1 and result[0] == 512)
    if result[0] != 0 and not (cmd.find("puppetd") != -1 and result[0] == 512):
        raise CmdError(result[0], result[1], cmd)
    '''
    return result

def helper():
    '''
    '''
    print usage

def tar():
    LD = time.localtime()
    filename = '%s_%s_%s_%s_%s_%s_apt-get.tar' % (LD.tm_year, LD.tm_mon, LD.tm_mday, LD.tm_hour, LD.tm_min, LD.tm_sec)
    result = exec_root_cmd('tar -cvf %s /etc/apt/sources.list /var/lib/apt/lists /var/cache/apt/*' % (filename))

def decompression(path, filename):
    #path = os.path.dirname(os.path.abspath(__file__))

    result = exec_root_cmd('find -name "%s"' % (filename))
    #for line in result[1].split("\n"):
    if result[1]:
        #print result[1]
        result = exec_root_cmd('find %s -name "source"' % (path))
        if not result[1]:
            exec_root_cmd('mkdir %s/source' % (path))
        else:
            result = raw_input('%s/source has exit, do you want delete (Y/n)' % (path))
            #if len(result) == 1:
            while (result != 'y' and result != 'n' and result != 'Y' and result != 'N'):
                print 'error args!'
                result = raw_input('%s/source has exit, do you want delete (Y/n)' % (path))
            if result == 'y' or result == 'Y':
                exec_root_cmd('rm -rf %s/source' % (path))
                exec_root_cmd('mkdir %s/source' % (path))
            elif result == 'n' or result == 'N':
                pass
                
        result = exec_root_cmd('tar -xvf %s/%s -C %s/source/' % (path, filename, path))
        finish = False
        for line in result[1].split("\n"):
            print line
            if line == 'var/cache/apt/srcpkgcache.bin':
                finish = True
        if not finish:
            return "decompression error!!"
        return finish
    else:
        print 'can not find "apt-get.tar"'
        return False


def nfs_deploy(path):
    etc = exec_root_cmd('find %s -name "etc"' % (path))
    var = exec_root_cmd('find %s -name "var"' % (path))
    if etc[1] and var[1]:
        result = exec_root_cmd('find -name "/etc/apt/sources.list_backup"')
        if not result[1]:
            exec_root_cmd('mv /etc/apt/sources.list /etc/apt/sources.list_backup')
        exec_root_cmd('cp %s/etc/apt/sources.list /etc/apt/sources.list' % (path))
        exec_root_cmd('mv /var/lib/apt/lists /var/lib/apt/lists_backup')
        exec_root_cmd('ln -sf %s/source/var/lib/apt/lists /var/lib/apt/lists' % (path))
        exec_root_cmd('cp -Rf /var/cache/apt /var/cache/apt_backup')
        exec_root_cmd('apt-get clean')
        exec_root_cmd('find %s/source/var/cache/apt/ -maxdepth 1 -type f -name "*.bin" -exec ln -sf {} /var/cache/apt \;' % (path))
        exec_root_cmd('find %s/source/var/cache/apt/archives/ -maxdepth 1 -type f -name "*.deb" -exec ln -sf {} /var/cache/apt/archives \;' % (path))
        exec_root_cmd('find %s/source/var/cache/apt/archives/partial -maxdepth 1 -type f -name "*.deb" -exec ln -sf {} /var/cache/apt/archives/partial \;' % (path))
    else:
        print 'source error'

def single_node_deploy(path, filename):
    #path = os.path.dirname(os.path.abspath(__file__))
    if decompression(path):
        nfs_deploy(path, filename)

def undeploy():
    exec_root_cmd('cp /etc/apt/sources.list_backup /etc/apt/sources.list')
    exec_root_cmd('rm /var/lib/apt/lists')
    exec_root_cmd('mv /var/lib/apt/lists_backup /var/lib/apt/lists')
    exec_root_cmd('find /var/cache/apt -type l -exec rm -rf {} \;')
    exec_root_cmd('find /var/cache/apt_backup/ -maxdepth 1 -type f -name "*.bin" -exec mv {} /var/cache/apt \;')
    exec_root_cmd('find /var/cache/apt_backup/archives/ -maxdepth 1 -type f -name "*.deb" -exec mv {} /var/cache/apt/archives \;')
    exec_root_cmd('find /var/cache/apt_backup/archives/partial -maxdepth 1 -type f -name "*.deb" -exec mv {} /var/cache/apt/archives/partial \;')
    exec_root_cmd('rm -rf /var/cache/apt_backup')

if __name__ == '__main__':
    '''
    function: main()
    '''
    path = os.path.dirname(os.path.abspath(__file__))
    if (len(sys.argv) > 1):
        if(sys.argv[1] == "-t" or sys.argv[1] == "--tar"):
            tar()
        elif(sys.argv[1] == "-d" or sys.argv[1] == "--decompression"):
            result = exec_root_cmd('find -name "%s"' % (sys.argv[2]))
            if (result):
                decompression(path, sys.argv[2])
            else:
                print 'file "%s" not exit' % (sys.argv[2])
        elif(sys.argv[1] == "-n" or sys.argv[1] == "--nfs_deploy"):
            nfs_deploy(path)
        elif(sys.argv[1] == "-s" or sys.argv[1] == "--single_node_deploy"):
            result = exec_root_cmd('find -name "%s"' % (sys.argv[2]))
            if (result):
                single_node_deploy(path, sys.argv[2])
            else:
                print 'file "%s" not exit' % (sys.argv[2])
        elif(sys.argv[1] == "-u" or sys.argv[1] == "--undeploy"):
            undeploy()
    else:
        helper()
