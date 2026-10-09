"""Official author-directory monitor. Dates are observation dates, never publication dates."""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlencode
from bs4 import BeautifulSoup
from .base import curl_get

DIRECTORY = 'https://www.sdwang.org/research.html'
SNAPSHOT = Path(__file__).resolve().parents[2] / 'database' / 'shaoda_wang_tracking.json'

def clean(text):
    return re.sub(r'\s+', ' ', text.replace('\u200b', '').replace('\ufeff', '')).strip()

def identity(title):
    return re.sub(r'[^a-z0-9]', '', title.lower())

def parse_directory(html):
    soup = BeautifulSoup(html, 'lxml')
    works = {}
    sections = ['publication', 'working_paper', 'work_in_progress', 'other_writing']
    paragraphs = soup.select('.paragraph')
    if len(paragraphs) != 4:
        raise ValueError('Research-directory layout changed: expected four sections')
    for paragraph, section in zip(paragraphs, sections):
        for media in paragraph.select('ul'):
            media.decompose()
        links = {identity(a.get_text()): urljoin(DIRECTORY, a.get('href', '')) for a in paragraph.select('a[href]') if identity(a.get_text())}
        for br in paragraph.select('br'):
            br.replace_with(' ')
        text = clean(paragraph.get_text())
        matches = list(re.finditer(r'"([^\"]+)"', text))
        for i, match in enumerate(matches):
            title = clean(match.group(1))
            key = identity(title)
            tail = clean(text[match.end():matches[i+1].start() if i+1 < len(matches) else len(text)])
            coauthors = re.search(r'\(with\s+(.*?)\)', tail)
            authors = 'Shaoda Wang' + (', ' + coauthors.group(1) if coauthors else '')
            metadata = clean(re.sub(r'^\s*\(with\s+.*?\)\s*', '', tail))
            works[key] = dict(title=title, authors=authors, section=section, status=metadata, paper_url=links.get(key, ''), directory_url=DIRECTORY)
    if len(works) < 20 or 'courtcapturelocalprotectionismandeconomicintegrationevidencefromchina' not in works:
        raise ValueError('Incomplete author directory; refusing to overwrite tracking baseline')
    return works

def reconcile(previous, works, observed_at):
    if previous is None:
        return dict(baseline_at=observed_at, last_checked=observed_at, works=works, events={})
    events = dict(previous.get('events', {}))
    for key, work in works.items():
        old = previous['works'].get(key)
        if old == work:
            continue
        version = hashlib.sha256(json.dumps(work, sort_keys=True).encode()).hexdigest()[:16]
        event_id = key + ':' + version
        if event_id not in events:
            events[event_id] = dict(work, event_id=event_id, change='new_work' if old is None else 'metadata_update', observed_at=observed_at, previous=old)
    # Retain disappeared works: removal or a partial response must not cause false new-work alerts.
    merged = dict(previous['works']); merged.update(works)
    return dict(baseline_at=previous['baseline_at'], last_checked=observed_at, works=merged, events=events)

class ShaodaWangScraper:
    source_id = 'shaoda_wang'
    source_name = 'Shaoda Wang (王绍达)'

    def __init__(self, snapshot_path=SNAPSHOT):
        self.snapshot_path = Path(snapshot_path)

    def scrape(self, since_date):
        try:
            works = parse_directory(curl_get(DIRECTORY))
            previous = json.loads(self.snapshot_path.read_text()) if self.snapshot_path.exists() else None
            tracked = reconcile(previous, works, datetime.now().isoformat(timespec='seconds'))
            self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.snapshot_path.with_suffix('.tmp')
            temporary.write_text(json.dumps(tracked, ensure_ascii=False, indent=2), encoding='utf-8')
            temporary.replace(self.snapshot_path)
            articles = []
            # Replay retained events until the ordinary database URL dedup acknowledges them.
            for event in tracked['events'].values():
                description = f"Author-directory observation ({event['change']}); publication date unavailable. Section: {event['section']}. Status: {event['status'] or 'not stated'}. Paper: {event['paper_url'] or DIRECTORY}."
                articles.append(dict(source_id=self.source_id, title=event['title'] + ' [Research update]', authors=event['authors'], affiliations='', date=event['observed_at'][:10], date_basis='first_observed', abstract=description, keywords=[], type='research_update', url=DIRECTORY + '?' + urlencode({'wang_event': event['event_id']}), paper_url=event['paper_url'], change=event['change'], observed_at=event['observed_at']))
            return articles, 'SUCCESS', None
        except Exception as exc:
            return [], 'FAILED', str(exc)
