# -*- coding: utf-8 -*-


class FileSystem:
    def __init__(self, name, job_owner, size, private):
        self.name = name
        self.job_owner = job_owner
        self.size = size
        self.private = private

    def hasAccess(self, job):
        return (not self.private or job == self.job_owner)
