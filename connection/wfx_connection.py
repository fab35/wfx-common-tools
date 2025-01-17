#!/usr/bin/python3
#
# Created: 2019-06-04 16:00:00
# Main author:
#     - Marc Dorval <marc.dorval@silabs.com>
#
import os
import sys
import time
import socket
import logging

logging.basicConfig(level=logging.INFO)

try:
    import serial
except ImportError:
    loaded_serial = False
    print("'serial'     is not installed. UART connection impossible")
else:
    loaded_serial = True
    logging.getLogger("serial").setLevel(logging.WARNING)
print('loaded_serial     ' + str(loaded_serial))

try:
    import paramiko
except ImportError:
    loaded_paramiko = False
    print("'paramiko'   is not installed. SSH connection impossible")
else:
    loaded_paramiko = True
    logging.getLogger("paramiko").setLevel(logging.WARNING)
print('loaded_paramiko   ' + str(loaded_paramiko))

try:
    import telnetlib
except ImportError:
    loaded_telnetlib = False
    print("'telnetlib'  is not installed. TELNET connection impossible")
else:
    loaded_telnetlib = True
    logging.getLogger("telnetlib").setLevel(logging.WARNING)
print('loaded_telnetlib  ' + str(loaded_telnetlib))


class SshTarget(paramiko.client.SSHClient):

    def __init__(self, host, name=None, wait=False, user="root", port=22, password=""):
        super().__init__()
        self.user = user
        self.host = host
        self.port = port
        self.password = password
        self.name = name if name else host
        self.stdin = None
        self.stdout = None
        self.stderr = None
        self.result = None
        self.error = None
        self.local_trace = False
        if len(self.name) > 10:
            self.name = "…" + self.name[-9:]
        self.__connect(wait)

    def __connect(self, wait=False):
        cmd_name = "%-6s" % self.name
        err = None
        self.set_missing_host_key_policy(paramiko.client.AutoAddPolicy)
        start = now = time.time()
        while start + 10 > now:
            try:
                self.connect(self.host, username=self.user, port=self.port, timeout=1, banner_timeout=1,
                             auth_timeout=1, password=self.password)
                peer = self.get_transport().getpeername()
                logging.info("%-13s I'm connected to %s:%d as %s" % (cmd_name, peer[0], peer[1], self.user))
                return
            except socket.timeout:
                if not wait:
                    break
                if err != socket.timeout:
                    logging.info("%-13s I %s" % (cmd_name, "didn't boot yet. Wait."))
                    err = socket.timeout
            except paramiko.ssh_exception.NoValidConnectionsError:
                if not wait:
                    break
                if err != paramiko.ssh_exception.NoValidConnectionsError:
                    logging.info("%-13s %s" % (cmd_name, "boot nearly finished"))
                    err = paramiko.ssh_exception.NoValidConnectionsError
            except paramiko.ssh_exception.SSHException:
                self.__send_key(self.password)
                return self.__connect()
            now = time.time()
        logging.info("%-13s I can't connect to %s:%d as %s" % (cmd_name, self.host, self.port, self.user))
        raise Exception("%s: Cannot connect over SSH to %s:%d as %s" % (cmd_name, self.host, self.port, self.user))

    def __send_key(self, original_pwd):
        # This is very specific to the Raspberry PI, where SSH using a password for root is not possible.
        # Therefore we try to log using the 'pi' account to add our public key and copy it to the root account
        a = paramiko.Agent()
        ks = a.get_keys()
        k = ks[0].get_base64()
        for pwd in {'default_password', original_pwd}:
            if pwd is not None:
                print("Trying to add the tester public key to /root/.ssh/authorized_keys using \'" + pwd + "\'")
                try:
                    tmp_dut = SshTarget(self.host, name='tmp_dut', port=self.port, user='pi', password=pwd)
                    print(type(tmp_dut))
                    tmp_dut.write('sudo mkdir -p /root/.ssh')
                    tmp_dut.write('echo ' + 'ssh-rsa ' + str(k) + '> ~/.ssh/authorized_keys2')
                    tmp_dut.write('sudo tee -a /root/.ssh/authorized_keys < ~/.ssh/authorized_keys2')
                except paramiko.ssh_exception.SSHException:
                    pass

    def write(self, text):
        if self is not None:
            self.stdin, self.stdout, self.stderr = self.exec_command(text, environment={'ENV': '/etc/profile'})

    def read(self):
        self.result = str(self.stdout.read(), "utf-8").strip()
        self.error = str(self.stderr.read(), "utf-8").strip()
        if not self.result:
            return "ERROR: " + self.error
        else:
            return self.result


class AbstractConnection(object):
    link = None
    connection = None
    nickname = ''
    trace = False

    def configure(self, *args, **kwargs):
        raise NotImplementedError()

    def write(self, text):
        raise NotImplementedError()

    def read(self):
        raise NotImplementedError()

    def run(self, cmd, wait_ms=0):
        raise NotImplementedError()


class Uart(AbstractConnection):

    def __init__(self, nickname="uart", port=None, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=0.1):
        object.__init__(self)
        self.nickname = nickname
        self.conn = 'UART ' + str(port) + '/' + str(baudrate) + '/' + str(bytesize) + '/' + parity + '/' + str(stopbits)
        if port:
            self.configure(port, baudrate, bytesize, parity, stopbits, timeout)
            return

    def configure(self, port, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=0.1):
        self.connection = None
        self.link = None
        try:
            self.link = serial.Serial(port, baudrate, bytesize, parity, stopbits, timeout)
            self.connection = port
            if self is None:
                raise Exception("%s %s" % (self.nickname, 'Can not connect to ' + port))
            agent_reply = self.run('wfx_test_agent')
            if agent_reply == '':
                agent_error = ' No \'wfx_test_agent\' on ' + port + '. Communication is OK, but we miss the agent!!'
                raise Exception("%s %s" % (self.nickname, str(agent_error)))
        except serial.serialutil.SerialException as oops:
            if 'PermissionError' in str(oops):
                uart_error = port + ' is present, but already used. Use \'uarts()\' to list available COM ports'
                logging.error("%s %s" % (self.nickname, str(uart_error)))
                raise Exception("%s %s" % (self.nickname, str(uart_error)))
            if 'FileNotFoundError' in str(oops):
                uart_error = ' No ' + port + ' COM port. Use \'uarts()\' to list available COM ports after connecting.'
                uart_error += '\nCurrently available ports:\n' + uarts()
                logging.error("%s: %s" % (self.nickname, str(uart_error)))
                print(uarts())
                raise Exception("%s %s" % (self.nickname, str(uart_error)))

    def write(self, text):
        if self.link is not None:
            if self.trace:
                for line in text.strip().split('\n'):
                    print(str.format("%-8s U>>|  " % self.nickname), end='')
                    print(line)
            self.link.write(bytes(text.strip() + '\n', 'utf-8'))

    def read(self):
        lines = ''
        if self.link is not None:
            reading = True
            while reading:
                line = str(self.link.readline(), "utf-8").strip()
                if line == '':
                    reading = False
                else:
                    if lines != '':
                        lines += '\n'
                    lines += line
                    if self.trace:
                        print(str.format('<<U %8s|  %s' % (self.nickname, line)))
        return lines

    def run(self, cmd, wait_ms=0):
        self.write(cmd)
        time.sleep(wait_ms/1000.0)
        return self.read()


class Telnet(AbstractConnection):

    def __init__(self, name=None, user="pi", host="10.5.124.249", password=None):
        self.nickname = name if name else 'telnet'
        self.conn = 'TELNET ' + user + '@' + host
        super().__init__()
        if host:
            self.configure(user=user, host=host, password=password)

    def configure(self, user="pi", host="10.5.124.249", password=None):
        self.link = telnetlib.Telnet(user)
        self.link.read_until("login: ")
        self.link.write(user + "\n")
        if password:
            self.link.read_until("Password: ")
            self.link.write(password + "\n")

    def write(self, text):
        if self.link is not None:
            if self.trace:
                for line in text.strip().split('\n'):
                    print(str.format("%-8s S>>|  " % self.nickname), end='')
                    print(line)
            self.link.write(bytes(text.strip() + '\n', 'utf-8'))

    def read(self):
        if self.link is not None:
            res = self.link.read_all()
            if self.trace:
                for line in res.split('\n'):
                    print(str.format("<<S %8s|  " % self.nickname), end='')
                    print(line)
            return res
        else:
            return ''

    def run(self, cmd, wait_ms=0):
        self.write(cmd)
        time.sleep(wait_ms/1000.0)
        return self.read()


class Ssh(AbstractConnection):

    def __init__(self, name=None, user="pi", host="10.5.124.249", port=22, password=""):
        self.nickname = name if name else 'ssh'
        self.conn = 'SSH ' + user + '@' + host + ':' + str(port)
        super().__init__()
        if host:
            self.configure(user=user, host=host, port=port, password=password)

    def configure(self, user="pi", host="10.5.124.249", port=22, password="default_password"):
        self.link = SshTarget(user=user, host=host, name=self.nickname, port=port, password=password)

    def write(self, text):
        if self.link is not None:
            if self.trace:
                for line in text.strip().split('\n'):
                    print(str.format("%-8s S>>|  " % self.nickname), end='')
                    print(line)
            self.link.write(bytes(text.strip() + '\n', 'utf-8'))

    def read(self):
        if self.link is not None:
            res = self.link.read()
            if self.trace:
                for line in res.split('\n'):
                    print(str.format("<<S %8s|  " % self.nickname), end='')
                    print(line)
            return res
        else:
            return ''

    def run(self, cmd, wait_ms=0):
        self.write(cmd)
        time.sleep(wait_ms/1000.0)
        return self.read()


class Direct(AbstractConnection):

    def __init__(self, name=None):
        self.nickname = name if name else 'direct'
        self.command_res = None
        self.conn = 'Direct'
        super().__init__()

    def configure(self, *args, **kwargs):
        pass

    def write(self, text):
        if self.trace:
            for line in text.strip().split('\n'):
                print(str.format("%-8s D>>|  " % self.nickname), end='')
                print(line)
        self.command_res = os.popen(text).read().strip()

    def read(self):
        if self.command_res:
            res = self.command_res
            if self.trace:
                for line in res.split('\n'):
                    print(str.format("<<D %8s|  " % self.nickname), end='')
                    print(line)
            return res
        else:
            return ''

    def run(self, cmd, wait_ms=None):
        self.write(cmd)
        return self.read()


class WfxConnection(object):

    def __init__(self, nickname, **kwargs):
        self.nickname = nickname
        self.link = None
        self.trace = False

        if 'host' in kwargs:
            port = kwargs['port'] if 'port' in kwargs else ""
            if port == 'telnet':
                host = kwargs['host']
                if 'user' not in kwargs:
                    raise Exception("%s: Missing 'user'. Telnet Connection impossible to host %s" % (nickname, host))
                user = kwargs['user']
                print('%s: Configuring a Telnet connection to host %s for user %s' % (nickname, host, user))
                password = kwargs['password'] if 'password' in kwargs else None
                self.link = Telnet(nickname, host=host, user=user, password=password)

        if not self.link:
            if 'host' in kwargs:
                if not loaded_paramiko:
                    raise Exception("'paramiko'   is not installed. SSH connection impossible for " + nickname)
                host = kwargs['host']
                port = kwargs['port'] if 'port' in kwargs else 22
                user = kwargs['user'] if 'user' in kwargs else 'root'
                print('%s: Configuring a SSH connection to host %s for user %s' % (nickname, host, user))
                password = kwargs['password'] if 'password' in kwargs else None
                self.link = Ssh(nickname, host=host, user=user, port=port, password=password)

        if not self.link:
            if 'port' in kwargs:
                if not loaded_serial:
                    raise Exception("'serial'   is not installed. UART connection impossible for " + nickname)
                port = kwargs['port']
                print('%s: Configuring a UART connection using %s' % (nickname, port))
                self.link = Uart(nickname, port=port)
                if self.link is None:
                    if port in uarts():
                        raise Exception(port + ' is detected but is not available. Check for other applications using ' + port)

        if not self.link:
            if not kwargs:
                print('%s: Configuring a Direct connection' % nickname)
                self.link = Direct(nickname)

    def write(self, text):
        if self.link is not None:
            if self.trace:
                for line in text.strip().split('\n'):
                    print(str.format("%-8s S>>|  " % self.nickname), end='')
                    print(line)
            self.link.write(bytes(text.strip() + '\n', 'utf-8'))

    def read(self):
        if self.link is not None:
            res = self.link.read()
            if self.trace:
                for line in res.split('\n'):
                    print(str.format("<<S %8s|  " % self.nickname), end='')
                    print(line)
            return res
        else:
            return ''

    def run(self, cmd, wait_ms=0):
        self.write(cmd)
        time.sleep(wait_ms/1000.0)
        return self.read()


# Functions allowing discovery of possible connections
def uarts():
    if loaded_serial == 0:
        return "'serial' is not installed. Can't list UARTs"
    com_ports = os.popen('python -m serial.tools.list_ports').read().replace(' ', '').strip().split('\n')
    res = ''
    for port in com_ports:
        try:
            serial.Serial(port)
        except serial.serialutil.SerialException as oops:
            if 'PermissionError' in str(oops):
                res += '%-5s (IN USE)\n' % port
        else:
            res += '%-5s (free)\n' % port
        finally:
            pass
    return res.strip()


def networks():
    try:
        import ifaddr
    except ImportError:
        return "ifaddr not installed. Can't list networks"
    adapters = ''
    all_adapters = ifaddr.get_adapters()
    for adapter in all_adapters:
        for ip in adapter.ips:
            if '::' not in str(ip.ip) and '169.' not in str(ip.ip):
                ip_add = ip.ip + "/" + str(ip.network_prefix)
                adapters += str.format("%-20s %s\n" % (ip_add, adapter.nice_name))
    return adapters


if __name__ == '__main__':
    if sys.version_info < (3, 0):
        sys.stderr.write("This tools was developed for Python 3 and wasn't tested with Python 2.x\n")
        sys.exit(0)

    print('You\'re using a ', sys.platform, 'platform')

    print(uarts())
    print(networks())

    uart_out = WfxConnection('UartOUT', port='COM8')
    uart_in = WfxConnection('UartIN', port='COM19')

    print(uarts())

    eth = Ssh('master', host='10.5.124.249', user='pi', port=2186, password='default_password')
    tel = Telnet('telnet', host='10.5.124.249', user='pi', port='telnet', password='default_password')

    me = Direct('WinPC')
    me.trace = False
    print(me.run('dir'))
    print(me.run('dir wfx_*.py'))

    uart_out.trace = True
    uart_in.trace = True
    eth.trace = True

    uart_out.write('Hello\nHave a nice day!')
    print(uart_in.read())

    uart_out.write('wfx_test_agent write_test_data {j:{a:1}}')
    print(uart_in.read())

    eth.write('uname -r')
    print(eth.read())

    print(eth.run('uname -a'))
    print(eth.run('wfx_test_agent write_test_data {}'))
