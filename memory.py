# -*- coding: utf-8 -*-
from Queue import Queue
from event import EventType, Event


class MemorySegment():
    def __init__(self, position, size, used, program_segment=None):
        self.position = int(position)
        self.size = int(size)
        self.used = used
        self.program_segment = program_segment


class Memory():
    def __init__(self, size_memory, size_segment):
        self.size_memory = int(size_memory)
        self.size_segment = int(size_segment)
        self.number_of_segments = int(self.size_memory / self.size_segment)
        self.free_mem_segments = []
        self.mem_segments_table = []
        for i in range(0, self.number_of_segments):
            self.mem_segments_table.append(MemorySegment(i, size_segment, False))
            self.free_mem_segments.append(self.mem_segments_table[i])
        self.OVERHEAD = 100
        self.FULL = False
        self.queue = Queue()

    def tryAllocate(self, job, program_segment):
        if len(self.free_mem_segments) > 0:
            for i in self.free_mem_segments:
                if i.size >= program_segment.size:
                    i.used = True
                    i.program_segment = program_segment
                    job.next_segment = program_segment
                    program_segment.memory = i
                    self.free_mem_segments.remove(i)
                    return True
        else:
            return False

    def request(self, job, program_segment, event_queue, current_time):
        if self.queue.qsize() > 0 and job.segment_tree.__getitem__(0) == program_segment:
            self.queue.put(program_segment)
            return
        if self.tryAllocate(job, program_segment):
            event_queue.put(Event(EventType.SegmentLoaded, current_time + self.OVERHEAD, job))
            if len(self.free_mem_segments) == 0:
                self.FULL = True
        else:
            self.queue.put(program_segment)
        return

    def unloadTree(self, segment_tree, identifier=0):
        children = segment_tree.__getitem__(identifier).children
        for i in self.mem_segments_table:
                if i.program_segment == segment_tree.__getitem__(identifier):
                    i.used = False
                    i.program_segment = None
                    self.free_mem_segments.append(i)
                    segment_tree.__getitem__(identifier).memory = None
                    self.free_mem_segments.sort(key=lambda x: x.position)
        for child in children:
            self.unloadTree(segment_tree, child)

    def release(self, job, event_queue, current_time):
        self.unloadTree(job.segment_tree)
        if self.queue.qsize() == 0:
            return
        temp_queue = Queue()
        while not self.queue.empty():
            temp_program_segment = self.queue.get()
            if temp_program_segment.job != job:
                temp_queue.put(temp_program_segment)
        self.queue = temp_queue
        new_program_segment = self.queue.get()
        self.queue.task_done()
        self.FULL = False
        if self.tryAllocate(new_program_segment.job, new_program_segment):
            if len(self.free_mem_segments) == 0:
                self.FULL = True
            event_queue.put(Event(EventType.SegmentLoaded, current_time + self.OVERHEAD, new_program_segment.job))
            return

    def printMemory(self):
        for i in range(0, len(self.mem_segments_table)):
            if not self.mem_segments_table[i].used:
                print "Segment - " + str(i) + "  (" + "".join(str(i * self.size_segment / 1024) + "-" + str((i + 1) * self.size_segment / 1024 - 1)).ljust(11) + "Kb)" + " --------------- free --------------"
            else:
                print "Segment - " + str(i) + "  (" + "".join(str(i * self.size_segment / 1024) + "-" + str((i + 1) * self.size_segment / 1024 - 1)).ljust(11) + "Kb) " + self.mem_segments_table[i].program_segment.job.name + " " + str(self.mem_segments_table[i].program_segment.size / 1024) + " Kbytes and program segment " + str(self.mem_segments_table[i].program_segment.identifier)
