# -*- coding: utf-8 -*-
import sys
from job import JobAction, Job
from event import EventType, Event, EventQueue
from device import DeviceType, Device, DeviceManagement
from memory import Memory
from tree import Tree
from processor import Processor
from disk import DiskOperation, Disk
from fileSystem import FileSystem
from numpy import random

_ROOT = 0


def main():
    # Checa os parâmetros
    if (len(sys.argv) != 4):
        print("Usage: python " + sys.argv[0] + " <inicio> <fim> <arquivo>")
        sys.exit()
    else:
        (_ROOT, _DEPTH, _BREADTH) = range(3)
        cpu = Processor(1, 1)
        memory = Memory(10 * 1024 * 1024, 1024 * 1024)  # 10MB memory
        # Seguir ordem Printer -> Reader -> Disk para declaração no vetor devices
        devices = [
            DeviceManagement(DeviceType.Printer, 2 * 1000 * 1000 * 1000, 2),
            DeviceManagement(DeviceType.Reader, 100 * 1000 * 1000, 2),
            DeviceManagement(DeviceType.Disk, 8002 * 1000, 1)
        ]
        disk = Disk(8002 * 1000, 2 * 1000, 500 * 1024 * 1024)
        start = int(sys.argv[1])
        end = int(sys.argv[2])
        event_queue = EventQueue()
        event_queue.put(Event(EventType.BeginSimulation, start))
        event_queue.put(Event(EventType.EndSimulation, end))
        current_time = 0
        while not event_queue.empty():
            current_event = event_queue.get()
            current_job = current_event.job
            if current_event.current_time > current_time:
                current_time = current_event.current_time
            if current_event.typename == EventType.BeginSimulation:
                jobs = readJobs(disk, cpu)
                for i in jobs:
                    event_queue.put(Event(EventType.BeginJob, i.scheduled_time, i))
                current_time = start

            # Início do Job
            elif current_event.typename == EventType.BeginJob:
                event_queue.put(Event(EventType.RequestMemory, current_time, current_job))

            # Final do Job
            elif current_event.typename == EventType.EndJob:
                pass

            elif current_event.typename == EventType.RequestMemory:
                memory.request(current_job, current_job.segment_tree.__getitem__(_ROOT), event_queue, current_time)

            elif current_event.typename == EventType.ReleaseMemory:
                print "\nMEMORY CONTENT BEFORE RELEASE"
                memory.printMemory()
                print ""
                memory.release(current_job, event_queue, current_time)
                event_queue.put(Event(EventType.EndJob, current_time, current_job))

            elif current_event.typename == EventType.RequestCPU:
                current_job.active_segment = current_job.next_segment
                cpu.request(current_event.job, event_queue, current_time)

            elif current_event.typename == EventType.BeginTimeSlice:
                cpu.beginTimeslice(event_queue, current_time)
                # Schedule next interruption
                if current_job.nextAction()[0] == JobAction.Nothing or current_job.nextAction()[1] <= 0:
                    # Advance
                    current_job.advanceAction(cpu.TIMESLICE)
                # Little Fix
                if current_job.missingTime() < current_job.nextAction()[1]:
                    event_queue.put(Event(EventType.ReleaseCPU, current_time + current_job.missingTime(), current_job, current_job.missingTime() - current_job.nextAction()[1]))
                elif current_job.nextAction()[0] != JobAction.Nothing and current_job.nextAction()[1] <= cpu.TIMESLICE:
                    if current_job.nextAction()[0] == JobAction.SegmentReference:
                        event_queue.put(Event(EventType.SegmentReference, current_time + current_job.nextAction()[1], current_job))
                    if current_job.nextAction()[0] == JobAction.IO:
                        if current_job.ios[current_job.current_io].typename == DeviceType.Disk:
                            event_queue.put(Event(EventType.RequestFile, current_time + current_job.nextAction()[1], current_job))
                        else:
                            event_queue.put(Event(EventType.RequestIO, current_time + current_job.nextAction()[1], current_job))
                elif current_job.missingTime() < cpu.TIMESLICE:
                    event_queue.put(Event(EventType.ReleaseCPU, current_time + current_job.missingTime(), current_job, current_job.missingTime()))
            elif current_event.typename == EventType.UseCPU:
                pass

            elif current_event.typename == EventType.SegmentLoaded:
                event_queue.put(Event(EventType.RequestCPU, current_time, current_job))

            elif current_event.typename == EventType.ReleaseCPU:
                event_queue = cpu.release(current_job, event_queue, current_time)
                if current_job.missingTime() == 0:
                    event_queue.put(Event(EventType.ReleaseMemory, current_time, current_job))

            elif current_event.typename == EventType.RequestIO:
                if cpu.running_job == current_job:
                    event_queue.put(Event(EventType.ReleaseCPU, current_time, current_job))
                devices[current_job.ios[current_job.current_io].device_number].request(current_job, event_queue, current_time)

            elif current_event.typename == EventType.UseIO:
                event_queue.put(Event(EventType.ReleaseIO, current_time + devices[current_job.ios[current_job.current_io].device_number].time, current_job))

            elif current_event.typename == EventType.ReleaseIO:
                devices[current_job.ios[current_job.current_io].device_number].release(current_job, event_queue, current_time)
                current_job.advanceIO()
                event_queue.put(Event(EventType.RequestCPU, current_time, current_job))

            elif current_event.typename == EventType.SegmentReference:
                if current_job.next_segment.memory is None:
                    event_queue.put(Event(EventType.SegmentFault, current_time, current_job))
                else:
                    slice_run = current_job.nextAction()[1]
                    current_job.active_segment = current_job.next_segment
                    if current_job.missingTime() <= cpu.TIMESLICE:
                        event_queue.put(Event(EventType.ReleaseCPU, current_time + current_job.missingTime() - slice_run, current_job, current_job.missingTime() - slice_run))

            # Novo segmento sorteado nao está na memoria
            elif current_event.typename == EventType.SegmentFault:
                if cpu.running_job == current_job:
                    event_queue.put(Event(EventType.ReleaseCPU, current_time, current_job))

                # request memory
                if not memory.FULL:
                    memory.request(current_job, current_job.next_segment, event_queue, current_time)
                else:
                    memory_full_time_evaluation = 10
                    if current_job.missingTime() > current_job.nextAction()[1]:
                        event_queue.put(Event(EventType.RequestCPU, current_time + memory_full_time_evaluation, current_job))

            elif current_event.typename == EventType.EndTimeSlice:
                cpu.endTimeslice(event_queue, current_time)

            elif current_event.typename == EventType.RequestFile:
                if cpu.running_job == current_job:
                    event_queue.put(Event(EventType.ReleaseCPU, current_time, current_job))
                disk.diskRequest(current_job, current_job.ios[current_job.current_io].file.name, current_job.ios[current_job.current_io].operation, current_job.ios[current_job.current_io].number_tracks, event_queue, current_time)

            elif current_event.typename == EventType.UseFile:
                event_queue.put(Event(EventType.ReleaseFile, current_time + disk.useTime(current_job.ios[current_job.current_io].number_tracks), current_job, disk.useTime(current_job.ios[current_job.current_io].number_tracks)))

            elif current_event.typename == EventType.ReleaseFile:
                disk.diskRelease(current_job, event_queue, current_time)
                current_job.advanceIO()
                event_queue.put(Event(EventType.RequestCPU, current_time, current_job))

            elif current_event.typename == EventType.EndSimulation:
                # Zera eventos na fila para finalizar a simulacao
                while not event_queue.empty():
                    event_queue.get()
                    event_queue.task_done()
                current_time = end

            if current_job is not None:
                print "".join(str(current_event.current_time).ljust(15)) + "".join(current_event.typename.ljust(20)) + "".join(current_job.name.ljust(10)) + "".join(current_event.action.ljust(50)) + " " + str(current_job.executed_time) + "ns/" + str(current_job.execution_time) + "ns"
            else:
                print "".join(str(current_event.current_time).ljust(15)) + "".join(current_event.typename.ljust(20)) + "".join(" -".ljust(10)) + "".join(current_event.action.ljust(48)) + "       -"
            if current_event.typename == EventType.ReleaseMemory:
                print "\nMEMORY CONTENT AFTER RELEASE"
                memory.printMemory()
                print ""


def readJobs(disk, cpu):
    jobs = []
    with open(sys.argv[3], "r") as file:
        n_segments = 0
        ios = []

        # Lista de Jobs ordenada pelo tempo de início
        for line in file:
            segment_tree = Tree()
            line = line.split("\n")[0]
            items = line.split(" ")
            n_io = int(items[2])
            n_segments = int(items[5])
            # Organiza segmentos do job
            for i in range(0, n_segments):
                line = next(file)
                line = line.split("\n")[0]
                items_segment = line.split(" ")
                if len(items_segment) == 2:
                    segment_tree.add_node(int(items_segment[0]), items_segment[1])
                else:
                    segment_tree.add_node(int(items_segment[0]), items_segment[1], int(items_segment[2]))
            job = Job(items[0], items[1], None, items[3], items[4], segment_tree)
            # Organiza IOs
            for i in range(0, n_io):
                line = next(file)
                line = line.split("\n")[0]
                items_io = line.split(" ")
                io_name = items_io[0]
                if io_name == DeviceType.Printer:
                    ios.append(Device(DeviceType.Printer, int(random.normal(cpu.TIMESLICE / 2, cpu.TIMESLICE / 10))))
                elif io_name == DeviceType.Reader:
                    ios.append(Device(DeviceType.Reader, int(random.normal(cpu.TIMESLICE / 2, cpu.TIMESLICE / 10))))
                elif io_name == DeviceType.Disk:
                    filename = items_io[1]
                    if items_io[2] == "r":
                        read_write = DiskOperation.Read
                    else:
                        read_write = DiskOperation.Write
                    n_opers = int(items_io[3])
                    size = int(items_io[4])
                    is_private = items_io[5]
                    sys_file = FileSystem(filename, job, size, is_private)
                    time = int(random.normal(cpu.TIMESLICE / 2, cpu.TIMESLICE / 10))
                    ios.append(Device(DeviceType.Disk, time, sys_file, read_write, n_opers))
                    disk.addFile(sys_file)
            job.ios = ios
            # Coloca o job no segmento para facilitar impressao da memoria
            for i in range(0, segment_tree.size):
                segment_tree.__getitem__(i).job = job
            jobs.append(job)
            ios = []
    printJobs(jobs)
    return jobs


def printJobs(jobs):
    for job in jobs:
        print "---------------------------------------------------------------------------------------"
        print "Job Info:"
        print "         Name: " + "".join(job.name.ljust(5)) + "\n         ExecutionTime: " + "".join(str(job.execution_time).ljust(5)) + "\n         StartTime: " + "".join(str(job.scheduled_time).ljust(5)) + "\n         Priority: " + "".join(str(job.priority).ljust(5))
        print "Segments:"
        for i in range(0, job.segment_tree.size):
            if job.segment_tree.__getitem__(i).parent is not None:
                print "         Identifier: " + str(i) + "\n         Size: " + str(job.segment_tree.__getitem__(i).size) + " Bytes\n         Parent: " + str(job.segment_tree.__getitem__(i).parent.identifier)
            else:
                print "         Identifier: " + str(i) + "\n         Size: " + str(job.segment_tree.__getitem__(i).size) + " Bytes\n         Parent: - "
        print "I/Os: "
        for i in job.ios:
            if i.typename == DeviceType.Disk:
                print "         Type: " + i.typename + "\n         LoadTime: " + str(i.time) + "ns\n         File: " + i.file.name + "\n         Operation: " + i.operation + "\n         #Tracks: " + str(i.number_tracks)
            else:
                print "         Type: " + i.typename + "\n         LoadTime: " + str(i.time) + "ns"
    print "---------------------------------------------------------------------------------------\n"
    print "".join("CURRENT TIME".ljust(20)) + "".join("EVENT".ljust(15)) + "".join("JOB".ljust(15)) + "".join("ACTION".ljust(43)) + "EXECUTED/EXECUTION\n"


if __name__ == "__main__":
    main()
