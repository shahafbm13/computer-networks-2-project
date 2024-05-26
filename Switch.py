import time

import Host
import Link
import Message
import time


class Switch:
    def __init__(self, address, number_of_io_ports):
        self.address = address
        self.number_of_io_ports = number_of_io_ports
        self.io_ports = [None] * number_of_io_ports  # list of links
        self.mac_table = [None] * 10  # list of MAC addresses
        self.used_ports = 0

    def initialize_port(self, port, link):
        if port < 0 or port > self.number_of_io_ports:
            print("Invalid port number")
        else:
            print(link)
            self.io_ports[port] = link
            self.used_ports += 1

    def add_to_table(self, mac_address, port, message, link_list, print_flag=False):
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
            self.mac_table[found_entry][3] = time.time()  # updates TTL
            # if print_flag:
            #     print(updated entry for {mac_address} on port {port}')
        else:  # mac address does not exist in table
            if None in self.mac_table:  # there is an empty entry
                self.mac_table[self.mac_table.index(None)] = [True, mac_address, port, time.time()]
                # if print_flag:
                #     print(f'no mac address found, added entry for {mac_address} which came from {message.src_address}')
            else:  # replace the oldest entry
                oldest_entry = self.get_oldest_entry()
                self.mac_table[self.mac_table.index(oldest_entry)] = [True, mac_address, port, time.time()]
                # if print_flag:
                #     print(
                #         f'no mac address found, replacing {oldest_entry[1]} for {mac_address} on port {self.io_ports.index(port)}')
            if print_flag:
                self.print_mac_table(link_list)
            return "flood"
        return "added"

    # check if entry for MAC address already exists
    # if it does, update the entry
    # if it does not, check if there is an empty entry
    # if there is, add the entry
    # if there is not, replace the oldest entry

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

    def flooding(self, host_list, message, switch_list=[]):
        valid_links = [links for links in self.io_ports if links.host1 != message.src_address]
        for link in valid_links:
            if type(link.host1) == Host.Host:  # switch to host
                link.send_message_from_switch(message, link.host1)
            else:  # switch to switch
                if link.host1.address == self.address:
                    target_switch = link.host2
                else:
                    target_switch = link.host1
                link.send_message_from_switch_to_switch(message, target_switch, host_list)

    def check_address_in_table(self, address):
        if address in self.mac_table:
            return True
        else:
            return False

    # NEED TO FIX SENDING MESSAGES FROM SWITCH TO SWITCH AND FLOODING BETWEEN COMPUTERS

    def receive_message(self, message, link, host_list, switch_list, link_list, print_flag=False):
        answer = self.add_to_table(message.src_address, link, message, link_list, print_flag)
        if message.src_address in switch_list:
            self.receive_message_from_switch(message, link, host_list, link_list, print_flag=print_flag)
        # need to send if no flooding
        target_host = host_list[message.dst_address]
        if answer == "flood":
            self.flooding(host_list, message, switch_list)
        else:
            link.send_message_from_switch(message, target_host, print_flag=False)

    def receive_message_from_switch(self, message, link, host_list, link_list, print_flag=False):
        answer = self.add_to_table(message.src_address, link, message, link_list, print_flag=print_flag)
        target_host = host_list[message.dst_address]
        if answer == "flood":
            self.flooding(host_list, message)
        else:
            link.send_message_from_switch(message, target_host, print_flag=False)

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
                      f"   {link_list.index(entry[2])}   | {entry[3]}")
        print("\n")
