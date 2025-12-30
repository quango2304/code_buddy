import subprocess
import threading
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool

# Root directory for command execution
ROOT_DIR = Path.cwd()

# Store for background processes: {process_id: {"process": Popen, "output": str}}
_processes: dict[str, dict] = {}
_process_counter = 0
_lock = threading.Lock()


def _read_output(process_id: str) -> None:
    """Background thread to read process output."""
    proc_info = _processes.get(process_id)
    process = proc_info["process"]
    try:
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                with _lock:
                    proc_info["output"] += line
    except Exception:
        pass


@tool
def run_command(
    command: Annotated[str, "The shell command to execute"],
    working_dir: Annotated[str, "Working directory (relative to project root)"] = ".",
    background: Annotated[bool, "If True, run in background and return process ID"] = False,
    timeout: Annotated[int, "Timeout in seconds for foreground commands"] = 60,
) -> str:
    """Run a shell command.

    Returns:
        Command output for foreground, or process ID for background commands.
    """
    global _process_counter

    cwd = ROOT_DIR / working_dir
    if not cwd.exists():
        return f"Error: Directory '{working_dir}' does not exist"

    try:
        if background:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
            )

            with _lock:
                _process_counter += 1
                process_id = f"proc_{_process_counter}"
                _processes[process_id] = {"process": process, "output": ""}

            # Start background thread to read output
            thread = threading.Thread(target=_read_output, args=(process_id,))
            thread.daemon = True
            thread.start()

            return f"Started background process: {process_id}"
        else:
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"
            if result.returncode != 0:
                output += f"\n[exit code]: {result.returncode}"
            return output or "(no output)"

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def read_command_output(
    process_id: Annotated[str, "The process ID returned by run_command"],
    clear: Annotated[bool, "If True, clear the output buffer after reading"] = True,
) -> str:
    """Read output from a background command.

    Returns:
        The accumulated output from the process.
    """
    with _lock:
        proc_info = _processes.get(process_id)
        if not proc_info:
            return f"Error: Process '{process_id}' not found"

        output = proc_info["output"]
        if clear:
            proc_info["output"] = ""

        process = proc_info["process"]
        status = "running" if process.poll() is None else f"exited ({process.returncode})"

    return f"[status: {status}]\n{output}" if output else f"[status: {status}]\n(no new output)"


@tool
def send_command_input(
    process_id: Annotated[str, "The process ID returned by run_command"],
    input_text: Annotated[str, "Text to send to the process stdin"],
    terminate: Annotated[bool, "If True, terminate the process instead of sending input"] = False,
) -> str:
    """Send input to a running background command.

    Returns:
        Status message.
    """
    with _lock:
        proc_info = _processes.get(process_id)
        if not proc_info:
            return f"Error: Process '{process_id}' not found"

        process = proc_info["process"]

    if terminate:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        with _lock:
            del _processes[process_id]
        return f"Process '{process_id}' terminated"

    if process.poll() is not None:
        return f"Error: Process '{process_id}' has already exited"

    try:
        process.stdin.write(input_text)
        process.stdin.flush()
        return f"Sent input to '{process_id}'"
    except Exception as e:
        return f"Error sending input: {str(e)}"