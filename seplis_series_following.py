from loguru import logger

from flexget import plugin
from flexget.event import event
from flexget.utils.cached_input import cached

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
        entries = []
        user_ids = []

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
                        year = f' {series["premiered"][:4]}' if series['premiered'] else ''
                        entries.append({
                            'title': title + year,
                            'seplis_id': series['id'],
                        })
        return entries

@event('plugin.register')
def register_plugin():
    plugin.register(seplis_series_following, 'seplis_series_following', api_ver=2)