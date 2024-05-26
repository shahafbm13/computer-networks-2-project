class Timeline:
    def __init__(self):
        self.timeline = []

    def create_timeline(self, host_list, id):
        '''
        loops over all hosts and creates events for each host
        after that, loops over all hosts, and then their created events,
        and appends them to the timeline
        finally, sorts the timeline by the schedule time and tie breaks with
        message ID
        '''

        for host in host_list:
            host.create_events(id, host_list)

        for host in host_list:
            for event in host.events:
                self.timeline.append(event)
        self.timeline.sort(key=lambda x: (x.schedule_time, x.message_id))
