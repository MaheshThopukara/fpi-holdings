"""Fetch NSDL's fortnightly FPI report (assets under custody) and keep data/fpi_auc.json up to date.

Runs on GitHub Actions. NSDL publishes a report for the 15th and the last day of each month, a few days later.
Each run reads the list of reports, adds any new ones to the JSON, and exits. Nothing is written when nothing changed.
"""
import datetime as dt
import html
import json
import pathlib
import re
import sys
import urllib.request

BASE = 'https://www.fpi.nsdl.co.in/web/'
LIST = BASE + 'Reports/FPI_Fortnightly_Selection.aspx'
OUT = pathlib.Path(__file__).parent / 'data' / 'fpi_auc.json'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36'
SINCE = dt.date(2025, 12, 31)          # keep this year's history plus the year-end starting point


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,*/*'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode('utf-8', 'ignore')


def num(s):
    s = s.replace(',', '').strip()
    neg = s.startswith('(') and s.endswith(')')
    v = float(s.strip('()'))
    return -v if neg else v


def parse(page):
    """The Grand Total row: 8 blocks of 12 columns (AUC start INR/USD, net 1st half INR/USD, net 2nd half INR/USD, AUC end INR/USD).
    Column 1 of a block is equity, column 12 the total."""
    t = re.sub(r'<script.*?</script>|<style.*?</style>', '', page, flags=re.S)
    t = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', t)))
    dates = re.findall(r'AUC as on ([A-Za-z]+ \d+, \d{4})', t)
    g = t[t.rfind('Grand Total'):].split()[2:2 + 96]
    if len(dates) < 2 or len(g) < 96:
        raise ValueError('unexpected report layout')
    d = dt.datetime.strptime(dates[-1], '%B %d, %Y').date()
    row = {'d': d.isoformat(), 'eq': num(g[72]), 'eqUsd': num(g[84]), 'tot': num(g[83]), 'net': num(g[48]), 'netUsd': num(g[60])}
    if not (1e6 < row['eq'] < 1e8):                         # ₹10 lakh cr .. ₹1,000 lakh cr: anything else is a parse error
        raise ValueError('equity AUC out of range: %s' % row['eq'])
    return row


def main():
    old = json.loads(OUT.read_text()) if OUT.exists() else []
    have = {r['d'] for r in old}
    opts = re.findall(r'<option value="~/(StaticReports/[^"]+)">([^<]+)', get(LIST))
    if not opts:
        sys.exit('NSDL list page had no reports')
    new = []
    for path, _ in opts[:6]:                                # the newest few are enough; history is already in the file
        row = parse(get(BASE + path))
        if dt.date.fromisoformat(row['d']) >= SINCE and row['d'] not in have:
            new.append(row)
    if not new:
        print('no new report; latest on file', max(have) if have else None)
        return
    rows = sorted(old + new, key=lambda r: r['d'])
    OUT.write_text(json.dumps(rows, indent=1) + '\n')
    print('added', [r['d'] for r in new])


if __name__ == '__main__':
    main()
