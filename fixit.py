import os, sys
import subprocess
from install_erpnext import exec_in_shell

is_redhat = is_debian = None


def fix_all():
    global is_redhat, is_debian
    is_redhat, is_debian = validate_package_manager()
    if is_redhat:
        install_using_yum()
    elif is_debian:
        install_using_apt()


def validate_package_manager():
        import platform
        # Check OS
        operating_system = platform.system()
        print "Your operating system = ", operating_system
        if operating_system != 'Linux':
                raise Exception,'Sorry, This installer only works for Linux based Operating System'

        #Check Python version
        python_version = sys.version.split(" ")[0]
        print "Your python version = ", python_version
        if not (python_version and int(python_version.split(".")[0]) == 2 and \
         int(python_version.split(".")[1]) == 7 ):
                raise Exception, "Hey! needs python version 2.7+"
        # check distribution
        distribution = platform.linux_distribution()[0].lower().replace('"', '')
        print "Dristribution = ", distribution
        is_redhat = distribution in ("redhat", "red hat enterprise linux server",
         "centos", "centos linux", "fedora")
        is_debian = distribution in ("debian", "ubuntu", "elementary os",
         "linuxmint")
        return is_redhat, is_debian


def install_using_apt():
        try:
                exec_in_shell("apt-get update")
        except subprocess.CalledProcessError:
                raise "please check broken ppa repository"

        packages = "libmysqlclient-dev python-setuptools python-dev build-essential python-mysqldb python-pip git memcached ntp vim screen htop"
        print "-"*80
        print "Installing Packages: (This may take some time)"
        print packages
        print "-"*80
        exec_in_shell("apt-get install -y %s" % packages)
        try:
                exec_in_shell("which mysql")
        except subprocess.CalledProcessError:
                packages = "mysql-server"
                print "Installing Packages:", packages
                exec_in_shell("apt-get install -y %s" % packages)
        update_config_for_debian()


def update_config_for_debian():
        for service in ("mysql",):
                exec_in_shell("service %s restart" % service)


def install_using_yum():
        packages = "gcc MySQL-python git memcached ntp vim-enhanced screen"

        print "-"*80
        print "Installing Packages: (This may take some time)"
        print packages
        print "-"*80
        exec_in_shell("yum install -y %s" % packages)

        try:
                exec_in_shell("which mysql")
        except subprocess.CalledProcessError:
                packages = "mysql mysql-server mysql-devel"
                print "Installing Packages:", packages
                exec_in_shell("yum install -y %s" % packages)
                exec_in_shell("service mysqld restart")
                update_config_for_redhat()


def update_config_for_redhat():
    # set to autostart on startup
    for service in ("mysqld", "memcached"):
        exec_in_shell("chkconfig --level 2345 %s on" % service)
        exec_in_shell("service %s restart" % service)


def setup_python_pip():
    try:
        exec_in_shell("which pip")
    except subprocess.CalledProcessError:
        exec_in_shell("easy_install install pip")
    try:
        exec_in_shell("which virtualenv")
    except subprocess.CalledProcessError:
        exec_in_shell("pip install virtualenv")
if __name__ == "__main__":
    from install_erpnext import parse_args
    args = parse_args()
    if os.getuid() != 0:
        raise Exception, "Please run this script as root or try to use sudo"
    fix_all()
