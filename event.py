from Queue import PriorityQueue


class EventType:
    BeginSimulation = "BEGIN SIMULATION"
    EndSimulation = "END SIMULATION"
    BeginJob = "BEGIN JOB"
    EndJob = "END JOB"
    RequestMemory = "REQUEST MEMORY"
    ReleaseMemory = "RELEASE MEMORY"
    UseMemory = "USE MEMORY"
    RequestCPU = "REQUEST CPU"
    UseCPU = "USE CPU"
    ReleaseCPU = "RELEASE CPU"
    RequestIO = "REQUEST IO"
    UseIO = "USE IO"
    ReleaseIO = "RELEASE IO"
    SegmentFault = "SEGMENT FAULT"
    SegmentReference = "SEGMENT REFERENCE"
    BeginTimeSlice = "BEGIN TIME SLICE"
    EndTimeSlice = "END TIME SLICE"
    UseFile = "USE FILE"
    ReleaseFile = "RELEASE FILE"
    RequestFile = "REQUEST FILE"
    SegmentLoaded = "SEGMENT LOADED"


class Event():
    def __init__(self, typename, current_time, job=None, sum_time=0):
        self.typename = typename
        self.current_time = int(current_time)
        self.job = job
        self.action = ""
        if self.typename == EventType.BeginJob:
            self.action = "starting.."
        elif self.typename == EventType.SegmentLoaded:
            self.action = "segment #" + str(job.next_segment.identifier) + " allocated"
        elif self.typename == EventType.BeginSimulation:
            self.action = "Begin simulation"
        elif self.typename == EventType.EndSimulation:
            self.action = "End simulation"
        elif self.typename == EventType.RequestMemory:
            self.action = "is waiting for memory."
        elif self.typename == EventType.EndJob:
            self.action = "finished "
        elif self.typename == EventType.RequestCPU:
            self.action = "is waiting to run"
        elif self.typename == EventType.UseCPU:
            self.action = "will use the CPU"
        elif self.typename == EventType.ReleaseCPU:
            self.action = "stopped running (run for " + str(job.execution_time - job.missingTime() + job.nextAction()[1] + sum_time) + "ns/" + str(job.execution_time) + "ns)"
        elif self.typename == EventType.ReleaseMemory:
            self.action = "deallocated"
        elif self.typename == EventType.RequestIO:
            self.action = "is waiting for I/O " + job.ios[job.current_io].typename
        elif self.typename == EventType.UseIO:
            self.action = "is using device " + str(job.ios[job.current_io].typename) + " doing I/O operation (" + str(job.current_io + 1) + "/" + str(len(job.ios)) + ")"
        elif self.typename == EventType.ReleaseIO:
            self.action = "finished I/O " + job.ios[job.current_io].typename
        elif self.typename == EventType.BeginTimeSlice:
            self.action = "will run for its timeslice"
        elif self.typename == EventType.EndTimeSlice:
            self.action = "finished its timeslice"
        elif self.typename == EventType.SegmentReference:
            self.action = "referenced segment #" + str(job.next_segment.identifier) + " in " + str(job.next_action[1]) + "ns"
        elif self.typename == EventType.SegmentFault:
            self.action = "segment #" + str(job.next_segment.identifier) + " is not in memory"
        elif self.typename == EventType.UseFile:
            self.action = "does " + job.ios[job.current_io].operation + " of file " + job.ios[job.current_io].file.name + " of " + str(job.ios[job.current_io].number_tracks) + " sectors doing I/O operation (" + str(job.current_io + 1) + "/" + str(len(job.ios)) + ")"
        elif self.typename == EventType.ReleaseFile:
            self.action = "finished file access in " + str(sum_time) + "ns"
        elif self.typename == EventType.RequestFile:
            self.action = "is waiting for file access in " + str(job.ios[job.current_io].time) + "ns"
        else:
            self.action = "NULL"


class EventQueue(PriorityQueue):
    def __init__(self):
        PriorityQueue.__init__(self)
        self.counter = 0

    def put(self, event):
        priority = event.current_time
        PriorityQueue.put(self, (priority, self.counter, event))
        self.counter += 1

    def get(self, *args, **kwargs):
        _, _, event = PriorityQueue.get(self, *args, **kwargs)
        return event
