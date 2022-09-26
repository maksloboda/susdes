import jenkins
import typing


class JobData:
    fullname: str

    def __init__(self, fullname):
        self.fullname = fullname


class TestSystemWrapper:
    con: jenkins.Jenkins

    def __init__(self, address, login, password):
        self.con = jenkins.Jenkins(address, login, password)

    def get_homework_list(self) -> typing.List[JobData]:
        return [JobData(i["fullname"]) for i in self.con.get_jobs()]
