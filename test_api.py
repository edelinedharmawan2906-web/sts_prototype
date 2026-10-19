import unittest
from fastapi.testclient import TestClient
from api import app,sessions,ROOT
from demo_data import run_demo,landmarks

class ApiTest(unittest.TestCase):
    def setUp(self):
        sessions.clear();self.client=TestClient(app)
    def tearDown(self):
        for sid in list(sessions):
            (ROOT/'results_api'/(sid+'.json')).unlink(missing_ok=True)
        sessions.clear()
    def test_end_to_end(self):
        sid,result=run_demo(self.client)
        self.assertEqual(result['complete'],1);self.assertEqual(result['cycles'],1)
        self.assertEqual(result['mode'],'LATIHAN')
        second=self.client.post('/sessions',json={}).json()['session_id']
        self.assertEqual(self.client.get('/sessions/'+second).json()['complete'],0)
        self.assertEqual(self.client.post('/sessions/'+sid+'/finish').status_code,200)
        self.assertTrue((ROOT/'results_api'/(sid+'.json')).exists())
        self.assertEqual(self.client.post('/sessions/'+sid+'/frames',json={'t':99}).status_code,409)
        data=self.client.get('/sessions/'+sid+'/export').json()
        self.assertEqual(data['angle_source'],'geometry_2d');self.assertGreater(len(data['frames']),300)
    def test_validation_and_missing(self):
        sid=self.client.post('/sessions',json={}).json()['session_id'];url='/sessions/'+sid
        self.assertEqual(self.client.post(url+'/calibration',json={'posture':'berdiri'}).status_code,409)
        self.client.post(url+'/calibration',json={'posture':'duduk','delay':10})
        for t in (0,1,2):
            self.assertEqual(self.client.post(url+'/frames',json={'t':t,'landmarks':None}).status_code,200)
        self.assertEqual(sessions[sid].pending['deadline'],10)
        self.assertEqual(self.client.post(url+'/frames',json={'t':2}).status_code,409)
        self.assertEqual(self.client.post(url+'/frames',json={'t':3,'landmarks':[]}).status_code,422)
        low=landmarks();low[23]['visibility']=.1
        self.assertIsNone(self.client.post(url+'/frames',json={'t':3,'landmarks':low}).json()['measurement'])
        self.assertEqual(self.client.get('/sessions/no-such-id').status_code,404)
    def test_geometry(self):
        from measurements import measure
        from types import SimpleNamespace as NS
        m=measure(NS(pose_landmarks=NS(landmark=[NS(**v) for v in landmarks()])),640,480)
        self.assertAlmostEqual(m['hip'],90);self.assertAlmostEqual(m['knee'],90)
        self.assertAlmostEqual(m['lean'],0)

if __name__=='__main__':unittest.main()
