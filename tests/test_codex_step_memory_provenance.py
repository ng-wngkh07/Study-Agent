"""Actual MLX log memory must survive per-step recording without becoming process RSS."""
import json
import pytest
from app.run_ledger import RunLedger
from app.training_telemetry import TrainingTelemetry

@pytest.mark.parametrize(('suffix','expected'),[('2.667 GB',2.667),('3200 MB',3.2)])
def test_recorded_step_preserves_reported_mlx_memory_separate_from_rss(tmp_path,suffix,expected):
    ledger=RunLedger(tmp_path/'runs',tmp_path/'events.jsonl')
    original={'run_id':'memory-proof','status':'RUNNING','created_at':'2026-10-04T03:00:00Z',
              'telemetry':{'start_time':'2026-10-04T03:00:00Z','step_losses':[],
                           'peak_memory_mb':1945.4,'mlx_peak_memory_gb':None}}
    (ledger.runs_dir/'memory-proof.json').write_text(json.dumps(original))
    log=tmp_path/'train.log';log.write_text(f'Iter 5: Train loss 2.044, Peak mem {suffix}\n')
    observer=TrainingTelemetry(ledger,'memory-proof',log,tmp_path/'no-adapter');observer.poll();observer.poll()
    telemetry=ledger.get_run('memory-proof')['telemetry']
    assert len(telemetry['step_losses'])==1
    step=telemetry['step_losses'][0]
    assert step.get('mlx_peak_memory_gb')==expected
    assert step.get('memory_mb_measured') is False
    assert telemetry['peak_memory_mb']==1945.4
    assert telemetry['mlx_peak_memory_gb']==expected

def test_loss_without_memory_is_explicitly_unmeasured(tmp_path):
    ledger=RunLedger(tmp_path/'runs',tmp_path/'events.jsonl')
    (ledger.runs_dir/'unknown.json').write_text(json.dumps({'run_id':'unknown','telemetry':{'step_losses':[],'peak_memory_mb':0}}))
    log=tmp_path/'train.log';log.write_text('Iter 10: Train loss 1.25\n')
    TrainingTelemetry(ledger,'unknown',log,tmp_path/'no-adapter').poll()
    step=ledger.get_run('unknown')['telemetry']['step_losses'][0]
    assert step.get('memory_mb_measured') is False
    assert step.get('mlx_peak_memory_gb') is None

def test_memory_of_previous_line_cannot_be_attributed_to_unmeasured_step(tmp_path):
    ledger=RunLedger(tmp_path/'runs',tmp_path/'events.jsonl')
    (ledger.runs_dir/'unknown.json').write_text(json.dumps({'run_id':'unknown','status':'RUNNING','created_at':'2026-10-04T03:00:00Z','telemetry':{'start_time':'2026-10-04T03:00:00Z','step_losses':[],'peak_memory_mb':0}}))
    log=tmp_path/'train.log';log.write_text('Iter 5: Train loss 1.5, Peak mem 2.6 GB\nIter 10: Train loss 1.25\n')
    TrainingTelemetry(ledger,'unknown',log,tmp_path/'no-adapter').poll()
    steps=ledger.get_run('unknown')['telemetry']['step_losses']
    assert steps[0].get('mlx_peak_memory_gb')==2.6
    assert steps[1].get('mlx_peak_memory_gb') is None
