"""Immutable per-sample history; a bad amendment never erases a good revision."""
import copy
import datetime
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path


class SampleLedger:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def record(self, sample_id, payload, status, reason, review=None):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',sample_id):
            raise ValueError('Invalid stable sample ID')
        if status not in ('proposed','source_verified','accepted','quarantined'):
            raise ValueError('Invalid sample state')
        target = payload.get('reference', payload.get('answer',''))
        target_hash = hashlib.sha256(target.encode()).hexdigest()
        if status=='accepted' and not (
            isinstance(review,dict) and review.get('reviewer')=='Codex'
            and review.get('grade')=='pass' and review.get('answer_sha256')==target_hash
            and review.get('source_verified') is True):
            raise ValueError('Accepted content requires a review bound to the exact target')
        existing = sorted(self.directory.glob(sample_id+'--*.json'))
        revision = max((int(p.stem.rsplit('--',1)[1]) for p in existing), default=0)+1
        event = {'schema':'study-sample-revision-v1','stable_id':sample_id,'revision':revision,
                 'status':status,'reason':str(reason),'payload':copy.deepcopy(payload),
                 'payload_sha256':hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
                 'answer_sha256':target_hash,'review':copy.deepcopy(review),
                 'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        path = self.directory/f'{sample_id}--{revision:05d}.json'
        # Publish a complete event atomically. Interrupted temporary files are
        # ignored; exclusive linking prevents replacing another writer's event.
        tmp = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                    dir=self.directory, prefix='.pending-', delete=False) as f:
                tmp = Path(f.name)
                json.dump(event,f,ensure_ascii=False,indent=2)
                f.write('\n');f.flush();os.fsync(f.fileno())
            os.link(tmp, path)
            directory_fd = os.open(self.directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if tmp is not None:
                tmp.unlink(missing_ok=True)
        return event

    def history(self):
        return [json.loads(p.read_text()) for p in sorted(self.directory.glob('*.json'))]

    def accepted(self):
        selected = {}
        for event in self.history():
            if event['status']=='accepted': selected[event['stable_id']]=event
        return list(selected.values())
