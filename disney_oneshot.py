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

jobsNum = 10
# nEvents_in = 6240925
nEvents_in = 100

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


def CreateJobInput(number):
    job = copy.deepcopy(config.JOB_TEMPLATE)
    job['container']['cmd'] = job['container']['cmd'].format(
            job_id=number+1,
            IMAGE_TAG=IMAGE_TAG,
            mfirstEvent=int(float(number*(nEvents_in/jobsNum))),
	   # nEvents=17786274/
            nEvents=int(float(nEvents_in/jobsNum + (((number + 1) == jobsNum) and [nEvents_in%jobsNum][0] or 0) ))
        )
    job['required_outputs']['output_uri'] = job['required_outputs']['output_uri'].format(job_id=number+1)

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


def makeRun(tag, verbose=False):
    jobs = [
        stub.CreateJob(Job(
            input=CreateJobInput(i),
            kind='docker',
            metadata=CreateMetaData(tag)
        ))
        for i in range(jobsNum)
	#for i in [1, 4, 9, 10, 16, 17, 21, 24, 27, 42, 56, 64, 85, 94, 96]
    ]

    if verbose:
        print("Job", jobs[0])

    return WaitForCompleteness(jobs, tag, verbose=verbose)


def main():
    # uncompleted_jobs = []
    parser = argparse.ArgumentParser(description='Start run')
    # parser.add_argument(
    #     '--seed',
    #     help='Random seed of simulation',
    #     default=1
    # )
    # args = parser.parse_args()
    tag = f'{RUN}_oneshot'

    print("result:", makeRun(tag=tag, verbose=True))


if __name__ == '__main__':
    stub = new_client()
    main()
