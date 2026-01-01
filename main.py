import shlex
import click
import storage, feature
import pyperclip


@click.group()
def cli():
    pass


@cli.command()
@click.option("--site", prompt=">Enter site name: ", type=str)
@click.option("--username", prompt=">Enter username", type=str)
@click.option("--password", prompt=">Enter password: ", type=str)
def add(site, username, password):
    username = username.strip()
    site = site.strip()
    password = password.strip()

    result = feature.add(site, username, password)
    if result:
        click.echo(">>added.")


@cli.command()
def List():
    feature.show_data()


@cli.command()
@click.option("--id", prompt = ">Enter ID: ", type=str)
def reveal(id):
    id = int(id.strip())
    pyperclip.copy(feature.reveal(id))
    print("password copy on your clipboard")


@cli.command()
@click.option('--id', prompt = ">Enter ID: ", type=str)
def remove(id):
    id = int(id.strip())
    if feature.remove(id):
        print('>removed.')


def shell():
    print(" WELCOME ".center(100, '*'))
    cli(shlex.split('--help'), standalone_mode=False)
    
    while True:
        storage.check_db()
        storage.fix_id()
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
