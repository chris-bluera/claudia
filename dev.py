#!/usr/bin/env python3
"""
Claudia Development Runner

Starts all development services:
- PostgreSQL (Docker Compose)
- Backend (FastAPI/uvicorn)
- Frontend (Vite)

Usage: python3 dev.py
"""
import subprocess
import sys
import signal
import threading
import time
from pathlib import Path
from typing import Optional

# ANSI color codes
RESET = '\033[0m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
GREEN = '\033[32m'
RED = '\033[31m'
GRAY = '\033[90m'

# Service configurations
SERVICES = {
    'postgres': {
        'name': 'postgres',
        'color': YELLOW,
        'command': ['docker-compose', 'up'],
        'cwd': Path(__file__).parent,
    },
    'backend': {
        'name': 'backend',
        'color': BLUE,
        'command': ['uv', 'run', 'uvicorn', 'app.main:app', '--reload'],
        'cwd': Path(__file__).parent / 'backend',
    },
    'frontend': {
        'name': 'frontend',
        'color': GREEN,
        'command': ['npm', 'run', 'dev'],
        'cwd': Path(__file__).parent / 'frontend',
    },
}

processes: dict[str, subprocess.Popen] = {}
shutdown_requested = False


def log(service: str, message: str, color: str = RESET):
    """Print colored log message with service prefix"""
    prefix = f"{color}[{service}]{RESET}"
    # Handle multi-line messages
    for line in message.rstrip().split('\n'):
        if line.strip():
            print(f"{prefix} {line}", flush=True)


def stream_output(service_name: str, proc: subprocess.Popen, color: str):
    """Stream process output with colored prefix"""
    if proc.stdout is None:
        log('dev', f"No stdout for {service_name}", RED)
        return

    try:
        for line in iter(proc.stdout.readline, b''):
            if shutdown_requested:
                break
            try:
                decoded = line.decode('utf-8', errors='replace')
                log(service_name, decoded, color)
            except Exception as e:
                log('dev', f"Error decoding output from {service_name}: {e}", RED)
    except Exception as e:
        if not shutdown_requested:
            log('dev', f"Error streaming {service_name}: {e}", RED)


def start_service(service_key: str) -> Optional[subprocess.Popen]:
    """Start a service and return its process"""
    config = SERVICES[service_key]
    name = config['name']
    color = config['color']

    log('dev', f"Starting {name}...", GRAY)

    try:
        proc = subprocess.Popen(
            config['command'],
            cwd=config['cwd'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )

        # Start thread to stream output
        thread = threading.Thread(
            target=stream_output,
            args=(name, proc, color),
            daemon=True
        )
        thread.start()

        log('dev', f"Started {name} (PID: {proc.pid})", GRAY)
        return proc

    except FileNotFoundError:
        log('dev', f"Failed to start {name}: command not found", RED)
        log('dev', f"  Command: {' '.join(config['command'])}", RED)
        return None
    except Exception as e:
        log('dev', f"Failed to start {name}: {e}", RED)
        return None


def shutdown(_signum=None, _frame=None):
    """Gracefully shutdown all services"""
    global shutdown_requested

    if shutdown_requested:
        log('dev', "Force shutdown...", RED)
        sys.exit(1)

    shutdown_requested = True
    log('dev', "Shutting down services...", GRAY)

    # Terminate processes in reverse order
    for service_name in reversed(list(processes.keys())):
        proc = processes[service_name]
        if proc and proc.poll() is None:
            log('dev', f"Stopping {service_name}...", GRAY)
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                log('dev', f"Force killing {service_name}...", YELLOW)
                proc.kill()
            except Exception as e:
                log('dev', f"Error stopping {service_name}: {e}", RED)

    log('dev', "All services stopped", GRAY)
    sys.exit(0)


def main():
    """Main entry point"""
    global processes

    # Register signal handlers
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    log('dev', "Starting Claudia development environment", BLUE)
    log('dev', "Press Ctrl+C to stop all services", GRAY)
    print()

    # Start services in order
    for service_key in ['postgres', 'backend', 'frontend']:
        proc = start_service(service_key)
        if proc:
            processes[service_key] = proc
            # Brief pause between service starts
            time.sleep(0.5)
        else:
            log('dev', f"Failed to start {service_key}, aborting", RED)
            shutdown()

    print()
    log('dev', "All services started successfully", GREEN)
    log('dev', "Backend: http://localhost:8000", BLUE)
    log('dev', "Frontend: http://localhost:5173", GREEN)
    log('dev', "API Docs: http://localhost:8000/api/docs", BLUE)
    print()

    # Wait for processes to complete or exit
    try:
        while not shutdown_requested:
            # Check if any process has died
            for service_name, proc in processes.items():
                if proc.poll() is not None:
                    exit_code = proc.returncode
                    log('dev', f"{service_name} exited with code {exit_code}", RED)
                    shutdown()

            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()


if __name__ == '__main__':
    main()
