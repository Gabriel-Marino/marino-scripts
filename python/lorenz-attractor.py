import argparse
import os

import matplotlib.pyplot as plt

from numpy import arange
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
    
    def lorenz(self, state: tuple[float, float, float], t: float) -> list[float]:
        x, y, z = state
        return [self.sigma * (-x + y), x * (self.rho - z) - y, x * y - self.beta * z]

class ParserHandler(Attractor):

    INITIALSTATE = [1.0, 1.0, 1.0]

    def get_parser(self) -> argparse.ArgumentParser:

        parser = argparse.ArgumentParser(
            prog=os.path.basename(__file__),
            usage="%(prog)s [options]",
            description="",
            epilog=""
        )

        parser.add_argument("--beta" , type=float, default=self.beta, help="")
        parser.add_argument("--rho"  , type=float, default=self.rho, help="")
        parser.add_argument("--sigma", type=float, default=self.sigma, help="")
        parser.add_argument("--initialstate", type=float, nargs=3, default=self.INITIALSTATE, help="")

        return parser


def main() -> None:
    try:
        parserHandler = ParserHandler()
        parser = parserHandler.get_parser()
        args = parser.parse_args()

        t = arange(0.0, 24.0, 0.01)

        attractor = Attractor()
        attractor.setup(
            beta = args.beta,
            rho = args.rho,
            sigma = args.sigma
        )

        states = odeint(attractor.lorenz, args.initialstate, t)

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.plot(states[:,0], states[:,1], states[:,2])
        plt.show()
    
    except Exception as e:
        print(f"An exception occured: {e}")

if __name__ == "__main__":
    main()
