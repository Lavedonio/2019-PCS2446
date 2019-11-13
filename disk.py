# -*- coding: utf-8 -*-
from Queue import Queue
from event import EventType, Event


class DiskOperation:
    Write = "WRITE"
    Read = "READ"


class Disk:
    def __init__(self, access_time, data_transfer_time, size):
        self.access_time = int(access_time)
        self.total_size = int(size)
        self.data_transfer_time = int(data_transfer_time)
        self.remaining_size = self.total_size
        self.using_job = None
        self.queue_list = Queue()
        self.number_operations = Queue()
        self.operation_list = Queue()
        self.files = Queue()

    def diskRequest(self, job, filename, operation, number_operations, event_queue, current_time):
        if self.using_job is None:
            self.using_job = job
            if operation == DiskOperation.Write:
                self.total_size -= 512 * int(number_operations)
            event_queue.put(Event(EventType.UseFile, current_time, job))
        else:
            self.queue_list.put(job)
            self.operation_list.put(operation)
            self.number_operations.put(number_operations)

    def diskRelease(self, job, event_queue, current_time):
        self.using_job = None
        if not self.queue_list.empty():
            self.using_job = self.queue_list.get()
            if self.operation_list.get() == DiskOperation.Write:
                self.total_size -= 512 * self.number_operations.get()
            event_queue.put(Event(EventType.UseFile, current_time, self.using_job))

    def addFile(self, file):
        if self.findFile(self.files, file.name) is None:
            self.files.put(file)
        return True

    def findFile(self, files, filename):
        for file in list(files.queue):
            if file.name == filename:
                return file
        return None

    def useTime(self, n_access):
        return self.access_time + int(n_access) * self.data_transfer_time
