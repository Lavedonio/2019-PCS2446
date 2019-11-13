# -*- coding: utf-8 -*-
from Queue import Queue
from event import EventType, Event


class DeviceType:
    Printer = "Printer"
    Disk = "Disk"
    Reader = "Reader"


class Device:
    def __init__(self, typename, time, file=None, oper=None, number_tracks=None):
        self.typename = typename
        self.time = time
        self.file = file
        self.operation = oper
        self.number_tracks = number_tracks

        if self.typename == DeviceType.Printer:
            self.device_number = 0

        elif self.typename == DeviceType.Reader:
            self.device_number = 1

        elif self.typename == DeviceType.Disk:
            self.device_number = 2


class DeviceManagement:
    def __init__(self, typename, time, n_devices):
        self.typename = typename
        self.time = time
        self.n_devices = n_devices
        self.jobs_queue = Queue()
        self.jobs_using_devices = []
        self.OVERHEAD = 10

    def request(self, job, event_queue, current_time):
        if len(self.jobs_using_devices) == self.n_devices:
            self.jobs_queue.put(job)
            # print "------> " + job.name + " is waiting for device " + self.typename
        else:
            self.jobs_using_devices.append(job)
            event_queue.put(Event(EventType.UseIO, current_time + self.OVERHEAD, job))
            # print "------> " + job.name + " got device " + self.typename
        return

    def release(self, job, event_queue, current_time):
        for i in range(-1, len(self.jobs_using_devices) - 1):
            if self.jobs_using_devices[i] == job:
                self.jobs_using_devices.pop(i)
        # print "------> " + job.name + " is releasing device " + self.typename
        if not self.jobs_queue.empty():
            new_job = self.jobs_queue.get()
            self.jobs_using_devices.append(new_job)
            event_queue.put(Event(EventType.UseIO, current_time + self.OVERHEAD, new_job))
            # print "------> " + job.name + " got device " + self.typename
        return
