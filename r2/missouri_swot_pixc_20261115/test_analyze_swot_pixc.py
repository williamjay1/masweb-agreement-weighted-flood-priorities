import hashlib
import tempfile
import unittest
from pathlib import Path
import h5py
import numpy as np
import pandas as pd
from pyproj import Transformer
import analyze_swot_pixc as a

class PipelineTest(unittest.TestCase):
    def test_verified_streaming_and_missing_unknown(self):
        # Synthetic fixtures only, never project science data.
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as d:
            root=Path(d); raw=root/'raw'; raw.mkdir()
            sample=pd.DataFrame({'x':[200000.,200030.,200090.], 'y':[1600000.]*3,
                                 's30':[1,0,1], 'l30':[1,1,0]})
            sample.to_csv(root/'optical.csv',index=False)
            nominal=pd.DataFrame({'x_epsg5070':sample.x,'y_epsg5070':sample.y,'s30':sample.s30,'l30':sample.l30,
                                  'in_nominal_033_259':[True]*3,'in_nominal_033_272':[True]*3})
            nominal.to_csv(root/'nominal.csv',index=False)
            name='SWOT_test_01.nc'; path=raw/name
            x=[200000.,200000.,200030.,200030.,200090.,200090.,200090.]
            y=[1600000.]*len(x)
            lon,lat=Transformer.from_crs(5070,4326,always_xy=True).transform(x,y)
            with h5py.File(path,'w') as f:
                g=f.create_group('pixel_cloud')
                vals={'latitude':lat,'longitude':lon,'classification':np.array([3,4,5,3,4,3,4],dtype='uint8'),
                      'classification_qual':np.array([0,0,0,4,8,0,0],dtype='uint32'),
                      'geolocation_qual':np.array([0,0,0,4,4,0,4294967295],dtype='uint32')}
                for k,v in vals.items():
                    ds=g.create_dataset(k,data=v)
                    if k.endswith('_qual'): ds.attrs['_FillValue']=np.uint32(4294967295)
            digest=a.md5(path)
            manifest=pd.DataFrame([
                {'tile':'033_272_090L','filename':name,'bytes':path.stat().st_size,'md5_nasa':digest},
                {'tile':'033_259_218L','filename':'bad.nc','bytes':3,'md5_nasa':'0'*32},
                {'tile':'033_259_219L','filename':'missing.nc','bytes':3,'md5_nasa':'0'*32},
            ])
            (raw/'bad.nc').write_bytes(b'bad'); manifest.to_csv(root/'manifest.csv',index=False)
            run=a.run(root/'manifest.csv',raw,root/'optical.csv',root/'nominal.csv',root/'out',2)
            self.assertEqual(run['status_counts'],{'analyzed':1,'md5_mismatch':1,'missing':1})
            obs=pd.read_csv(root/'out/optical_cells_detected_water.csv')
            self.assertEqual(obs['pass_033_272_strict_class_3_points'].tolist(),[1,0,1])
            self.assertEqual(obs['pass_033_272_strict_class_4_points'].tolist(),[1,0,0])
            self.assertEqual(obs['pass_033_272_strict_class_5_points'].tolist(),[0,1,0])
            self.assertEqual(obs['pass_033_272_strict_main_water_detected'].tolist(),[True,False,True])
            self.assertEqual(obs['pass_033_272_strict_water_345_detected'].tolist(),[True,True,True])
            self.assertEqual(obs['pass_033_272_sensitivity_prior_unwrap_class_3_points'].tolist(),[1,1,1])
            self.assertEqual(obs['pass_033_272_sensitivity_prior_unwrap_class_4_points'].tolist(),[1,0,0])
            self.assertNotIn('dry', ' '.join(obs.columns).lower())
            self.assertEqual(run['files'][0]['stats']['input_points'],7)

    def test_relative_tolerance_not_applied(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as d:
            root=Path(d)
            pd.DataFrame({'x':[200000.], 'y':[1600000.], 's30':[1], 'l30':[0]}).to_csv(root/'o.csv',index=False)
            pd.DataFrame({'x_epsg5070':[200000.01], 'y_epsg5070':[1600000.], 's30':[1], 'l30':[0]}).to_csv(root/'n.csv',index=False)
            with self.assertRaises(ValueError): a.load_sample(root/'o.csv',root/'n.csv')

    def test_misaligned_optical_geometry_rejected(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as d:
            root=Path(d)
            pd.DataFrame({'x':[0], 'y':[1], 's30':[1], 'l30':[0]}).to_csv(root/'o.csv',index=False)
            pd.DataFrame({'x_epsg5070':[0], 'y_epsg5070':[2], 's30':[1], 'l30':[0]}).to_csv(root/'n.csv',index=False)
            with self.assertRaises(ValueError): a.load_sample(root/'o.csv',root/'n.csv')

if __name__=='__main__': unittest.main()
