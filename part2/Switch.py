import Host
import time
import Event
import queue


class Switch:
    def __init__(self, address, number_of_io_ports, queue_type="input", isFluid=False, scheduling_algorithm="FIFO"):
        self.address = address
        self.number_of_io_ports = number_of_io_ports
        self.io_ports = [None] * number_of_io_ports  # list of links
        self.mac_table = [None] * 3  # list of MAC addresses
        self.used_ports = 0
        self.isFluid = isFluid
        self.queue_type = queue_type
        if queue_type == "input" or queue_type == "output":
            self.switch_queues = [[] for _ in range(number_of_io_ports)]
            self.departure_times = [0] * number_of_io_ports
        else:  # queue_type == "virtual"
            self.switch_queues = [[[] for _ in range(number_of_io_ports)] for _ in
                                  range(number_of_io_ports)]
            self.departure_times = [[0,0] * number_of_io_ports for _ in range(number_of_io_ports)]
        self.scheduling_algorithm = scheduling_algorithm
        self.total_hol_time = 0
        self.cant_send_flags = [False] * number_of_io_ports

    def initialize_port(self, port, link):
        if port < 0 or port > self.number_of_io_ports:
            print("Invalid port number")
        else:
            self.io_ports[port] = link
            self.used_ports += 1

    def add_to_table(self, mac_address, port, message, link_list, print_flag=False, start_time=0):
        found_entry = None
        for entry in self.mac_table:
            if entry is None:
                continue
            elif entry[1] == mac_address:
                found_entry = self.mac_table.index(entry)
                break
        if found_entry is not None:  # mac address already exists in table
            self.mac_table[found_entry][0] = 'True'
            self.mac_table[found_entry][2] = port
            self.mac_table[found_entry][3] = (time.time() - start_time)  # updates TTL
        else:  # mac address does not exist in table
            if None in self.mac_table:  # there is an empty entry
                self.mac_table[self.mac_table.index(None)] = [True, mac_address, port, (time.time() - start_time)]
            else:  # replace the oldest entry
                oldest_entry = self.get_oldest_entry()
                self.mac_table[self.mac_table.index(oldest_entry)] = [True, mac_address, port,
                                                                      (time.time() - start_time)]
            if print_flag:
                self.print_mac_table(link_list)
            return "flood"
        return "added"

    def check_TTL(self, entry):
        if abs(time.time() - entry[3]) >= entry[3]:
            return True
        else:
            return False

    def get_oldest_entry(self):
        oldest_entry = self.mac_table[0][3]
        for entry in self.mac_table:
            if entry[3] < oldest_entry:
                oldest_entry = entry[3]
        for entry in self.mac_table:
            if entry[3] == oldest_entry:
                return entry

    def flooding(self, host_list, message, main_timeline, switch_list=[], start_time=0):
        valid_links = [links for links in self.io_ports if links.host1 != message.src_address]
        for link in valid_links:
            if type(link.host1) == Host.Host:  # switch to host
                link.send_message_from_switch(message, link.host1, start_time=start_time)
            else:  # switch to switch
                if link.host1.address == self.address:
                    target_switch = link.host2
                else:
                    target_switch = link.host1
                link.send_message_from_switch_to_switch(message, target_switch, host_list, start_time=start_time)

    def flooding_lab2(self, host_list, message, main_timeline, switch_list=[], start_time=0):
        sending_host = host_list[message.src_address]
        valid_hosts = [host for host in host_list if host.address != sending_host.address]
        if self.queue_type == "input" or self.queue_type == "output":
            for i in range(len(valid_hosts)):
                self.switch_queues[i].insert(0, message)
                main_timeline.timeline.append(
                    Event.Event(message.schedule_time, "send", self.address,
                                valid_hosts[i].address, message.message_id))
            main_timeline.timeline.sort(key=lambda x: (x.schedule_time, x.message_id))
        else:
            for i in range(len(valid_hosts)):
                for j in range(len(valid_hosts)):
                    self.switch_queues[i][j].insert(0, message)
                    main_timeline.timeline.append(
                        Event.Event(message.schedule_time, "send", self.address,
                                    valid_hosts[i].address, message.message_id))
            main_timeline.timeline.sort(key=lambda x: (x.schedule_time, x.message_id))

    def check_address_in_table(self, address):
        if address in self.mac_table:
            return True
        else:
            return False

    def receive_message(self, message, link, host_list, switch_list, link_list, main_timeline, print_flag=False,
                        start_time=0):
        answer = self.add_to_table(message.src_address, link, message, link_list, print_flag, start_time=start_time)
        if message.src_address in switch_list:
            self.receive_message_from_switch(message, link, host_list, link_list, print_flag=print_flag,
                                             start_time=start_time)
        target_host = host_list[message.dst_address]
        if answer == "flood":
            self.flooding_lab2(host_list, message, main_timeline, switch_list, start_time=start_time)
        # else:
        #     link.send_message_from_switch(message, target_host, print_flag=False, start_time=start_time)
        else:
            if self.queue_type == "input":
                correct_queue = self.switch_queues[link_list.index(link)]

            elif self.queue_type == "output":
                print("output queues not implemented yet")

            else:  # virtual queues
                print("Virtual queues not implemented yet")

    def receive_message_from_switch(self, message, link, host_list, link_list, print_flag=False, start_time=0):
        answer = self.add_to_table(message.src_address, link, message, link_list, print_flag=print_flag,
                                   start_time=start_time)
        target_host = host_list[message.dst_address]
        if answer == "flood":
            self.flooding(host_list, message, start_time=start_time)
        else:
            link.send_message_from_switch(message, target_host, print_flag=False, start_time=start_time)

    def get_port_by_message(self, message):
        for entry in self.mac_table:
            if entry[1] == message.get_msg_src_mac():
                return entry[2]
        return None

    def print_mac_table(self, link_list):
        print(f"\nMAC Table for switch {self.address}:\n")
        print("Used | Addr. | Port  | TTL")
        for entry in self.mac_table:
            if entry is None:
                print(f"{None} | {None}  | {None}  | {None}")
            else:
                print(f"{entry[0]} |   {entry[1]}   |"
                      f"   {link_list.index(entry[2])}    | {entry[3]} ")
        print("\n")

    def get_id(self):
        return self.address

    def calculate_hol_blocking(self, curr_message):
        top_of_queues = self.find_top_of_queues()
        if curr_message != top_of_queues[0]:
            print("error in HoL blocking calculation - cant find current message in queue")
        elif len(top_of_queues[0]) == 1:
            print("error in HoL blocking calculation - only one message in queue")
        else:
            next_sending_message = top_of_queues[1]
            curr_queue = self.find_correct_queue(curr_message)
            if len(curr_queue) == 0:
                print("error in HoL blocking calculation - cant find correct current queue")
            else:
                for i in range(1, len(curr_queue) - 1):
                    if curr_queue[i].scheduling_time < next_sending_message.scheduling_time:
                        self.total_hol_time += 1
                    else:
                        break

    def find_correct_queue(self, message):
        for queue in self.switch_queues:
            if message in queue:
                return queue[0]
        return None

    def find_top_of_queues(self):
        temp = []
        for i in range(len(self.switch_queues)):
            if len(self.switch_queues[i]) > 0:
                temp.append(self.switch_queues[i][0])
        return temp.sort(key=lambda x: x.schedule_time)

