# RedditImages.bundle
a Plex Media Server channel for images/gif content from reddit.com

with services for `imgur.com` and `gfycat.com` content.

### Usage:
Multiple reddit paths can be imported by creating a `paths.txt` file in: `Plex Media Server\Plug-in Support\Data\com.plexapp.plugins.redditimages\DataItems`. Each line represents one entry, with the format `name, path`. path can be the full url or the subpath.

example `paths.txt` file:
```
pics subreddit, https://www.reddit.com/r/pics
gifs subreddit, /r/gifs
gifs and pics, /r/gifs+pics
user curated multi, /user/Username/m/multiname
```

Then load them by using the `Import paths from paths.txt` button in the channels main menu.
