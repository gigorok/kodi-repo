import sys
import urllib
import urllib2
from urlparse import parse_qsl
import xbmcgui
import xbmcplugin
import xbmcaddon
import json

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

_addon_name = 'plugin.video.video-hub'
_addon = xbmcaddon.Addon(id=_addon_name)

API_URL = _addon.getSetting("api_url")
API_KEY = _addon.getSetting("api_key")


def api_request(url):
    """
    Make API request.

    :return: JSON string
    :rtype: list
    """
    req = urllib2.Request(url)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Accept', 'application/json')
    req.add_header('X-Api-Key', API_KEY)
    req.add_header('X-Api-Version', 'V1')
    resp = urllib2.urlopen(req)
    return resp.read()


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urllib.urlencode(kwargs))


def get_items(item_id=None):
    url = "%s/api/items" % API_URL
    if item_id is not None:
        url = '{0}?{1}'.format(url, urllib.urlencode({'item_id': item_id}))

    json_string = api_request(url)
    return json.loads(json_string)


def list_items(item_id=None):
    items = get_items(item_id)
    for item in items:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=item['label'])

        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt(item['art'])

        # Set additional info for the list item.
        # Here we use a category name for both properties for for simplicity's sake.
        # setInfo allows to set various information for an item.
        # For available properties see the following link:
        # http://mirrors.xbmc.org/docs/python-docs/15.x-isengard/xbmcgui.html#ListItem-setInfo
        list_item.setInfo('video', item['info'])

        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = item['is_folder']

        if is_folder:
            url = get_url(action='listing', item_id=item['id'])
        else:
            url = get_url(action='play', url=item['url'])
            # Set 'IsPlayable' property to 'true'.
            # This is mandatory for playable items!
            list_item.setProperty('IsPlayable', 'true')

        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'listing':
            # Display the list of videos in a provided category.
            list_items(params['item_id'])
        elif params['action'] == 'play':
            # Play a video from a provided URL.
            play_video(params['url'])
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        list_items()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
