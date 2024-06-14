class Timeline:
    def __init__(self):
        self.timeline = []

    def create_timeline(self, host_list, id):
        # creates a timeline by creating events for each host in the host list
        # and then appending the events to the timeline, then sorting the timeline
        for host in host_list:
            host.create_events(id, host_list)

        for host in host_list:
            for event in host.events:
                self.timeline.append(event)
        self.timeline.sort(key=lambda x: (x.schedule_time, x.message_id))

    def find_next_event(self, event):
        for timeline_event in self.timeline:
            if timeline_event.event_type == "send" and timeline_event != event:
                return self.timeline.index(timeline_event)
        return -1

    def add_event_later(self, event, delay=0.5):
        event.schedule_time += delay
        self.timeline.append(event)
        self.timeline.sort(key=lambda x: (x.schedule_time, x.message_id))
