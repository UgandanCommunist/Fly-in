from utils import Visualizer


def main() -> None:
    visuals = Visualizer()
    visuals.on_draw()
    visuals.run()


if __name__ == "__main__":
    main()
