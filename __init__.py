# -*- coding: utf-8 -*-
# Copyright (c) 2024 Manuel Schneider

import json
import re
from pathlib import Path
from time import sleep
from urllib import request, parse

from albert import *

md_iid = "5.0"
md_version = "2.1.1"
md_name = "Arch Linux Wiki"
md_description = "Search Arch Linux Wiki articles"
md_license = "MIT"
md_url = "https://github.com/albertlauncher/albert-plugin-python-arch-wiki"
md_authors = ["@ManuelSchneid3r"]
md_maintainers = ["@ManuelSchneid3r"]


class Plugin(PluginInstance, GeneratorQueryHandler):
    wikiurl = "https://wiki.archlinux.org/title/"
    baseurl = 'https://wiki.archlinux.org/api.php'
    search_url = "https://wiki.archlinux.org/index.php?search=%s"
    user_agent = "org.albert.extension.python.archwiki"

    def __init__(self):
        PluginInstance.__init__(self)
        GeneratorQueryHandler.__init__(self)

    def defaultTrigger(self):
        return 'awiki '

    @staticmethod
    def makeIcon():
        return makeImageIcon(Path(__file__).parent / "arch.svg")

    def fetch(self, query: str, batch_size: int, offset: int):

        params = {
            'action': 'query',
            'format': 'json',
            'formatversion': 2,
            'list': 'search',
            'srlimit': batch_size,
            'sroffset': offset,
            'srsearch': query,
        }

        get_url = "%s?%s" % (self.baseurl, parse.urlencode(params))
        req = request.Request(get_url, headers={'User-Agent': self.user_agent})

        with request.urlopen(req) as response:
            data = json.loads(response.read().decode())

        results = []

        for match in data['query']['search']:

            title = match['title']
            snippet = re.sub("<.*?>", "", match['snippet'])
            url = self.wikiurl + parse.quote(title.replace(' ', '_'))

            results.append(
                StandardItem(
                    id=self.id(),
                    text=title,
                    subtext=snippet if snippet else url,
                    icon_factory=Plugin.makeIcon,
                    actions=[
                        Action("open", "Open article", lambda u=url: openUrl(u)),
                        Action("copy", "Copy URL", lambda u=url: setClipboardText(u))
                    ]
                )
            )

        return results

    def items(self, ctx):
        query = ctx.query.strip()

        if not query:
            yield [
                StandardItem(
                    id=self.id(),
                    text=self.name(),
                    subtext="Enter a query to search in the Arch Wiki",
                    icon_factory=Plugin.makeIcon
                )
            ]
            return

        # avoid rate limiting
        for _ in range(50):
            sleep(0.01)
            if not ctx.isValid:
                return


        offset = 0
        items = self.fetch(query, 10, offset)

        if not items:
            yield [
                StandardItem(
                    id=self.id(),
                    text="Search '%s'" % query.string,
                    subtext="No results. Start online search on Arch Wiki",
                    icon_factory=self.makeIcon,
                    actions=[Action("search", "Open search",
                                    lambda s=query.string: openUrl(self.search_url % s))]
                )
            ]
            return

        while items:
            yield items
            offset += 10
            items = self.fetch(query, 10, offset)
