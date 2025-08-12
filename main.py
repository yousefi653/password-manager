import shlex
import click


@click.group()
def cli():
    pass


def shell():
    while True:
        try:
            command = input(">>>").strip()
            args = shlex.split(command)

            if args[0] == "quit":
                break

            cli(*args, standalone_mode=False)
        except Exception as error:
            print(f"Had Error: {error}")


if __name__ == "__main__":
    shell()
