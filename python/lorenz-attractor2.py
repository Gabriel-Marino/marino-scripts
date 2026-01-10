import argparse
import os
import random

import matplotlib.pyplot as plt
import numpy as np

from matplotlib.animation import FuncAnimation, writers
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from mpl_toolkits.mplot3d import Axes3D
from scipy.integrate import odeint

class ParserHandler:

    DEFAULT_INITIALSTATE = [1.0, 1.0, 1.0]
    DEFAULT_STEP_SIZE = 0.01
    DEFAULT_TOTAL_STEPS = 5000
    DEFAULT_CMAP = 'gist_heat'
    DEFAULT_BETA=8.0/3.0
    DEFAULT_RHO=28.0
    DEFAULT_SIGMA=10.0

    def get_parser(self) -> argparse.ArgumentParser:

        parser = argparse.ArgumentParser(
            prog=os.path.basename(__file__),
            usage="%(prog)s [options]",
            description="",
            epilog=""
        )

        parser.add_argument("-b", "--beta" , type=float, default=self.DEFAULT_BETA, help=f"Default: {self.DEFAULT_BETA}.")
        parser.add_argument("-r", "--rho"  , type=float, default=self.DEFAULT_RHO, help=f"Default: {self.DEFAULT_RHO}.")
        parser.add_argument("-s", "--sigma", type=float, default=self.DEFAULT_SIGMA, help=f"Default: {self.DEFAULT_SIGMA}.")
        parser.add_argument("-ts", "--totalsteps", type=int, default=self.DEFAULT_TOTAL_STEPS, help=f"Default: {self.DEFAULT_TOTAL_STEPS}.")
        parser.add_argument("-ss", "--stepsize", type=float, default=self.DEFAULT_STEP_SIZE, help=f"Default: {self.DEFAULT_STEP_SIZE}.")
        parser.add_argument("-is", "--initialstate", type=float, nargs=3, default=self.DEFAULT_INITIALSTATE, help=f"Default: {self.DEFAULT_INITIALSTATE}.")
        parser.add_argument("-cm", "--colormap", type=str, default=self.DEFAULT_CMAP, help=f'Default: {self.DEFAULT_CMAP}.')

        return parser

class Attractor(ParserHandler):

    def __init__(self) -> None:

        super().__init__()

        self.beta = self.DEFAULT_BETA
        self.rho = self.DEFAULT_RHO
        self.sigma = self.DEFAULT_SIGMA

    def setup(self, beta: float, rho: float, sigma: float, initialState: list[float]) -> None:
        self.beta = beta
        self.rho = rho
        self.sigma = sigma
        print(f"\u03B2={beta}, \u03C1={rho}, \u03C3={sigma}, {initialState}")

    def lorenz(self, state: tuple[float, float, float], step: float) -> list[float]:
        x, y, z = state
        return [
            self.sigma * (-x + y),
            x * (self.rho - z) - y,
            x * y - self.beta * z
            ]

def main() -> None:

    try:
        attractor = Attractor()
        parser = attractor.get_parser()
        args = parser.parse_args()

        steps = np.arange(0.0, args.totalsteps*args.stepsize, args.stepsize)

        attractor.setup(
            beta = args.beta,
            rho = args.rho,
            sigma = args.sigma,
            initialState=args.initialstate
        )

        states0 = odeint(attractor.lorenz, args.initialstate, steps)
        states1 = odeint(attractor.lorenz, [x + random.uniform(-.5*x, .5*x) for x in args.initialstate], steps)
        points0 = states0.reshape(-1, 1, 3)
        points1 = states1.reshape(-1, 1, 3)
        segments0 = np. concatenate([points0[:-1], points0[1:]], axis=1)
        segments1 = np. concatenate([points1[:-1], points1[1:]], axis=1)

        colors0 = np.linspace(0, 1, len(segments0))
        colors1 = np.linspace(0, 1, len(segments1))

        lc0 = Line3DCollection(segments0, cmap=args.colormap, norm=plt.Normalize(0,1))
        lc1 = Line3DCollection(segments1, cmap=f"{args.colormap}_r", norm=plt.Normalize(0,1))
        lc0.set_array(colors0[:-1])
        lc1.set_array(colors1[:-1])
        lc0.set_linewidth(1)
        lc1.set_linewidth(1)

        fig = plt.figure()
        fig.patch.set_alpha(0.0)

        ax = fig.add_subplot(111, projection='3d')
        ax.set_axis_off()
        ax.set_facecolor((0, 0, 0, 0))
        ax.add_collection3d(lc0)
        ax.add_collection3d(lc1)

        plt.subplots_adjust(left=0, bottom=0, right=1, top=1)
        # plt.show()

        def _update(num):
            lc0.set_segments(segments0[:num])
            lc1.set_segments(segments1[:num])
            lc0.set_array(colors0[:num])
            lc1.set_array(colors1[:num])
            print(f"{100*num/len(segments0):.2f}% ({num}/{len(segments0)})", end="\r", flush=True)
            return lc0, lc1

        MAXTIME = 69
        NUMOFFRAMES = len(segments0)
        MAXINTERVAL = int(1000*MAXTIME/NUMOFFRAMES)
        anim = FuncAnimation(fig, _update, frames=NUMOFFRAMES, interval=MAXINTERVAL, blit=False)
        anim.save(f"{os.path.basename(__file__)}"[:-2]+"mp4", writer='ffmpeg', dpi=200)

    except Exception as e:
        print(f"An exception occured: {e}")

if __name__ == "__main__":
    main()
