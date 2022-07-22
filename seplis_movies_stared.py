from loguru import logger

from flexget import plugin
from flexget.event import event
from flexget.utils.cached_input import cached

logger = logger.bind(name='seplis_movies_stared')

class seplis_movies_stared:
    """
    watchlist:
        priority: 1
        seplis_movies_stared:
            - username
    """

    schema = {
        'type': 'array', # list of usernames
    }
    @cached('seplis_movies_stared', persist='1 minute')
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
                f'https://api.seplis.net/1/users/{uid}/movies-stared',
                params={
                    'per_page': 1000,
                }
            )
            for movie in r.json():
                if movie['title']:
                    year = f' ({movie["release_date"][:4]})' if movie['release_date'] else ''
                    entries.append({
                        'title': movie['title'] + year,
                        'seplis_id': movie['id'],
                    })
        return entries

@event('plugin.register')
def register_plugin():
    plugin.register(seplis_movies_stared, 'seplis_movies_stared', api_ver=2)