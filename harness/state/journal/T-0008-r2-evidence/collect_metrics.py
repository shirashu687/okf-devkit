from pathlib import Path
from collections import Counter
import json

root = Path(__file__).resolve().parent
result = {}
for arm in ('A', 'B'):
    path = root / arm
    events = [json.loads(line) for line in (path/'trial-events.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    seq = [event['seq'] for event in events]
    assert len(seq) == len(set(seq)) and seq == sorted(seq), (arm, 'duplicate or unordered sequence')
    counts = Counter(event['kind'] for event in events)
    reads = [event for event in events if event['kind'] == 'read']
    known = [event['chars_read'] for event in reads if isinstance(event.get('chars_read'), int)]
    result[arm] = {
        'event_count':len(events), 'events_by_kind':dict(counts),
        'search_retry_events':sum(event.get('search_retry') is True for event in events),
        'read_events_with_character_counts':len(known), 'read_events_total':len(reads),
        'recorded_read_chars_only':sum(known) if known else None,
        'self_report':json.loads((path/'trial-result.json').read_text(encoding='utf-8-sig')),
    }
(root/'metrics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
