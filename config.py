IMAGE = 'mrphys/mfsimage'
IMAGE_TAG = 'bBase'
COMPATIBLE_TAGS = {}
RESULTS_TEMPLATE = {
    'error': 'Some',
    'args': None,
    'status': None,
}
JOB_TEMPLATE = {
    'nEvents':0,
    'mfirstEvent':0,
    'input': ['eos:/eos/experiment/ship/data/Mbias/background-prod-2018/{fileName}'],
    'container': {
        'workdir':
        '',
        'name':
        '{}:{}'.format(IMAGE, IMAGE_TAG),
        'volumes': [
            '/home/sashab1/ship-shield:/shield',
            '/home/sashab1/ship/shared:/shared'
        ],
        'cpu_needed': 3,
        'max_memoryMB': 2048,
        'min_memoryMB': 1024,
        'run_id':'near_run3',
        'cmd':
        '''/bin/bash -l -c 'alienv -w sw setenv  FairShip/latest  -c  python2 /sw/slc7_x86-64/FairShip/master-1/macro/run_simScript.py   --MuonBack --sameSeed 1 --seed 1 -f /input/{fileName}  --nEvents {nEvents}  --firstEvent {mfirstEvent} --output /output --FastMuon; '''
	'''alienv -w sw setenv  FairShip/latest  -c  python2 /sw/slc7_x86-64/FairShip/master-1/macro/ShipReco.py -g /output/geofile_full.conical.MuonBack-TGeant4.root -f /output/ship.conical.MuonBack-TGeant4.root ;'''
	'''mv ship.conical.MuonBack-TGeant4_rec.root /output/' ''',
    },
    'required_outputs': {
        'output_uri': 'eos:/eos/experiment/ship/user/ekurbato/fastFlux/Dec_22/{fileName}/base/{job_id}/',
    }
}

METADATA_TEMPLATE = {
    'user': {
        'tag': '',
        'image_tag': IMAGE_TAG,
    },
    'disney': {}
}

RUN = 'FS'
