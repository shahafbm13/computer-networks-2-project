import time
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import Host
import Link
import Timeline
import Switch

host_list = []
link_list = []
switch_list = []

total_id = 0
print_flag = True
time_limit = False
queue_type = "input"

np.random.seed(0)


def create_main_timeline(main_timeline, number_of_packets):
    global total_id
    for host in host_list:
        host.create_timeline(number_of_packets)
    main_timeline.create_timeline(host_list, total_id)


# noinspection DuplicatedCode
def run_timeline(main_timeline, start_time):
    enough_time_passed = False
    for event in main_timeline.timeline:
        while enough_time_passed is False:  # check if event should be executed
            if event.schedule_time < start_time:
                enough_time_passed = True  # to exit loop
        enough_time_passed = False  # reset flag for next iteration
        if time.time() - start_time >= 5:
            print("Simulation took too long. Exiting.")
            return -1
        random_message_size = np.random.randint(64, 1518)
        scheduling_host = host_list[int(event.scheduling_object_id)]
        target_host = host_list[event.target_object_id]
        message = host_list[event.scheduling_object_id].create_message(scheduling_host.address, target_host.address,
                                                                       message_size=random_message_size,
                                                                       message_id=event.message_id,
                                                                       schedule_time=event.schedule_time,
                                                                       start_time=start_time,
                                                                       print_flag=print_flag)
        for link in link_list:
            if (link.host1 == scheduling_host and link.host2 == target_host) or (
                    link.host2 == scheduling_host and link.host1 == target_host):
                if link.is_link_busy(time.time(), random_message_size):  # link is busy, add to queue
                    scheduling_host.host_buffer.put(message)
                    if print_flag:
                        print(f'Host <{scheduling_host.address}> added message to buffer')

                else:  # link is not busy
                    temp = scheduling_host.host_buffer.empty()
                    if temp:
                        link.time_sent = time.time()
                        link.send_message(message, host_list, print_flag, start_time)
                    else:
                        scheduling_host.host_buffer.put(message)
                        queued_message = scheduling_host.host_buffer.get()
                        link.time_sent = time.time()
                        link.send_message(queued_message, host_list, print_flag, start_time)


def get_switch_by_hosts(scheduling_host, target_host):
    for switch in switch_list:
        if scheduling_host in switch.hosts and target_host in switch.hosts:
            return switch


# noinspection DuplicatedCode
def run_timeline_switch(main_timeline, start_time):
    # Function to create messages for switches according to the main timeline and start time
    message_list = []
    enough_time_passed = False
    for event in main_timeline.timeline:
        while enough_time_passed is False:  # check if event should be executed
            if event.schedule_time < start_time:
                enough_time_passed = True  # to exit loop
        enough_time_passed = False  # reset flag for next iteration
        if time_limit:
            if time.time() - start_time >= 10:
                print("Simulation took too long. Exiting.")
                return -1
        if event.event_type == "create":
            random_message_size = np.random.randint(64, 1518)
            scheduling_host = host_list[int(event.scheduling_object_id)]
            target_host = host_list[event.target_object_id]
            event.message_id = len(message_list)
            message = host_list[event.scheduling_object_id].create_message(scheduling_host.address, target_host.address,
                                                                           message_size=random_message_size,
                                                                           message_id=event.message_id,
                                                                           schedule_time=event.schedule_time,
                                                                           start_time=start_time, print_flag=print_flag)
            message_list.append(message)
            for switch in switch_list:
                for link in link_list:
                    if (link.host1 == scheduling_host and link.host2 == switch) or (
                            link.host2 == scheduling_host and link.host1 == switch):
                        if link.is_link_busy(event.schedule_time, random_message_size):
                            scheduling_host.host_buffer.put(message)
                        else:  # link is not busy
                            if scheduling_host.host_buffer.empty():
                                link.send_message_to_switch_part_2(message, switch, host_list, switch_list, link_list,
                                                                   print_flag,
                                                                   start_time)
                                link.time_sent = time.time() - start_time

                            else:
                                scheduling_host.host_buffer.put(message)
                                queued_message = scheduling_host.host_buffer.get()
                                link.send_message_to_switch_part_2(queued_message, switch, host_list, switch_list,
                                                                   link_list,
                                                                   print_flag, start_time)
                                link.time_sent = time.time() - start_time
            next_message_to_send, sending_switch = check_queues_for_earliest()
            if next_message_to_send is not None:
                sending_switch.send_message_to_host_part_2(next_message_to_send, link_list, host_list, start_time,
                                                           print_flag)


def check_queues_for_earliest():
    for switch in switch_list:
        top_of_queues = []
        if queue_type == "input":
            for queue in switch.switch_queues:
                for i in range(len(queue)):
                    top_of_queues.append(queue[i])
            if len(top_of_queues) == 0:
                return None, switch
            earliest_message = min(top_of_queues, key=lambda x: x.schedule_time)
            return earliest_message, switch


def send_rest_of_queue(start_time):
    for curr_host in host_list:
        while not curr_host.host_buffer.empty():
            if time_limit:
                if time.time() - start_time >= 10:
                    print("Simulation took too long. Exiting.")
                    break
            curr_link = find_link(curr_host)
            if curr_link.is_link_busy(time.time() - start_time, curr_host.host_buffer.queue[0].message_size):
                queued_message = curr_host.host_buffer.get()
                curr_link.send_message(queued_message, host_list, print_flag, start_time)
                curr_link.time_sent = time.time() - start_time


def send_rest_of_queue_part_2(start_time):
    amount_of_messages_in_buffer = 0
    messages_in_switch = 0
    for host in host_list:
        amount_of_messages_in_buffer += len(host.host_buffer.queue)
    for switch in switch_list:
        for queue in switch.switch_queues:
            messages_in_switch += len(queue)
    print(f'Amount of messages in buffers at start: {amount_of_messages_in_buffer}')
    while amount_of_messages_in_buffer > 0 or messages_in_switch > 0:
        for switch in switch_list:
            if messages_in_switch > 0:
                earliest_message, sending_switch = check_queues_for_earliest()
                if earliest_message is not None:
                    curr_link = [link for link in link_list if link.host1.address == earliest_message.src_address][0]
                    if not curr_link.is_link_busy(time.time() - start_time, earliest_message.message_size):
                        if print_flag:
                            print(f'sending message {earliest_message.message_id} of size {earliest_message.message_size} to host {earliest_message.dst_address}')
                        message_still_in_switch = sending_switch.send_message_to_host_part_2(earliest_message,
                                                                                             link_list, host_list,
                                                                                             start_time,
                                                                                             print_flag)
                        if message_still_in_switch:
                            messages_in_switch += 1
                        messages_in_switch -= 1
                    else:  # link is busy
                        sending_switch.calculate_hol_time(earliest_message, curr_link.host1.address)
                        # NEED TO CHECK HOL BLOCKING
                else:  # no messages in queues
                    break
        if amount_of_messages_in_buffer > 0:
            earliest_message_from_buffer = find_earliest_from_buffer()
            if earliest_message_from_buffer is not None:
                curr_link = [link for link in link_list if
                             link.host1.address == earliest_message_from_buffer.src_address][0]
                curr_host = curr_link.host1
                if not curr_link.is_link_busy(time.time() - start_time, earliest_message_from_buffer.message_size):
                    curr_link.send_message_to_switch_part_2(earliest_message_from_buffer, curr_link.host2, host_list,
                                                            switch_list, link_list, print_flag, start_time)
                    curr_link.time_sent = time.time() - start_time
                    curr_host.host_buffer.get()
                    amount_of_messages_in_buffer -= 1
                    messages_in_switch += 1
                    if print_flag:
                        for host in host_list:
                            print(
                                f'host {host.address} has a {len(host.host_buffer.queue)} messages in buffer')


def find_earliest_from_buffer():
    temp = []
    for host in host_list:
        if not host.host_buffer.empty():
            temp.append(host.host_buffer.queue[0])
    if len(temp) == 0:
        return None
    return min(temp, key=lambda x: x.schedule_time)


def find_link(host):
    for link in link_list:
        if link.host1 == host or link.host2 == host:
            return link


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


def build_AND_plot_B1_graph(switch_list, link_list, host_list, images_list):
    G = nx.Graph()
    # G.add_node("switch",image =images_list["switch"])
    for host in host_list:
        G.add_node(host, image=images_list["PC"])
    for switch in switch_list:
        G.add_node(switch, image=images_list["switch"])
        for link in link_list:
            if link.host1 == host_list[0] and link.host2 == switch:
                G.add_edge(switch, host_list[0])
            elif link.host1 == host_list[1] and link.host2 == switch:
                G.add_edge(switch, host_list[1])
            elif link.hosBt1 == host_list[2] and link.host2 == switch:
                G.add_edge(switch, host_list[2])

    # Get a reproducible layout and create figure
    pos = nx.spring_layout(G, seed=1734289230)
    fig, ax = plt.subplots()

    # Note: the min_source/target_margin kwargs only work with FancyArrowPatch objects.
    # Force the use of FancyArrowPatch for edge drawing by setting `arrows=True`,
    # but suppress arrowheads with `arrowstyle="-"`
    nx.draw_networkx_edges(
        G,
        pos=pos,
        ax=ax,
        arrows=True,
        arrowstyle="-",
        min_source_margin=15,
        min_target_margin=15,
    )

    # Transform from data coordinates (scaled between xlim and ylim) to display coordinates
    tr_figure = ax.transData.transform
    # Transform from display to figure coordinates
    tr_axes = fig.transFigure.inverted().transform

    # Select the size of the image (relative to the X axis)
    icon_size = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.025
    icon_center = icon_size / 2.0

    # Add the respective image to each node
    for n in G.nodes:
        xf, yf = tr_figure(pos[n])
        xa, ya = tr_axes((xf, yf))
        # get overlapped axes and plot icon
        a = plt.axes([xa - icon_center, ya - icon_center, icon_size, icon_size])
        a.imshow(G.nodes[n]["image"])
        a.axis("off")
    plt.show()


def plot_graph_B1(switch_list, link_list, host_list):
    G = nx.Graph()
    # G.add_node("switch",image =images_list["switch"])
    for host in host_list:
        G.add_node(host)
    for switch in switch_list:
        G.add_node(switch)
        for link in link_list:
            if link.host1 == host_list[0] and link.host2 == switch:
                G.add_edge(switch, host_list[0])
            elif link.host1 == host_list[1] and link.host2 == switch:
                G.add_edge(switch, host_list[1])
            elif link.host1 == host_list[2] and link.host2 == switch:
                G.add_edge(switch, host_list[2])

    node_sizes = [2000 if node in switch_list else 500 for node in G.nodes()]

    # Get positions for the nodes in the graph
    pos = nx.spring_layout(G)

    fig, ax = plt.subplots()
    labels = {node: f"{node.get_id()}" for node in G.nodes()}
    for node in G.nodes():
        if node in switch_list:
            labels[node] = f" Switch id :  {node.get_id()} "
        if node in host_list:
            labels[node] = f" Host id  : {node.get_id()}"

    # Draw the graph on the axis
    nx.draw(G, pos, with_labels=False, node_size=node_sizes, node_color='lightblue', font_size=8, font_weight='bold',
            ax=ax)
    nx.draw_networkx_labels(G, pos, labels, font_size=8)

    # Display the graph
    plt.title('Network Graph with Switches and Hosts')
    plt.show()


def plot_B2_graph(switch_list, link_list, host_list, number_of_ports_one, number_of_ports_two):
    G = nx.Graph()
    # G.add_node("switch",image =images_list["switch"])
    # for host in host_list:
    #     G.add_node(host)
    for switch in switch_list:
        for link in link_list:
            for i in range(number_of_ports_one):
                if link.host1 == host_list[i] and link.host2.address == switch.address:
                    G.add_edge(switch, host_list[i])

            for j in range(number_of_ports_two):
                if link.host1 == host_list[j + number_of_ports_one] and link.host2.address == switch.address:
                    G.add_edge(switch, host_list[j + number_of_ports_one])
    G.add_edge(switch_list[0], switch_list[1])

    node_sizes = [2000 if node in switch_list else 500 for node in G.nodes()]

    # Get positions for the nodes in the graph
    pos = nx.spring_layout(G)

    fig, ax = plt.subplots()
    labels = {node: f"{node.get_id()}" for node in G.nodes()}
    for node in G.nodes():
        if node in switch_list:
            labels[node] = f" Switch id :  {node.get_id()} "
        if node in host_list:
            labels[node] = f" Host id  : {node.get_id()}"

    # Draw the graph on the axis
    nx.draw(G, pos, with_labels=False, node_size=node_sizes, node_color='lightblue', font_size=8, font_weight='bold',
            ax=ax)
    nx.draw_networkx_labels(G, pos, labels, font_size=8)

    # Display the graph
    plt.title('Network Graph with Clouds')
    plt.show()


def main():
    # Main function to initialize and run the simulation
    # choice = input("Enter Question Number for simulation (A/B1/B2):  ").upper()
    # number_of_packets = int(input("Enter number of packets to simulate per host: "))
    choice = 'B1'
    number_of_packets = 3

    if choice == "A":
        host_list.append(Host.Host(0, 2, total_id))
        host_list.append(Host.Host(1, 2, total_id))
        link_list.append(Link.Link(2, host_list[0], host_list[1],
                                   transmission_rate=1000, prop_delay=2, error_rate=0))

        main_timeline = Timeline.Timeline()
        create_main_timeline(main_timeline, number_of_packets)
        start_time = time.time()
        term = run_timeline(main_timeline, start_time)
        if term != -1:
            send_rest_of_queue(start_time)
        # if print_flag:
        simulation_end(number_of_packets)

    if choice == "B1":
        host_list.append(Host.Host(0, 2, total_id))
        host_list.append(Host.Host(1, 2, total_id))
        host_list.append(Host.Host(2, 2, total_id))
        switch_list.append(Switch.Switch(3, 3, "input"))
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
        run_timeline_switch(main_timeline, start_time)
        send_rest_of_queue_part_2(start_time)
        if print_flag:
            for switch in switch_list:
                switch.print_mac_table(link_list)
                print(f"\nTotal HoL blocking times for switch {switch.address}: {switch.total_hol_time}")

        # G = build_AND_plot_B1_graph(switch_list,link_list,host_list,icons_list)
        # plot_graph_B1(switch_list, link_list, host_list)

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
        run_timeline_switch(main_timeline, start_time)
        send_rest_of_queue(start_time)
        if print_flag:
            for switch in switch_list:
                switch.print_mac_table(link_list)
        plot_B2_graph(switch_list, link_list, host_list, number_of_ports_one, number_of_ports_two)


main()
