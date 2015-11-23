# DumbPrefs v1.0 by Cory <babylonstudio@gmail.com>
# DumbKeyboard v1.0 by Cory <babylonstudio@gmail.com>

class DumbKeyboard:

        clients = ['Plex for iOS', 'Plex Media Player', 'Plex Web']
        KEYS       = list('abcdefghijklmnopqrstuvwxyz1234567890-=;[]\\\',./')
        SHIFT_KEYS = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_+:{}|\"<>?')

        def __init__(self, prefix, oc, callback, dktitle=None, dkthumb=None, dkplaceholder=None, dksecure=False, **kwargs):

                cb_hash = hash(str(callback)+str(kwargs))
                Route.Connect(prefix+'/dumbkeyboard/%s'                     % cb_hash, self.Keyboard)
                Route.Connect(prefix+'/dumbkeyboard/%s/submit'              % cb_hash, self.Submit)
                Route.Connect(prefix+'/dumbkeyboard/%s/history'             % cb_hash, self.History)
                Route.Connect(prefix+'/dumbkeyboard/%s/history/clear'       % cb_hash, self.ClearHistory)
                Route.Connect(prefix+'/dumbkeyboard/%s/history/add/{query}' % cb_hash, self.AddHistory)

                oc.add(DirectoryObject(
                        key   = Callback(self.Keyboard, query=dkplaceholder),
                        title = str(dktitle) if dktitle else u'%s' % L('DumbKeyboard Search'),
                        thumb = dkthumb
                ))

                if not 'DumbKeyboard-History' in Dict:
                        Dict['DumbKeyboard-History'] = []
                        Dict.Save()

                self.Callback = callback
                self.callback_args = kwargs
                self.secure = dksecure

        def Keyboard(self, query=None, shift=False):

                oc = ObjectContainer()

                if self.secure and query:
                        string = ''.join(['*' for i in range(len(query[:-1]))]) + query[-1]
                else:
                        string = query if query else ""

                oc.add(DirectoryObject(
                        key   = Callback(self.Submit, query=query),
                        title = u'%s: %s' % (L('Submit'), string.replace(' ', '_')),
                ))

                if len(Dict['DumbKeyboard-History']) > 0:
                        oc.add(DirectoryObject(
                                key   = Callback(self.History),
                                title = u'%s' % L('Search History'),
                        ))

                oc.add(DirectoryObject(
                        key   = Callback(self.Keyboard, query=query+" " if query else " "),
                        title = 'Space',
                ))

                if query:
                        oc.add(DirectoryObject(
                                key   = Callback(self.Keyboard, query=query[:-1]),
                                title = 'Backspace',
                        ))

                oc.add(DirectoryObject(
                        key   = Callback(self.Keyboard, query=query, shift=True),
                        title = 'Shift',
                ))                        

                for key in self.KEYS if not shift else self.SHIFT_KEYS:
                        oc.add(DirectoryObject(
                                key   = Callback(self.Keyboard, query=query+key if query else key),
                                title = u'%s' % key,
                        ))

                return oc

        def History(self):

                oc = ObjectContainer()

                if len(Dict['DumbKeyboard-History']) > 0:
                        oc.add(DirectoryObject(
                                key   = Callback(self.ClearHistory),
                                title = u'%s' % L('Clear History')
                        ))

                for item in Dict['DumbKeyboard-History']:
                        oc.add(DirectoryObject(
                                key   = Callback(self.Submit, query=item),
                                title = u'%s' % item,
                        ))

                return oc

        def ClearHistory(self):

                Dict['DumbKeyboard-History'] = []
                Dict.Save()

                return self.History()

        def AddHistory(self, query):

                if not query in Dict['DumbKeyboard-History']:
                        Dict['DumbKeyboard-History'].append(query)
                        Dict.Save()

        def Submit(self, query):

                self.AddHistory(query)

                kwargs = {'query': query}
                kwargs.update(self.callback_args)
                
                return self.Callback(**kwargs)

class DumbPrefs:

        clients = ['Plex for iOS', 'Plex Media Player', 'Plex Home Theater', 'OpenPHT', 'Plex for Roku']

        def __init__(self, prefix, oc, title=None, thumb=None):

                Route.Connect(prefix+'/dumbprefs/list',     self.ListPrefs)
                Route.Connect(prefix+'/dumbprefs/listenum', self.ListEnum)
                Route.Connect(prefix+'/dumbprefs/set',      self.Set)
                Route.Connect(prefix+'/dumbprefs/settext',  self.SetText)

                oc.add(DirectoryObject(
                        key   = Callback(self.ListPrefs),
                        title = title if title else L('Preferences'),
                        thumb = thumb,
                ))

                self.prefix = prefix
                self.host = 'http://127.0.0.1:32400'

                self.GetPrefs()

        def GetPrefs(self):

                try:
                        data  = HTTP.Request("%s/:/plugins/%s/prefs" % (self.host, Plugin.Identifier), headers=Request.Headers, immediate=True, cacheTime=0).content
                        prefs = XML.ElementFromString(data).xpath('/MediaContainer/Setting')
                except Exception as e:
                        Log(str(e))
                        prefs = []

                defaultPrefs = []
                for pref in prefs:
                        item = {}
                        item['id']      = pref.xpath("@id")[0]
                        item['type']    = pref.xpath("@type")[0]
                        item['label']   = pref.xpath("@label")[0]
                        item['default'] = pref.xpath("@default")[0]
                        item['secure']  = True if pref.xpath("@secure")[0] == "true" else False
                        if item['type'] == "enum":
                                item['values'] = pref.xpath("@values")[0].split("|")

                        defaultPrefs.append(item)

                self.prefs = defaultPrefs

        def Set(self, key, value):

                HTTP.Request("%s/:/plugins/%s/prefs/set?%s=%s" % (self.host, Plugin.Identifier, key, value), headers=Request.Headers, immediate=True)
                return ObjectContainer()

        def ListPrefs(self):

                oc = ObjectContainer(no_cache=True)

                for pref in self.prefs:

                        do = DirectoryObject()

                        value = Prefs[pref['id']] if not pref['secure'] else ''.join(['*' for i in range(len(Prefs[pref['id']]))])
                        title = u'%s: %s = %s' % (L(pref['label']), pref['type'], value)

                        if pref['type'] == 'enum':
                                do.key = Callback(self.ListEnum, id=pref['id'])
                        elif pref['type'] == 'bool':
                                do.key = Callback(self.Set, key=pref['id'], value=str(not Prefs[pref['id']]).lower())
                        elif pref['type'] == 'text':
                                if Client.Product in DumbKeyboard.clients:
                                        DumbKeyboard(self.prefix, oc, self.SetText, id=pref['id'],
                                                dktitle       = title,
                                                dkplaceholder = Prefs[pref['id']],
                                                dksecure      = pref['secure']
                                        )
                                else:
                                        oc.add(InputDirectoryObject(
                                                key   = Callback(self.SetText, id=pref['id']),
                                                title = title
                                        ))
                                continue
                        else:
                                do.key = Callback(self.ListPrefs)

                        do.title = title

                        oc.add(do)

                return oc

        def ListEnum(self, id):

                oc = ObjectContainer()

                for pref in self.prefs:
                        if pref['id'] == id:
                                for i, option in enumerate(pref['values']):
                                        oc.add(DirectoryObject(
                                                key = Callback(self.Set, key=id, value=i),
                                                title = u'%s' % option,
                                        ))
                return oc

        def SetText(self, query, id):

                return self.Set(key=id, value=query)
