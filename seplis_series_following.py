from loguru import logger

from flexget import plugin
from flexget.event import event
from flexget.utils.cached_input import cached
from flexget.entry import Entry


logger = logger.bind(name='seplis_series_following')

class seplis_series_following:
    """
    configure_series:
      from:
        seplis_series_following:
          - username
    """

    schema = {
        'type': 'array', # list of usernames
    }
    @cached('seplis_series_following', persist='1 minute')
    def on_task_input(self, task, config):
        user_ids = []
        entries = []
        for u in config:
            r = task.requests.get(f'https://api.seplis.net/1/users?username={u}')
            d = r.json()
            if not d:
                raise plugin.PluginError(f'Unknown user: {u}')
            user_ids.append(d[0]['id'])

        for uid in user_ids:
            r = task.requests.get(
                f'https://api.seplis.net/1/users/{uid}/shows-following',
                params={
                    'per_page': 1000,
                }
            )
            for series in r.json():
                titles = [series['title'], *series['alternative_titles']]
                for title in titles:
                    if title:
                        entry = Entry()
                        entry['title'] = series['title']
                        year = int(series["premiered"][:4]) if series['premiered'] else None
                        entry['title'] += f' ({year})' if year else ''
                        entry['seplis_year'] = year
                        entry['seplis_id'] = series['id']
                        yield entry

@event('plugin.register')
def register_plugin():
    plugin.register(seplis_series_following, 'seplis_series_following', api_ver=2)