import click
import os
import sys
import configparser

APP_NAME = "SusDesign"
CONF_NAME = "data.conf"
config_keys = ["jenkins_address", "jenkins_login", "jenkins_password", "student_name", "repository_url"]


def load_data_from_config() -> dict:
    path = os.path.join(click.get_app_dir(APP_NAME), CONF_NAME)
    config = configparser.ConfigParser()
    try:
        config.read(path)
        values = {}
        for key in config_keys:
            values[key] = config["data"][key]
        return values
    except Exception as e:
        click.echo(f"read error: {e}", sys.stderr)
        return {}


# Tries to write data to the config
# returns true on success
def write_data_to_config(data) -> bool:
    app_dir = click.get_app_dir(APP_NAME)
    try:
        os.makedirs(app_dir)

    except FileExistsError:
        pass
    except PermissionError:
        click.echo("failed to create folders", sys.stderr)
        return False
    path = os.path.join(app_dir, CONF_NAME)
    config = configparser.ConfigParser()
    try:
        for key in config_keys:
            if key not in data:
                raise KeyError("missing data")
    except KeyError:
        click.echo("config data is not full", sys.stderr)
        return False

    config["data"] = data

    try:
        with open(path, "w") as f:
            config.write(f)
    except Exception as e:
        click.echo(f"write error: {e}", sys.stderr)
        return False

    return True


@click.group()
def cli():
    pass


# Sets all the data of the user
@click.command()
@click.option("--jenkins_address", prompt=True)
@click.option("--jenkins_login", prompt=True)
@click.option("--jenkins_password", prompt=True, hide_input=True)
@click.option("--student_name", prompt=True)
@click.option("--repository_url", prompt=True)
def setup(jenkins_address, jenkins_login, jenkins_password, student_name, repository_url):
    data = {
        i: j for i, j in
        zip(config_keys, [jenkins_address, jenkins_login, jenkins_password, student_name, repository_url])
    }
    if not write_data_to_config(data):
        click.echo("failed to save the data to the config", sys.stderr)
        sys.exit(1)
    click.echo("Saved")


@click.command()
@click.option("--setting")
@click.option("--value", prompt=True, hide_input=lambda x: x == "jenkins_password")
def update(setting, value):
    data = load_data_from_config()
    if not data:
        click.echo("failed to load the config, try setup first", sys.stderr)
    if setting not in config_keys:
        click.echo("no such property", sys.stderr)
        sys.exit(1)
    data[setting] = value
    write_data_to_config(data)


cli.add_command(setup)
cli.add_command(update)

if __name__ == "__main__":
    cli()
