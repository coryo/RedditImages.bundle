from DumbTools import DumbPrefs

APIS = {
        'imgur.com': SharedCodeService.Imgur,
        'gfycat.com': SharedCodeService.Gfycat,
}

NAME       = 'RedditImages'
PLEX_PATH  = '/photos/redditimages'

ICON  = "icon-default.png"

PATHS = [
        "/r/pics/hot",
]

####################################################################################################      
def ErrorMessage(error, message):
        return ObjectContainer(
                header  = u'%s' % error,
                message = u'%s' % message, 
        )
        
def UrlEncode(url, params=None):
        return '%s?%s' % (url, '&'.join(["%s=%s" % (k,v) for k,v in params.iteritems()])) if params else url           

####################################################################################################      
def Start():

        ObjectContainer.title1 = NAME
        HTTP.CacheTime  = CACHE_1DAY
        HTTP.User_Agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36'
        if not 'paths' in Dict:
                Dict['paths'] = PATHS
                Dict.Save()

        for name, api in APIS.iteritems():
                Route.Connect(PLEX_PATH + '/%s/album' % name, api.GetAlbum)            

@handler(PLEX_PATH, NAME)
def MainMenu():       

        oc = ObjectContainer(no_cache=True)

        for item in Dict['paths']:
                oc.add(DirectoryObject(
                        key = Callback(Listing, url="https://www.reddit.com/%s.json" % item),
                        title = u'%s' % item,
                ))

        # preferences
        if Client.Product in DumbPrefs.clients:
                DumbPrefs(PLEX_PATH, oc)
        else:
                oc.add(PrefsObject(
                        title   = L('preferences'),
                        tagline = L('preferences'),
                        summary = L('preferences'),
                ))

        return oc

####################################################################################################      
@route(PLEX_PATH + '/listing')
def Listing(url, after=None):

        oc = ObjectContainer(content=ContainerContent.Mixed)

        params = {}
        if after:
                params['after'] = after

        data = JSON.ObjectFromURL(UrlEncode(url, params), cacheTime=CACHE_1MINUTE)

        for item in data['data']['children']:

                item_thumb = item['data']['thumbnail']
                item_url   = item['data']['url']
                item_title = item['data']['title']
                
                for api_name, api in APIS.iteritems():
                        if api_name in item_url:
                                obj = api.ListObject(item_url, item_title, item_thumb, allow_animated=bool(Prefs['animated']))
                                break

                if obj: oc.add(obj)

        if data['data']['after']:
                oc.add(NextPageObject(
                        key = Callback(Listing, url=url, after=data['data']['after'])
                ))

        return oc
