#! /usr/bin/env python3

# Plot animated geodesics in 3D using hardware acceleration, possibly multiple at once.
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
""

import argparse
from pathlib import Path
import sys
from typing import Union

import h5py
import numpy as np
import numpy.typing as npt
import pyqtgraph.opengl as gl
from pyqtgraph.Qt import QtCore, QtGui


class Visualizer:
    """Visulization object

    Examples
    --------
    >>> v = Visualizer(['results1.h5', 'results2.h5'])
    >>> v.animation()

    """

    def __init__(
        self,
        results_files: Union[list, Path],
        schwarz_photon_sphere: bool = True,
        mass: float = 1,
    ):

        # Make sure we are working with a list of files, important for multiple
        # geodesics at once
        if not isinstance(results_files, list):
            results_files: list = [results_files]
        self.results_files: list = results_files
        self.do_photon_sphere: bool = schwarz_photon_sphere
        self.mass: float = mass

        # Some initializations for later
        self.traces: dict = dict()
        self.app = QtGui.QApplication(sys.argv)
        self.w = gl.GLViewWidget()
        self.w.opts["distance"]: float = 80
        self.w.setWindowTitle("Black Hole Geodesics")
        self.w.setGeometry(0, 110, 1920, 1080)
        self.w.show()

        # Create the coordinate axes
        orientation = gl.GLAxisItem()
        orientation.setSize(x=10, y=10, z=10)
        self.w.addItem(orientation)

        # Do we want to see a schwarzschild photon sphere for a reference?
        if self.do_photon_sphere:
            sphere_mesh = gl.MeshData.sphere(rows=10, cols=10, radius=3 * self.mass)
            self.photon_sphere = gl.GLMeshItem(
                meshdata=sphere_mesh,
                smooth=True,
                color=(1, 1, 1, 0.4),
                shader="shaded",
                glOptions="translucent",
            )
            self.photon_sphere.translate(0, 0, 0)
            self.w.addItem(self.photon_sphere)

        # Go through each file given and get the cartesian coords
        for result_file in results_files:
            with h5py.File(result_file, "r") as hf:

                # I use the try except structure so that this works even for a
                # single geodesic
                try:
                    self.t: npt.NDArray[np.float64] = np.column_stack(
                        (self.t, hf["time"][:])
                    )
                except AttributeError:
                    self.t: npt.NDArray[np.float64] = hf["time"][:]
                except ValueError:
                    print(
                        "These simulations do not have matching dimensions!\nThe"
                        " product of `num_steps` and `time_step` must be the same!"
                    )
                    sys.exit(-1)
                try:
                    self.x: npt.NDArray[np.float64] = np.column_stack(
                        (self.x, hf["x"][:])
                    )
                except AttributeError:
                    self.x: npt.NDArray[np.float64] = hf["x"][:]
                try:
                    self.y: npt.NDArray[np.float64] = np.column_stack(
                        (self.y, hf["y"][:])
                    )
                except AttributeError:
                    self.y: npt.NDArray[np.float64] = hf["y"][:]
                try:
                    self.z: npt.NDArray[np.float64] = np.column_stack(
                        (self.z, hf["z"][:])
                    )
                except AttributeError:
                    self.z: npt.NDArray[np.float64] = hf["z"][:]

        # Get the points into the form pyqtgraph expects and plot them
        pts: npt.NDArray[np.float64] = np.vstack(
            [self.x[0], self.y[0], self.z[0]]
        ).transpose()
        self.traces = gl.GLScatterPlotItem(pos=pts)
        self.w.addItem(self.traces)

    def start(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
            QtGui.QApplication.instance().exec_()

    def set_plotdata(self, name, points, color, width):
        self.traces[name].setData(pos=points)  # , color=color, width=width)

    def update(self):
        """Update the plot

        Roll the coordinate arrays so that the next item in the array becomes
        the first. Set this item as the current displayed point.
        """

        self.x: npt.NDArray[np.float64] = np.roll(self.x, -10, axis=0)
        self.y: npt.NDArray[np.float64] = np.roll(self.y, -10, axis=0)
        self.z: npt.NDArray[np.float64] = np.roll(self.z, -10, axis=0)
        pts: npt.NDArray[np.float64] = np.vstack(
            [self.x[0], self.y[0], self.z[0]]
        ).transpose()
        self.traces.setData(pos=pts)

    def animation(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(20)
        self.start()


def cli():
    """Command line interface for animated 3D plotting module."""

    parser = argparse.ArgumentParser()
    # Accept one or more arguments
    parser.add_argument(
        "datapath", nargs="+", type=Path, help="The path(s) to the data file(s)."
    )
    args = parser.parse_args()

    v = Visualizer(args.datapath)
    v.animation()


# Start Qt event loop unless running in interactive mode.
if __name__ == "__main__":
    cli()
