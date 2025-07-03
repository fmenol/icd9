import json
import re
import requests
from pyquery import PyQuery as pq
from urllib.parse import urlparse
from collections import deque
from typing import Any, Callable, List, Dict, Optional


class Scraper:
    def __init__(self, handlers: List[Callable]):
        self.stack: deque = deque()
        self.hostname: str = ''
        self.handlers: List[Callable] = handlers
        self.cache: Dict[str, str] = {}

    def path(self, url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.path}?{parsed.query}"

    def push(self, depth: int, url: str, parents: Optional[List[Any]] = None) -> None:
        if parents is None:
            parents = []
        if not self.hostname:
            self.hostname = f"http://{urlparse(url).netloc}"
        self.stack.appendleft([depth, url, parents])

    def run(self):
        n = 0
        while len(self.stack):
            n += 1
            item = self.stack.popleft()
            depth = item[0]
            url = str(item[1])
            parents = item[2]
            print(f"proc: {depth}\t{len(self.stack)}\t{url}")

            if depth >= len(self.handlers):
                print(f"reached max-depth {depth} on {url}")
                continue

            if url in self.cache:
                print("cache hit")
                links = json.loads(self.cache[url])
            else:
                resp = requests.get(url)
                html = resp.content
                dom = pq(html)

                handler = self.handlers[depth]
                links = handler(dom)
                if len(links) == 0 and depth < len(self.handlers) - 1:
                    links = self.handlers[depth + 1](dom)
                self.cache[url] = json.dumps(links)

            for link in reversed(links):
                link['depth'] = depth + 1
                path = link['href']
                newparents = list(parents)
                newparents.append(link)
                newurl = f"{self.hostname}/{path}"
                if path:
                    self.push(depth + 1, newurl, newparents)
                else:
                    print(link)
                    yield newparents


def levelFactory(asel: str, textsel: str, extractor: Callable) -> Callable:
    def f(dom):
        aels = dom.find(asel)
        links = []
        for el in aels:
            el = pq(el)
            text = el.find(textsel).text()
            code = extractor(text)
            href = el.find('a').attr('href')
            ret = {'href': href}
            ret.update(code)
            links.append(ret)
        return list(filter(bool, links))
    return f

def startendExtractorFactory(regex: str) -> Callable:
    matcher = re.compile(regex)
    def f(text: str) -> Dict[str, Any]:
        if not text:
            return {'code': None}
        match = matcher.search(text)
        if not match:
            print(f"no codes from {text}")
            return {'code': None}
        group = match.groupdict()
        if group.get('end'):
            code = f"{group['start']}-{group['end']}"
        else:
            code = group['start']
        return {'code': code, 'descr': group['descr']}
    return f

def singleExtractorFactory(regex: str) -> Callable:
    matcher = re.compile(regex)
    def f(text: str) -> Dict[str, Any]:
        if not text:
            return {'code': None}
        match = matcher.search(text)
        if match:
            group = match.groupdict()
            if group.get('code'):
                return dict(group)
        print(f"no codes from {text}")
        return {'code': None}
    return f


if __name__ == '__main__':
    regex1 = r'^(\d+\.\s*)?(?P<descr>[\-\d\w\s\,\.]*)\s*\((?P<start>\w?\d+)(-(?P<end>\w?\d+)\))?'
    regex2 = r'^(?P<descr>[\-\d\w\s\,\.]*)\s*\((?P<start>\w?\d+)(-(?P<end>\w?\d+)\))?'
    regex3 = r'^\s*(?P<code>\w?\d+(\.\d*)?)\s+(?P<descr>.*)'
    l1links = levelFactory('.lvl1', 'div.chapter', startendExtractorFactory(regex1))
    l2links = levelFactory('.lvl2', 'div.section', startendExtractorFactory(regex2))
    l3links = levelFactory('.lvl3', 'div.dlvl', singleExtractorFactory(regex3))
    l4links = levelFactory('.lvl4', 'div.dlvl', singleExtractorFactory(regex3))
    l5links = levelFactory('.lvl5', 'div.dlvl', singleExtractorFactory(regex3))
    handlers = [l1links, l2links, l3links, l4links, l5links]
    scraper = Scraper(handlers)
    scraper.push(0, 'http://icd9cm.chrisendres.com/index.php?action=contents')
    hierarchies = scraper.run()

    with open('./codes.json', 'w') as f:
        codes = [x for x in hierarchies]
        f.write(json.dumps(codes))

