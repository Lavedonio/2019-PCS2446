# -*- coding: utf-8 -*-
from job import JobQueue
from event import EventType, Event, EventQueue
from Queue import Queue


class Processor:
    def __init__(self, max_jobs, cores):
        self.queue = JobQueue()
        self.processing_jobs = Queue()
        self.job_data = []
        self.running_job = None
        self.to_run_job = None
        self.max_jobs = int(max_jobs)
        self.cores = int(cores)
        self.TIMESLICE = 100 * 1000
        self.last_timeslice = 0
        self.ini = 1  # Inicio do processador, to_run_job deve ser igual ao ultimo elemento da lista

    def request(self, job, event_queue, current_time):
        for i in self.job_data:
            if i[0] == job and i[0] != self.job_data[-1]:
                print "Processor::Request of existing Job"
                return
        self.job_data.append((job, current_time))
        if self.processing_jobs.qsize() < self.cores * self.max_jobs:
            self.insertJob(job, event_queue, current_time)
            return
        else:
            # print "Put job " + job.name + " in the CPU queue."
            self.queue.put(job)

    def insertJob(self, job, event_queue, current_time):
        self.processing_jobs.put(job)

        self.processing_jobs.task_done()
        # event_queue.put(Event(EventType.UseCPU, current_time, job))
        if self.running_job == None:
            self.running_job = job
            event_queue.put(Event(EventType.BeginTimeSlice, current_time, self.running_job))

    def beginTimeslice(self, event_queue, current_time):
        self.last_timeslice = current_time
        event_queue.put(Event(EventType.EndTimeSlice, current_time + self.TIMESLICE, self.running_job))

    def endTimeslice(self, event_queue, current_time, job=None):
        # little fix
        for i in list(event_queue.queue):
            if i[2].job == self.running_job and (i[2].typename == EventType.EndJob or i[2].typename == EventType.ReleaseCPU):
                if i[2] is not None and i[2].current_time == current_time:
                    return
        # Removes executing job
        if self.running_job is not None:
            # Little Fix 2
            fix = 0
            # if job != None:
            #     if job.missingTime() < job.next_action[1]:
            #         fix = job.missingTime() - job.next_action[1]
            self.running_job.addExecutedTime(current_time - self.last_timeslice + fix)
        # Next job
        new_job = self.processing_jobs.get()
        self.processing_jobs.put(new_job)
        self.processing_jobs.task_done()
        self.running_job = list(self.processing_jobs.queue)[0]
        if self.running_job is None:
            event_queue.put(Event(EventType.BeginTimeSlice, current_time, self.running_job))
        self.last_timeslice = current_time

    def release(self, job, event_queue, current_time):
        flag = 0
        for i in list(self.processing_jobs.queue):
            if i == job:
                flag = 1
        if flag == 0:
            print "Processor::Release error : Job does not exist"
        if self.running_job == job:
            # Cancel timeslice
            event_queue = self.cancelEvent(job, EventType.EndTimeSlice, event_queue)
            if self.processing_jobs.qsize() == 1:
                event_queue = self.cancelEvent(job, EventType.BeginTimeSlice, event_queue)
                # Little Fix 2
                # print job.next_action
                # print current_time
                # print job.missingTime()
                fix = 0
                # if job.missingTime() < job.next_action[1]:
                #     fix = job.missingTime() - job.next_action[1]
                self.running_job.addExecutedTime(current_time - self.last_timeslice + fix)
                self.running_job = None
            else:
                self.endTimeslice(event_queue, current_time, job)
        # Remove from processing jobs
        temp_queue = Queue()
        while not self.processing_jobs.empty():
            temp_job = self.processing_jobs.get()
            if temp_job != job:
                temp_queue.put(temp_job)
        self.processing_jobs = temp_queue
        # Remove data
        for i in self.job_data:
            if i[0] == job:
                self.job_data.remove(i)
        # Pick next job on the line to be executed.
        if not self.queue.empty():
            start_job = self.queue.get()
            self.queue.task_done()
            self.insertJob(start_job, event_queue, current_time)
        return event_queue

    def cancelEvent(self, job, event_type, event_queue):
        new_queue = EventQueue()
        while not event_queue.empty():
            event = event_queue.get()
            if event.job != job or event.typename != event_type:
                new_queue.put(event)
        return new_queue
