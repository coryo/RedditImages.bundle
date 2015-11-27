from DumbTools import DumbPrefs

REDDIT_API = "https://www.reddit.com{endpoint}.json"
APIS = {
        'imgur.com': SharedCodeService.Imgur,
        'gfycat.com': SharedCodeService.Gfycat,
}

NAME       = 'RedditImages'
PLEX_PATH  = '/photos/redditimages'

ICONS = {
        'default': 'icon-default.png',
        'prefs': 'icon-settings.png'
}

# path:display_name
DEFAULT_PATHS = {
        "/r/pics": "/r/pics",
        "/r/gifs": "/r/gifs"
}

CATEGORIES = ['hot', 'new', 'rising', 'controversial', 'top', 'gilded']
SORTABLE   = ['top', 'controversial']

####################################################################################################      
def ErrorMessage(error, message):

        return ObjectContainer(
                header  = u'%s' % error,
                message = u'%s' % message, 
        )
        
def UrlEncode(url, params=None):

        return '%s?%s' % (url, '&'.join(["%s=%s" % (k,v) for k,v in params.iteritems()])) if params else url           

def FixPath(path):

        path = path.split('?')[0].split('reddit.com')[-1]

        if not path.startswith('/'):
                path = '/'+path

        if path.endswith('/'):
                path = path[:-1]

        return path

@route(PLEX_PATH + '/import/{file}')
def ImportPathsFromFile(file="paths.txt"):

        if Data.Exists(file):
                start = len(Dict['paths'])
                data = Data.Load(file)
                for line in data.splitlines():
                        lineitems = line.split(',')
                        name = lineitems[0].strip()
                        path = lineitems[-1].strip()
                        AddPath(FixPath(path), name=name if name != path else FixPath(path), silent=True)
                return ErrorMessage("import", "imported %d paths" % (start - len(Dict['paths'])))
        return ErrorMessage("import", "failed: file doesn't exist")

####################################################################################################      
def Start():

        ObjectContainer.title1 = NAME
        HTTP.CacheTime  = CACHE_1DAY
        HTTP.User_Agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36'

        if not 'paths' in Dict or len(Dict['paths']) == 0:
                Dict['paths'] = DEFAULT_PATHS
                Dict.Save()

        for name, api in APIS.iteritems():
                Route.Connect(PLEX_PATH + '/%s/album' % name, api.GetAlbum)

@handler(PLEX_PATH, NAME, thumb=ICONS['default'])
def MainMenu():       

        oc = ObjectContainer(title2=NAME, no_cache=True)

        for path, path_name in Dict['paths'].iteritems():
                oc.add(DirectoryObject(
                        key   = Callback(Categories, path=path),
                        title = u'%s' % path_name,
                ))
        oc.objects.sort(key=lambda obj: obj.title)

        oc.add(InputDirectoryObject(
                key   = Callback(AddPath),
                title = u'%s' % L('Add a Path'),
        ))
        oc.add(DirectoryObject(
                key   = Callback(ListPaths, action='rem'),
                title = u'%s' % L('Remove a Path'),
        ))
        oc.add(DirectoryObject(
                key   = Callback(ImportPathsFromFile, file='paths.txt'),
                title = u'%s' % L('Import paths from paths.txt'),
        ))

        # preferences
        if Client.Product in DumbPrefs.clients:
                DumbPrefs(PLEX_PATH, oc,
                        thumb = R(ICONS['prefs']))
        else:
                oc.add(PrefsObject(
                        title   = L('preferences'),
                        tagline = L('preferences'),
                        summary = L('preferences'),
                ))

        return oc

@route(PLEX_PATH + '/paths/list/{action}')
def ListPaths(action='rem'):

        oc = ObjectContainer(title2=u'%s %s' % (L('Paths'), L(action)))

        for path, name in Dict['paths'].iteritems():
                do = DirectoryObject()
                if action == 'rem':
                        do.key   = Callback(RemovePath, query=path)
                        do.title = "%s: %s" % (L('Remove'), name)
                oc.add(do)
        oc.objects.sort(key=lambda obj: obj.title)

        return oc

@route(PLEX_PATH + '/paths/add')
def AddPath(query, name=None, silent=False):

        if not query in Dict['paths']:
                Dict['paths'][query] = name if name else query
                Dict.Save()
        return None if silent else ErrorMessage("AddPath", query)

@route(PLEX_PATH + '/paths/remove')
def RemovePath(query, silent=False):

        if query in Dict['paths']:
                del Dict['paths'][query]
                Dict.Save()
        return None if silent else ErrorMessage("RemovePath", query)
####################################################################################################    
@route(PLEX_PATH + '/categories')
def Categories(path):

        oc = ObjectContainer(title2=u'%s %s' % (Dict['paths'][path], L('Categories')))

        for cat in CATEGORIES:
                oc.add(DirectoryObject(
                        key   = Callback(Listing, path=path, category=cat),
                        title = "%s/%s" % (Dict['paths'][path], cat)
                ))

        return oc

@route(PLEX_PATH + '/listing')
def Listing(path, category='hot', after=None):

        oc = ObjectContainer(title2=u'%s/%s' % (Dict['paths'][path],category), content=ContainerContent.Mixed)

        params = {}

        params['limit'] = Prefs['limit']

        if after:
                params['after'] = after

        if category in SORTABLE:
                ptitle = "Edit Prefs: limit=%s, time=%s, animated=%s" % (Prefs['limit'], Prefs['time'], Prefs['animated'])
                params['t']    = Prefs['time']
                params['sort'] = category
        else:
                ptitle = "Edit Prefs: limit=%s, animated=%s" % (Prefs['limit'], Prefs['animated'])

        DumbPrefs(PLEX_PATH, oc,
                title = ptitle,
                thumb = R(ICONS['prefs'])
        )

        data = JSON.ObjectFromURL(url = UrlEncode(REDDIT_API.format(endpoint="%s/%s" % (path, category)), params),
                                  cacheTime = CACHE_1MINUTE*5)

        for item in data['data']['children']:

                item_thumb = item['data']['thumbnail']
                item_url   = item['data']['url']
                item_title = item['data']['title']
                
                obj = None
                
                for api_name, api in APIS.iteritems():
                        if api_name in item_url:
                                obj = api.ListObject(item_url, item_title, item_thumb, allow_animated=bool(Prefs['animated']))
                                break

                if obj: oc.add(obj)

        if data['data']['after']:
                oc.add(NextPageObject(
                        key = Callback(Listing, path=path, category=category, after=data['data']['after'])
                ))

        return oc
