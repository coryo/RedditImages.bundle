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

DEFAULT_PATHS = ["/r/pics", "/r/gifs"]

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

        path = path.split('reddit.com')[-1]

        if not path.startswith('/'):
                path = '/'+path

        if path.endswith('/'):
                path = path[:-1]

        return path

def ImportPathsFromFile(file="paths.txt"):

        if Data.Exists(file):
                data = Data.Load(file)
                for line in data.splitlines():
                        AddPath(FixPath(line), silent=True)
                Data.Save("%s.bk" % file, data)
                Data.Remove(file)

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

        ImportPathsFromFile("paths.txt")

@handler(PLEX_PATH, NAME, thumb=ICONS['default'])
def MainMenu():       

        oc = ObjectContainer(title2=NAME, no_cache=True)

        for item in Dict['paths']:
                oc.add(DirectoryObject(
                        key   = Callback(Categories, path=item),
                        title = u'%s' % item,
                ))

        oc.add(InputDirectoryObject(
                key   = Callback(AddPath),
                title = u'%s' % L('Add a Path'),
        ))
        oc.add(DirectoryObject(
                key   = Callback(ListPaths, action='rem'),
                title = u'%s' % L('Remove a Path'),
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

@route(PLEX_PATH + '/paths/list')
def ListPaths(action='rem'):

        oc = ObjectContainer(title2=u'%s %s' % (L('Paths'), L(action)))

        for path in Dict['paths']:
                do = DirectoryObject()
                if action == 'rem':
                        do.key   = Callback(RemovePath, path=path)
                        do.title = "%s: %s" % (L('Remove'), path)
                oc.add(do)

        return oc

@route(PLEX_PATH + '/paths/add')
def AddPath(query, silent=False):

        if not query in Dict['paths']:
                Dict['paths'].append(query)
                Dict.Save()
        return None if silent else ErrorMessage("AddPath", query)

@route(PLEX_PATH + '/paths/remove')
def RemovePath(query, silent=False):

        if query in Dict['paths']:
                Dict['paths'].remove(query)
                Dict.Save()
        return None if silent else ErrorMessage("RemovePath", query)
####################################################################################################    
@route(PLEX_PATH + '/categories')
def Categories(path):

        oc = ObjectContainer(title2=u'%s %s' % (path, L('Categories')))

        for cat in CATEGORIES:
                oc.add(DirectoryObject(
                        key   = Callback(Listing, path=path, category=cat),
                        title = "%s/%s" % (path, cat)
                ))

        return oc

@route(PLEX_PATH + '/listing')
def Listing(path, category='hot', after=None):

        oc = ObjectContainer(title2=u'%s/%s' % (path,category), content=ContainerContent.Mixed)

        params = {}
        if after:
                params['after'] = after

        if category in SORTABLE:
                DumbPrefs(PLEX_PATH, oc,
                        title = "Edit Prefs: time=%s, animated=%s" % (Prefs['time'], Prefs['animated']),
                        thumb = R(ICONS['prefs'])
                )
                params['t']    = Prefs['time']
                params['sort'] = category

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
