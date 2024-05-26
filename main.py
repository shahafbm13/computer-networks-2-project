import time

import numpy as np

import Host
import Link
import Switch
import Timeline

host_list = []
link_list = []
switch_list = []

total_id = 0
print_flag = True

np.random.seed(0)


def create_main_timeline(main_timeline, number_of_packets):
    global total_id
    for host in host_list:
        host.create_timeline(number_of_packets)
    main_timeline.create_timeline(host_list, total_id)


# noinspection DuplicatedCode
def create_message(main_timeline, start_time):
    enough_time_passed = False
    for event in main_timeline.timeline:
        while enough_time_passed is False:  # check if event should be executed
            if event.schedule_time < start_time:
                enough_time_passed = True  # to exit loop
        enough_time_passed = False  # reset flag for next iteration
        if time.time() - start_time >= 10:
            print("Simulation took too long. Exiting.")
            return -1
        random_message_size = np.random.randint(64, 1518)
        scheduling_host = host_list[int(event.scheduling_object_id)]
        target_host = host_list[event.target_object_id]
        message = host_list[event.scheduling_object_id].create_message(scheduling_host.address, target_host.address
                                                                       , message_size=random_message_size,
                                                                       message_id=event.message_id,
                                                                       schedule_time=event.schedule_time,
                                                                       start_time=start_time,
                                                                       print_flag=print_flag)
        for link in link_list:
            if (link.host1 == scheduling_host and link.host2 == target_host) or (
                    link.host2 == scheduling_host and link.host1 == target_host):
                if link.is_link_busy(time.time(), random_message_size):  # link is busy, add to queue
                    link.link_queue.put(message)

                else:  # link is not busy
                    temp = link.link_queue.empty()
                    if temp:
                        link.time_sent = time.time()
                        link.send_message(message, host_list, print_flag)
                    else:
                        link.link_queue.put(message)
                        queued_message = link.link_queue.get()
                        link.time_sent = time.time()
                        link.send_message(queued_message, host_list, print_flag)


def get_switch_by_hosts(scheduling_host, target_host):
    for switch in switch_list:
        if scheduling_host in switch.hosts and target_host in switch.hosts:
            return switch


# noinspection DuplicatedCode
def create_message_switches(main_timeline, start_time):
    # Function to create messages for switches according to the main timeline and start time
    enough_time_passed = False
    for event in main_timeline.timeline:
        while enough_time_passed is False:  # check if event should be executed
            if event.schedule_time < start_time:
                enough_time_passed = True  # to exit loop
        enough_time_passed = False  # reset flag for next iteration
        if time.time() - start_time >= 10:
            print("Simulation took too long. Exiting.")
            return -1
        random_message_size = np.random.randint(64, 1518)
        scheduling_host = host_list[int(event.scheduling_object_id)]
        target_host = host_list[event.target_object_id]
        message = host_list[event.scheduling_object_id].create_message(scheduling_host.address, target_host.address
                                                                       , message_size=random_message_size,
                                                                       message_id=event.message_id,
                                                                       schedule_time=event.schedule_time,
                                                                       print_flag=print_flag)
        for switch in switch_list:
            for link in link_list:
                if (link.host1 == scheduling_host and link.host2 == switch) or (
                        link.host2 == scheduling_host and link.host1 == switch):
                    if link.is_link_busy(event.schedule_time, random_message_size):
                        link.link_queue.put(message)

                    else:  # link is not busy
                        if link.link_queue.empty():
                            link.send_message_to_switch(message, switch, host_list, switch_list, link_list, print_flag)
                            link.time_sent = time.time()

                        else:
                            link.link_queue.put(message)
                            queued_message = link.link_queue.get()
                            link.send_message_to_switch(queued_message, switch, host_list, switch_list, link_list,
                                                        print_flag)
                            link.time_sent = time.time()


def send_rest_of_queue(start_time):
    for link in link_list:
        while not link.link_queue.empty():
            if time.time() - start_time >= 10:
                print("Simulation took too long. Exiting.")
                break
            if link.is_link_busy(time.time() - start_time, link.link_queue.queue[0].message_size):
                queued_message = link.link_queue.get()
                link.send_message(queued_message, host_list, print_flag)
                link.time_sent = time.time()


def simulation_end(number_of_packets):
    print("\nSimulation ended, printing stats:\n")
    if number_of_packets <= 10:
        for host in host_list:
            host.print_total_stats(print_flag)
            print("\n")
    else:
        for host in host_list:
            host.print_average_stats(print_flag, len(host_list))
            print("\n")


def create_hosts(number_of_packets):
    global total_id
    for i in range(len(host_list)):
        host = Host.Host(i, 2, total_id)
        total_id += 1
        host.create_timeline(number_of_packets)
        host_list.append(host)


def create_links(link_ids):
    for i in range(len(host_list)):
        for j in range(i + 1, len(host_list)):
            link = Link.Link(host_list[i], host_list[j], link_ids)
            link_ids += 1
            link_list.append(link)


def create_hosts_for_switches():
    global total_id
    number_of_hosts_cloud_one = np.random.randint(2, 5)
    number_of_hosts_cloud_two = np.random.randint(2, 5)
    link_ids = number_of_hosts_cloud_one + number_of_hosts_cloud_two + 2  # 2 for the switches
    switch_ids = link_ids - 2
    for i in range(number_of_hosts_cloud_one):
        host_list.append(Host.Host(i, link_ids + i, i))
    for i in range(number_of_hosts_cloud_two):
        host_list.append(Host.Host(i + number_of_hosts_cloud_one, link_ids + i + number_of_hosts_cloud_one,
                                   i + number_of_hosts_cloud_one))
    return link_ids, switch_ids, number_of_hosts_cloud_one, number_of_hosts_cloud_two


def create_switches(switch_ids, number_of_ports_one, number_of_ports_two):
    # Function to create switches with given IDs and number of ports
    switch_list.append(Switch.Switch(switch_ids, number_of_ports_one + 1))
    switch_list.append(Switch.Switch(switch_ids + 1, number_of_ports_two + 1))


def create_links_for_switches(link_ids, number_of_hosts_cloud_one, number_of_hosts_cloud_two):
    # Function to create links for switches with given IDs and number of ports
    for i in range(number_of_hosts_cloud_one):
        link = Link.Link(link_ids + i, host_list[i], switch_list[0])
        link_list.append(link)
    for i in range(number_of_hosts_cloud_two):
        link = Link.Link(link_ids + i + number_of_hosts_cloud_one, host_list[i + number_of_hosts_cloud_one],
                         switch_list[1])
        link_list.append(link)
    link_list.append(Link.Link(link_ids + number_of_hosts_cloud_one +
                               number_of_hosts_cloud_two, switch_list[0], switch_list[1]))


#
def main():
    # Main function to initialize and run the simulation
    choice = input("Enter Question Number for simulation (A/B1/B2):  ")
    number_of_packets = int(input("Enter number of packets to simulate per host: "))
    if choice == "A":
        host_list.append(Host.Host(0, 2, total_id))
        host_list.append(Host.Host(1, 2, total_id))
        link_list.append(Link.Link(2, host_list[0], host_list[1],
                                   transmission_rate=10, prop_delay=0, error_rate=0))

        main_timeline = Timeline.Timeline()
        create_main_timeline(main_timeline, number_of_packets)
        start_time = time.time()
        term = create_message(main_timeline, start_time)
        if term != -1:
            send_rest_of_queue(start_time)
        if print_flag:
            simulation_end(number_of_packets)

    if choice == "B1":
        host_list.append(Host.Host(0, 2, total_id))
        host_list.append(Host.Host(1, 2, total_id))
        host_list.append(Host.Host(2, 2, total_id))
        switch_list.append(Switch.Switch(3, 3))
        link_list.append(Link.Link(4, host_list[0], switch_list[0],
                                   transmission_rate=1000, prop_delay=0, error_rate=0))
        link_list.append(Link.Link(5, host_list[1], switch_list[0],
                                   transmission_rate=1000, prop_delay=0, error_rate=0))
        link_list.append(Link.Link(6, host_list[2], switch_list[0],
                                   transmission_rate=1000, prop_delay=0, error_rate=0))

        for switch in switch_list:
            for link in link_list:
                if link.host1 == host_list[0] and link.host2 == switch:
                    switch.initialize_port(link.object_id - 4, link)
                elif link.host1 == host_list[1] and link.host2 == switch:
                    switch.initialize_port(link.object_id - 4, link)
                elif link.host1 == host_list[2] and link.host2 == switch:
                    switch.initialize_port(link.object_id - 4, link)

        main_timeline = Timeline.Timeline()
        create_main_timeline(main_timeline, number_of_packets)
        start_time = time.time()
        create_message_switches(main_timeline, start_time)
        send_rest_of_queue(start_time)
        if print_flag:
            for switch in switch_list:
                switch.print_mac_table(link_list)

    if choice == "B2":
        link_ids, switch_ids, number_of_ports_one, number_of_ports_two = create_hosts_for_switches()
        create_switches(switch_ids, number_of_ports_one, number_of_ports_two)
        create_links_for_switches(link_ids, number_of_ports_one, number_of_ports_two)

        for switch in switch_list:
            for link in link_list:
                for i in range(number_of_ports_one):
                    if link.host1 == host_list[i] and link.host2.address == switch.address:
                        switch.initialize_port(i, link)
                for j in range(number_of_ports_two):
                    if link.host1 == host_list[j + number_of_ports_one] and link.host2.address == switch.address:
                        switch.initialize_port(j, link)
        switch_list[0].initialize_port(number_of_ports_one, link_list[-1])
        switch_list[1].initialize_port(number_of_ports_two, link_list[-1])

        main_timeline = Timeline.Timeline()
        create_main_timeline(main_timeline, number_of_packets)
        start_time = time.time()
        create_message_switches(main_timeline, start_time)
        send_rest_of_queue(start_time)
        if print_flag:
            for switch in switch_list:
                switch.print_mac_table(link_list)


main()
