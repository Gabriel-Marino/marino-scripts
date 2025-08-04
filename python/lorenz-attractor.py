import argparse
import os

import matplotlib.pyplot as plt
import numpy as np

from mpl_toolkits.mplot3d.art3d import Line3DCollection
from mpl_toolkits.mplot3d import Axes3D
from scipy.integrate import odeint

class Attractor():

    def __init__(self) -> None:
        self.beta = 8.0/3.0
        self.rho = 28.0
        self.sigma = 10.0

    def setup(self, beta: float, rho: float, sigma: float) -> None:
        self.beta = beta
        self.rho = rho
        self.sigma = sigma

    def lorenz(self, state: tuple[float, float, float], step: float) -> list[float]:
        x, y, z = state
        return [self.sigma * (-x + y), x * (self.rho - z) - y, x * y - self.beta * z]

class ParserHandler(Attractor):

    INITIALSTATE = [1.0, 1.0, 1.0]
    STEP_SIZE = 0.01
    TOTAL_STEPS = 3000
    CMAP = 'gist_heat'

    def get_parser(self) -> argparse.ArgumentParser:

        parser = argparse.ArgumentParser(
            prog=os.path.basename(__file__),
            usage="%(prog)s [options]",
            description="",
            epilog=""
        )

        parser.add_argument("--beta" , type=float, default=self.beta, help=f"Default: {self.beta}.")
        parser.add_argument("--rho"  , type=float, default=self.rho, help=f"Default: {self.rho}.")
        parser.add_argument("--sigma", type=float, default=self.sigma, help=f"Default: {self.sigma}.")
        parser.add_argument("--totalsteps", type=float, default=self.TOTAL_STEPS, help=f"Default: {self.TOTAL_STEPS}.")
        parser.add_argument("--stepsize", type=float, default=self.STEP_SIZE, help=f"Default: {self.STEP_SIZE}.")
        parser.add_argument("--initialstate", type=float, nargs=3, default=self.INITIALSTATE, help=f"Default: {self.INITIALSTATE}.")
        parser.add_argument("--colormap", type=str, default=self.CMAP, help=f'Default: {self.CMAP}.')

        return parser

def main() -> None:

    try:
        parserHandler = ParserHandler()
        parser = parserHandler.get_parser()
        args = parser.parse_args()

        steps = np.arange(0.0, args.totalsteps*args.stepsize, args.stepsize)

        attractor = Attractor()
        attractor.setup(
            beta = args.beta,
            rho = args.rho,
            sigma = args.sigma
        )

        states = odeint(attractor.lorenz, args.initialstate, steps)
        points = states.reshape(-1, 1, 3)
        segments = np. concatenate([points[:-1], points[1:]], axis=1)

        colors = np.linspace(0, 1, len(segments))

        lc = Line3DCollection(segments, cmap=args.colormap, norm=plt.Normalize(0,1))
        lc.set_array(colors[:-1])
        lc.set_linewidth(2)

        fig = plt.figure()
        fig.patch.set_alpha(0.0)

        ax = fig.add_subplot(111, projection='3d')
        ax.set_axis_off()
        ax.set_facecolor((0, 0, 0, 0))
        ax.add_collection3d(lc)

        plt.show()

    except Exception as e:
        print(f"An exception occured: {e}")

if __name__ == "__main__":
    main()
