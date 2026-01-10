import argparse
import os

import matplotlib.pyplot as plt
import numpy as np

from mpl_toolkits.mplot3d.art3d import Line3DCollection
from mpl_toolkits.mplot3d import Axes3D
from scipy.integrate import odeint

class ParserHandler:

    DEFAULT_INITIALSTATE = [1.0, 0.0, 0.0]
    DEFAULT_STEP_SIZE = 0.01
    DEFAULT_TOTAL_STEPS = 3000
    DEFAULT_CMAP = 'gist_heat'
    DEFAULT_a=1.4

    def get_parser(self) -> argparse.ArgumentParser:

        parser = argparse.ArgumentParser(
            prog=os.path.basename(__file__),
            usage="%(prog)s [options]",
            description="",
            epilog=""
        )

        parser.add_argument("-a", "--a" , type=float, default=self.DEFAULT_a, help=f"Default: {self.DEFAULT_a}.")
        parser.add_argument("-ts", "--totalsteps", type=int, default=self.DEFAULT_TOTAL_STEPS, help=f"Default: {self.DEFAULT_TOTAL_STEPS}.")
        parser.add_argument("-ss", "--stepsize", type=float, default=self.DEFAULT_STEP_SIZE, help=f"Default: {self.DEFAULT_STEP_SIZE}.")
        parser.add_argument("-is", "--initialstate", type=float, nargs=3, default=self.DEFAULT_INITIALSTATE, help=f"Default: {self.DEFAULT_INITIALSTATE}.")
        parser.add_argument("-cm", "--colormap", type=str, default=self.DEFAULT_CMAP, help=f'Default: {self.DEFAULT_CMAP}.')

        return parser

class Attractor(ParserHandler):

    def __init__(self) -> None:

        super().__init__()

        self.a = self.DEFAULT_a

    def setup(self, a: float, initialState: list[float]) -> None:
        self.a = a

        print(f"a={a}, {initialState}")

    def halvorsen (self, state: tuple[float, float, float], step: float) -> list[float]:
        x, y, z = state
        return [
            -self.a * x - 4*(y + z) - y*y,
            -self.a * y - 4*(z + x) - z*z,
            -self.a * z - 4*(x + y) - x*x
            ]

def main() -> None:

    try:
        attractor = Attractor()
        parser = attractor.get_parser()
        args = parser.parse_args()

        steps = np.arange(0.0, args.totalsteps*args.stepsize, args.stepsize)

        attractor.setup(
            a=args.a,
            initialState=args.initialstate
        )

        states0 = odeint(attractor.halvorsen, args.initialstate, steps)
        points0 = states0.reshape(-1, 1, 3)
        segments0 = np. concatenate([points0[:-1], points0[1:]], axis=1)

        colors0 = np.linspace(0, 1, len(segments0))

        lc0 = Line3DCollection(segments0, cmap=args.colormap, norm=plt.Normalize(0,1))
        lc0.set_array(colors0[:-1])
        lc0.set_linewidth(2)

        fig = plt.figure()
        fig.patch.set_alpha(0.0)

        ax = fig.add_subplot(111, projection='3d')
        ax.set_axis_off()
        ax.view_init(elev=-30, azim=-120)
        ax.set_facecolor((0, 0, 0, 0))
        ax.add_collection3d(lc0)

        plt.subplots_adjust(left=0, bottom=0, right=1, top=1)
        plt.show()

    except Exception as e:
        print(f"An exception occured: {e}")

if __name__ == "__main__":
    main()
