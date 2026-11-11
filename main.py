import shlex

import click
import pyperclip

import feature
import storage
from logger import get_logger

logger = get_logger(__name__)

SENSITIVE_FLAGS = {"--password", "-p"}


def _redact(args):
    """Return the command arguments with password values masked for logging."""
    redacted = []
    hide_next = False

    for arg in args:
        if hide_next:
            redacted.append("***")
            hide_next = False
            continue
        if arg in SENSITIVE_FLAGS:
            redacted.append(arg)
            hide_next = True
            continue
        if arg.startswith("--password="):
            redacted.append("--password=***")
            continue
        redacted.append(arg)

    return redacted


@click.group()
def cli():
    logger.debug("cli group invoked")

@cli.command()
@click.option("--site", prompt=">Enter site name: ", type=str)
@click.option("--username", prompt=">Enter username", type=str)
@click.option("--password", prompt=">Enter password: ", type=str)
def add(site, username, password):
    username = username.strip()
    site = site.strip()
    password = password.strip()

    logger.info("add: saving entry site=%r username=%r", site, username)
    result = feature.add(site, username, password)
    if result:
        logger.info("add: entry saved site=%r", site)
        click.echo(">>added.")
    else:
        logger.warning("add: entry not saved site=%r", site)


@cli.command()
def List():
    logger.info("list: requested")
    feature.show_data()
    logger.info("list: displayed")


@cli.command()
@click.option("--id", prompt = ">Enter ID: ", type=str)
def reveal(id):
    id = int(id.strip())
    logger.info("reveal: copying entry id=%s", id)
    pyperclip.copy(feature.reveal(id))
    logger.info("reveal: entry id=%s copied to clipboard", id)
    print("password copy on your clipboard")


@cli.command()
@click.option('--id', prompt = ">Enter ID: ", type=str)
def remove(id):
    id = int(id.strip())
    logger.info("remove: deleting entry id=%s", id)
    if feature.remove(id):
        logger.info("remove: entry id=%s deleted", id)
        print('>removed.')
    else:
        logger.warning("remove: entry id=%s not deleted", id)


@cli.command()
def signup():
    logger.info("signup: requested")
    feature.signup()


@cli.command()
def login():
    logger.info("login: requested")
    feature.login()


def shell():
    logger.info("shell: application starting")
    print(" WELCOME ".center(100, '*'))
    cli(shlex.split('--help'), standalone_mode=False)
    
    while True:
        try:
            command = input(">>>").strip()
            args = shlex.split(command)

            if not args:
                logger.debug("shell: empty command ignored")
                continue

            logger.debug("shell: command=%r", _redact(args))

            if args[0] == "quit":
                logger.info("shell: quit requested")
                break
            if args[0] == "clear":
                logger.debug("shell: screen cleared")
                click.clear()
                continue

            cli(args, standalone_mode=False)
        except (EOFError, KeyboardInterrupt):
            logger.info("shell: input closed, exiting")
            break
        except Exception as error:
            logger.exception("shell: command failed: %s", error)
            print(f"Had Error: {error}")


if __name__ == "__main__":
    try:
        shell()
    except Exception:
        logger.exception("application crashed")
        raise
    finally:
        logger.info("shell: application stopped")
