import subprocess

import click
import os
import sys
import configparser

import jenkins

APP_NAME = "SusDesign"
CONF_NAME = "data.conf"
config_keys = ["jenkins_address", "jenkins_login", "jenkins_password", "student_name", "repository_url"]


def try_load_config() -> dict:
    config = load_data_from_config()
    if not config:
        click.echo("failed to load the config, try setup first", sys.stderr)
        sys.exit(1)
    return config

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
    data = try_load_config()
    if setting not in config_keys:
        click.echo("no such property", sys.stderr)
        sys.exit(1)
    data[setting] = value
    write_data_to_config(data)

@click.group()
def homework():
    pass

def get_jenkins_connection(data):
    con = jenkins.Jenkins(data["jenkins_address"], username=data["jenkins_login"], password=data["jenkins_password"])
    return con

@click.command("list")
def homework_list():
    data = try_load_config()
    con = get_jenkins_connection(data)
    jobs = [f"{idx + 1}. {job_data['fullname']}" for idx, job_data in enumerate(con.get_jobs())]
    click.echo("\n".join(jobs))


def is_build_by_current_student(data, build_info) -> bool:
    def find_value_where_key(where, key, desired):
        for idx, value in enumerate(where):
            if key in value and value[key] == desired:
                return value
        return None
    action_data = find_value_where_key(build_info["actions"], "_class", "hudson.model.ParametersAction")
    if not action_data:
        return False
    action_parameters = action_data.get("parameters")
    if not action_parameters:
        return False
    student_info = find_value_where_key(action_parameters, "name", "STUDENT_NAME")
    return student_info and student_info["value"] == data["student_name"]


def format_build(build_info):
    string = f"{build_info['displayName']}: {build_info['result']} { 'KEEP' if build_info['keepLog'] else 'DONT KEEP'}\n"
    if build_info['result'] == 'SUCCESS':
        if build_info['keepLog']:
            return click.style(string, fg="green")
        else:
            return click.style(string, fg="yellow")
    elif build_info['result'] == 'FAILURE':
        return click.style(string, fg="red")
    else:
        return click.style(string, fg="white")




@click.command("stat")
@click.argument("homework")
def homework_stat(homework):
    data = try_load_config()
    con = get_jenkins_connection(data)
    if all(map(lambda x: x["fullname"] != homework, con.get_jobs())):
        click.echo("no such homework", sys.stderr)
        sys.exit(1)
    builds = con.get_job_info(homework)["builds"]
    info = filter(
        lambda x: is_build_by_current_student(data, x),
        map(
            lambda x: con.get_build_info(homework, x['number']),
            builds
        )
    )

    click.echo_via_pager(
        map(
            format_build,
            info
        )
    )

@click.command("submit")
@click.argument("homework")
def homework_submit(homework):
    data = try_load_config()
    con = get_jenkins_connection(data)
    if all(map(lambda x: x["fullname"] != homework, con.get_jobs())):
        click.echo("no such homework", sys.stderr)
        sys.exit(1)
    completed = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True)
    current_commit = completed.stdout.strip().decode("utf-8")
    number = con.build_job(homework, {
        "STUDENT_NAME": data["student_name"],
        "GITHUB_CLONE_URL": data["repository_url"],
        "GIT_COMMIT_HASH": current_commit,
    })
    # This is not the display name sadly ;(
    # click.echo(number)


homework.add_command(homework_list)
homework.add_command(homework_stat)
homework.add_command(homework_submit)

cli.add_command(setup)
cli.add_command(homework)
cli.add_command(update)

if __name__ == "__main__":
    cli()
