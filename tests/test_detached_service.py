import json
import os
import subprocess
import sys
import time
from scripts.start_detached_service import start_detached


def test_child_owns_independent_session_and_survives_parent_exit(tmp_path):
    observation=tmp_path/'child.json'
    parent=tmp_path/'parent.py'
    # Publish the observation atomically: existence alone does not imply the
    # child's write has finished (the former test sometimes read empty JSON).
    pending = tmp_path / 'child.pending'
    child='import json,os,time; from pathlib import Path; time.sleep(0.1); Path('+repr(str(pending))+').write_text(json.dumps({"pid":os.getpid(),"session":os.getsid(0),"cwd":os.getcwd()})); os.replace('+repr(str(pending))+','+repr(str(observation))+')'
    parent.write_text('from scripts.start_detached_service import start_detached\nprint(start_detached('+repr([sys.executable,'-c',child])+','+repr(str(tmp_path/'log'))+','+repr(str(tmp_path))+'))\n')
    result=subprocess.run([sys.executable,str(parent)],env=dict(os.environ,PYTHONPATH=os.getcwd()),capture_output=True,text=True,check=True)
    pid=int(result.stdout)
    deadline=time.monotonic()+3
    while not observation.exists() and time.monotonic()<deadline:time.sleep(0.02)
    data=json.loads(observation.read_text())
    assert data['pid']==pid==data['session']
    assert data['cwd']==str(tmp_path)
