# -*- coding: UTF-8 -*-

# 2022-01-09

import sys
from resources.lib import control, log_utils

params = dict(control.parse_qsl(sys.argv[2].replace('?','')))

action = params.get('action')
name = params.get('name')
table = params.get('table')
title = params.get('title')
source = params.get('source')

# navigator -------------------
if action == None or action == 'root':
    from resources.lib.indexers import navigator
    navigator.navigator().root()
##    if pydevd.connected: pydevd.kill_all_pydev_threads()

elif action == 'playExtern':
    import json
    if not control.visible(): control.busy()
    try:
        sysmeta = {}
        for key, value in params.items():
            if key == 'action': continue
            elif key == 'year' or key == 'season' or key == 'episode': value = int(value)
            sysmeta.update({key : value})
        if int(params.get('season')) == 0:
            mediatype = 'movie'
        else:
            mediatype = 'tvshow'
        sysmeta.update({'mediatype': mediatype})
        if control.getSetting('hosts.mode') == '2':
            sysmeta.update({'select': '2'})
        else:
            sysmeta.update({'select': '0'})
        sysmeta = json.dumps(sysmeta)
        params.update({'sysmeta': sysmeta})
        from resources.lib import sources
        sources.sources().play(params)
    except:
        pass

elif action == 'movieNavigator':
    from resources.lib.indexers import navigator
    navigator.navigator().movies()

elif action == 'tvNavigator':
    from resources.lib.indexers import navigator
    navigator.navigator().tvshows()

elif action == 'toolNavigator':
    from resources.lib.indexers import navigator
    navigator.navigator().tools()

elif action == "settings":
    from resources import settings
    settings.run(params)

elif action == 'UpdatePlayCount':
    from resources.lib import playcountDB
    playcountDB.UpdatePlaycount(params)
    control.execute('Container.Refresh')

# elif action == 'searchNavigator':
#     from resources.lib.indexers import navigator
#     navigator.navigator().search()


# listings -------------------------------

elif action == 'listings':
    from resources.lib.indexers import listings
    listings.listings().get(params)

elif action == 'movieYears':
    from resources.lib.indexers import listings
    listings.listings().movieYears()

elif action == 'movieGenres':
    from resources.lib.indexers import listings
    listings.listings().movieGenres()

elif action == 'tvGenres':
    from resources.lib.indexers import listings
    listings.listings().tvGenres()

# search ----------------------
elif action == 'searchNew':
    from resources.lib import searchDB
    searchDB.search_new(table)

elif action == 'searchClear':
    from resources.lib import searchDB
    searchDB.search_clear(table)

elif action == 'searchDelTerm':
    from resources.lib import searchDB
    searchDB.search_del_term(table, name)

# person ----------------------
elif action == 'person':
    from resources.lib.indexers import person
    person.person().get(params)

elif action == 'personSearch':
    from resources.lib.indexers import person
    person.person().search()

elif action == 'personCredits':
    from resources.lib.indexers import person
    person.person().getCredits(params)

# elif action == 'personChangeSearchDB':
#     from resources.lib.indexers import person
#     person.person().changeSearchDB()

elif action == 'playfromPerson':
    if not control.visible(): control.busy()
    import json
    sysmeta = json.loads(params['sysmeta'])
    if sysmeta['mediatype'] == 'movie':
        from resources.lib.indexers import movies
        sysmeta = movies.movies().super_meta('', id=sysmeta['tmdb_id'])
        sysmeta = json.dumps(sysmeta)
    else:
        from resources.lib.indexers import tvshows
        sysmeta = tvshows.tvshows().super_meta('', id=sysmeta['tmdb_id'])
        sysmeta = control.quote_plus(json.dumps(sysmeta))

    params.update({'sysmeta': sysmeta})
    from resources.lib import sources
    sources.sources().play(params)

# movies ----------------------
elif action == 'movies':
    from resources.lib.indexers import movies
    movies.movies().get(params)

elif action == 'moviesSearch':
    from resources.lib.indexers import movies
    movies.movies().search()

# elif action == 'movieChangeSearchDB':
#     from resources.lib.indexers import movies
#     movies.movies().changeSearchDB()

#---------------------------------------
# elif action == 'moviePerson':
#     from resources.lib.indexers import movies
#     movies.movies().person()
#
# elif action == 'movieCertificates':
#     from resources.lib.indexers import movies
#     movies.movies().certifications()
#
# elif action == 'movieYears':
#     from resources.lib.indexers import movies
#     movies.movies().years()
#
# elif action == 'moviePersons':
#     from resources.lib.indexers import movies
#     movies.movies().persons()


# tvshows ---------------------------------
elif action == 'tvshows': # 'tvshowPage'
    from resources.lib.indexers import tvshows
    tvshows.tvshows().get(params)

elif action == 'tvshowsSearch':
    from resources.lib.indexers import tvshows
    tvshows.tvshows().search()

# elif action == 'tvChangeSearchDB':
#     from resources.lib.indexers import tvshows
#     tvshows.tvshows().changeSearchDB()
#
# elif action == 'tvPerson':
#     from resources.lib.indexers import tvshows
#     tvshows.tvshows().person()
#
# elif action == 'tvNetworks':
#     from resources.lib.indexers import tvshows
#     tvshows.tvshows().networks()
#
# elif action == 'tvCertificates':
#     from resources.lib.indexers import tvshows
#     tvshows.tvshows().certifications()
#
# elif action == 'tvPersons':
#     from resources.lib.indexers import tvshows
#     tvshows.tvshows().persons(params)

# seasons ---------------------------------
elif action == 'seasons':
    from resources.lib.indexers import seasons
    seasons.seasons().get(params)  # params

# episodes ---------------------------------
elif action == 'episodes':
    from resources.lib.indexers import episodes
    episodes.episodes().get(params)

# sources ---------------------------------
elif action == 'play':
    if not control.visible(): control.busy()
    from resources.lib import sources
    sources.sources().play(params)

elif action == 'addItem':
    from resources.lib import sources
    sources.sources().addItem(title)

elif action == 'playItem':
    #log_utils.log(__name__ + ' - start playItem', log_utils.LOGINFO)
    # if control.getSetting('watcher.control') == 'true':
    #     #log_utils.log(__name__ + ' - watcher playItem', log_utils.LOGINFO)
    #     control.setSetting(id='watcher.control', value='false')
    # else:
    if not control.visible(): control.busy()
    from resources.lib import sources
    sources.sources().playItem(title, source)

# Settings ------------------------------
elif action == 'addonSettings':
    control.openSettings()

elif action == 'resetSettings':
    status = control.resetSettings()
    if status:
        control.reload_profile()
        control.sleep(500)
        control.execute('RunAddon("%s")' % control.addonId)
        
elif action == 'resolverSettings':
    import resolveurl as resolver
    resolver.display_settings()
    from resources.lib.indexers import navigator
    navigator.navigator().tools()

elif action == 'downloadNavigator':
    from resources.lib.indexers import navigator
    navigator.navigator().downloads()

elif action == 'download':
    image = params.get('image')
    from resources.lib import downloader
    from resources.lib import sources
    import json
    try: downloader.download(name, image, sources.sources().sourcesResolve(json.loads(source)[0], True))
    except: pass
