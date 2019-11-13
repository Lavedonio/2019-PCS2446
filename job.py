# -*- coding: utf-8 -*-
from numpy import random
from Queue import PriorityQueue


class JobAction:
    Nothing = "Nothing"
    IO = "IO"
    SegmentReference = "SegmentReference"


class Job:
    def __init__(self, name, execution_time, ios, scheduled_time, priority, segment_tree):
        self.name = name
        self.execution_time = int(execution_time)
        self.ios = ios
        self.current_io = 0
        self.scheduled_time = int(scheduled_time)
        self.priority = int(priority)
        self.segment_tree = segment_tree
        self.next_action = (JobAction.Nothing, 0)
        self.executed_time = 0
        self.active_segment = None
        self.next_segment = None

    def addExecutedTime(self, time):
        self.executed_time += time
        self.next_action = (self.next_action[0], int(self.next_action[1]) - time)

    def missingTime(self):
        return self.execution_time - self.executed_time

    def nextAction(self):
        # If the next action is I/O, do it
        if self.current_io < len(self.ios) and (self.ios[self.current_io].time < self.next_action[1] or self.next_action[0] == JobAction.Nothing or self.next_action[1] <= 0):
            return (JobAction.IO, self.ios[self.current_io].time)
        return self.next_action

    def advanceIO(self):
        self.current_io += 1

    def advanceAction(self, TIMESLICE):
        transverse = random.randint(0, 8) % 3
        reference_time = int(random.normal(TIMESLICE / 2, TIMESLICE / 10))

        if transverse == 0:
            if len(self.active_segment.children) > 0:
                self.next_action = (JobAction.SegmentReference, reference_time)
                rand = int((random.rand() * 10000) % len(self.active_segment.children))
                i = 0
                while (rand > 0):
                    rand -= 1
                    i += 1
                self.next_segment = self.segment_tree.__getitem__(self.active_segment.children[i])

            elif self.active_segment.parent is not None:
                self.next_action = (JobAction.SegmentReference, reference_time)
                self.next_segment = self.active_segment.parent

            else:
                self.next_action = (JobAction.SegmentReference, reference_time)
                self.next_segment = self.active_segment

        elif transverse == 1:
            if self.active_segment.parent is not None:
                self.next_action = (JobAction.SegmentReference, reference_time)
                self.next_segment = self.active_segment.parent

            elif len(self.active_segment.children) > 0:
                self.next_action = (JobAction.SegmentReference, reference_time)
                rand = int((random.rand() * 10000) % len(self.active_segment.children))
                i = 0
                while (rand > 0):
                    rand -= 1
                    i += 1
                self.next_segment = self.segment_tree.__getitem__(self.active_segment.children[i])

            else:
                self.next_action = (JobAction.SegmentReference, reference_time)
                self.next_segment = self.active_segment

        else:
            self.next_action = (JobAction.SegmentReference, reference_time)
            self.next_segment = self.active_segment


class JobQueue(PriorityQueue):
    def __init__(self):
        PriorityQueue.__init__(self)
        self.counter = 0

    def put(self, job):
        priority = 10 - job.priority  # Ordenar por job de maior prioridade
        PriorityQueue.put(self, (priority, self.counter, job))
        self.counter += 1

    def get(self, *args, **kwargs):
        _, _, job = PriorityQueue.get(self, *args, **kwargs)
        return job
