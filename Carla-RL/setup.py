import atexit
import collections
import os
import random
import signal
import subprocess
import sys
import time
from typing import Any, List, Mapping, Optional, Sequence, Tuple, Union

import carla
import numpy as np
import transforms3d.euler
import logging

# logging.set_verbosity(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

def setup(
    town: str,
    fps: int = 20,
    server_timestop: float = 30.0,
    client_timeout: float = 20.0,
    num_max_restarts: int = 10,
):
    """Returns the `CARLA` `server`, `client` and `world`.

    Args:
        town: The `CARLA` town identifier.
        fps: The frequency (in Hz) of the simulation.
        server_timestop: The time interval between spawing the server
        and resuming program.
        client_timeout: The time interval before stopping
        the search for the carla server.
        num_max_restarts: Number of attempts to connect to the server.

    Returns:
        client: The `CARLA` client.
        world: The `CARLA` world.
        frame: The synchronous simulation time step ID.
        server: The `CARLA` server.
    """
    assert town in ("Town01", "Town02", "Town03", "Town04", "Town05")

    # The attempts counter.
    attempts = 0

    while attempts < num_max_restarts:
        logging.debug("{} out of {} attempts to setup the CARLA simulator".format(
            attempts + 1, num_max_restarts))

        # Random assignment of port.
        port = 2000 + attempts

        # Start CARLA server.
        env = os.environ.copy()
        env["SDL_VIDEODRIVER"] = "offscreen"
        env["SDL_HINT_CUDA_DEVICE"] = "0"
        logging.debug("Inits a CARLA server at port={}".format(port))

        if os.name == 'nt':  # Windows
            server = subprocess.Popen(
                str(os.path.join(os.environ.get("CARLA_ROOT"), "CarlaUE4.exe")) + f' -opengl ' + f' -carla-rpc-port={port}' + f" -quality-level=Epic ",
                stdout=None, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP, env=env, shell=True
            )
            atexit.register(lambda: os.kill(server.pid, signal.SIGTERM))
        else:  # Linux/Unix
            server = subprocess.Popen(
                f'DISPLAY= ' + str(os.path.join(os.environ.get("CARLA_ROOT"), "CarlaUE4.sh")) + f' -opengl ' + f' -carla-rpc-port={port}' + f" -quality-level=Epic ",
                stdout=None, stderr=subprocess.STDOUT, preexec_fn=os.setsid, env=env, shell=True
            )
            atexit.register(os.killpg, server.pid, signal.SIGKILL)

        time.sleep(server_timestop)

        # Connect client.
        logging.debug("Connects a CARLA client at port={}".format(port))
        try:
            client = carla.Client("localhost", port)  # pylint: disable=no-member
            client.set_timeout(client_timeout)
            logging.debug("Loading world: {}".format(town))
            client.load_world(map_name=town)
            world = client.get_world()
            world.set_weather(carla.WeatherParameters.ClearNoon)  # pylint: disable=no-member
            frame = world.apply_settings(
                carla.WorldSettings(  # pylint: disable=no-member
                    synchronous_mode=True,
                    fixed_delta_seconds=1.0 / fps,
                ))
            logging.debug("Server version: {}".format(client.get_server_version()))
            logging.debug("Client version: {}".format(client.get_client_version()))
            return client, world, frame, server
        except RuntimeError as msg:
            logging.debug(msg)
            attempts += 1
            logging.debug("Stopping CARLA server at port={}".format(port))
            
            if os.name == 'nt':  # Windows
                os.kill(server.pid, signal.SIGTERM)
            else:  # Linux/Unix
                os.killpg(server.pid, signal.SIGKILL)
                
            atexit.unregister(lambda: os.kill(server.pid, signal.SIGTERM))

    logging.debug(
        "Failed to connect to CARLA after {} attempts".format(num_max_restarts))
    sys.exit()
