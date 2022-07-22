import os
import re
import logging

from flexget import plugin
from flexget.event import event
from flexget.utils.template import RenderError
from flexget.utils.pathscrub import pathscrub


log = logging.getLogger('clean_target')


class CleanupTarget(object):
    schema = {
        'type': 'object',
        'properties': {
            'location': {'type': 'string', 'format': 'path'},
            'remove': {'type': 'string', 'format': 'regex'},
        },
        'additionalProperties': False
    }

    @plugin.priority(255)
    def on_task_output(self, task, config):
        location = config.get('location', "")
        remove = config.get('remove', "")
        if not location:
            return
        if not remove:
            return
        for entry in task.accepted:
            self.clean_target(task, entry, location, remove)

    def clean_target(self, task, entry, location, remove):
        try:
            location_rendered = entry.render(location)
            location_rendered = pathscrub(os.path.expanduser(location_rendered))
            remove_rendered = entry.render(remove)
        except RenderError as err:
            raise plugin.PluginWarning(f'Path value replacement `{remove}` failed: {err.args[0]}')

        if not os.path.isdir(location_rendered):
            log.error(f'Location is not a directory: {location_rendered}')
            return

        try:
            pattern = re.compile(remove_rendered, re.IGNORECASE | re.UNICODE)
        except re.error as e:
            raise plugin.PluginError('Invalid regex `%s`: %s' % (remove_rendered, e))

        for name in os.listdir(location_rendered):
            path = os.path.join(location_rendered, name)
            if os.path.isfile(path) and pattern.match(name):
                if task.options.test:
                    log.info(f'Would clean {path}')
                else:
                    try:
                        os.remove(path)
                        log.info(f'Cleaning {path}')
                    except os.error as e:
                        log.error(f'An error occurred trying to remove file {path}: {e}')


@event('plugin.register')
def register_plugin():
    plugin.register(CleanupTarget, 'clean_target', api_ver=2)
