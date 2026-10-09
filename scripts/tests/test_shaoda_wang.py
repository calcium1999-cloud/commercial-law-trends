import sys, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT / 'scripts'))
from scrapers.shaoda_wang import parse_directory, reconcile, ShaodaWangScraper
from run_weekly import filter_and_dedup, get_existing_urls, validate_db, validate_html
HTML=(Path(__file__).parent / 'fixtures' / 'shaoda_wang_research.html').read_text()
class WangTests(unittest.TestCase):
 def test_live_fixture(self):
  w=parse_directory(HTML); self.assertEqual(len(w),28)
  court=next(x for x in w.values() if x['title'].startswith('Court Capture'))
  self.assertIn('Forthcoming',court['status']); self.assertTrue(court['paper_url'].endswith('.pdf'))
  self.assertTrue(any(x['section']=='work_in_progress' and not x['paper_url'] for x in w.values()))
 def test_baseline_no_historical_flood(self):
  self.assertEqual(reconcile(None,parse_directory(HTML),'2026-10-09T12:00:00')['events'],{})
 def test_changes_and_retry_dedup(self):
  w=parse_directory(HTML); b=reconcile(None,w,'2026-10-09T12:00:00')
  self.assertEqual(reconcile(b,w,'2026-10-09T13:00:00')['events'],{})
  changed={k:dict(v) for k,v in w.items()}; k=next(iter(changed)); changed[k]['status']='Published'; changed['newpaper']=dict(changed[k],title='New paper')
  c=reconcile(b,changed,'2026-10-09T14:00:00'); self.assertEqual(len(c['events']),2)
  self.assertEqual(reconcile(c,changed,'2026-10-09T15:00:00')['events'],c['events'])
 def test_scraper_replay_and_failure(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'tracking.json'; scraper=ShaodaWangScraper(p)
   with patch('scrapers.shaoda_wang.curl_get',return_value=HTML):
    self.assertEqual(scraper.scrape('2026-10-09')[0],[])
   before=p.read_text()
   with patch('scrapers.shaoda_wang.curl_get',return_value='<html>broken</html>'):
    self.assertEqual(scraper.scrape('2026-10-09')[1],'FAILED'); self.assertEqual(p.read_text(),before)
   modified=HTML.replace('Forthcoming','Published')
   with patch('scrapers.shaoda_wang.curl_get',return_value=modified):
    a= scraper.scrape('2026-10-09')[0]; self.assertEqual(len(a),1)
    self.assertEqual(scraper.scrape('2026-10-10')[0],a)
    self.assertEqual(filter_and_dedup(a,get_existing_urls({'articles':a})),([],1))
 def test_project_validation(self):
  self.assertEqual(validate_db(ROOT / 'database' / 'articles.json'),[])
  self.assertEqual(validate_html(),[])
unittest.main(verbosity=2)
