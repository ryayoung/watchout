import os
import sys
import pty
import select
import codecs
import subprocess
from datetime import datetime, timedelta
from time import perf_counter
from watchout.config import RunDetail


def run_command(cmd: list[str], display: bool = False) -> RunDetail:
    """
    Runs a command and mirrors its output to the current terminal, while **also**
    capturing the output as a string.

    Both the terminal output (to the current terminal) and the captured output are true
    TTY output, meaning they will have colors and other formatting preserved.

    The current terminal will receive the output in real-time, as the subprocess
    produces it, thus mirroring the observed behavior of running the given command
    directly in the terminal.
    """
    # Create a pseudo-terminal
    master_fd, slave_fd = pty.openpty()

    ran_at = datetime.now()
    start_time = perf_counter()
    # Run the command using the slave end of the PTY as its stdin, stdout, and stderr
    process = subprocess.Popen(cmd, stdin=slave_fd, stdout=slave_fd, stderr=slave_fd)

    os.close(slave_fd)  # Close the slave end in the parent process

    decoder = codecs.getincrementaldecoder('utf-8')()

    # Read and forward the output from the master end
    output = []
    # Use a massive buffer because we are just the middleman. We're sending the data
    # back to `print`, so buffering will be handled downstream.
    buffer_size = 1024 * 1024 * 1024  # 1 GB in bytes
    try:
        while True:
            # Wait for input from either the PTY or stdin
            rlist, _, _ = select.select([master_fd, sys.stdin], [], [])

            if master_fd in rlist:
                data = os.read(master_fd, buffer_size)
                if not data:
                    break
                decoded_data = decoder.decode(data)
                output.append(decoded_data)
                if display:
                    sys.stdout.write(decoded_data)
                    sys.stdout.flush()

            if sys.stdin in rlist:
                input_data = sys.stdin.readline()
                os.write(master_fd, input_data.encode())

    except OSError:
        pass  # End of output

    if remaining_data := decoder.decode(b'', final=True):
        output.append(remaining_data)
        if display:
            print(remaining_data, end='', flush=True)

    os.close(master_fd)  # Close the master end
    return_code = process.wait()  # Wait for the process to complete
    failed = return_code != 0

    end_time = perf_counter()

    duration = timedelta(seconds=end_time - start_time)
    return RunDetail(''.join(output), duration, ran_at, failed)



def run_command_(cmd: list[str], display: bool = False) -> RunDetail:
    """
    Runs a command and mirrors its output to the current terminal, while **also**
    capturing the output as a string.

    Both the terminal output (to the current terminal) and the captured output are true
    TTY output, meaning they will have colors and other formatting preserved.

    The current terminal will receive the output in real-time, as the subprocess
    produces it, thus mirroring the observed behavior of running the given command
    directly in the terminal.
    """
    # Create a pseudo-terminal
    master_fd, slave_fd = pty.openpty()

    ran_at = datetime.now()
    start_time = perf_counter()
    # Run the command using the slave end of the PTY as its stdin, stdout, and stderr
    process = subprocess.Popen(cmd, stdin=slave_fd, stdout=slave_fd, stderr=slave_fd)

    os.close(slave_fd)  # Close the slave end in the parent process

    decoder = codecs.getincrementaldecoder('utf-8')()

    # Read and forward the output from the master end
    output = []
    # Use a massive buffer because we are just the middleman. We're sending the data
    # back to `print`, so buffering will be handled downstream.
    buffer_size = 1024 * 1024 * 1024  # 1 GB in bytes
    try:
        while True:
            if not (data := os.read(master_fd, buffer_size)):
                break

            decoded_data = decoder.decode(data)
            output.append(decoded_data)
            # Always flush, because `os.read()` only returns flushed data
            if display:
                print(decoded_data, end='', flush=True)
    except OSError as e:
        pass  # End of output

    if remaining_data := decoder.decode(b'', final=True):
        output.append(remaining_data)
        if display:
            print(remaining_data, end='', flush=True)

    os.close(master_fd)  # Close the master end
    return_code = process.wait()  # Wait for the process to complete
    failed = return_code != 0

    end_time = perf_counter()

    duration = timedelta(seconds=end_time - start_time)
    return RunDetail(''.join(output), duration, ran_at, failed)


