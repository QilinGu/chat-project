import os
import simplejson as json
import pytz
from datetime import datetime
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template import Template, Context
from fabric.api import run, env, cd, task, prefix, sudo, local
from fabric.colors import (green, red, cyan, magenta, yellow)
from fabric.contrib.files import exists
from fabric.network import disconnect_all
from fabric.operations import put


env.use_ssh_config = True
env.hosts = ['x']
# env.hosts = ['deploy']
settings.configure()


class Log(object):
    """ Log file configuration insance for supervisor """
    def __init__(self, logging):
        self.logging = logging

    def set_attrs(self):
        logging = self.logging
        self.logdir = logging.get("logdir")
        self.logfile = logging.get("logfile")
        self.maxbytes = logging.get("logfile_maxbytes", 1024)
        self.backups = logging.get("logfile_backups", 8)

    def run(self):
        """ logdir and logfile is here """
        logging = self.logging
        if not ("logdir" and "logfile" in logging):
            message = "Both logdir and logfile must exists "\
                      "in logging directive, will not use custom "\
                      "logging.."
            raise Exception(message)
        if exists(logging['logdir']):
            if "purge" in logging and logging['purge']:
                print yellow('purging all existing log files')
                with cd(logging['logdir']):
                    # supervisor.log supervisor.log.[1-n] etc..
                    ff = ([x for x in run('ls').split(' ') if x])
                    for x in ff:
                        x = x.replace('\r', '')
                        if x.split('.')[-1].isdigit():
                            sudo('rm %s' % x)
                    sudo('touch %s' % logging['logfile'])
                    sudo('cat /dev/null > %s' % logging['logfile'])
            run('touch %s' % logging['logfile'])
        else:
            # create log dir and base log file
            print yellow("remote logdir does not exists, creating..")
            run('mkdir -p %s' % logging['logdir'])
            with cd(logging['logdir']):
                run('touch %s' % logging['logfile'])
        self.set_attrs()


class BaseTask:
    def __init__(self):
        self.deploy_clone = ''
        self.remote_dir = ''
        self.remote_dir_conf = ''
        self.ini = {}
        self.out = 'out'

    def load_legend(self, branch_name):
        """ """
        try:
            with open('legend.json', 'r') as f:
                self.ini = json.loads(f.read())
                self.ini["project_branch"] = branch_name
            if self.ini['keep_last_src_tree_count'] and self.ini['keep_last_src_tree_count'] < 2:
                raise ImproperlyConfigured('number of backup src tree extemely low,'
                                           ' increase that number bitch!')
            return True
        except IOError:
            return False

    def compose_filename(self, templatename):
        target = ""
        try:
            if templatename.split('.')[0].split('_')[1] == 'template':
                target = \
                    templatename.split('.')[0].split('_')[0] \
                    + '_' + self.ini['project_appname'] + \
                    '.' + templatename.split('.')[1]
        except IndexError:
            target = templatename
        except Exception, e:
            raise e
        return target

    def render_conf(self, filename, dirname):
        # continue with non-task templates
        target_filename = self.compose_filename(filename)
        with open(os.path.join(dirname, filename), 'r') as f:
            t = Template(f.read())
            c = Context(self.ini)
            # open the target file at the
            # remote and then write rendered text inside
            os.chdir(self.out)
            with open(target_filename, 'w+') as target:
                target.write(t.render(c))
            # upload rendered config file to remote
            tt = '%s/%s' % (
                self.remote_dir_conf, target_filename)
            put(target_filename, tt)
            os.remove(target_filename)
            os.chdir('..')

    def render_task(self, task, template, avail):
        """ Renders a supervisor task from 'tasks' """
        managed = True if task['name'] in avail else False

        try:
            # stop task first if managed
            if managed:
                sudo('supervisorctl stop %s' % task['name'])
            # check for use_custom_logging flag, if valid then proceed
            # to create approporiate Log instance for this tasks
            if "use_custom_logging" and "logging" in task:
                print cyan("will attempt to use Log..")
                logging = task["logging"]
                try:
                    l = Log(logging)
                    l.run()
                except Exception, e:
                    print red(e.message)
                else:
                    # attach log object to context
                    task["log"] = l

            c = Context(task)
            target_filename = task.get("filename")
            with open(target_filename, 'w+') as target:
                target.write(template.render(c))
            tt = "%s/tasks/%s" % (self.remote_dir_conf, target_filename)
            # send rendered task file to remote
            put(target_filename, tt)
        except Exception, e:
            print red(e.message)
            raise e

    def run_management_command(self, command, branch=None):
        # runs a management command inside project dir
        target = self.ini['projects_root'] + '/' + self.ini[
            'project_address'] + '/venv'

        if not branch:
            branch = self.ini['project_appname']

        with cd(self.ini['projects_root'] + '/' +
                self.ini['project_address'] + '/src/' + branch):
            with prefix('source %s' % (target + '/bin/activate')):
                return run('python manage.py %s' % command)

    def production_src(self):
        assert self.ini['projects_root']
        assert self.ini['project_address']
        return self.ini['projects_root'] + '/' + self.ini['project_address'] + '/src'

    def parse_validate_output(self, out):
        parsed = out.split(' ')
        assert len(parsed) == 3
        assert str(parsed[0]) == "0"


class DeployTask(BaseTask):
    """ helper class for task:deploy """

    def link_settings(self):
        # link production settings
        settings_dict = self.ini.get("settings")

        self.base =  \
            '%s/%s/src/%s/%s/' %\
            (self.ini.get('remote_projects_dir'),
             self.ini.get('project_address'),
             self.ini.get('project_appname'),
             self.ini.get('project_appname'))

        # if None given use production settings
        filename = settings_dict.get("active_setting", "production") + '.py'
        self.original = '%sconfigs/%s' % (self.base, filename)
        self.target = '%ssettings.py' % (self.base)

        if not exists(self.original):
            raise ImproperlyConfigured(
                red('original settings file does not exists, '
                    'check active_setting key @legend'))

        if exists(self.target) and not settings_dict.get('overwrite_settings', False):
            print yellow('skipping linking,'
                         'since target file already exists')
        else:
            print green('linking settings file \'%s\'' % filename)
            if exists(self.target):
                print magenta('removing old link')
                run('rm %s' % self.target)
            run('ln -s %s %s' % (self.original, self.target))

    def restore_permissions(self):
        with cd(self.production_src()):
            print yellow("restore permissions to www-data")
            run('sudo chown -R www-data:www-data %s' % self.deploy_clone)


    def validate_prod(self):
        # prod validate
        with cd(self.production_src()):
            self.parse_validate_output(self.run_management_command('validate'))

    def cleanup(self):
        try:
            os.removedirs(self.out)
        except:
            pass

    def collectstatic(self):
        manage_dir = "%s/%s" % (self.production_src(), self.ini['project_appname'])
        with cd(manage_dir):
            self.run_management_command("collectstatic --noinput")

    def reload(self):
        print cyan('reload app server')
        self.vassals = self.ini['projects_root'] + '/vassals'
        self.uwsgi_file = 'uwsgi_%s.ini' %\
            (self.ini['project_appname'])
        self.nginx_enabled_sites = '/etc/nginx/sites-enabled'
        self.nginx_file = 'nginx_%s.conf' %\
            self.ini['project_appname']

        if exists('%s/%s' % (self.vassals, self.uwsgi_file)):
            run('rm  %s/%s' % (self.vassals, self.uwsgi_file))
        run('ln -s %s/%s  %s/%s' % (self.remote_dir_conf,
             self.uwsgi_file, self.vassals, self.uwsgi_file))
        run('sudo service nginx reload')
        # run('sudo supervisorctl reread')
        target = self.ini['projects_root'] + '/' + self.ini[
            'project_address'] + '/venv'
        self.run_management_command("compile_pyc")
        run('sync')

    def discard_old_trees(self):
        with cd(self.production_src()):
            output = run('find  . -type d -iname "%s_*" | sort' % self.ini['project_appname'])
            dirs = [x.strip('\r')[2:] for x in output.split('\n')]
            for x in range(len(dirs) - self.ini.get('keep_last_src_tree_count', 10)):
                print yellow("removing old source tree: %s" % dirs[x])
                sudo('rm -rf %s' % dirs[x])

    def src(self):
        def suffix():
            # branch suffix *_140128_22_30
            return datetime.now().strftime("%y%m_%d_%H_%M")

        try:
            self.deploy_clone = '%s_%s' % (self.ini['project_appname'], suffix())
            deploy_clone_dir = "/%s" % self.deploy_clone
            with cd("/tmp"):
                if exists(self.ini["project_appname"]):
                    print yellow('remove old clone: %s' % self.ini["project_appname"])
                    run('rm -rf %s' % self.ini["project_appname"])

                run('git clone -b %s %s' % (self.ini["project_branch"], self.ini['project_source_repo']))
                with cd(self.ini['project_appname']):
                    run('rm -rf .git .gitignore')
                # move fresh clone to prod src dir
                run('cp -rf %s %s' % (self.ini["project_appname"], self.production_src() + deploy_clone_dir))

            with cd(self.production_src()):
                if exists(self.ini['project_appname']):
                    print yellow('remove old link %s' % self.ini['project_appname'])
                    run('rm -rf %s' % self.ini['project_appname'])
                # link tree
                run('ln -s %s %s' % (self.deploy_clone, self.ini['project_appname']))
        except KeyError:
            print yellow(
                'Src::no repo url found,'
                'not doing anything with /src')

    def venv(self):
        no_reqs = "No requirement instructions found for venv"
        target = self.ini['projects_root'] + '/' + self.ini[
            'project_address'] + '/venv'
        with cd(target):
            if not exists('bin'):
                print green('Venv::Creating.. to %s' % target)
                run('virtualenv %s' % target)
            else:
                print cyan(
                    'already seems to have a env..'
                    'do not create a new env')
        req_base = '%s/%s/src/%s/deploy' % \
                   (self.ini['projects_root'],
                    self.ini['project_address'],
                    self.ini['project_appname'])

        # default requirements file for venv
        reqs = self.ini["requirements"]
        if not (reqs and reqs["config_dir"] and reqs["requirements"]):
            raise ImproperlyConfigured(no_reqs)

        config_dir = reqs["config_dir"]
        req_file = reqs["requirements"]
        if not (config_dir and req_file):
            raise ImproperlyConfigured("use_config enabled but "
                                       "no config_dir or requirements found")
        target_req = "%s/%s/%s" % (req_base, config_dir, req_file)

        if exists(target_req):
            print green("requirements computed as: %s" % target_req)
            # print green('Found requirements file, installing it')
            with prefix('source %s' % (target + '/bin/activate')):
                    run('pip install -r %s' % target_req)
        else:
            print red(no_reqs)
            raise ImproperlyConfigured(no_reqs)

    def files(self):
        uwsgi_log = self.ini['projects_root'] + '/' + self.ini[
            'project_address'] + '/log/uwsgi_log'
        nginx_access = self.ini['projects_root'] + '/' + self.ini[
            'project_address'] + '/log/nginx_access'
        nginx_error = self.ini['projects_root'] + '/' + self.ini[
            'project_address'] + '/log/nginx_error'
        run('touch %s %s %s ' %
            (uwsgi_log, nginx_error, nginx_access))
        run('sudo chmod uog+w %s/%s/log/*' % (self.ini[
            'projects_root'], self.ini['project_address']))
        # if using ssl
        if self.ini["use_ssl"]:
            print yellow("Nginx configured to use ssl, "
                         " make sure certificates "
                         "exists in config/ssl dir")

    def revert_permissions(self):
        target_dir = "%s/%s" % (self.ini['projects_root'], self.ini['project_address'])
        print red(target_dir)
        print yellow(exists(target_dir))

    def check_dir(self):
        try:
            os.makedirs(self.out)
        except OSError:
            pass

        self.remote_dir = self.ini['remote_projects_dir'] + \
            '/%s' % self.ini['project_address']
        self.remote_dir_conf = self.remote_dir + '/conf'

        # basic dirs
        dirs = [
            self.remote_dir_conf,
            self.remote_dir + '/src',
            self.remote_dir + '/log',
            self.remote_dir + '/venv'
        ]

        # if ssl is enabled, create a dir for certificate
        if self.ini["use_ssl"]:
            dirs.append(self.remote_dir_conf + '/ssl')

        # check if we have any tasks to deploy
        if len(self.ini["tasks"]) > 0:
            dirs.append(self.remote_dir_conf + '/tasks')

        for d in dirs:
            run('mkdir -p %s' % d)

    def validate(self):
        pass

    def render(self):
        print green('render start')
        try:
            if not (os.path.exists(self.ini['project_conf_dir'])
                and self.ini['overwrite_conf']):
                print red("skip rendering process")
                return False
            print green('..|continue render process|..')
            for dirname, dirnames, filenames in \
                os.walk(self.ini['project_conf_dir']):
                target_filename = ''
                for filename in filenames:
                    # render task here
                    if filename.startswith("task"):
                        continue
                    else:
                        self.render_conf(filename, dirname)
        except KeyError:
            print yellow('project_conf_dir or overwrite_conf not '
                         'found in legend, skipping..')
        print green('render end')

    def render_tasks(self):
        print green("start render tasks..")
        target = self.ini['projects_root'] + '/' + self.ini[
            'project_address'] + '/conf/tasks/'
        run('rm -rf %s*.conf' % target)

        if not "tasks" in self.ini:
            print red("No tasks found, skipping")
            return

        avail = [x.split(' ')[0] for x in sudo('supervisorctl avail').split('\n')]
        template = None
        try:
            with open(os.path.join("conf", "task_template.conf"), 'r') as f:
                template = Template(f.read())

            # check tasks, remove invalid ones
            for task in self.ini["tasks"]:
                if not ("name" and "filename" and
                            "command" and "user" in task):
                    self.ini["tasks"].remove(task)

            os.chdir(self.out)
            for task in self.ini["tasks"]:
                self.render_task(task, template, avail)
                # TODO: attempt to restart supervisor?
            os.chdir("..")
        except Exception, e:
            print red("Exception during task render: %s" % e.message)
            raise e
        else:
            # reload supervisor,
            # supervisor starts task if autostart set to true
            sudo('supervisorctl reload')
        print yellow("end of render_task")

    def reload_search(self):
        print green("start reload search..")
        key = "update_haystack_index"
        if key in self.ini and self.ini[key]:
            print yellow("will reload/update search index")
            self.run_management_command("update_index")

    def nodejs(self):
        if self.ini.get('install_node', False):
            with cd(self.production_src()):
                print yellow('installing node js')
                sudo('apt-get install python-software-properties -y')
                sudo('apt-add-repository ppa:chris-lea/node.js -y')
                sudo('apt-get update -y')
                sudo('apt-get install nodejs -y')
                run('node -v')
        if self.ini.get('install_npm_modules', False) and exists(self.ini['node_dir']):
            with cd(self.ini['node_dir']):
                print yellow('installing node packages')
                packages = ' '.join(self.ini.get('npm_packages', []))
                if packages:
                    run('npm install %s' % packages)

@task
def deploy(branch_name):
    obj = DeployTask()
    if obj.load_legend(branch_name):
        try:
            obj.revert_permissions()
            obj.check_dir()
            obj.render()
            obj.files()
            obj.discard_old_trees()
            obj.src()
            obj.venv()
            obj.link_settings()
            obj.collectstatic()
            obj.validate_prod()
            obj.reload()
            obj.restore_permissions()
            obj.nodejs()
            obj.render_tasks()
            obj.reload_search()
            obj.cleanup()
        except:
            raise
        finally:
            # os.system("rm -rfv out")
            local('rm -rfv out')
            disconnect_all()
    else:
        print red('legend.txt is required and does not exists',
                  bold=True)
