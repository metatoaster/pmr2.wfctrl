import os
from os.path import abspath, isabs, isdir, join, normpath, relpath
import logging

logger = logging.getLogger(__name__)

def dummy_action(workspace):
    return


class BaseWorkspace(object):
    """
    Base workspace object
    """

    marker = None
    files = None

    def __init__(self, working_dir, **kw):
        self.working_dir = abspath(normpath(working_dir))
        self.reset()

    def reset(self):
        self.files = set()

    def initialize(self, **kw):
        # Unused here.
        raise NotImplementedError

    def check_marker(self):
        # Unused here.
        raise NotImplementedError

    def add_file(self, filename):
        """
        Add a file.  Should be relative to the root of the working_dir.
        """

        if not isabs(filename):
            # Normalize a relative path into absolute path based inside
            # the workspace working dir.
            filename = abspath(normpath(join(self.working_dir, filename)))

        if not filename.startswith(self.working_dir):
            raise ValueError('filename not inside working dir')
        # get the relative path, stripping out working dir + separator
        relname = filename[len(self.working_dir) + 1:]

        self.files.add(relname)

    def get_tracked_subpaths(self):
        return sorted(list(self.files))

    def save(self, **kw):
        raise NotImplementedError


class Workspace(BaseWorkspace):
    """
    Default workspace, file based.
    """

    def save(self, **kw):
        """
        They are already on filesystem, do nothing.
        """


class CmdWorkspace(BaseWorkspace):
    """
    Default workspace, file based.
    """

    def __init__(self, working_dir, marker=None, cmd_table=None, **kw):
        """
        marker
            The marker path that denotes that this was already
            initialized.
        cmd_table
            A dictionary of callable objects that will be used for
            certain situations.  Keys are:

            - init
            - save
        """

        assert marker is not None

        BaseWorkspace.__init__(self, working_dir)
        self.cmd_table = {}
        if cmd_table:
            self.cmd_table.update(cmd_table)
        self.marker = marker
        self.initialize()

    def get_cmd(self, name):
        cmd = self.cmd_table.get(name)
        if not cmd:
            logger.info('%s required but no init defined', name)
            return dummy_action
        return cmd

    def check_marker(self):
        target = join(self.working_dir, self.marker)
        logger.debug('checking isdir: %s', target)
        return isdir(target)

    def initialize(self, **kw):
        if self.check_marker():
            logger.debug('already initialized: %s', self.working_dir)
            return
        return self.get_cmd('init')(self, **kw)

    def save(self, **kw):
        """
        They are already on filesystem, do nothing.
        """

        return self.get_cmd('save')(self, **kw)


class BaseCmd(object):
    """
    Base command module

    For providing external command encapsulation.
    """

    def __init__(self, **kw):
        pass

    def init(self, workspace, **kw):
        raise NotImplementedError

    def save(self, workspace, **kw):
        raise NotImplementedError

    @property
    def cmd_table(self):
        return {
            'init': self.init,
            'save': self.save,
        }


class BaseDvcsCmd(BaseCmd):
    """
    Base DVCS based command.
    """

    def __init__(self, remote=None):
        self.remote = remote

    def init(self, workspace, **kw):
        if self.remote:
            self.clone(workspace)
        else:
            self.init_new(workspace)

    def save(self, workspace, message='', **kw):
        for path in workspace.get_tracked_subpaths():
            self.add(workspace, path)
        self.commit(workspace, message)
        self.push(workspace)

    def clone(self, workspace, **kw):
        raise NotImplementedError

    def init_new(self, workspace, **kw):
        raise NotImplementedError

    def add(self, workspace, path, **kw):
        raise NotImplementedError

    def commit(self, workspace, message, **kw):
        raise NotImplementedError

    def push(self, workspace, **kw):
        raise NotImplementedError
