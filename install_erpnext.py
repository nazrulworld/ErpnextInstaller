# Copyright (c) 2013, Web Notes Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

#!/usr/bin/env python
from __future__ import unicode_literals
import os, sys
import argparse
import subprocess
import re

is_redhat = is_debian = None
root_password = None
requirements = [
    "GitPython==0.3.2.RC1",
    "Jinja2==2.7.2",
    "MarkupSafe==0.18",
    "MySQL-python==1.2.5",
    "Werkzeug==0.9.4",
    "argparse==1.2.1",
    "async==0.6.1",
    "chardet==2.2.1",
    "cssmin==0.2.0",
    "dropbox==2.0.0",
    "gitdb==0.5.4",
    "google-api-python-client==1.2",
    "gunicorn==18.0",
    "httplib2==0.8",
    "markdown2==2.2.0",
    "pygeoip==0.3.0",
    "python-dateutil==2.2",
    "python-memcached==1.53",
    "pytz==2013d",
    "requests==2.2.1",
    "semantic-version==2.2.2",
    "six==1.5.2",
    "slugify==0.0.1",
    "smmap==0.8.2",
    "termcolor==1.1.0",
    "urllib3==1.7.1",
    "wsgiref==0.1.2",
]


def install(install_path):
    setup_folders(install_path)
    install_erpnext(install_path)
    post_install(install_path)


def install_pre_requisites():
    install_python_modules()
    print "-"*80
    print "Pre-requisites Installed"
    print "-"*80


def install_python_modules():
    print "-"*80
    print "Installing Python Modules: (This may take some time)"
    print "-"*80
    exec_in_shell("pip install {}".format(' '.join(requirements)))


def install_erpnext(install_path):
    print
    print "-"*80
    print "Installing ERPNext"
    print "-"*80

    # ask for details
    global root_password
    if not root_password:
        root_password = get_root_password()
        test_root_connection(root_password)

    db_name = raw_input("ERPNext Database Name: ")
    if not db_name:
        raise Exception, "Sorry! You must specify ERPNext Database Name"

    # setup paths
    sys.path = [".", "lib", "app"] + sys.path
    import wnf

    # install database, run patches, update schema
    # setup_db(install_path, root_password, db_name)
    wnf.install(db_name, root_password=root_password)

    setup_cron(install_path)


def get_root_password():
    # ask for root mysql password
    import getpass
    root_pwd = None
    root_pwd = getpass.getpass("MySQL Root user's Password: ")
    return root_pwd


def test_root_connection(root_pwd):
    out = exec_in_shell("mysql -u root %s -e 'exit'" % \
        (("-p"+root_pwd) if root_pwd else "").replace('$', '\$').replace(' ', '\ '))
    if "access denied" in out.lower():
        raise Exception("Incorrect MySQL Root user's password")


def setup_folders(install_path):
    os.chdir(install_path)
    app = os.path.join(install_path, "app")
    if not os.path.exists(app):
        print "Cloning erpnext"
        exec_in_shell("cd %s && git clone --branch master https://github.com/webnotes/erpnext.git app" % install_path)
        exec_in_shell("cd app && git config core.filemode false")
        if not os.path.exists(app):
            raise Exception, "Couldn't clone erpnext repository"

    lib = os.path.join(install_path, "lib")
    if not os.path.exists(lib):
        print "Cloning wnframework"
        exec_in_shell("cd %s && git clone --branch master https://github.com/webnotes/wnframework.git lib" % install_path)
        exec_in_shell("cd lib && git config core.filemode false")
        if not os.path.exists(lib):
            raise Exception, "Couldn't clone wnframework repository"

    public = os.path.join(install_path, "public")
    for p in [public, os.path.join(public, "files"), os.path.join(public, "backups"),
        os.path.join(install_path, "logs")]:
            if not os.path.exists(p):
                os.mkdir(p)


def create_virtual_env(install_path, env_name):
    os.chdir(install_path)
    if env_name == 'lib' or env_name == 'app':
        env_name = '%s_env' % env_name
    try:
        exec_in_shell('which virtualenv')
    except subprocess.CalledProcessError:
        exec_in_shell('pip install virtualenv')
        exec_in_shell('pip install -U virtualenv')
    exec_in_shell('virtualenv %s' % env_name)

    return os.path.join(install_path, '%s/bin' % env_name)


def setup_conf(install_path, db_name):
    import string, random
    # generate db password
    char_range = string.ascii_letters + string.digits
    db_password = "".join((random.choice(char_range) for n in xrange(16)))

    # make conf file
    with open(os.path.join(install_path, "lib", "conf", "conf.py"), "r") as template:
        conf = template.read()

    conf = re.sub("db_name.*", 'db_name = "%s"' % (db_name,), conf)
    conf = re.sub("db_password.*", 'db_password = "%s"' % (db_password,), conf)

    with open(os.path.join(install_path, "conf.py"), "w") as conf_file:
        conf_file.write(conf)

    return db_password


def post_install(install_path):
    pass


def exec_in_shell(cmd):
    # using Popen instead of os.system - as recommended by python docs
    import subprocess
    out = subprocess.check_output(cmd, shell=True)
    return out


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--venv', default=False)
    parser.add_argument('--username', default='erpnext')
    parser.add_argument('--password', default='erpnext')
    parser.add_argument('--no_install_prerequisites', default=False, action='store_true')

    return parser.parse_args()


def setup_cron(install_path):
    erpnext_cron_entries = [
        "*/3 * * * * cd %s && python lib/wnf.py --run_scheduler >> erpnext-sch.log 2>&1" % install_path,
        "0 */6 * * * cd %s && python lib/wnf.py --backup >> erpnext-backup.log 2>&1" % install_path
        ]
    for row in erpnext_cron_entries:
        try:
            existing_cron = exec_in_shell("crontab -l")
            if row not in existing_cron:
                exec_in_shell('{ crontab -l; echo "%s"; } | crontab' % row)
        except:
            exec_in_shell('echo "%s" | crontab' % row)


if __name__ == "__main__":

    from fixit import validate_package_manager
    is_redhat, is_debian = validate_package_manager()    
    if is_redhat: pass
    elif is_debian: pass
    else:
        raise Exception, "install has been abroted!"
    args = parse_args()
    install_path = os.getcwd()

    venv = args.venv
    if venv and not os.path.isdir(os.path.join(install_path, venv)):
        y = raw_input("virtual environment not created, do you want without virtual environment?")

        if re.match('y|ye|yes', y.lower()):
            pass
        else:
            raise Exception, "install process cancelled!"

    if venv:
        y = raw_input("we are sorry, do you active virtual environment yet?")
        if re.match('y|ye|yes', y.lower()):
            pass
        else:
            raise Exception, "please active virtual environment first, then try again!"

    if not args.no_install_prerequisites:
        install_pre_requisites()

    install(install_path=install_path)
    print
    print "-"*80
    print "Installation complete"
    print "To start the development server,"
    print "Login as {username} with password {password}".format(username=args.username, password=args.password)
    print "cd {}".format(install_path)
    print "./lib/wnf.py --serve"
    print "-"*80
    print "Open your browser and go to http://localhost:8000"
    print "Login using username = Administrator and password = admin"
