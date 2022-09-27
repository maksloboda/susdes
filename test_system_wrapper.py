import pickle

import jenkins
import typing


CACHE_VERSION = 1


class JobData:
    fullname: str

    def __init__(self, fullname):
        self.fullname = fullname


class BuildData:
    raw_data: dict
    is_in_progress: bool

    def __init__(self, raw_data):
        self.raw_data = raw_data
        self.is_in_progress = raw_data["inProgress"]


class TestSystemWrapper:
    con: jenkins.Jenkins
    build_data_cache: typing.Dict
    cache_path: str

    def __init__(self, address: str, login: str, password: str, cache_path: str):
        self.con = jenkins.Jenkins(address, login, password)
        self.cache_path = cache_path
        self.build_data_cache = dict()
        self.load_cache()

    def get_homework_list(self) -> typing.List[JobData]:
        return [JobData(i["fullname"]) for i in self.con.get_jobs()]

    def get_builds(self, homework_name: str, reset_cache: bool = False) -> typing.List[BuildData]:
        if reset_cache:
            self.build_data_cache = dict()

        builds = self.con.get_job_info(homework_name, fetch_all_builds=True)["builds"]
        result = list(
            map(
                lambda x: self.get_build_info(homework_name, x),
                builds
            )
        )
        self.flush_cache()
        return result

    def load_cache(self):
        try:
            with open(self.cache_path, "rb") as f:
                content = f.read()
                obj = pickle.loads(content)
                if obj[0] == CACHE_VERSION:
                    self.build_data_cache = obj[1]
        except FileNotFoundError:
            pass

    def flush_cache(self):
        with open(self.cache_path, "wb") as f:
            f.write(pickle.dumps((CACHE_VERSION, self.build_data_cache)))

    def get_build_info(self, homework_name: str, build_metadata: dict):
        number = build_metadata['number']
        homework_cache = dict()
        if homework_name in self.build_data_cache:
            homework_cache = self.build_data_cache[homework_name]
        else:
            self.build_data_cache[homework_name] = homework_cache

        if number in homework_cache:
            return homework_cache[number]
        else:
            build_data_dict = self.con.get_build_info(homework_name, number)
            build_data = BuildData(build_data_dict)
            if not build_data.is_in_progress:
                homework_cache[number] = build_data
            return build_data

    def build_job(self, homework_name, params: dict):
        self.con.build_job(homework_name, params)
