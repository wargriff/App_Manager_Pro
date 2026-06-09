"""python -m app_manager"""

from app_manager.bootstrap import bootstrap
from app_manager.application import ApplicationWindow


def main():
    bootstrap()
    ApplicationWindow().run()


if __name__ == "__main__":
    main()
