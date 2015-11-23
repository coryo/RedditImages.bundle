from DumbTools import DumbPrefs

GfycatAPI = SharedCodeService.Gfycat
ImgurAPI  = SharedCodeService.Imgur

NAME       = 'RedditImages'
PLEX_PATH  = '/photos/redditimages'

ICON  = "icon-default.png"

PATHS = [
        "/r/pics/hot",
]

SUPPORTED_IMAGE_HOSTS = ['imgur.com', 'gfycat.com']

def ErrorMessage(error, message):

        return ObjectContainer(
                header  = u'%s' % error,
                message = u'%s' % message, 
        )
        
def UrlType(url):

        site = None
        t = None
        if 'imgur.com' in url:
                site = 'imgur'
                if '/a/' in url:
                        t = 'album'
                elif url.endswith('.gifv') or url.endswith('.webm') or url.endswith('.gif'):
                        t = 'vid'
                else:
                        t = 'img'
        elif 'gfycat.com' in url:
                site = 'gfycat'
                t = 'vid'

        return (site, t)                
            
def Start():

        ObjectContainer.title1 = NAME
        HTTP.CacheTime  = CACHE_1DAY
        HTTP.User_Agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36'
        if not 'paths' in Dict:
                Dict['paths'] = PATHS
                Dict.Save()

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

@route(PLEX_PATH + '/listing')
def Listing(url):

        oc = ObjectContainer(content=ContainerContent.Mixed)

        data = JSON.ObjectFromURL(url)

        for item in data['data']['children']:

                item_thumb = item['data']['thumbnail']
                item_url   = item['data']['url']
                item_title = item['data']['title']

                item_type = UrlType(item_url)
                
                if item_type[0] == 'imgur':
                        # Imgur specifics
                        item_thumb = ImgurAPI.ThumbForUrl(item_url) if item_thumb == 'nsfw' else item_thumb
                        if item_type[1] == 'album':
                                oc.add(PhotoAlbumObject(
                                        key = Callback(Album, site='imgur', id=ImgurAPI.GetId(item_url)),
                                        rating_key = item_url,
                                        title = u'[ia] %s' % item_title,
                                        thumb = Resource.ContentsOfURLWithFallback(item_thumb)
                                ))
                        elif item_type[1] == 'vid' and Prefs['animated']:
                                oc.add(VideoClipObject(
                                        url = item_url,
                                        title = u'[iv] %s' % item_title,
                                        thumb = Resource.ContentsOfURLWithFallback(item_thumb)
                                ))
                        elif item_type[1] == 'img':
                                oc.add(PhotoObject(
                                        url = item_url,
                                        title = u'[i] %s' % item_title,
                                        thumb = Resource.ContentsOfURLWithFallback(item_thumb)
                                ))
                elif item_type[0] == 'gfycat':
                        # Gfycat specifics
                        if item_type[1] == 'vid' and Prefs['animated']:
                                oc.add(VideoClipObject(
                                        url = item_url,
                                        title = u'[gfy] %s' % item_title,
                                        thumb = Resource.ContentsOfURLWithFallback(item_thumb)
                                ))
                else:
                        #support other image hosts
                        pass

        return oc

@route(PLEX_PATH + '/album/{site}/{id}')
def Album(site, id):

        if site == 'imgur':
                return ImgurAPI.GetAlbum(id)

        return ObjectContainer()
