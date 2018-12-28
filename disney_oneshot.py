#!/usr/bin/env python3
import time
import json
import base64
import copy
import argparse
from disneylandClient import (
    new_client,
    Job,
    RequestWithId,
)
import config
from config import RUN, IMAGE_TAG
# import disney_common as common

STATUS_IN_PROCESS = set([
    Job.PENDING,
    Job.PULLED,
    Job.RUNNING,
])
STATUS_FINAL = set([
    Job.COMPLETED,
    Job.FAILED,
])
exludeList = """
"""
exludeList = [int(i)-1 for i in exludeList.split()]

def get_result(jobs):
    results = []
    for job in jobs:
        if job.status != Job.COMPLETED:
            raise Exception(
                "Incomplete job while calculating result: %d",
                job.id
            )
    return 0, 0, 0, 0

def CreateMetaData(tag):
    metadata = copy.deepcopy(config.METADATA_TEMPLATE)
    metadata['user'].update([
        ('tag', tag),
    ])
    return json.dumps(metadata)


def CreateJobInput(number, options):
    job = copy.deepcopy(config.JOB_TEMPLATE)
    job['container']['cmd'] = job['container']['cmd'].format(
            job_id=number+1,
            IMAGE_TAG=IMAGE_TAG,
            #mfirstEvent=int(float(number*(nEvents_in/jobsNum))),
            mfirstEvent = options['startPoints'][number],
            # mfirstEvent = startPoints[number],
            #nEvents=int(float(nEvents_in/jobsNum + (((number + 1) == jobsNum) and [nEvents_in%jobsNum][0] or 0) ))
            # nEvents = chunkLength[number]
            nEvents = options['chunkLength'][number],
            fileName = 'pythia8_Geant4_10.0_withCharmandBeauty' + str(int(options['fileN']*1000)) + '_mu.root'
        )
    job['required_outputs']['output_uri'] = job['required_outputs']['output_uri'].format(job_id=number+1, fileName=str(options['fileN']))
    job['input'][0] = job['input'][0].format(fileName = 'pythia8_Geant4_10.0_withCharmandBeauty' + str(int(options['fileN']*1000)) + '_mu.root')
    with open('logs/'+str(number)+'.json', 'w') as outfile:
        json.dump(job, outfile)

    return json.dumps(job)


def WaitForCompleteness(jobs, tag, verbose=False):
    uncompleted_jobs = jobs

    while True:
        time.sleep(10)
        uncompleted_jobs = [
            stub.GetJob(RequestWithId(id=job.id))
            for job in uncompleted_jobs
        ]
        if verbose:
            print("[{}] Job :\n {}\n".format(time.time(), uncompleted_jobs[0]))
        else:
            print("[{}] Waiting...".format(time.time()))

        failed_jobs = [job for job in uncompleted_jobs if job.status == Job.FAILED]
        uncompleted_jobs = [
            job for job in uncompleted_jobs
            if job.status not in STATUS_FINAL
        ]
        if len(failed_jobs) > 0:
            print('Job failed, restarting')
            print (json.loads(failed_jobs[0].metadata))
            new_jobs = [stub.CreateJob(Job(input=job.input, kind='docker', metadata=CreateMetaData(tag + '_restarted'))) for job in failed_jobs]
            uncompleted_jobs = uncompleted_jobs + copy.deepcopy(new_jobs)

        print('Jobs left: {}'.format(len(uncompleted_jobs)))

        if not uncompleted_jobs:
            break

    jobs_results = [stub.GetJob(RequestWithId(id=job.id)) for job in jobs]

    if any(job.status == Job.FAILED for job in jobs_results):
        print("Some jobs failed! They were restarted and completed if you are reading this")
        print(list(job for job in jobs if job.status == Job.FAILED))
        raise SystemExit(1)
    return jobs_results


def makeRun(options, tag, verbose=False):
    jobs = [
        stub.CreateJob(Job(
            input=CreateJobInput(i, options),
            kind='docker',
            metadata=CreateMetaData(tag)
        ))
        for i in range(options['jobsNum']) if i not in exludeList
	#for i in [1, 4, 9, 10, 16, 17, 21, 24, 27, 42, 56, 64, 85, 94, 96]
    ]

    if verbose:
        print("Job", jobs[0])

    return WaitForCompleteness(jobs, tag, verbose=verbose)


def main():

    fileLen = {0: 13450391, 16000: 6242698, 66000: 6112412, 27000: 6238416, 63000: 6242811, 21000: 6236055, 34000: 6241933, 57000: 6240829, 10000: 6237695, 23000: 6234706, 26000: 6241631, 15000: 6245846, 60000: 6239611, 58000: 6235854, 29000: 6237372, 31000: 6238463, 39000: 6244654, 4000: 6237671, 22000: 2110646, 44000: 2793980, 59000: 6235770, 9000: 6239653, 47000: 6236843, 36000: 6239944, 14000: 6239735, 5000: 6238535, 45000: 6238019, 51000: 6242407, 41000: 6240065, 19000: 6234737, 49000: 6238063, 55000: 6240257, 33000: 6240302, 8000: 6239151, 20000: 6238057, 25000: 6236993, 61000: 6236622, 13000: 6244139, 38000: 6239812, 52000: 6243558, 30000: 6238488, 2000: 6238126, 3000: 6239983, 43000: 6239453, 28000: 6234302, 7000: 6246430, 53000: 6237809, 35000: 6238593, 56000: 6239181, 12000: 6239670, 18000: 6242505, 48000: 6238654, 54000: 6240632, 1000: 6240925, 62000: 3702269, 42000: 6242558, 64000: 6239932, 32000: 3881168, 6000: 6242602, 17000: 6243827, 40000: 6237918, 24000: 6238708, 50000: 5520395, 11000: 6238705, 65000: 6239301, 37000: 6238285, 46000: 6240834}
    
    # uncompleted_jobs = []
    parser = argparse.ArgumentParser(description='Start run')
    parser.add_argument(
        '--fileN',
        type=int,
        help='file #  for muonback input',
        default=0
    )
    parser.add_argument(
        '--jobsNum',
        type=int,
        help='Number of jobs',
        default=1
    )
    args = parser.parse_args()

    # jobsNum = 100
    jobsNum = args.jobsNum
    
    nEvents_in = fileLen[args.fileN*1000]
    #nEvents_in = 100
    n = nEvents_in
    k = jobsNum
    startPoints = [i * (n // k) + min(i, n % k) for i in range(k)]
    chunkLength = [(n // k) + (1 if i < (n % k) else 0) for i in range(k)]
    chunkLength[-1] = chunkLength[-1] - 1

    my_options = {'startPoints':startPoints, 'chunkLength':chunkLength, 'fileN':args.fileN, 'jobsNum':jobsNum} 
    tag = f'{RUN}_oneshot'

    print("result:", makeRun(my_options, tag=tag, verbose=True))


if __name__ == '__main__':
    stub = new_client()
    main()
