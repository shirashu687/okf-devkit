"""Same output-level acceptance oracle for both trials; authored before submissions."""
from html.parser import HTMLParser
from types import SimpleNamespace
import json
from okf_devkit import renderer

class Output(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.targets = [], []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('h2','h3','h4') and 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'a' and attrs.get('href','').startswith('#'):
            self.targets.append(attrs['href'][1:])

def render(headings):
    body = '\n\n'.join('## '+title for title in headings)+'\n'
    page = renderer.Page(SimpleNamespace(body=body), 'a.md', 'a.html')
    md = renderer._markdown()
    renderer._prepare_page(page, md)
    content = md.renderer.render(page.tokens, md.options, {})
    toc = renderer._render_toc(page.headings)
    output = Output()
    output.feed(content + toc)
    return content, toc, output

cases = [
    ['Foo','Foo','Foo-2'], ['Foo-2','Foo','Foo'],
    ['Foo','Foo','Bar'], ['Foo','Foo','Foo','Foo-2','Foo-3','Foo'],
    ['Foo-2','Foo-2','Foo-2-2','Foo','Foo'],
    ['!!!','!!!','section','section-2'], ['日本語','日本語','日本語-2'],
]
results = []
for headings in cases:
    content, toc, output = render(headings)
    assert len(output.ids) == len(headings), (headings, 'missing heading')
    assert len(output.ids) == len(set(output.ids)), (headings, output.ids)
    assert output.targets == output.ids, (headings, output.targets, output.ids)
    assert (content,toc) == render(headings)[:2], 'non-deterministic rendering'
    if headings == ['Foo','Foo','Bar']:
        assert output.ids == ['foo','foo-2','bar'], output.ids
    results.append({'input':headings,'anchors':output.ids,'result':'pass'})
print(json.dumps({'cases':results,'passed':len(results)},ensure_ascii=False))
