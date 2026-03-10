#!/usr/bin/env python3
import importlib.util
import json
import mimetypes
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'
ON_DEMAND = OUT / 'on-demand'


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


render_mod = load_module(ROOT / 'scripts' / 'render_digest.py', 'render_digest_mod')
pdf_mod = load_module(ROOT / 'scripts' / 'pdf_deep_read.py', 'pdf_deep_read_mod')


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(OUT), **kwargs)

    def end_json(self, code: int, obj):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/health':
            return self.end_json(200, {'ok': True, 'mode': 'local-server'})
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != '/api/deep-read':
            return self.end_json(404, {'ok': False, 'error': 'not found'})
        length = int(self.headers.get('Content-Length', '0') or '0')
        try:
            payload = json.loads(self.rfile.read(length) or b'{}')
        except Exception as e:
            return self.end_json(400, {'ok': False, 'error': f'bad json: {e}'})

        try:
            title = payload.get('title') or 'paper'
            pdf_link = payload.get('pdf_link') or ''
            item = dict(payload)
            if pdf_link:
                cache = pdf_mod.CACHE / f"{pdf_mod.slugify(title)}.pdf"
                pdf_path = pdf_mod.download(pdf_link, cache)
                item['pdf_analysis'] = pdf_mod.analyze(pdf_path, title, payload.get('summary', ''))
            else:
                item['pdf_analysis'] = {'mode': 'abstract', 'focus': render_mod.infer_focus(item)}
            ON_DEMAND.mkdir(parents=True, exist_ok=True)
            slug = render_mod.slugify(title)
            out = ON_DEMAND / f'{slug}.html'
            html = render_mod.render_analysis_html(item)
            out.write_text(html)
            return self.end_json(200, {'ok': True, 'path': f'./on-demand/{slug}.html', 'mode': item['pdf_analysis'].get('mode', 'abstract')})
        except Exception as e:
            return self.end_json(500, {'ok': False, 'error': str(e)})


def main():
    import os
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '8765'))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f'serving {OUT} at http://{host}:{port}')
    server.serve_forever()


if __name__ == '__main__':
    main()
