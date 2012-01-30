from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import util
from google.appengine.api.images import Image, PNG
from google.appengine.api.urlfetch import fetch
import os
import re
import logging
from base64 import b64decode

FB_APP_ID = '221899141232550'
FB_APP_NS = 'castline'
FB_APP_NS_URL = 'http://ogp.me/ns/fb/castline'
APP_DOMAIN = '127.0.0.1:8080' if os.environ['APPLICATION_ID'][0:3] == 'dev' \
              else 'castlineapp.appspot.com'


class ObjectModel(db.Model):
    name = db.StringProperty(required = True)
    image = db.BlobProperty()
    image_type = db.StringProperty()
    description = db.StringProperty()
    og_type = 'object'
    slugifier = re.compile('[^a-zA-Z0-9]+')
    @classmethod
    def slugify(cls, string):
        return cls.slugifier.sub('-', string)
    def getType(self):
        return FB_APP_NS + ':' + self.og_type
    def getTitle(self):
        return self.name or "Unknown"
    def getDescription(self):
        return self.description or ""
    def getUrl(self, image=False):
        return 'http://' + APP_DOMAIN + '/' + self.og_type + '/' + ('image/' if image else '') + self.key().name()
    def getImageUrl(self):
        if self.image:
            return self.getUrl(True)
        return 'https://s-static.ak.fbcdn.net/images/devsite/attachment_blank.png'

class PodcastModel(ObjectModel):
    og_type = "podcast"

class PodcastEpisodeModel(ObjectModel):
    og_type = "podcast_episode"
    podcast = db.ReferenceProperty(PodcastModel)

class BaseHandler(webapp.RequestHandler):
    def write(self, string):
        self.response.out.write(string)

    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&apos;",
        ">": "&gt;",
        "<": "&lt;",
    }

    def html_escape(self, string):
        return "".join([self.html_escape_table.get(c, c) for c in string])


class ObjectHandler(BaseHandler):
    model = ObjectModel

    def getNamespaces(self):
        return {
            'og': 'http://ogp.me/ns',
            'fb': 'http://ogp.me/ns/fb',
            FB_APP_NS: FB_APP_NS_URL
        }
    def getProperties(self, obj):
        properties = {
            "fb:app_id": FB_APP_ID,
            "og:type": obj.getType(),
            "og:url": obj.getUrl(),
            "og:title": self.html_escape(obj.getTitle()),
            "og:description": self.html_escape(obj.getDescription()),
            "og:image": obj.getImageUrl(),
        }
        for (key, value) in self.getExtraProperties(obj).items():
            properties[key] = value
        return properties
    def getExtraProperties(self, obj):
        return {}

    def getHeader(self, obj):
        return (
            '<html>\n' +
            '\t<head prefix="' +
                ' '.join(['%s: %s#' % item for item in self.getNamespaces().items()]) +
            '">\n' +
            '\n'.join([
                '\t\t<meta property="%s" content="%s" />' % item
                for item in self.getProperties(obj).items()
            ]) +
            '\t</head>\n'
            '\t<body>\n'
        )
    def getFooter(self):
        return (
            '\t</body>\n' +
            '</html>'
        )

    def get(self, image, key):
        if key == '':
            for item in self.model.all():
                self.write('<a href="' + item.getUrl() + '">' + item.name + '</a><br/>')
            return
        obj = self.model.get_by_key_name(key)
        if not obj:
            logging.info(key)
            return self.error(404)
        if image:
            self.response.headers["Content-Type"] = obj.image_type
            self.write(obj.image)
        else:
            self.write(self.getHeader(obj))
            self.write('<h2>' + obj.name + '</h2>')
            self.write('<img src="' + obj.getImageUrl() + '">')
            self.write(obj.description)
            self.write(self.getFooter())


class PodcastObjectHandler(ObjectHandler):
    model = PodcastModel
    pass

class PodcastEpisodeObjectHandler(ObjectHandler):
    model = PodcastEpisodeModel
    def getExtraProperties(self, obj):
        return {
            "castline:podcast": obj.podcast.getUrl()
        }

class ActionHandler(BaseHandler):
    def post(self):

        podcast_name = self.request.get('podcast_name')
        podcast_episode_name = self.request.get('podcast_episode_name')
        podcast_episode_image = self.request.get('podcast_episode_image')

        try:
            image = b64decode(podcast_episode_image)
            if (Image(image).format == PNG):
                image_type = 'image/png'
            else:
                image_type = 'image/jpeg'
            logging.info(image_type)
        except:
            image_type = image = None
            logging.info (podcast_episode_image)

        if not podcast_name or not podcast_episode_name:
            return self.error(404)
        podcast = PodcastModel.get_or_insert(
            ObjectModel.slugify(podcast_name),
            name = podcast_name,
            image = image,
            image_type = image_type
        )
        podcast_episode = PodcastEpisodeModel.get_or_insert(
            ObjectModel.slugify(podcast_episode_name),
            name = podcast_episode_name,
            podcast = podcast,
            image = image,
            image_type = image_type
        )
        self.write(podcast_episode.getUrl())


class Handler(webapp.RequestHandler):
    def get(self, path):
        self.response.out.write('This is a private, experimental app... sorry')

if __name__ == '__main__':
    util.run_wsgi_app(webapp.WSGIApplication([
        ('/podcast_episode(/image)?/?(.*)', PodcastEpisodeObjectHandler),
        ('/podcast(/image)?/?(.*)', PodcastObjectHandler),
        ('/action', ActionHandler),
        ('(.*)', Handler)
    ], debug=True))
