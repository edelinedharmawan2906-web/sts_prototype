"""Local learning API. Run one worker; sessions are stored in memory."""
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import json
import math
import statistics
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ConfigDict
from engine import Engine, Config
from calibration import collect_calibration, speed_stats
from diagnostics import pose_quality
from measurements import measure
from signals import MAX_SAMPLE_GAP
from serialization import json_scalar

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="TA STS — FastAPI", version="0.1.0")
sessions = {}

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

class NewSession(StrictModel):
    width: int = Field(default=640, ge=100, le=4096)
    height: int = Field(default=480, ge=100, le=4096)

class Landmark(StrictModel):
    x: float
    y: float
    z: float = 0
    visibility: float = Field(ge=0, le=1)

class Frame(StrictModel):
    t: float = Field(ge=0, description="Seconds from session origin; strictly increasing")
    landmarks: list[Landmark] | None = Field(default=None, min_length=33, max_length=33)

class Capture(StrictModel):
    posture: str = Field(pattern="^(duduk|berdiri)$")
    delay: float = Field(default=10, ge=0, le=30)

class Session:
    def __init__(self, dimensions):
        self.width, self.height = dimensions.width, dimensions.height
        self.engine = Engine(Config(**json.loads((ROOT/'config.json').read_text())))
        self.mode = 'CAL_DUDUK'
        self.last_t = None
        self.filtered = None
        self.pending = None
        self.samples = []
        self.sitting_samples = []
        self.seated = self.standing = None
        self.ready_since = None
        self.rows = []
        self.message = 'Rekam duduk dahulu'
        self.closed = False

    def response(self):
        e = self.engine
        return dict(mode=self.mode, phase=e.state, message=self.message,
                    complete=e.complete, cycles=e.cycles, attempts=e.results,
                    measurement=self.filtered, calibrated=self.standing is not None,
                    calibration_samples=len(self.samples), closed=self.closed)

    def ingest(self, frame):
        t = frame.t
        if self.last_t is not None and t <= self.last_t:
            raise HTTPException(409, 'Timestamp harus meningkat; gunakan detik, bukan milidetik')
        if len(self.rows) >= 36000:
            raise HTTPException(409, 'Batas 36000 frame; akhiri sesi lalu buat sesi baru')
        if self.last_t is not None and t-self.last_t > MAX_SAMPLE_GAP:
            self.engine.missing(); self.filtered=None; self.samples=[]; self.ready_since=None
        self.last_t=t
        # Countdown starts on next frame, including missing-pose frames.
        if self.pending and self.pending['deadline'] is None:
            self.pending['deadline']=t+self.pending['delay']
        landmarks = None if frame.landmarks is None else SimpleNamespace(landmark=frame.landmarks)
        result = SimpleNamespace(pose_landmarks=landmarks)
        quality = pose_quality(result)
        try:
            m = measure(result,self.width,self.height) if quality['accepted'] else None
        except ValueError:
            m=None
        if m is None:
            self.filtered=None; self.samples=[]; self.ready_since=None
            self.message=self.engine.missing()
        else:
            if self.filtered is None:
                self.filtered=m.copy(); self.filtered['_t']=t-1/30
            alpha=1-math.exp(-max(t-self.filtered['_t'],1e-3)/.12)
            for key in ('y','lean','hip','knee','thigh','ankle'):
                self.filtered[key]+=alpha*(m[key]-self.filtered[key])
            self.filtered['_t']=t
            if self.pending:
                remaining=self.pending['deadline']-t
                self.message=f'Persiapan {max(0,math.ceil(remaining))} detik'
                if remaining<=0:
                    done=collect_calibration(self.samples,t,self.filtered)
                    self.message=f'Merekam {self.pending["posture"]}: tahan diam 1 detik'
                    if done:
                        self.commit_calibration()
            if self.mode=='KEMBALI':
                progress=(self.seated-self.filtered['y'])/(self.seated-self.standing)
                if progress<=self.engine.cfg.seated_progress and self.filtered['hip']<120:
                    if self.ready_since is None: self.ready_since=t
                    if t-self.ready_since>=1:
                        self.mode='LATIHAN'
                else:
                    self.ready_since=None
            if self.mode=='LATIHAN':
                f=self.filtered
                progress=(self.seated-f['y'])/(self.seated-self.standing)
                self.message=self.engine.update(t,progress,f['lean'],f['hip'],f['knee'],f['thigh'],f['ankle'],False)
        self.rows.append(dict(t=t,landmarks=None if frame.landmarks is None else [lm.model_dump() for lm in frame.landmarks],measurement=None if self.filtered is None else dict(self.filtered),phase=self.engine.state,mode=self.mode))
        return self.response()

    def commit_calibration(self):
        e=self.engine
        ys=[m['y'] for _,m in self.samples]
        if self.pending['posture']=='duduk':
            self.seated=float(statistics.median(ys))
            self.sitting_samples=list(self.samples)
            e.lean_base=statistics.mean(m['lean'] for _,m in self.samples)
            e.lean_sd=statistics.pstdev(m['lean'] for _,m in self.samples)
            self.mode='CAL_BERDIRI'; self.message='Duduk tersimpan; rekam berdiri'
        else:
            standing=float(statistics.median(ys))
            if self.seated-standing < self.height*.08:
                self.samples=[]; self.message='Kenaikan belum cukup; rekam berdiri diulang'
                return
            try:
                e.speed_baseline,e.speed_sd,e.rise_threshold=speed_stats(self.sitting_samples,self.seated-standing,e.cfg.speed_sd_multiplier,e.cfg.speed_window)
            except ValueError:
                self.pending=None; self.samples=[]; self.mode='CAL_DUDUK'
                self.message='Kalibrasi noise gagal; ulangi dari duduk'
                return
            self.standing=standing; self.mode='KEMBALI'
            self.message='Berdiri tersimpan; kembali duduk selama 1 detik'
        self.pending=None; self.samples=[]

    def export(self):
        e=self.engine
        return dict(version='0.5.6+api0.1',source='TA original engine',angle_source='geometry_2d',
                    config=vars(e.cfg),hand_warning={'enabled':False,'status':'DITUNDA'},
                    dimensions={'width':self.width,'height':self.height},
                    calibration=dict(seated_y=self.seated,standing_y=self.standing,lean_base=e.lean_base,lean_sd=e.lean_sd,speed_baseline=e.speed_baseline,speed_sd=e.speed_sd,rise_threshold=e.rise_threshold),
                    complete=e.complete,cycles=e.cycles,attempts=e.results,frames=self.rows)

def get_session(sid, writable=False):
    if sid not in sessions: raise HTTPException(404,'Sesi tidak ditemukan')
    s=sessions[sid]
    if writable and s.closed: raise HTTPException(409,'Sesi sudah diakhiri')
    return s

@app.get('/health')
def health(): return {'status':'ok','engine':'TA v0.5.6'}

@app.get('/')
def home(): return FileResponse(ROOT/'connection_test.html')

@app.get('/sts-client.ts')
def client_source(): return FileResponse(ROOT/'sts-client.ts',media_type='text/plain')

@app.post('/sessions',status_code=201)
def create_session(body:NewSession):
    if len(sessions)>=10: raise HTTPException(409,'Hapus sesi lama; batas belajar 10 sesi')
    sid=uuid4().hex; sessions[sid]=Session(body)
    return {'session_id':sid,**sessions[sid].response()}

@app.post('/sessions/{sid}/calibration')
def calibrate(sid:str,body:Capture):
    s=get_session(sid,True)
    expected='CAL_DUDUK' if body.posture=='duduk' else 'CAL_BERDIRI'
    if s.mode!=expected or s.pending:
        raise HTTPException(409,'Urutan: rekam duduk, rekam berdiri, kembali duduk, latihan')
    s.pending=dict(posture=body.posture,delay=body.delay,deadline=None); s.samples=[]
    return s.response()

@app.post('/sessions/{sid}/frames')
def ingest(sid:str,body:Frame): return get_session(sid,True).ingest(body)

@app.get('/sessions/{sid}')
def status(sid:str): return get_session(sid).response()

@app.post('/sessions/{sid}/finish')
def finish(sid:str):
    s=get_session(sid)
    if not s.closed:
        if s.engine.state=='BANGKIT':
            s.engine.observation_missing=True
            s.engine.finish(s.last_t or 0,False)
        s.closed=True
        data=json.loads(json.dumps(s.export(),default=json_scalar,allow_nan=False))
        output=ROOT/'results_api'; output.mkdir(exist_ok=True)
        (output/(sid+'.json')).write_text(json.dumps(data,indent=2),encoding='utf-8')
    return s.response()

@app.get('/sessions/{sid}/export')
def export(sid:str):
    data=get_session(sid).export()
    return json.loads(json.dumps(data,default=json_scalar,allow_nan=False))

@app.delete('/sessions/{sid}',status_code=204)
def delete(sid:str):
    get_session(sid); del sessions[sid]
