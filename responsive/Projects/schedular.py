from queue import PriorityQueue
import sys
class Process:
    def __init__(self, name: str, priority: int, arrival_time: int, total_time: int, block_interval: int):
        self.name = name
        self.priority = priority
        self.arrival_time = arrival_time
        self.total_time = total_time
        self.block_interval = block_interval
        self.remaining_time = total_time
        self.time_since_last_block = 0  # Cumulative runtime since last block
        self.block_end_time = 0
        self.completion_time = 0
        self.start_time = None
        self.round_robin_count = 0
        self.current_burst_start = 0  # Track when current burst started
        self.waiting_time = 0
        self.turnaround_time = 0
    def __lt__(self, other):
        # should we handle if thye are the same priroouty. i guess it wouldnt matter?? idk
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.arrival_time < other.arrival_time
class Scheduler:
    def __init__(self, time_slice: int, block_duration: int):
        self.time_slice = time_slice
        self.block_duration = block_duration
        self.current_time = 0
        self.arrival_queue = PriorityQueue()
        self.ready_queue = PriorityQueue()
        self.blocked_queue = PriorityQueue()
        self.completed_processes = []
        self.rr_counter = 0
        self.current_process = None
    def read_input_file(self, filename: str) -> None:
        with open(filename, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    name, priority, arrival, total, block = line.split()
                    process = Process(
                        name=name,
                        priority=int(priority),
                        arrival_time=int(arrival),
                        total_time=int(total),
                        block_interval=int(block)
                    )
                    print(f"ADDING TO ARRIVAL QUEUE: {process.name}")
                    print(f"with data: {process.name} {process.priority} {process.arrival_time} {process.total_time} {process.block_interval}")
                    self.arrival_queue.put((process.arrival_time, process))
    def check_arrivals(self) -> None:

        while not self.arrival_queue.empty():
            arrival_time, process = self.arrival_queue.queue[0]
            if arrival_time <= self.current_time:
                self.arrival_queue.get()
                process.round_robin_count = self.rr_counter
                self.rr_counter += 1
                print(f"ADDING TO READY QUEUE: {process.name}")
                self.ready_queue.put(process)
            else:
                break
    def check_blocked(self) -> None:

        temp_blocked = PriorityQueue()
        while not self.blocked_queue.empty():
            process = self.blocked_queue.get()
            if process.block_end_time <= self.current_time:
                # Process has finished blocking
                process.round_robin_count = self.rr_counter
                self.rr_counter += 1
                print(f"UNBLOCKING: {process.name} at time {self.current_time}")
                self.ready_queue.put(process)
            else:
                temp_blocked.put(process)
        self.blocked_queue = temp_blocked




    def run(self) -> float:
        print(f"timeSlice: {self.time_slice}\tblockDuration: {self.block_duration}")
        total_waiting_time = 0
        total_turnaround_time = 0
        process_comp = []
        while not (self.arrival_queue.empty() and self.ready_queue.empty() and
                  self.blocked_queue.empty() and self.current_process is None):
            self.check_arrivals()
            self.check_blocked()
            # Handle idle time
            if self.current_process is None and self.ready_queue.empty():
                next_time = float('inf')
                next_block_end = float('inf')
                if not self.arrival_queue.empty():
                    next_time = self.arrival_queue.queue[0][0]
                if not self.blocked_queue.empty():
                    # Find the process that will unblock first
                    blocked_processes = []
                    temp_blocked = PriorityQueue()
                    while not self.blocked_queue.empty():
                        process = self.blocked_queue.get()
                        blocked_processes.append(process)
                        temp_blocked.put(process)
                    self.blocked_queue = temp_blocked
                    if blocked_processes:
                        # Calculate remaining block time for each process
                        for process in blocked_processes:
                            time_already_blocked = self.current_time - (process.block_end_time - self.block_duration)
                            remaining_block_time = max(0, self.block_duration - time_already_blocked)
                            process_unblock_time = self.current_time + remaining_block_time
                            next_block_end = min(next_block_end, process_unblock_time)
                next_time = min(next_time, next_block_end)
                if next_time == float('inf'):
                    break
                idle_duration = next_time - self.current_time
                print(f"{self.current_time}\t(IDLE)\t{idle_duration}\tIdle")
                self.current_time = next_time
                continue
            # Get next process if none is running
            if self.current_process is None and not self.ready_queue.empty():
                self.current_process = self.ready_queue.get()
                self.current_process.current_burst_start = self.current_time
                if self.current_process.start_time is None:
                    self.current_process.start_time = self.current_time
            if self.current_process:
                # Calculate run duration considering blocking and time slice
                time_until_block = (self.current_process.block_interval -
                                  self.current_process.time_since_last_block) if self.current_process.block_interval > 0 else float('inf')
                run_duration = min(
                    self.time_slice,
                    self.current_process.remaining_time,
                    time_until_block
                )
                print(f"{self.current_time}\t{self.current_process.name}\t{run_duration}", end="\t")
                self.current_process.remaining_time -= run_duration
                self.current_process.time_since_last_block += run_duration
                self.current_time += run_duration
                if self.current_process.remaining_time == 0:
                    print("Terminated")
                    self.current_process.completion_time = self.current_time
                    print(f"Completion time: {self.current_process.completion_time}")
                    self.current_process.turnaround_time = (self.current_process.completion_time -  self.current_process.arrival_time)
                    self.current_process.waiting_time = (self.current_process.turnaround_time -
                                                       self.current_process.total_time)
                    process_comp.append(self.current_process)
                    self.current_process = None
                elif (self.current_process.block_interval > 0 and
                      self.current_process.time_since_last_block >= self.current_process.block_interval):
                    print("Blocked")
                    self.current_process.time_since_last_block = 0
                    self.current_process.block_end_time = self.current_time + self.block_duration
                    self.blocked_queue.put(self.current_process)
                    self.current_process = None
                else:
                    print("Preempted")
                    self.current_process.round_robin_count = self.rr_counter
                    self.rr_counter += 1
                    self.ready_queue.put(self.current_process)
                    self.current_process = None
                    # TIME STAMP WHEN IT ENDS - arrival = turnaround time
        # Print results
        print("\nProcess\tArrival\tBurst\tStart\tFinal\tWait\tTurnaround")
        for p in process_comp:
            print(f"{p.name}\t{p.arrival_time}\t{p.total_time}\t{p.start_time}\t{p.completion_time}\t{p.waiting_time}\t{p.turnaround_time}")
        if process_comp:
            avg_waiting_time = sum(p.waiting_time for p in process_comp) / len(process_comp)
            avg_turnaround_time = sum(p.turnaround_time for p in process_comp) / len(process_comp)
            print(f"\nAverage Waiting Time: {avg_waiting_time}")
            print(f"Average Turnaround Time: {avg_turnaround_time}")
            return avg_turnaround_time
        return 0.0
if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    print('NOW RUNNING')
    input_file = str(sys.argv[1])
    time_slice = int(sys.argv[2])
    block_duration = int(sys.argv[3])
    scheduler = Scheduler(time_slice, block_duration)
    scheduler.read_input_file(input_file)
    scheduler.run()
    print('ENDING..')