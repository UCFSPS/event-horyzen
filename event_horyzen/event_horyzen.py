#!/usr/bin/env python3
"""Evaluate geodesics for different spacetime backgrounds."""

# Copyright (C) 2021 David Wright
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
from datetime import datetime as dt
from multiprocessing import cpu_count, Pool
from pathlib import Path
import pickle as pl
from shutil import copy2
from typing import Union

import h5py
import matplotlib.pyplot as plt
import numpy as np
from yaml import safe_load

from event_horyzen.fantasy import geodesic_integrator


def run(conf_path: Union[Path, str, None] = None) -> None:
    """Run routine for geodesic motion simulation.

    Given the configuration file(s), simulate the gedoesic(s).

    Parameters
    ----------
    conf_path : Union[Path, str, None], optional
        The path to the YAML configuration file. If None, use default
        config.yml.

    Examples
    --------
    FIXME: Add docs.

    """
    # Make the path to config file a list if it is not so that it works with the
    # multiprocessing implementation
    if conf_path is None:
        conf_path = Path(__file__).parent / "config.yml"
    if not isinstance(conf_path, list):
        conf_path = [conf_path]

    # Empty lists to store values during multiprocessing
    args_list = []
    filename_list = []
    out_dir_list = []
    a_list = []

    # Loop over each provided configuration file
    for datapath in conf_path:
        with open(datapath, "r") as f:
            conf = safe_load(f)

            metric = conf["background_choice"].lower()
            bh_params = conf[metric]
            bh_params_list = list(bh_params.values())

        particle_params = conf["test_particle"]

        # Initial 4-position and 4-momentum
        q0 = particle_params["q0"]
        p0 = particle_params["p0"]

        # Simulation parameters
        num_steps = conf["num_steps"]
        time_step = conf["time_step"]
        integration_order = conf["integration_order"]
        omega = conf["omega"]
        use_hdf5 = conf.get("use_hdf5", True)

        # The arguments are stored as a tuple so they can be mapped using Pool.starmap()
        # An example argument tuple with added information is shown below
        #
        # (N=1000, delta=0.5, omega=1, q0=q0, p0=p0, Param = bh_params_list, order=2 )]
        #
        # When you create your own argument tuple, you need to drop the keywords
        # and just use positional arguments
        args = (num_steps, time_step, omega, q0, p0, bh_params_list, integration_order)
        args_list.append(args)

        # Append information about each simulation
        filename_list.append(datapath)
        out_dir_list.append(conf["output_dir"])

        a_list.append(bh_params_list[1] / bh_params_list[0])

    # Start a multiprocessing pool and use as many cores as available to run the
    # requested simulations
    with Pool(cpu_count()) as pool:
        results = pool.starmap(geodesic_integrator, args_list)

    results = np.array(results)

    # Colons are not present in timestamp because they are not allowed in Windows
    # filenames!
    dt_string = dt.now().strftime("%Y-%m-%dT%H%M%S")

    # Iterate over each simulation and act
    for i, sim in enumerate(filename_list):

        # Get a unique output directory
        out_dir = Path(out_dir_list[i])
        sim_dir = Path(dt_string + "_" + sim.stem)
        p = out_dir / sim_dir
        p.mkdir(parents=True, exist_ok=True)

        # Copy the config file to the output directory so this simulation is
        # reproducible
        copy2(sim, p)

        # We'll make a basic plot
        fig = plt.figure()
        ax = plt.axes(projection="3d")

        # Read in Boyer-Lindquist coords
        t = results[i, :, 0, 0]
        r = results[i, :, 0, 1]
        theta = results[i, :, 0, 2]
        phi = results[i, :, 0, 3]

        # We need the Kerr parameter in order to convert to cartesian from
        # Boyer-Lindquist coords
        a = a_list[i]

        # Get cartesian coords for plotting
        x = np.sqrt(r ** 2 + a ** 2) * np.sin(theta) * np.cos(phi)
        y = np.sqrt(r ** 2 + a ** 2) * np.sin(phi) * np.sin(theta)
        z = r * np.cos(theta)

        ax.scatter3D(x, y, z, c=t, s=1)
        plt.savefig(p / "basic-plot.png")

        # Pickle the plot so it can be interactively viewed later
        with open(p / "basic-plot.pickle", "wb") as f:
            pl.dump(fig, f)

        # h5 files show significant file size reductions, and this is very
        # evident for N>10,000 simulations. If you don't care, see the
        # numpy.savetxt block below.
        if use_hdf5:
            with h5py.File(p / "results.h5", "w") as hf:
                hf.create_dataset("time", data=t)
                hf.create_dataset("radius", data=r)
                hf.create_dataset("theta", data=theta)
                hf.create_dataset("phi", data=phi)
                hf.create_dataset("x", data=x)
                hf.create_dataset("y", data=y)
                hf.create_dataset("z", data=z)

        print("Output saved in", p)

        # If you prefer not to work with h5 files, set use_hdf5 in the configuration
        # file to False.
        if not use_hdf5:
            np.savetxt(p / "t.txt", t, header="Time values")
            np.savetxt(p / "r.txt", r, header="Radius values")
            np.savetxt(p / "theta.txt", theta, header="Theta values")
            np.savetxt(p / "phi.txt", phi, header="Phi values")
            np.savetxt(p / "x.txt", x, header="Cartesian X values")
            np.savetxt(p / "y.txt", y, header="Cartesian Y values")
            np.savetxt(p / "z.txt", z, header="Cartesian Z values")
            np.save(p / "results.npy", results)


def copy_default_config(dest: Union[Path, str] = None) -> None:
    """Copy default configuration.

    Parameters
    ----------
    dest : Union[Path, str], optional
        The destination to copy to

    Examples
    --------
    >>> from event_horyzen.event_horyzen import copy_default_config
    >>> copy_default_config()

    The above copies to your current working directory.
    This next example copies to a chosen location.

    >>> from event_horyzen.event_horyzen import copy_default_config
    >>> copy_default_config("/tmp/default-config.yml")

    Or

    >>> from event_horyzen.event_horyzen import copy_default_config
    >>> from pathlib import Path
    >>> dest = Path("/tmp/default-config.yml")
    >>> copy_default_config(dest)

    """
    if dest is None:
        dest = Path.cwd()
    copy2(Path(__file__).parent / "config.yml", dest)
    print("Copied default configuration to {}".format(dest))


def cli():
    """CLI interface for event_horyzen module."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "datapath",
        nargs="*",
        default=Path(__file__).parent / "config.yml",
        type=Path,
        help="The path(s) to the configuration file(s). Defaults to the included"
        "`config.yml` if not provided.",
    )
    args = parser.parse_args()

    run(args.datapath)


if __name__ == "__main__":
    cli()
