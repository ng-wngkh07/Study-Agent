"""Observe actual MLX loss/save events without relabeling unchanged weights."""
import math
import re
from pathlib import Path
from app.run_ledger import compute_file_sha256, STATUS_RUNNING


class TrainingTelemetry:
    def __init__(self, ledger, run_id, log_path: Path, adapter_dir: Path):
        self.ledger, self.run_id = ledger, run_id
        self.log_path, self.adapter_dir = Path(log_path), Path(adapter_dir)
        self.offset = 0
        self.pending = ''
        self.loss_steps = set()
        self.latest_loss_step = 0
        self.saved_step = 0
        self.peak_gb = None
        self.checkpoint_stats = {}

    def poll(self, final=False):
        if self.log_path.is_file():
            with self.log_path.open('r',encoding='utf-8',errors='replace') as f:
                f.seek(self.offset); chunk = self.pending+f.read(); self.offset = f.tell()
            lines = chunk.splitlines(keepends=True)
            self.pending = ''
            if lines and not lines[-1].endswith(('\n','\r')) and not final:
                self.pending = lines.pop()
            old_peak = self.peak_gb
            for line in lines:
                # Keep the value reported on this line separate from process RSS.
                # An earlier peak must not fill a later unmeasured step.
                line_peak_gb = None
                peak = re.search(r'Peak mem(?:ory)?(?:\s*\(GB\))?\s*:?\s*([0-9.]+)\s*(GB|MB)?',line,re.I)
                if peak:
                    measured = float(peak[1])/(1000 if (peak[2] or 'GB').upper()=='MB' else 1)
                    if math.isfinite(measured) and measured > 0:
                        line_peak_gb = measured
                        self.peak_gb=max(self.peak_gb or 0,measured)
                loss = re.search(r'Iter\s+(\d+):\s+Train\s+loss\s+([0-9.eE+-]+)',line)
                if loss:
                    step,value = int(loss[1]),float(loss[2])
                    if math.isfinite(value) and step not in self.loss_steps:
                        self.loss_steps.add(step); self.latest_loss_step=max(self.latest_loss_step,step)
                        self.ledger.record_step(self.run_id,step=step,loss=value,
                                                mlx_peak_memory_gb=line_peak_gb)
                saved = re.search(r'Iter\s+(\d+):\s+Saved adapter weights to',line)
                if saved: self.saved_step=max(self.saved_step,int(saved[1]))
            if self.peak_gb != old_peak:
                self.ledger.update_status(self.run_id,STATUS_RUNNING,mlx_peak_memory_gb=self.peak_gb)
        if not self.adapter_dir.is_dir(): return
        numbered = []
        for path in sorted(self.adapter_dir.glob('*.safetensors')):
            match = re.match(r'^(\d+)_adapters\.safetensors$',path.name)
            if match: numbered.append((int(match[1]),path))
        for step,path in numbered:
            self._record(path,step)
        latest = self.adapter_dir/'adapters.safetensors'
        if latest.is_file():
            # A numbered checkpoint proves the step even when stdout is buffered.
            latest_hash = compute_file_sha256(latest)
            matched = [step for step,path in numbered if compute_file_sha256(path)==latest_hash]
            step = max(matched) if matched else self.saved_step
            if step>0: self._record(latest,step)

    def _record(self,path,step):
        st=path.stat(); signature=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns,step)
        if self.checkpoint_stats.get(path)==signature: return
        self.ledger.record_checkpoint(self.run_id,step=step,checkpoint_path=path)
        self.checkpoint_stats[path]=signature
