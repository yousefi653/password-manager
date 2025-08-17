import shlex
import click
import storage, feature


@click.group()
def cli():
    pass


@cli.command()
@click.option("--site", prompt=">Enter site name: ", type=str)
@click.option("--username", prompt=">Enter username", type=str)
@click.option("--password", prompt=">Enter password: ", type=str)
def add(site, username, password):
    result = feature.add(site, username, password)
    if result:
        click.echo(">>added.")


@cli.command()
def List():
    feature.show_data()


@cli.command()
@click.option("--id", prompt = ">Enter ID: ", type=int)
def reveal(id):
    print(f"password: {feature.reveal(id)}")


@cli.command()
@click.option('--id', prompt = ">Enter ID: ", type=int)
def remove(id):
    if feature.remove(id):
        print('>removed.')


def shell():
    while True:
        storage.check_db()
        try:
            command = input(">>>").strip()
            args = shlex.split(command)

            if args[0] == "quit":
                break
            if args[0] == "clear":
                click.clear()
                continue

            cli(args, standalone_mode=False)
        except Exception as error:
            print(f"Had Error: {error}")


if __name__ == "__main__":
    shell()
