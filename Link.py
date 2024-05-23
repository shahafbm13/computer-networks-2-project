import queue


class Link:
    def __init__(self, object_id, host1, host2, transmission_rate=1000, prop_delay=0, error_rate=0):
        self.object_id = object_id
        self.host1 = host1
        self.host2 = host2
        self.transmission_rate = transmission_rate
        self.prop_delay = prop_delay
        self.error_rate = error_rate
        self.time_sent = 0
        self.link_queue = queue.Queue()

    def send_message(self, message,host_list,print_flag=False):
        '''
        sends the message to the host2 end of the link
        '''

        dst_host= host_list[message.dst_address]
        dst_host.receive_message(message,self,print_flag)

    def send_message_to_switch(self, message, target_switch,host_list,switch_list,link_list, print_flag=False):
        target_switch.receive_message(message, self, host_list,switch_list,link_list,print_flag)

    def send_message_from_switch(self,message,target_host,print_flag=False):
        target_host.receive_message(message,self,print_flag)

    def send_message_from_switch_to_switch(self,message,target_switch,host_list,print_flag=False):
        target_switch.receive_message_from_switch(message,self,host_list,print_flag)

    def is_link_busy(self, curr_time, message_size):
        if self.time_sent == 0:
            return False
        else:
            if self.time_sent + self.prop_delay + (message_size / self.transmission_rate) < curr_time:
                return False
        return True


