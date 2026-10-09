from types import SimpleNamespace
from app.training_telemetry import TrainingTelemetry


def test_loss_progress_cannot_relabel_saved_checkpoint(tmp_path):
    seen=[]; losses=[]; updates=[]
    ledger=SimpleNamespace(record_checkpoint=lambda *a,**k:seen.append((k['checkpoint_path'].name,k['step'])),
        record_step=lambda *a,**k:losses.append(k['step']),update_status=lambda *a,**k:updates.append(k))
    log=tmp_path/'train.log'; weights=tmp_path/'adapters.safetensors'; weights.write_bytes(b'step40')
    log.write_text('Iter 40: Train loss 1.25, Peak mem 3.141 GB\nIter 40: Saved adapter weights to adapters.safetensors.\n')
    observer=TrainingTelemetry(ledger,'isolated',log,tmp_path);observer.poll()
    log.open('a').write('Iter 50: Train loss 1.20, Peak mem 3.145 GB\n');observer.poll();observer.poll()
    assert seen==[('adapters.safetensors',40)]
    assert losses==[40,50]
    assert updates[-1]['mlx_peak_memory_gb']==3.145


def test_buffered_save_event_uses_matching_numbered_weights(tmp_path):
    seen=[]
    ledger=SimpleNamespace(record_checkpoint=lambda *a,**k:seen.append((k['checkpoint_path'].name,k['step'])),
        record_step=lambda *a,**k:None,update_status=lambda *a,**k:None)
    log=tmp_path/'train.log';log.write_text('Iter 40: Train loss 1.2, Peak mem 3200 MB\n')
    (tmp_path/'adapters.safetensors').write_bytes(b'step40')
    (tmp_path/'0000040_adapters.safetensors').write_bytes(b'step40')
    observer=TrainingTelemetry(ledger,'isolated',log,tmp_path);observer.poll()
    assert ('adapters.safetensors',40) in seen
    assert observer.peak_gb==3.2


def test_partial_log_lines_are_not_lost_or_recorded_twice(tmp_path):
    losses=[]
    ledger=SimpleNamespace(record_checkpoint=lambda *a,**k:None,
        record_step=lambda *a,**k:losses.append((k['step'],k['loss'])),update_status=lambda *a,**k:None)
    log=tmp_path/'train.log';log.write_text('Iter 10: Train loss 1.')
    observer=TrainingTelemetry(ledger,'isolated',log,tmp_path);observer.poll();assert losses==[]
    log.open('a').write('25, Peak mem 2.7 GB\n');observer.poll();observer.poll(final=True)
    assert losses==[(10,1.25)]
